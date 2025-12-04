import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Home")

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

hero_section = html.Div(
    [
        html.Div([
            html.H2("UPLB University Planning and Maintenance Office", className="fw-bold mb-2", style={"color": "#8D1436", "textShadow": "0 2px 8px rgba(0,0,0,0.12)"}),
            html.H3("Dashboard Intelligence", className="fw-bold", style={"color": "#8D1436", "textShadow": "0 2px 8px rgba(0,0,0,0.12)"}),
        ], style={"background": "rgba(255,255,255,0.75)", "borderRadius": "12px", "display": "inline-block", "padding": "32px 48px", "boxShadow": "0 4px 24px rgba(0,0,0,0.10)"})
    ],
    style={
        "backgroundImage": "url('/assets/hero-bg.jpg')",
        "backgroundSize": "cover",
        "backgroundPosition": "center",
        "padding": "80px 20px",
        "textAlign": "center",
        "borderRadius": "12px",
        "marginBottom": "40px"
    }
)

card_data = [
    {
        "title": "Inventory & Procurement",
        "desc": "Monitor supplies, track purchasing trends, and manage procurement data.",
        "href": "/inventory"
    },
    {
        "title": "Forecasting & Budgeting",
        "desc": "Analyze consumption, predict future needs, and allocate budgets.",
        "href": "/forecasting"
    },
    {
        "title": "Operations & Service Delivery",
        "desc": "Track operations metrics and service performance across units.",
        "href": "/operations"
    },
    {
        "title": "Strategic Planning",
        "desc": "Long-term planning insights and organizational alignment tools.",
        "href": "/planning"
    }
]

cards = dbc.Row(
    [
        dbc.Col(
            dcc.Link(
                dbc.Card(
                    dbc.CardBody([
                        html.H4(item["title"], className="fw-bold"),
                        html.P(item["desc"], className="text-muted"),
                    ]),
                    className="shadow-sm h-100 position-relative"
                ),
                href=item["href"],
                style={"textDecoration": "none", "color": "inherit"}
            ),
            md=6,
            className="mb-4"
        )
        for item in card_data
    ]
)

layout = html.Div([
    header,
    dbc.Container([
        hero_section,
        cards
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px"}),
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
