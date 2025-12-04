import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Home")

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

# --------------- HERO SECTION --------------- #
hero_section = html.Div(
    [
        html.H1("Welcome to UPMO Dashboard!", className="text-white fw-bold"),
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

# --------------- CLICKABLE CARDS (2x2 GRID) --------------- #
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

# ---------------- PAGE LAYOUT ---------------- #
layout = html.Div([
    header,
    dbc.Container([
        hero_section,
        cards
    ], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px"})
])
