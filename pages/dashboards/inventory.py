import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from db_utils import get_db_connection, import_csvs_to_sqlite
import plotly.express as px
from dash import Input, Output, callback
import plotly.graph_objects as go

dash.register_page(__name__, path="/inventory", name="Inventory Dashboard")

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

def get_inventory_metrics(year=None, category=None):
    conn = get_db_connection()
    params = []
    sku_query = '''
        SELECT COUNT(DISTINCT i.SKU) AS total_skus
        FROM Item_Dimension i
        JOIN Job_Request_Fact_Table f ON i.ItemKey = f.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE 1=1
    '''
    if year and "all" not in year:
        sku_query += f" AND d.Year IN ({', '.join(['?' for _ in year])})"
        params.extend(year)
    if category and "all" not in category:
        sku_query += f" AND LOWER(i.Category) IN ({', '.join(['?' for _ in category])})"
        params.extend([c.lower() for c in category])
    sku_df = pd.read_sql_query(sku_query, conn, params=params)
    total_skus = int(sku_df["total_skus"].iloc[0]) if not sku_df.empty else 0

    stock_query = '''
        SELECT SUM(f.StockOnHand) AS total_stock
        FROM Job_Request_Fact_Table f
        JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE 1=1
    '''
    stock_params = []
    if year and "all" not in year:
        stock_query += f" AND d.Year IN ({', '.join(['?' for _ in year])})"
        stock_params.extend(year)
    if category and "all" not in category:
        stock_query += f" AND LOWER(i.Category) IN ({', '.join(['?' for _ in category])})"
        stock_params.extend([c.lower() for c in category])
    stock_df = pd.read_sql_query(stock_query, conn, params=stock_params)
    total_stock = int(stock_df["total_stock"].iloc[0]) if not stock_df.empty and pd.notnull(stock_df["total_stock"].iloc[0]) else 0

    stockout_query = '''
        SELECT COUNT(*) AS total_stockouts
        FROM Job_Request_Fact_Table f
        JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE f.RequestedQty > f.StockOnHand
    '''
    stockout_params = []
    if year and "all" not in year:
        stockout_query += f" AND d.Year IN ({', '.join(['?' for _ in year])})"
        stockout_params.extend(year)
    if category and "all" not in category:
        stockout_query += f" AND LOWER(i.Category) IN ({', '.join(['?' for _ in category])})"
        stockout_params.extend([c.lower() for c in category])
    stockout_df = pd.read_sql_query(stockout_query, conn, params=stockout_params)
    total_stockouts = int(stockout_df["total_stockouts"].iloc[0]) if not stockout_df.empty else 0

    obsolete_query = '''
        SELECT COUNT(DISTINCT i.SKU) AS total_obsoletes
        FROM Item_Dimension i
        JOIN Job_Request_Fact_Table f ON i.ItemKey = f.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE i.ObsoleteFlag = 1
    '''
    obsolete_params = []
    if year and "all" not in year:
        obsolete_query += f" AND d.Year IN ({', '.join(['?' for _ in year])})"
        obsolete_params.extend(year)
    if category and "all" not in category:
        obsolete_query += f" AND LOWER(i.Category) IN ({', '.join(['?' for _ in category])})"
        obsolete_params.extend([c.lower() for c in category])
    obsolete_df = pd.read_sql_query(obsolete_query, conn, params=obsolete_params)
    total_obsoletes = int(obsolete_df["total_obsoletes"].iloc[0]) if not obsolete_df.empty else 0

    conn.close()
    return total_skus, total_stock, total_stockouts, total_obsoletes

SQL_QUERY = '''
SELECT
    i.ItemKey,
    i.SKU,
    i.Category,
    SUM(
        CASE
            WHEN i.ObsoleteFlag = 1 
            OR f.RequestedQty > f.StockOnHand THEN 1
            ELSE 0
        END
    ) AS InventoryFailureFrequency
FROM
    Job_Request_Fact_Table f
JOIN
    Item_Dimension i ON f.ItemKey = i.ItemKey
GROUP BY
    i.SKU, i.Category, i.ItemKey
ORDER BY
    InventoryFailureFrequency DESC
'''

def get_inventory_failure_data():
    conn = get_db_connection()
    df = pd.read_sql_query(SQL_QUERY, conn)
    conn.close()
    return df

inv_df = get_inventory_failure_data()

def get_forecasted_demand_data(year=None, category=None):
    conn = get_db_connection()
    params = []
    if category:
        query = '''
        WITH ForecastedDemand AS (
            SELECT
                I.Category,
                I.SKU,
                SUM(J.ForecastQty) AS TotalForecastedQty
            FROM
                Job_Request_Fact_Table AS J
            JOIN
                Item_Dimension AS I ON J.ItemKey = I.ItemKey
            JOIN
                Date_Dimension D ON J.DateKey = D.DateKey
            WHERE 1=1
        '''
        if year:
            query += ' AND D.Year = ?'
            params.append(year)
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
        query += '''
            GROUP BY I.Category, I.SKU
        )
        SELECT * FROM (
            SELECT
                Category,
                SKU,
                TotalForecastedQty,
                ROW_NUMBER() OVER(PARTITION BY Category ORDER BY TotalForecastedQty DESC) AS CategoryRank,
                ROW_NUMBER() OVER(ORDER BY TotalForecastedQty DESC) AS OverallRank
            FROM ForecastedDemand
        )
        WHERE CategoryRank <= 4
        ORDER BY OverallRank
        '''
    else:
        query = '''
        WITH ForecastedDemand AS (
            SELECT
                I.Category,
                I.SKU,
                SUM(J.ForecastQty) AS TotalForecastedQty
            FROM
                Job_Request_Fact_Table AS J
            JOIN
                Item_Dimension AS I ON J.ItemKey = I.ItemKey
            JOIN
                Date_Dimension D ON J.DateKey = D.DateKey
            WHERE 1=1
        '''
        if year:
            query += ' AND D.Year = ?'
            params.append(year)
        query += '''
            GROUP BY I.Category, I.SKU
        )
        SELECT * FROM (
            SELECT
                Category,
                SKU,
                TotalForecastedQty,
                ROW_NUMBER() OVER(PARTITION BY Category ORDER BY TotalForecastedQty DESC) AS CategoryRank,
                ROW_NUMBER() OVER(ORDER BY TotalForecastedQty DESC) AS OverallRank
            FROM ForecastedDemand
        )
        WHERE OverallRank <= 5
        ORDER BY OverallRank
        '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_filtered_inventory_failure_data(year=None, category=None):
    conn = get_db_connection()
    query = '''
    SELECT
        i.ItemKey,
        i.SKU,
        i.Category,
        d.Year,
        SUM(
            CASE
                WHEN i.ObsoleteFlag = 1 
                OR f.RequestedQty > f.StockOnHand THEN 1
                ELSE 0
            END
        ) AS InventoryFailureFrequency
    FROM
        Job_Request_Fact_Table f
    JOIN
        Item_Dimension i ON f.ItemKey = i.ItemKey
    JOIN
        Date_Dimension d ON f.DateKey = d.DateKey
    WHERE 1=1
    '''
    params = []
    if year and "all" not in year:
        query += f" AND d.Year IN ({', '.join(['?' for _ in year])})"
        params.extend(year)
    if category and "all" not in category:
        query += f" AND LOWER(i.Category) IN ({', '.join(['?' for _ in category])})"
        params.extend([c.lower() for c in category])
    query += '''
    GROUP BY i.SKU, i.Category
    ORDER BY InventoryFailureFrequency DESC
    LIMIT 10
    '''
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

initial_df = get_filtered_inventory_failure_data()
bar_fig = px.bar(
    initial_df,
    x='InventoryFailureFrequency',
    y='SKU',
    color='Category',
    orientation='h',
    title='Overstocking or Obselescence Frequency by SKU and Category',
    labels={'InventoryFailureFrequency': 'Failure Frequency'}
)

initial_forecast_df = get_forecasted_demand_data()
forecast_fig = px.bar(
    initial_forecast_df,
    x='TotalForecastedQty',
    y='SKU',
    color='Category',
    orientation='h',
    title='Forecasted Demand by SKU and Category',
    labels={'TotalForecastedQty': 'Forecasted Qty'}
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
                    dbc.Button("Inventory", href="/inventory", color="primary", disabled=True),
                    dbc.Button("Forecasting", href="/forecasting", color="primary", disabled=False),
                    dbc.Button("Operations", href="/operations", color="primary", disabled=False),
                    dbc.Button("Planning", href="/planning", color="primary", disabled=False),
                ], size="md"),
            ], md=6, className="d-flex align-items-center justify-content-end"),
        ], className="mb-2", style={"paddingTop": "32px"}),
        dbc.Card(
            dbc.CardBody([
                html.H4("Inventory", className="mt-4"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Filter by Year"),
                        dbc.InputGroup([
                            dcc.Dropdown(
                                id="year-dropdown",
                                options=[{"label": "All Years", "value": "all"}] + [{"label": x, "value": x} for x in [2019, 2020, 2021, 2022, 2023]],
                                value=["all"],
                                multi=True,
                                placeholder="Select Year",
                                style={"width": "100%"}
                            ),
                            dbc.Button("Reset", id="reset-year-btn", color="secondary", size="sm", style={"minWidth": "70px"}),
                        ], className="mb-2", style={"display": "flex", "flexWrap": "nowrap"}),
                    ], md=6),
                    dbc.Col([
                        html.Label("Filter by Category"),
                        dbc.InputGroup([
                            dcc.Dropdown(
                                id="category-dropdown",
                                options=[{"label": "All Categories", "value": "all"}] + [{"label": x, "value": x.lower()} for x in ["Buildings", "Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                                value=["all"],
                                multi=True,
                                placeholder="Select Category",
                                style={"width": "100%"}
                            ),
                            dbc.Button("Reset", id="reset-category-btn", color="secondary", size="sm", style={"minWidth": "70px"}),
                        ], className="mb-2", style={"display": "flex", "flexWrap": "nowrap"}),
                    ], md=6),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Unique SKUs", className="card-title text-muted"),
                            html.H3(id="metric-total-skus", className="card-text fw-bold mb-0"),
                        ])
                    ], className="shadow-sm"), md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Stock (All Items)", className="card-title text-muted"),
                            html.H3(id="metric-total-stock", className="card-text fw-bold mb-0"),
                        ])
                    ], className="shadow-sm"), md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Stockouts", className="card-title text-muted"),
                            html.H3(id="metric-total-stockouts", className="card-text fw-bold mb-0"),
                        ])
                    ], className="shadow-sm"), md=3),
                    dbc.Col(dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Obsoletes", className="card-title text-muted"),
                            html.H3(id="metric-total-obsoletes", className="card-text fw-bold mb-0"),
                        ])
                    ], className="shadow-sm"), md=3),
                ], className="mb-4"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Inventory Overstocking or Obselescence Frequency", className="mt-4"),
                                dcc.Graph(id="inventory-bar-chart", figure=bar_fig, style={"height": "400px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Forecasted Demand", className="mt-4"),
                                dcc.Graph(id="forecasted-demand-chart", figure=forecast_fig, style={"height": "400px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                    ], md=6),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Total Stock per Month & Obsolete vs Active Items", className="mt-4"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Year"),
                                        dcc.Dropdown(
                                            id="chart-year-dropdown",
                                            options=[{"label": x, "value": x} for x in [2019, 2020, 2021, 2022, 2023]],
                                            value=2023,
                                            multi=False,
                                            style={"marginBottom": "8px"}
                                        ),
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("Category"),
                                        dcc.Dropdown(
                                            id="chart-category-dropdown",
                                            options=[{"label": x, "value": x.lower()} for x in ["Buildings", "Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                                            value="buildings",
                                            multi=False,
                                            style={"marginBottom": "8px"}
                                        ),
                                    ], md=6),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                dcc.Graph(id="stock-line-chart", style={"height": "400px"})
                                            ])
                                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                                    ], md=6),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                dcc.Graph(id="obsolete-pie-chart", style={"height": "400px"})
                                            ])
                                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                                    ], md=6),
                                ])
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                    ], width=12),
                ])
            ])
        )
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
    Output("stock-line-chart", "figure"),
    Output("obsolete-pie-chart", "figure"),
    [Input("chart-year-dropdown", "value"), Input("chart-category-dropdown", "value")]
)
def update_line_and_pie_chart(chart_year, chart_category):
    year_val = chart_year if chart_year else 2023
    cat_val = chart_category if chart_category else "buildings"
    conn = get_db_connection()
    line_query = '''
        SELECT d.Month, SUM(f.StockOnHand) AS total_stock
        FROM Job_Request_Fact_Table f
        JOIN Item_Dimension i ON f.ItemKey = i.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE d.Year = ? AND LOWER(i.Category) = ?
        GROUP BY d.Month
        ORDER BY d.Month
    '''
    line_df = pd.read_sql_query(line_query, conn, params=[year_val, cat_val])
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_map = {i+1: m for i, m in enumerate(months)}
    line_df["MonthName"] = line_df["Month"].map(month_map)
    all_months_df = pd.DataFrame({"Month": range(1,13), "MonthName": months})
    line_df = pd.merge(all_months_df, line_df, on=["Month", "MonthName"], how="left").fillna({"total_stock": 0})
    line_fig = px.line(line_df, x="MonthName", y="total_stock", title=f"Total Stock per Month in {year_val} ({cat_val.title()})", markers=True, labels={"total_stock": "Total Stock", "MonthName": "Month"})
    pie_query = '''
        SELECT i.ObsoleteFlag, COUNT(DISTINCT i.SKU) AS count
        FROM Item_Dimension i
        JOIN Job_Request_Fact_Table f ON i.ItemKey = f.ItemKey
        JOIN Date_Dimension d ON f.DateKey = d.DateKey
        WHERE d.Year = ? AND LOWER(i.Category) = ?
        GROUP BY i.ObsoleteFlag
    '''
    pie_df = pd.read_sql_query(pie_query, conn, params=[year_val, cat_val])
    conn.close()
    pie_labels = ["Active", "Obsolete"]
    pie_counts = [0, 0]
    for _, row in pie_df.iterrows():
        if row["ObsoleteFlag"] == 1:
            pie_counts[1] = row["count"]
        else:
            pie_counts[0] = row["count"]
    pie_fig = go.Figure(data=[go.Pie(labels=pie_labels, values=pie_counts, hole=0.4)])
    pie_fig.update_layout(title=f"Obsolete vs Active Items in {year_val} ({cat_val.title()})")
    return line_fig, pie_fig

@callback(
    Output("inventory-bar-chart", "figure"),
    Output("forecasted-demand-chart", "figure"),
    [Input("year-dropdown", "value"), Input("category-dropdown", "value")]
)
def update_charts(selected_year, selected_category):
    year_options = [2019, 2020, 2021, 2022, 2023]
    year = selected_year if isinstance(selected_year, list) else [selected_year]
    category = selected_category if isinstance(selected_category, list) else [selected_category]
    if sorted([int(y) for y in year if y != "all" and y is not None]) == year_options:
        year = ["all"]
    if not year or year == []:
        year = ["all"]
    if not category or category == []:
        category = ["all"]
    df_failure = get_filtered_inventory_failure_data(year, category)
    forecast_years = None if "all" in year else year
    forecast_categories = None if "all" in category else category
    combined_forecast_df = pd.DataFrame()
    if forecast_years is None and forecast_categories is None:
        combined_forecast_df = get_forecasted_demand_data()
    else:
        if forecast_years is None:
            forecast_years = [None]
        if forecast_categories is None:
            forecast_categories = [None]
        for y in forecast_years:
            for c in forecast_categories:
                df = get_forecasted_demand_data(y, c)
                combined_forecast_df = pd.concat([combined_forecast_df, df], ignore_index=True)
        if not combined_forecast_df.empty:
            combined_forecast_df = combined_forecast_df.groupby(["SKU", "Category"], as_index=False)["TotalForecastedQty"].sum()
            combined_forecast_df = combined_forecast_df.sort_values("TotalForecastedQty", ascending=False).head(5)
    fig_failure = px.bar(
        df_failure,
        x='InventoryFailureFrequency',
        y='SKU',
        color='Category',
        orientation='h',
        title='Overstocking or Obselescence by SKU and Category',
        labels={'InventoryFailureFrequency': 'Failure Frequency'}
    )
    fig_failure.update_yaxes(type='category')

    fig_forecast = px.bar(
        combined_forecast_df,
        x='TotalForecastedQty',
        y='SKU',
        color='Category',
        orientation='h',
        title='Forecasted Demand by SKU and Category',
        labels={'TotalForecastedQty': 'Forecasted Qty'}
    )
    fig_forecast.update_yaxes(type='category')
    return fig_failure, fig_forecast

@callback(
    Output("metric-total-skus", "children"),
    Output("metric-total-stock", "children"),
    Output("metric-total-stockouts", "children"),
    Output("metric-total-obsoletes", "children"),
    [Input("year-dropdown", "value"), Input("category-dropdown", "value")]
)
def update_metrics(selected_year, selected_category):
    year = selected_year if isinstance(selected_year, list) else [selected_year]
    category = selected_category if isinstance(selected_category, list) else [selected_category]
    if not year or year == []:
        year = ["all"]
    if not category or category == []:
        category = ["all"]
    total_skus, total_stock, total_stockouts, total_obsoletes = get_inventory_metrics(year, category)
    return f"{total_skus:,}", f"{total_stock:,}", f"{total_stockouts:,}", f"{total_obsoletes:,}"

@callback(
    Output("year-dropdown", "value"),
    Input("reset-year-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_year(n_clicks):
    return ["all"]

@callback(
    Output("category-dropdown", "value"),
    Input("reset-category-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_category(n_clicks):
    return ["all"]
