import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from db_utils import import_csvs_to_sqlite
import_csvs_to_sqlite()

app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.FLATLY]
)

app.layout = html.Div([
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)
