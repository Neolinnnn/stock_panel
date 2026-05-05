"""
stock_panel — 個股深度分析面板
啟動：python app.py
瀏覽：http://localhost:8050
"""
import os
from dotenv import load_dotenv
load_dotenv()

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State

from data.fetcher import (
    daily_ohlcv, minute_ohlcv, institutional_investors,
    margin_purchase, realtime_quote, stock_info,
)
from indicators.technical import compute_indicators, technical_summary, key_levels, detect_patterns
from indicators.chip import aggregate_chip, main_force_signal
from model.predict import predict as ml_predict

from layout.header     import build_header
from layout.chart      import build_main_chart, build_mini_charts
from layout.chip_panel import build_chip_panel, build_main_force_table
from layout.signal     import build_signal_card, build_gauge
from layout.analysis   import (
    build_tech_summary, build_key_levels, build_pattern_analysis,
    build_operation_suggestion, build_prediction_panel,
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="股票深度面板",
    suppress_callback_exceptions=True,
)

app.layout = html.Div([
    html.Div([
        dcc.Input(
            id="stock-input", type="text", placeholder="輸入股票代碼（例：3661）",
            debounce=True, n_submit=0,
            style={
                "width": "220px", "padding": "8px 12px", "fontSize": "14px",
                "background": "#161b22", "color": "#fafafa",
                "border": "1px solid #30363d", "borderRadius": "6px",
                "marginRight": "10px",
            },
        ),
        html.Button("分析", id="analyze-btn", n_clicks=0, style={
            "padding": "8px 20px", "fontSize": "14px", "fontWeight": "bold",
            "background": "#1f6feb", "color": "#fafafa",
            "border": "none", "borderRadius": "6px", "cursor": "pointer",
        }),
        html.Span(id="status-text", style={"color": "#888", "fontSize": "12px", "marginLeft": "12px"}),
    ], style={"display": "flex", "alignItems": "center", "padding": "12px 16px",
              "background": "#0d1117", "borderBottom": "1px solid #30363d"}),

    html.Div(id="panel-body", style={"padding": "12px"}),

    dcc.Interval(id="auto-refresh", interval=5 * 60 * 1000, n_intervals=0),
    dcc.Store(id="current-stock", data=""),
], style={"backgroundColor": "#0d1117", "minHeight": "100vh", "fontFamily": "system-ui, sans-serif"})


@app.callback(
    Output("current-stock", "data"),
    Input("analyze-btn", "n_clicks"),
    Input("stock-input", "n_submit"),
    State("stock-input", "value"),
    prevent_initial_call=True,
)
def store_stock(_, __, value):
    return (value or "").strip()


@app.callback(
    Output("panel-body", "children"),
    Output("status-text", "children"),
    Input("current-stock", "data"),
    Input("auto-refresh", "n_intervals"),
    prevent_initial_call=True,
)
def update_panel(stock_id: str, _intervals: int):
    if not stock_id:
        return _empty_panel(), ""

    try:
        df_day     = daily_ohlcv(stock_id, days=120)
        df_min     = minute_ohlcv(stock_id)
        chip_raw   = institutional_investors(stock_id, days=30)
        margin_raw = margin_purchase(stock_id, days=30)
        quote      = realtime_quote(stock_id)
        info       = stock_info(stock_id)

        if df_day.empty:
            return html.Div(f"找不到 {stock_id} 的資料，請確認代碼正確。",
                            style={"color": "#e74c3c", "padding": "24px"}), "查詢失敗"

        df = compute_indicators(df_day).dropna().reset_index(drop=True)
        chip_df  = aggregate_chip(chip_raw)
        summary  = technical_summary(df)
        levels   = key_levels(df)
        patterns = detect_patterns(df)
        signal   = main_force_signal(chip_df, df)
        pred     = ml_predict(df_day, chip_raw, margin_raw)
        accuracy = pred.get("accuracy", 0)

        header      = build_header(stock_id, info, quote, df)
        main_chart  = build_main_chart(df)
        mini_charts = build_mini_charts(df_day, df_min)

        body = html.Div([
            header,

            html.Div([
                html.Div([
                    main_chart,
                    html.Div(mini_charts,
                             style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr",
                                    "gap": "8px", "marginTop": "8px"}),
                ], style={"flex": "7", "minWidth": 0}),

                html.Div([
                    build_tech_summary(summary),
                    html.Div(style={"height": "8px"}),
                    build_chip_panel(chip_df),
                    build_main_force_table(chip_df),
                    build_signal_card(signal),
                    build_gauge(accuracy),
                ], style={"flex": "3", "minWidth": "260px", "maxWidth": "340px"}),

            ], style={"display": "flex", "gap": "12px", "alignItems": "flex-start"}),

            html.Div([
                html.Div([build_pattern_analysis(patterns)],         style={"flex": "1"}),
                html.Div([build_key_levels(levels)],                 style={"flex": "1"}),
                html.Div([build_operation_suggestion(summary, levels)], style={"flex": "1"}),
                html.Div([build_prediction_panel(pred)],             style={"flex": "1"}),
            ], style={"display": "flex", "gap": "10px", "marginTop": "12px"}),
        ])

        return body, f"已載入 {info.get('name', stock_id)}（{stock_id}）"

    except Exception as e:
        msg = str(e)
        if msg in ("'data'", "data"):
            msg = "FinMind API 查詢頻率過高，請稍後再試（匿名模式每小時限 10 次）"
        return html.Div(f"⚠ 錯誤：{msg}", style={"color": "#e74c3c", "padding": "24px"}), "發生錯誤"


def _empty_panel() -> html.Div:
    return html.Div([
        html.Div("輸入股票代碼後按「分析」開始。",
                 style={"color": "#555", "fontSize": "16px", "textAlign": "center",
                        "marginTop": "80px"}),
    ])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
