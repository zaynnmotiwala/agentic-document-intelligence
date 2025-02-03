from chatten_ui import ChattenUi
import dash


def create_dash_app() -> dash.Dash:
    app = dash.Dash(__name__, title="Chatten UI", external_scripts=["https://cdn.tailwindcss.com"])
    app.layout = ChattenUi(id="chatten")
    return app
