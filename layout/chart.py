import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc


def build_main_chart(df: pd.DataFrame) -> dcc.Graph:
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.50, 0.14, 0.18, 0.18],
        subplot_titles=("", "成交量", "KD (9,3,3)", "MACD (12,26,9)"),
    )

    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="K線",
        increasing_line_color="#e74c3c", decreasing_line_color="#27ae60",
        increasing_fillcolor="#e74c3c", decreasing_fillcolor="#27ae60",
    ), row=1, col=1)

    _line = lambda col, color, name: go.Scatter(
        x=df["date"], y=df[col], name=name,
        line=dict(color=color, width=1), mode="lines", showlegend=True,
    )
    for col, color, name in [
        ("bb_upper", "rgba(255,165,0,0.6)", "BB上軌"),
        ("bb_mid",   "rgba(255,165,0,0.3)", "BB中軌"),
        ("bb_lower", "rgba(255,165,0,0.6)", "BB下軌"),
        ("ma5",      "rgba(86,180,255,0.9)", "MA5"),
        ("ma20",     "rgba(255,200,50,0.9)", "MA20"),
        ("ma60",     "rgba(200,100,255,0.9)", "MA60"),
    ]:
        fig.add_trace(_line(col, color, name), row=1, col=1)

    bar_colors = [
        "#e74c3c" if c >= o else "#27ae60"
        for c, o in zip(df["close"], df["open"])
    ]
    fig.add_trace(go.Bar(
        x=df["date"], y=df["volume"], name="成交量",
        marker_color=bar_colors, opacity=0.8, showlegend=False,
    ), row=2, col=1)

    fig.add_trace(go.Scatter(x=df["date"], y=df["kd_k"], name="K",
                             line=dict(color="#3498db", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df["date"], y=df["kd_d"], name="D",
                             line=dict(color="#e67e22", width=1.5)), row=3, col=1)
    for level, color in [(80, "rgba(220,50,50,0.25)"), (20, "rgba(50,200,50,0.25)")]:
        fig.add_hline(y=level, line_dash="dash", line_color=color, row=3, col=1)

    osc_colors = ["#e74c3c" if v >= 0 else "#27ae60" for v in df["macd_osc"]]
    fig.add_trace(go.Bar(x=df["date"], y=df["macd_osc"], name="OSC",
                         marker_color=osc_colors, opacity=0.8, showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=df["date"], y=df["macd_dif"],    name="DIF",
                             line=dict(color="#e74c3c", width=1.5)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df["date"], y=df["macd_signal"], name="MACD",
                             line=dict(color="#3498db", width=1.5)), row=4, col=1)

    fig.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#fafafa", size=11),
        height=560,
        margin=dict(l=8, r=8, t=24, b=8),
        legend=dict(orientation="h", y=1.03, x=0, font=dict(size=10)),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    for i in range(1, 5):
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", row=i, col=1)
        fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", row=i, col=1)

    return dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"marginBottom": "10px"})


def build_mini_charts(df_day: pd.DataFrame, df_minute: pd.DataFrame) -> list:
    charts = []

    if not df_minute.empty:
        charts.append(dcc.Graph(figure=_mini(df_minute.tail(60), "60分K（短線）"),
                                config={"displayModeBar": False}))
    else:
        charts.append(dcc.Graph(figure=_empty_mini("60分K（短線）", "分K載入中..."),
                                config={"displayModeBar": False}))

    charts.append(dcc.Graph(figure=_mini(df_day.tail(60), "日K（中線）"),
                             config={"displayModeBar": False}))

    df_week = _to_weekly(df_day)
    if not df_week.empty:
        charts.append(dcc.Graph(figure=_mini(df_week.tail(40), "週K（長線）"),
                                config={"displayModeBar": False}))
    else:
        charts.append(dcc.Graph(figure=_empty_mini("週K（長線）", "資料不足"),
                                config={"displayModeBar": False}))

    return charts


def _mini(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        increasing_line_color="#e74c3c", decreasing_line_color="#27ae60",
        name="",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#aaa"), x=0.5),
        plot_bgcolor="#0d1117", paper_bgcolor="#161b22",
        height=200, margin=dict(l=4, r=4, t=28, b=4),
        font=dict(color="#fafafa"), showlegend=False,
        xaxis=dict(rangeslider_visible=False, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    return fig


def _empty_mini(title: str, msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(color="#555", size=13))
    fig.update_layout(
        title=dict(text=title, font=dict(size=12, color="#aaa"), x=0.5),
        plot_bgcolor="#0d1117", paper_bgcolor="#161b22",
        height=200, margin=dict(l=4, r=4, t=28, b=4),
    )
    return fig


def _to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    weekly = (
        d.set_index("date")
         .resample("W")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last",  "volume": "sum"})
         .dropna()
         .reset_index()
    )
    weekly["date"] = weekly["date"].astype(str)
    return weekly
