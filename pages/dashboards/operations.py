import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback
from db_utils import get_db_connection

dash.register_page(__name__, path="/operations", name="Operations Dashboard")

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

@callback(
    Output("total-issued-qty-display", "children"),
    [Input("ops-year-dropdown", "value"),
     Input("ops-month-dropdown", "value"),
     Input("ops-category-dropdown", "value")]
)
def display_total_issued_qty(selected_year, selected_month, selected_category):
    year = None if selected_year == "all" else selected_year
    month = None if selected_month == "all" else selected_month
    category = None if selected_category == "all" else selected_category
    df = get_consumption_rate_data(year, month, category)
    total = df["TotalIssuedQty"].sum() if not df.empty else 0
    return f"Total Issued Qty: {total:,}" if total else "No data available."

def get_section_requests_data(year=None, month=None, category=None, skus=None):
    conn = get_db_connection()
    params = []
    query = '''
        SELECT S.Section, I.Category, I.SKU, SUM(F.RequestedQty) AS TotalRequestedQty
        FROM Job_Request_Fact_Table F
        JOIN Item_Dimension I ON F.ItemKey = I.ItemKey
        JOIN Section_Dimension S ON F.SectionKey = S.SectionKey
        JOIN Date_Dimension D ON F.DateKey = D.DateKey
        WHERE 1=1
    '''
    if year:
        query += ' AND D.Year = ?'
        params.append(year)
    if month and month != "all":
        query += ' AND D.Month = ?'
        params.append(month)
    if category and category != "all":
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
    if skus and skus != ["all"]:
        sku_placeholders = ','.join(['?'] * len(skus))
        query += f' AND I.SKU IN ({sku_placeholders})'
        params.extend(skus)
    query += '''
        GROUP BY S.Section, I.Category, I.SKU
        ORDER BY TotalRequestedQty DESC
    '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
@callback(
    Output("section-sku-dropdown", "options"),
    Output("section-sku-dropdown", "value"),
    Output("section-sku-dropdown", "disabled"),
    [Input("section-category-dropdown", "value")]
)
def update_section_sku_dropdown(selected_category):
    conn = get_db_connection()
    if selected_category == "all":
        options = [{"label": "All SKUs", "value": "all"}]
        value = "all"
        disabled = True
    else:
        df = pd.read_sql_query("SELECT SKU FROM Item_Dimension WHERE LOWER(Category) = ?", conn, params=[selected_category])
        sku_list = sorted(set(df["SKU"].tolist()))
        options = [{"label": sku, "value": sku} for sku in sku_list]
        value = sku_list
        disabled = False
    conn.close()
    return options, value, disabled
@callback(
    Output("section-requests-chart", "figure"),
    [Input("section-year-dropdown", "value"),
     Input("section-month-dropdown", "value"),
     Input("section-category-dropdown", "value"),
     Input("section-sku-dropdown", "value")]
)
def update_section_requests_chart(selected_year, selected_month, selected_category, selected_skus):
    year = None if selected_year == "all" else selected_year
    month = None if selected_month == "all" else selected_month
    category = None if selected_category == "all" else selected_category
    if selected_category == "all":
        skus = ["all"]
    elif not selected_skus or selected_skus == []:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT SKU FROM Item_Dimension WHERE LOWER(Category) = ?", conn, params=[selected_category])
        skus = df["SKU"].tolist()
        conn.close()
    elif selected_skus == "all":
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT SKU FROM Item_Dimension WHERE LOWER(Category) = ?", conn, params=[selected_category])
        skus = df["SKU"].tolist()
        conn.close()
    else:
        skus = selected_skus if isinstance(selected_skus, list) else [selected_skus]
    df = get_section_requests_data(year, month, category, skus)
    if df.empty:
        fig = px.bar(title="No data available for selected filters")
    else:
        fig = px.bar(
            df,
            x="TotalRequestedQty",
            y="Section",
            color="SKU" if category and category != "all" else "Category",
            orientation="h",
            title="Section Requests by Amount",
            labels={"TotalRequestedQty": "Total Requested Qty"}
        )
        fig.update_yaxes(type="category")
    return fig

def get_consumption_rate_data(year=None, month=None, category=None):
    conn = get_db_connection()
    params = []
    if category and category != "all":
        query = '''
        SELECT
            I.SKU,
            I.Category,
            SUM(F.IssuedQty) AS TotalIssuedQty
        FROM Job_Request_Fact_Table F
        JOIN Item_Dimension I ON F.ItemKey = I.ItemKey
        JOIN Date_Dimension D ON F.DateKey = D.DateKey
        WHERE 1=1
        '''
    else:
        query = '''
        SELECT
            I.Category,
            SUM(F.IssuedQty) AS TotalIssuedQty
        FROM Job_Request_Fact_Table F
        JOIN Item_Dimension I ON F.ItemKey = I.ItemKey
        JOIN Date_Dimension D ON F.DateKey = D.DateKey
        WHERE 1=1
        '''
    if year:
        query += ' AND D.Year = ?'
        params.append(year)
    if month and month != "all":
        query += ' AND D.Month = ?'
        params.append(month)
    if category and category != "all":
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
        query += '''
        GROUP BY I.SKU, I.Category
        ORDER BY TotalIssuedQty 
        '''
    else:
        query += '''
        GROUP BY I.Category
        ORDER BY TotalIssuedQty 
        '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_ranked_sku_data(year=None, month=None, category=None):
    conn = get_db_connection()
    params = []
    if category and category != "all":
        query = '''
        SELECT
            I.Category,
            I.SKU,
            SUM(F.RequestedQty) AS TotalRequestedQty,
            ROW_NUMBER() OVER(PARTITION BY I.Category ORDER BY SUM(F.RequestedQty) DESC) AS CategoryRank
        FROM Job_Request_Fact_Table F
        JOIN Item_Dimension I ON F.ItemKey = I.ItemKey
        JOIN Date_Dimension D ON F.DateKey = D.DateKey
        WHERE 1=1
        '''
        if year:
            query += ' AND D.Year = ?'
            params.append(year)
        if month and month != "all":
            query += ' AND D.Month = ?'
            params.append(month)
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
        query += '''
        GROUP BY I.Category, I.SKU
        ORDER BY CategoryRank
        '''
    else:
        query = '''
        SELECT
            I.Category,
            I.SKU,
            SUM(F.RequestedQty) AS TotalRequestedQty,
            ROW_NUMBER() OVER(ORDER BY SUM(F.RequestedQty) DESC) AS OverallRank
        FROM Job_Request_Fact_Table F
        JOIN Item_Dimension I ON F.ItemKey = I.ItemKey
        JOIN Date_Dimension D ON F.DateKey = D.DateKey
        WHERE 1=1
        '''
        if year:
            query += ' AND D.Year = ?'
            params.append(year)
        if month and month != "all":
            query += ' AND D.Month = ?'
            params.append(month)
        query += '''
        GROUP BY I.Category, I.SKU
        ORDER BY OverallRank
        LIMIT 5
        '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

layout = html.Div([
    header,
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("Dashboard", className="fw-bold mb-4 d-inline-block mb-0"),
            ], md=6),
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("Inventory", href="/inventory", color="primary", disabled=False),
                    dbc.Button("Forecasting", href="/forecasting", color="primary", disabled=False),
                    dbc.Button("Operations", href="/operations", color="primary", disabled=True),
                    dbc.Button("Planning", href="/planning", color="primary", disabled=False),
                ], size="md"),
            ], md=6, className="d-flex align-items-center justify-content-end"),
        ], className="mb-2", style={"paddingTop": "32px"}),
        dbc.Card(
            dbc.CardBody([
                html.H4("Operations", className="mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Filter by Year"),
                        dcc.Dropdown(
                            id="ops-year-dropdown",
                            options=[{"label": "All Years", "value": "all"}] + [{"label": str(x), "value": x} for x in [2019, 2020, 2021, 2022, 2023]],
                            value="all",
                            placeholder="Select Year"
                        ),
                    ], md=4),
                    dbc.Col([
                        html.Label("Filter by Month"),
                        dcc.Dropdown(
                            id="ops-month-dropdown",
                            options=[{"label": "All Months", "value": "all"}] + [
                                {"label": name, "value": num} for num, name in enumerate([
                                    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
                                ], 1)
                            ],
                            value="all",
                            multi=False,
                            placeholder="Select Month"
                        ),
                    ], md=4),
                    dbc.Col([
                        html.Label("Filter by Category"),
                        dcc.Dropdown(
                            id="ops-category-dropdown",
                            options=[{"label": "All Categories", "value": "all"}] + [{"label": x, "value": x.lower()} for x in ["Buildings", "Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                            value="all",
                            placeholder="Select Category"
                        ),
                    ], md=4),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(id="consumption-rate-chart", style={"height": "400px"}),
                                html.Div(id="total-issued-qty-display", style={"fontSize": "1rm", "marginTop": "12px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "minHeight": "480px"}),
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(id="sku-ranking-chart", style={"height": "400px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)", "minHeight": "480px"}),
                    ], md=6),
                ]),
            ])
        ),
        dbc.Card([
            dbc.CardBody([
                html.H4("Section Requests by Amount", className="mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Year"),
                        dcc.Dropdown(
                            id="section-year-dropdown",
                            options=[{"label": "All Years", "value": "all"}] + [{"label": str(x), "value": x} for x in [2019, 2020, 2021, 2022, 2023]],
                            value="all",
                            placeholder="Select Year"
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("Month"),
                        dcc.Dropdown(
                            id="section-month-dropdown",
                            options=[{"label": "All Months", "value": "all"}] + [
                                {"label": name, "value": num} for num, name in enumerate([
                                    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
                                ], 1)
                            ],
                            value="all",
                            multi=False,
                            placeholder="Select Month"
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("Category"),
                        dcc.Dropdown(
                            id="section-category-dropdown",
                            options=[{"label": "All Categories", "value": "all"}] + [{"label": x, "value": x.lower()} for x in ["Buildings", "Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                            value="all",
                            placeholder="Select Category"
                        ),
                    ], md=3),
                    dbc.Col([
                        html.Label("SKU"),
                        dcc.Dropdown(
                            id="section-sku-dropdown",
                            options=[{"label": "All SKUs", "value": "all"}],
                            value="all",
                            multi=True,
                            placeholder="Select SKU(s)",
                            disabled=True
                        ),
                    ], md=3),
                ], className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(id="section-requests-chart", style={"height": "400px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                    ], md=12),
                ]),
            ])
        ])
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px", "backgroundColor": "#eaeaea"})
    ], style={"backgroundColor": "#eaeaea", "minHeight": "100vh"})

@callback(
	Output("consumption-rate-chart", "figure"),
	Output("sku-ranking-chart", "figure"),
	[Input("ops-year-dropdown", "value"),
	 Input("ops-month-dropdown", "value"),
	 Input("ops-category-dropdown", "value")]
)

def update_operations_charts(selected_year, selected_month, selected_category):
    year = None if selected_year == "all" else selected_year
    month = None if selected_month == "all" else selected_month
    category = None if selected_category == "all" else selected_category
    df = get_consumption_rate_data(year, month, category)
    if category:
        fig1 = px.pie(
            df,
            names="SKU",
            values="TotalIssuedQty",
            title=f"Material Consumption Rate by SKU in {category.capitalize()}",
        )
    else:
        fig1 = px.pie(
            df,
            names="Category",
            values="TotalIssuedQty",
            title="Material Consumption Rate by Category",
        )
    df2 = get_ranked_sku_data(year, month, category)
    if category:
	    fig2 = px.bar(
			df2,
			x="TotalRequestedQty",
			y="SKU",
			orientation="h",
			title=f"SKU Demand Ranking in {category.capitalize()}",
			text="TotalRequestedQty",
			labels={"TotalRequestedQty": "Total Requested Qty"}
		)
	    fig2.update_yaxes(type="category")
    else:
	    fig2 = px.bar(
			df2,
			x="TotalRequestedQty",
			y="SKU",
			orientation="h",
			title="Top 5 SKUs Overall by Demand",
			text="TotalRequestedQty",
			labels={"TotalRequestedQty": "Total Requested Qty"}
		)
	    fig2.update_yaxes(type="category")
    return fig1, fig2
