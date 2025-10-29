import os, json, requests, time
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
API_AUD = os.environ.get("API_AUDIENCE", "")

def _id_token_from_metadata(aud):
    if not aud:
        return None
    try:
        url = "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience={}&format=full".format(aud)
        h = {"Metadata-Flavor": "Google"}
        r = requests.get(url, headers=h, timeout=2)
        if r.ok:
            return r.text
    except Exception:
        return None

def auth_headers():
    tok = _id_token_from_metadata(API_AUD)
    if tok:
        return {"Authorization": f"Bearer {tok}"}
    return {}

def graph_from_series(y, title, yaxis):
    fig = go.Figure()
    fig.add_scatter(y=y, mode="lines")
    fig.update_layout(title=title, xaxis_title="step", yaxis_title=yaxis, margin=dict(l=40,r=20,t=40,b=40))
    return fig

app = Dash(__name__)
app.title = "WCCT UI"

app.layout = html.Div([
    html.H3("WCCT Solver UI"),
    html.Div([
        html.Span("API base"),
        dcc.Input(id="api-base", type="text", value=API_BASE, style={"width":"380px"}),
    ], style={"display":"grid","gridTemplateColumns":"max-content 400px","gap":"8px","alignItems":"center"}),
    html.Hr(),
    html.H4("Poisson RB SOR"),
    html.Div([
        html.Label("N"), dcc.Input(id="p-N", type="number", value=64),
        html.Label("steps"), dcc.Input(id="p-steps", type="number", value=400),
        html.Label("omega"), dcc.Input(id="p-omega", type="number", value=1.9, step=0.05),
        html.Button("Run solve", id="btn-solve")
    ], style={"display":"grid","gridTemplateColumns":"repeat(7, max-content)","gap":"8px","alignItems":"center"}),
    dcc.Graph(id="solve-graph"),
    html.Pre(id="solve-metrics", style={"whiteSpace":"pre-wrap"}),
    html.Hr(),
    html.H4("Xi series"),
    html.Div([
        html.Label("N"), dcc.Input(id="x-N", type="number", value=96),
        html.Label("T"), dcc.Input(id="x-T", type="number", value=150),
        html.Label("lam"), dcc.Input(id="x-lam", type="number", value=0.2, step=0.01),
        html.Label("m2"), dcc.Input(id="x-m2", type="number", value=0.0, step=0.01),
        html.Label("dt"), dcc.Input(id="x-dt", type="number", value=0.1, step=0.01),
        html.Label("seed"), dcc.Input(id="x-seed", type="number", value=42),
        html.Button("Run Xi", id="btn-xi")
    ], style={"display":"grid","gridTemplateColumns":"repeat(13, max-content)","gap":"8px","alignItems":"center"}),
    dcc.Graph(id="xi-graph"),
    html.Pre(id="xi-metrics", style={"whiteSpace":"pre-wrap"}),
])

@app.callback(
    Output("solve-graph","figure"),
    Output("solve-metrics","children"),
    Input("btn-solve","n_clicks"),
    State("api-base","value"),
    State("p-N","value"),
    State("p-steps","value"),
    State("p-omega","value"),
    prevent_initial_call=True
)
def run_solve(n, base, N, steps, omega):
    try:
        url = base.rstrip("/") + "/solve"
        payload = {"N": int(N), "steps": int(steps), "omega": float(omega)}
        r = requests.post(url, json=payload, timeout=60, headers=auth_headers())
        d = r.json()
        hist = d.get("hist", [])
        fig = graph_from_series(hist, "RB SOR convergence", "rel_error_to_truth")
        txt = json.dumps({
            "onnx_parity": d.get("onnx_parity"),
            "rel_to_truth": d.get("rel_to_truth"),
            "u_mean": d.get("u_mean"),
            "u_std": d.get("u_std"),
            "iters": d.get("iters")
        }, indent=2)
        return fig, txt
    except Exception as e:
        fig = graph_from_series([], "RB SOR convergence", "rel_error_to_truth")
        return fig, f"error: {e}"

@app.callback(
    Output("xi-graph","figure"),
    Output("xi-metrics","children"),
    Input("btn-xi","n_clicks"),
    State("api-base","value"),
    State("x-N","value"),
    State("x-T","value"),
    State("x-lam","value"),
    State("x-m2","value"),
    State("x-dt","value"),
    State("x-seed","value"),
    prevent_initial_call=True
)
def run_xi(n, base, N, T, lam, m2, dt, seed):
    try:
        url = base.rstrip("/") + "/v1/xi/series"
        payload = {"N": int(N), "T": int(T), "lam": float(lam), "m2": float(m2), "dt": float(dt), "seed": int(seed)}
        r = requests.post(url, json=payload, timeout=60, headers=auth_headers())
        d = r.json()
        xis = d.get("xis", [])
        fig = graph_from_series(xis, "Xi progression", "Xi")
        txt = json.dumps({
            "xi_final": d.get("xi_final"),
            "xi_mean": d.get("xi_mean"),
            "steps": d.get("steps")
        }, indent=2)
        return fig, txt
    except Exception as e:
        fig = graph_from_series([], "Xi progression", "Xi")
        return fig, f"error: {e}"

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
