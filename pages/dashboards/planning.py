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

# ---------------- HEADER ---------------- #
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
    className="mb-4"
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
        dbc.Card(
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
                        dcc.Graph(id="top3-category-bar", style={"height": "400px"})
                    ], md=12),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H5(id="pie-title-1"),
                        dcc.Graph(id="sku-pie-1", style={"height": "350px", "minHeight": "350px"})
                    ], md=4),
                    dbc.Col([
                        html.H5(id="pie-title-2"),
                        dcc.Graph(id="sku-pie-2", style={"height": "350px", "minHeight": "350px"})
                    ], md=4),
                    dbc.Col([
                        html.H5(id="pie-title-3"),
                        dcc.Graph(id="sku-pie-3", style={"height": "350px", "minHeight": "350px"})
                    ], md=4),
                ]),
            ])
        )
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px", "backgroundColor": "#eaeaea"})
    ], style={"backgroundColor": "#eaeaea", "minHeight": "100vh"})

@callback(
    Output("top3-category-bar", "figure"),
    Output("pie-title-1", "children"), Output("sku-pie-1", "figure"),
    Output("pie-title-2", "children"), Output("sku-pie-2", "figure"),
    Output("pie-title-3", "children"), Output("sku-pie-3", "figure"),
    [Input("planning-year-dropdown", "value")]
)
def update_planning_charts(selected_year):
    year = None if selected_year == "all" or selected_year is None else selected_year
    cat_df = get_top3_categories(year)
    bar_fig = px.bar(
        cat_df,
        x="StockoutEvents",
        y="Category",
        orientation="h",
        title=f"Top 3 Categories with Highest Stockout Risk ({selected_year if selected_year != 'all' else 'All Years'})",
        labels={"StockoutEvents": "Stockout Events"}
    )
    bar_fig.update_yaxes(type="category")
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
    return bar_fig, pie_titles[0], pie_figs[0], pie_titles[1], pie_figs[1], pie_titles[2], pie_figs[2]
