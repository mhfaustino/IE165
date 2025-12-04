import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, callback
from db_utils import get_db_connection

dash.register_page(__name__, path="/forecasting", name="Forecast Trend")

def get_sku_options(category=None):
    conn = get_db_connection()
    if category and category != "all":
        query = "SELECT SKU FROM Item_Dimension WHERE LOWER(Category) = ? ORDER BY SKU"
        df = pd.read_sql_query(query, conn, params=[category.lower()])
    else:
        query = "SELECT SKU FROM Item_Dimension ORDER BY SKU"
        df = pd.read_sql_query(query, conn)
    conn.close()
    options = [{"label": sku, "value": sku} for sku in df["SKU"].unique()]
    return [{"label": "All SKUs", "value": "all"}] + options
def get_mae_me_data(year=None, month=None, category=None, sku=None):
    conn = get_db_connection()
    query = '''
    WITH MaxYear AS (
        SELECT MAX(Year) AS Max_Year FROM Date_Dimension
    )
    SELECT
        AVG(ABS(T1.ForecastError_Demand)) AS Mean_Absolute_Error,
        AVG(T1.ForecastError_Demand) AS Mean_Error
    FROM Job_Request_Fact_Table AS T1
    INNER JOIN Date_Dimension AS T2 ON T1.DateKey = T2.DateKey
    CROSS JOIN MaxYear AS M
    INNER JOIN Item_Dimension AS I ON T1.ItemKey = I.ItemKey
    WHERE 1=1
    '''
    params = []
    if year:
        query += ' AND T2.Year = ?'
        params.append(year)
    else:
        query += ' AND T2.Year = M.Max_Year - 1'
    if month and month != "all":
        query += ' AND T2.Month = ?'
        params.append(month)
    if category and category != "all":
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
    if sku and sku != "all":
        query += ' AND I.SKU = ?'
        params.append(sku)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_qty_data(year=None, month=None, category=None, sku=None):
    conn = get_db_connection()
    query = '''
    WITH MaxYear AS (
        SELECT MAX(Year) AS Max_Year FROM Date_Dimension
    )
    SELECT
        SUM(T1.ForecastQty) AS Total_ForecastQty,
        SUM(T1.RequestedQty) AS Total_RequestedQty
    FROM Job_Request_Fact_Table AS T1
    INNER JOIN Date_Dimension AS T2 ON T1.DateKey = T2.DateKey
    CROSS JOIN MaxYear AS M
    INNER JOIN Item_Dimension AS I ON T1.ItemKey = I.ItemKey
    WHERE 1=1
    '''
    params = []
    if year:
        query += ' AND T2.Year = ?'
        params.append(year)
    else:
        query += ' AND T2.Year = M.Max_Year - 1'
    if month and month != "all":
        query += ' AND T2.Month = ?'
        params.append(month)
    if category and category != "all":
        query += ' AND LOWER(I.Category) = ?'
        params.append(category.lower())
    if sku and sku != "all":
        query += ' AND I.SKU = ?'
        params.append(sku)
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

def get_forecast_trend_data(input_year, category="Buildings"):
    conn = get_db_connection()
    prev_year = input_year - 1
    next_year = input_year + 1
    query = '''
    SELECT
        I.Category,
        I.SKU,
        ? AS PreviousForecastYear,
        ? AS CurrentForecastYear,
        ? AS FollowingForecastYear,
        SUM(CASE WHEN D.Year = ? THEN J.ForecastQty ELSE 0 END) AS PreviousYearForecast,
        SUM(CASE WHEN D.Year = ? THEN J.ForecastQty ELSE 0 END) AS CurrentYearForecast,
        SUM(CASE WHEN D.Year = ? THEN J.ForecastQty ELSE 0 END) AS FollowingYearForecast
    FROM
        Job_Request_Fact_Table AS J
    JOIN
        Date_Dimension AS D ON J.DateKey = D.DateKey
    JOIN
        Item_Dimension AS I ON J.ItemKey = I.ItemKey
    WHERE
        D.Year IN (?, ?, ?)
        AND LOWER(I.Category) = ?
    GROUP BY
        I.Category,
        I.SKU
    ORDER BY
        I.Category,
        CurrentYearForecast DESC
    '''
    params = [prev_year, input_year, next_year, prev_year, input_year, next_year, prev_year, input_year, next_year, category.lower()]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def prepare_line_chart_data(df, input_year):
    prev_year = input_year - 1
    next_year = input_year + 1
    rename_map = {
        "PreviousYearForecast": f"{prev_year}",
        "CurrentYearForecast": f"{input_year}",
        "FollowingYearForecast": f"{next_year}"
    }
    melted = pd.melt(
        df,
        id_vars=["SKU"],
        value_vars=["PreviousYearForecast", "CurrentYearForecast", "FollowingYearForecast"],
        var_name="YearType",
        value_name="ForecastQty"
    )
    melted["YearType"] = melted["YearType"].map(rename_map)
    return melted

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
                    dbc.Button("Forecasting", href="/forecasting", color="primary", disabled=True),
                    dbc.Button("Operations", href="/operations", color="primary", disabled=False),
                    dbc.Button("Planning", href="/planning", color="primary", disabled=False),
                ], size="md"),
            ], md=6, className="d-flex align-items-center justify-content-end"),
        ], className="mb-2", style={"paddingTop": "32px"}),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H4("Forecast Trend", className="mt-4"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Year"),
                                dcc.Dropdown(
                                    id="trend-year-dropdown",
                                    options=[{"label": str(x), "value": x} for x in [2022, 2021, 2019]],
                                    value=2022,
                                    placeholder="Select Year"
                                ),
                            ], md=6),
                            dbc.Col([
                                html.Label("Filter by Category"),
                                dcc.Dropdown(
                                    id="trend-category-dropdown",
                                    options=[{"label": "Buildings", "value": "buildings"}] + [{"label": x, "value": x.lower()} for x in ["Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                                    value="buildings",
                                    placeholder="Select Category"
                                ),
                            ], md=6),
                        ], className="mb-4"),
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(id="forecast-trend-chart", style={"height": "400px"})
                            ])
                        ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                    ], md=12),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H4("Forecasted Demand vs. Actual Consumption", className="mt-4"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Year"),
                                dcc.Dropdown(
                                    id="mae-year-dropdown",
                                    options=[{"label": str(x), "value": x} for x in [2023, 2022, 2021, 2019]],
                                    value=2023,
                                    placeholder="Select Year"
                                ),
                            ], md=3),
                            dbc.Col([
                                html.Label("Month"),
                                dcc.Dropdown(
                                    id="mae-month-dropdown",
                                    options=[{"label": "All Months", "value": "all"}] + [
                                        {"label": name, "value": num} for num, name in enumerate([
                                            "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
                                        ], 1)
                                    ],
                                    value="all",
                                    placeholder="Select Month"
                                ),
                            ], md=3),
                            dbc.Col([
                                html.Label("Category"),
                                dcc.Dropdown(
                                    id="mae-category-dropdown",
                                    options=[{"label": "All Categories", "value": "all"}] + [{"label": x, "value": x.lower()} for x in ["Buildings", "Custodial", "Electrical", "Grounds", "Landscaping", "Motorpool", "Office", "Plumbing", "Refrigeration"]],
                                    value="all",
                                    placeholder="Select Category"
                                ),
                            ], md=3),
                            dbc.Col([
                                html.Label("SKU"),
                                dcc.Dropdown(
                                    id="mae-sku-dropdown",
                                    options=get_sku_options(),
                                    value="all",
                                    placeholder="Select SKU"
                                ),
                            ], md=3),
                        ], className="mb-4"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        dcc.Graph(id="qty-chart", style={"height": "300px"})
                                    ])
                                ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                            ], md=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardBody([
                                        dcc.Graph(id="mae-me-chart", style={"height": "300px"})
                                    ])
                                ], style={"border": "3px solid #eaeaea", "boxShadow": "0 2px 8px rgba(0,0,0,0.04)"}),
                            ], md=6),
                        ])
                    ], md=12),
                ])
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
from dash import ctx
@callback(
    Output("mae-sku-dropdown", "options"),
    Output("mae-sku-dropdown", "disabled"),
    [Input("mae-category-dropdown", "value")]
)
def update_sku_options(selected_category):
    options = get_sku_options(selected_category)
    disabled = selected_category == "all"
    return options, disabled
@callback(
    Output("mae-me-chart", "figure"),
    Output("qty-chart", "figure"),
    [Input("mae-year-dropdown", "value"),
     Input("mae-month-dropdown", "value"),
     Input("mae-category-dropdown", "value"),
     Input("mae-sku-dropdown", "value")]
)
def update_mae_me_chart(year, month, category, sku):
    df_error = get_mae_me_data(year, month, category, sku)
    df_qty = get_qty_data(year, month, category, sku)
    df_error_long = df_error.melt(var_name="Metric", value_name="Value")
    fig_error = px.bar(
        df_error_long,
        x="Metric",
        y="Value",
        title="Forecast Error Metrics (MAE & ME)",
        text="Value",
        color_discrete_sequence=["#8D1436"]
    )
    fig_error.update_layout(yaxis_title="Value", xaxis_title="Metric")
    df_qty_long = df_qty.melt(var_name="Metric", value_name="Value")
    fig_qty = px.bar(
        df_qty_long,
        x="Value",
        y="Metric",
        orientation="h",
        title="Forecast & Request Quantities",
        text="Value",
        color_discrete_sequence=["#8D1436"]
    )
    fig_qty.update_layout(xaxis_title="Value", yaxis_title="Metric")
    return fig_error, fig_qty

@callback(
    Output("forecast-trend-chart", "figure"),
    [Input("trend-year-dropdown", "value"), Input("trend-category-dropdown", "value")]
)
def update_forecast_trend_chart(selected_year, selected_category):
    if selected_year is None:
        input_year = 2022
    else:
        input_year = int(selected_year)
    category = "Buildings" if selected_category is None or selected_category == "all" else selected_category.capitalize()
    df = get_forecast_trend_data(input_year, category=category)
    chart_df = prepare_line_chart_data(df, input_year)
    fig = px.line(
        chart_df,
        x="YearType",
        y="ForecastQty",
        color="SKU",
        markers=True,
        title=f"Forecasted Demand Trend for {category} ({input_year - 1}, {input_year}, {input_year + 1})"
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Forecasted Demand")
    return fig
