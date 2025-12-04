import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback
from db_utils import get_db_connection

dash.register_page(__name__, path="/planning", name="Planning Dashboard")

def get_stockout_risk_data(year=None, category=None):
    conn = get_db_connection()
    params = []
    if category and category != "all":
        query = '''
        SELECT
            i.SKU,
            i.Category,
            COUNT(*) AS StockoutEvents
        FROM Job_Request_Fact_Table f
        JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE f.IsStockout = 1
        '''
        if year:
            query += ' AND d.Year = ?'
            params.append(year)
        query += ' AND LOWER(i.Category) = ?'
        params.append(category.lower())
        query += '''
        GROUP BY i.SKU, i.Category
        ORDER BY StockoutEvents DESC
        '''
    else:
        query = '''
        SELECT
            i.Category,
            COUNT(*) AS StockoutEvents
        FROM Job_Request_Fact_Table f
        JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE f.IsStockout = 1
        '''
        if year:
            query += ' AND d.Year = ?'
            params.append(year)
        query += '''
        GROUP BY i.Category
        ORDER BY StockoutEvents DESC
        '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_top3_categories(year=None):
    conn = get_db_connection()
    params = []
    query = '''
    SELECT
        i.Category,
        COUNT(*) AS StockoutEvents
    FROM Job_Request_Fact_Table f
    JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
    JOIN Date_Dimension d ON f.DateKey = d.DateKey
    WHERE f.IsStockout = 1
    '''
    if year:
        query += ' AND d.Year = ?'
        params.append(year)
    query += '''
    GROUP BY i.Category
    ORDER BY StockoutEvents DESC
    LIMIT 5
    '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_stockout_sku_pie(year=None, category=None):
    conn = get_db_connection()
    params = []
    query = '''
    SELECT
        i.SKU,
        COUNT(*) AS StockoutEvents
    FROM Job_Request_Fact_Table f
    JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
    JOIN Date_Dimension d ON f.DateKey = d.DateKey
    WHERE f.IsStockout = 1
    '''
    if year:
        query += ' AND d.Year = ?'
        params.append(year)
    if category:
        query += ' AND LOWER(i.Category) = ?'
        params.append(category.lower())
    query += '''
    GROUP BY i.SKU
    ORDER BY StockoutEvents DESC
    '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            html.Div([
                html.Img(src="/assets/upmo.png", height="40px", style={"marginRight": "12px"}),
                html.Span("UPMO Intelligence", className="fw-bold fs-3")
            ], style={"display": "flex", "alignItems": "center"})
        ),

        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("About", href="/about")),
        ], className="ms-auto")
    ]),
    color="primary",
    dark=True,
    className="mb-4",
    style={"position": "sticky", "top": "0", "zIndex": "1000"}
)

layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Dashboard", className="fw-bold mb-4 d-inline-block mb-0"),
            ], md=6),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("Inventory", href="/inventory", color="primary", disabled=dash.page_registry[__name__]["path"]=="/inventory"),
                    dbc.Button("Forecasting", href="/forecasting", color="primary", disabled=dash.page_registry[__name__]["path"]=="/forecasting"),
                    dbc.Button("Operations", href="/operations", color="primary", disabled=dash.page_registry[__name__]["path"]=="/operations"),
                    dbc.Button("Planning", href="/planning", color="primary", disabled=dash.page_registry[__name__]["path"]=="/planning"),
                ], size="md"),
            ], md=6, className="d-flex align-items-center justify-content-end"),
        ], className="mb-2", style={"paddingTop": "32px"}),
        dbc.Card([
            dbc.CardBody([
                html.H4("Stockout Risk by Category & SKU", className="mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Filter by Year"),
                        dcc.Dropdown(
                            id="planning-year-dropdown",
                            options=[{"label": "All Years", "value": "all"}] + [{"label": str(x), "value": x} for x in [2019, 2020, 2021, 2022, 2023]],
                            value="all",
                            placeholder="Select Year"
                        ),
                    ], md=6),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(id="top3-category-bar", style={"height": "600px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "height": "100%"}),
                    ], md=7),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5(id="pie-title-1", style={"marginBottom": "8px"}),
                                dcc.Graph(id="sku-pie-1", style={"height": "260px", "minHeight": "260px", "marginBottom": "-16px"})
                            ], style={"padding": "12px 8px 0 8px"})
                        ], style={"borderTop": "3px solid #eaeaea", "borderRight": "3px solid #eaeaea", "borderBottom": "3px solid #eaeaea", "borderLeft": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "marginBottom": "32px", "minHeight": "260px"}),
                        html.Div(style={"height": "16px"}),
                        dbc.Card([
                            dbc.CardBody([
                                html.H5(id="pie-title-2", style={"marginBottom": "8px"}),
                                dcc.Graph(id="sku-pie-2", style={"height": "260px", "minHeight": "260px", "marginBottom": "-16px"})
                            ], style={"padding": "12px 8px 0 8px"})
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "marginBottom": "32px", "minHeight": "260px"}),
                    ], md=5),
                ]),
            ])
        ])
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px", "backgroundColor": "#eaeaea"}),
    html.Footer([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div("UPLB University Planning and Maintenance Office", className="fw-bold mb-1"),
                        html.Div("UPMO Bldg, Rambutan Road,", className="mb-0"),
                        html.Div("University of the Philippines Los Baños", className="mb-0"),
                        html.Div("Batong Malake, Los Baños, Philippines 4031", className="mb-2"),
                        html.Div([
                            html.Span([
                                html.I(className="bi bi-telephone-fill me-2"),
                                "0917 882 2479"
                            ], style={"marginRight": "24px"}),
                            html.Span([
                                html.I(className="bi bi-envelope-fill me-2"),
                                "upmo.uplb@up.edu.ph"
                            ])
                        ], style={"display": "flex", "alignItems": "center"})
                    ], style={"color": "#fff", "fontSize": "1rem"})
                ], md=8),
                dbc.Col([
                    html.Div([
                        html.Img(src="/assets/UPLB.png", height="120px", style={"marginRight": "16px"}),
                        html.Img(src="/assets/upmo.png", height="120px"),
                    ], style={"display": "flex", "justifyContent": "flex-end", "alignItems": "center", "height": "100%"})
                ], md=4)
            ], className="py-4")
        ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px"})
    ], style={"backgroundColor": "#00563F", "marginTop": "40px", "borderTop": "4px solid #eaeaea", "paddingLeft": "64px", "paddingRight": "64px"})
    ], style={"backgroundColor": "#eaeaea", "minHeight": "100vh"})

@callback(
    Output("top3-category-bar", "figure"),
    Output("pie-title-1", "children"), Output("sku-pie-1", "figure"),
    Output("pie-title-2", "children"), Output("sku-pie-2", "figure"),
    [Input("planning-year-dropdown", "value")]
)
def update_planning_charts(selected_year):
    year = None if selected_year == "all" or selected_year is None else selected_year
    cat_df = get_top3_categories(year)
    bar_fig = px.bar(
        cat_df,
        x="Category",
        y="StockoutEvents",
        title=f"Top Categories with Highest Stockout Risk ({selected_year if selected_year != 'all' else 'All Years'})",
        labels={"StockoutEvents": "Stockout Events", "Category": "Category"},
        color_discrete_sequence=["#8D1436"]
    )
    bar_fig.update_xaxes(type="category")
    pie_titles = []
    pie_figs = []
    for i in range(3):
        if i < len(cat_df):
            cat = cat_df.iloc[i]["Category"]
            pie_titles.append(f"SKU Stockout Distribution for {cat}")
            sku_df = get_stockout_sku_pie(year, cat)
            pie_figs.append(px.pie(sku_df, names="SKU", values="StockoutEvents", title=None))
        else:
            pie_titles.append("")
            pie_figs.append({"data": [], "layout": {}})
    return bar_fig, pie_titles[0], pie_figs[0], pie_titles[1], pie_figs[1]
