import plotly.graph_objects as go
from dash import html, dcc


def build_signal_card(signal: dict) -> html.Div:
    return html.Div([
        html.Div([
            html.Div(style={
                "width": "18px", "height": "18px", "borderRadius": "50%",
                "backgroundColor": signal["color"], "marginRight": "10px",
                "boxShadow": f"0 0 8px {signal['color']}",
                "flexShrink": "0",
            }),
            html.Div([
                html.Div("主力燈號", style={"fontSize": "11px", "color": "#888"}),
                html.Div(signal["label"], style={
                    "fontSize": "18px", "fontWeight": "bold", "color": signal["color"],
                }),
            ]),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
        html.Div(signal["desc"], style={"fontSize": "12px", "color": "#aaa"}),
    ], style={
        "padding": "10px 12px",
        "background": "#161b22",
        "borderRadius": "6px",
        "border": f"1px solid {signal['color']}44",
        "marginTop": "8px",
    })


def build_gauge(accuracy: float, label: str = "短線勝率") -> dcc.Graph:
    pct = round(accuracy * 100)
    color = "#27ae60" if pct >= 60 else "#f39c12" if pct >= 50 else "#e74c3c"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        title={"text": label, "font": {"size": 13, "color": "#888"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#555",
                     "tickfont": {"color": "#555", "size": 10}},
            "bar":  {"color": color, "thickness": 0.25},
            "bgcolor": "#0d1117",
            "bordercolor": "#30363d",
            "steps": [
                {"range": [0,  50], "color": "#1a0a0a"},
                {"range": [50, 65], "color": "#0a1a0a"},
                {"range": [65, 100], "color": "#0a1a0a"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": pct,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#161b22",
        height=160,
        margin=dict(l=16, r=16, t=32, b=8),
    )
    return dcc.Graph(figure=fig, config={"displayModeBar": False})
