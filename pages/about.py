
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/about", name="About")

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

# --------------- PROFILE CARD DATA --------------- #
profiles = [
	{"name": "Evangelista, Cathleen Eren", "email": "cmevangelista@up.edu.ph", "img": "/assets/profile/evangelista.jpg"},
	{"name": "Faustino, Mikaela Jessica", "email": "mhfaustino@up.edu.ph", "img": "/assets/profile/faustino.jpg"},
	{"name": "Manese, Reign Micaella", "email": "rdmanese@up.edu.ph", "img": "/assets/profile/manese.jpg"},
	{"name": "Puerto, Atasha Brianne", "email": "abpuerto@up.edu.ph", "img": "/assets/profile/puerto.jpg"},
]

# --------------- 1x4 RECTANGULAR PROFILE CARDS GRID --------------- #
profile_cards = dbc.Row([
	dbc.Col(
		dbc.Card([
			dbc.CardImg(src=profile["img"], top=True, style={"height": "260px", "objectFit": "cover"}),
			dbc.CardBody([
				html.Div([
					html.H5(profile["name"].split(",")[0] + ",", className="fw-bold mb-1 text-center"),
					html.H5(profile["name"].split(",")[1].strip(), className="fw-bold mb-2 text-center"),
				]),
				html.P(profile["email"], className="text-muted mb-0 text-center"),
			])
		], className="shadow-sm h-100", style={"minWidth": "220px", "maxWidth": "260px", "height": "350px"}),
		md=3, className="mb-4 d-flex justify-content-center"
	) for profile in profiles
], justify="center", className="justify-content-center")

# ---------------- PAGE LAYOUT ---------------- #
layout = html.Div([
	header,
	dbc.Container([
		html.H2("About", className="fw-bold mb-2"),
		html.Div([
			html.Img(src="/assets/upmo.png", style={"height": "140px", "marginBottom": "20px"}),
			html.P(
				"The University Planning and Maintenance Office (UPMO) is University of the Philippines Los Banos’s lead unit for campus development and facility upkeep. We ensure that the university’s physical environment remains safe, functional, and conducive to learning by overseeing infrastructure planning, building maintenance, utilities management, and the preservation of campus spaces. Through efficient services and long-term development initiatives, UPMO supports UPLB’s mission by providing a well-maintained and sustainable campus for the entire community.",
				className="mb-4 text-center",
				style={"maxWidth": "700px", "margin": "0 auto"}
			),
		], className="mb-4 text-center"),
		html.H2("Developers", className="fw-bold mb-2 mt-4"),
		profile_cards
	], fluid=True, style={"paddingLeft": "32px", "paddingRight": "32px"})
])
