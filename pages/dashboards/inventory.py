import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from db_utils import get_db_connection, import_csvs_to_sqlite

dash.register_page(__name__, path="/inventory", name="Inventory Dashboard")

# ---------------- HEADER ---------------- #
header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand("IE 165", className="fw-bold fs-3"),
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("About", href="/about")),
        ], className="ms-auto")
    ]),
    color="primary",
    dark=True,
    className="mb-4 w-100"
)

# SQL query for inventory failure frequency
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


import plotly.express as px
from dash import Input, Output, callback

def get_forecasted_demand_data(year=None, category=None):
    conn = get_db_connection()
    params = []
    if category:
        # Top 4 per selected category
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
        # Top 5 overall
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
    title='Inventory Failure Frequency by SKU and Category',
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
                html.P("View and analyze inventory...", className="text-muted"),
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
                    dbc.Col([
                        html.H4("Inventory Failure Frequency", className="mt-4"),
                        dcc.Graph(id="inventory-bar-chart", figure=bar_fig, style={"height": "400px"})
                    ], md=6),
                    dbc.Col([
                        html.H4("Forecasted Demand", className="mt-4"),
                        dcc.Graph(id="forecasted-demand-chart", figure=forecast_fig, style={"height": "400px"})
                    ], md=6),
                ])
            ])
        )
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px"})
])

@callback(
    Output("inventory-bar-chart", "figure"),
    Output("forecasted-demand-chart", "figure"),
    [Input("year-dropdown", "value"), Input("category-dropdown", "value")]
)
def update_charts(selected_year, selected_category):
    # Handle multi-select and 'all'
    year_options = [2019, 2020, 2021, 2022, 2023]
    year = selected_year if isinstance(selected_year, list) else [selected_year]
    category = selected_category if isinstance(selected_category, list) else [selected_category]
    # If all years are selected manually, treat as 'all'
    if sorted([int(y) for y in year if y != "all" and y is not None]) == year_options:
        year = ["all"]
    # Ensure at least 'all' is present if empty
    if not year or year == []:
        year = ["all"]
    if not category or category == []:
        category = ["all"]
    df_failure = get_filtered_inventory_failure_data(year, category)
    # For forecast, show top 5 SKUs from intersection of selected years and categories
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
        # Group by SKU and Category, sum TotalForecastedQty, then pick top 5
        if not combined_forecast_df.empty:
            combined_forecast_df = combined_forecast_df.groupby(["SKU", "Category"], as_index=False)["TotalForecastedQty"].sum()
            combined_forecast_df = combined_forecast_df.sort_values("TotalForecastedQty", ascending=False).head(5)
    fig_failure = px.bar(
        df_failure,
        x='InventoryFailureFrequency',
        y='SKU',
        color='Category',
        orientation='h',
        title='Inventory Failure Frequency by SKU and Category',
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

from dash import ctx

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
