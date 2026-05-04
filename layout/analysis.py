from dash import html, dcc
import plotly.graph_objects as go


_DIR_ICON  = {"up": "↑", "down": "↓", "neutral": "→"}
_DIR_COLOR = {"up": "#e74c3c", "down": "#27ae60", "neutral": "#f39c12"}


def build_tech_summary(summary: list) -> html.Div:
    rows = []
    for item in summary:
        icon  = _DIR_ICON[item["direction"]]
        color = _DIR_COLOR[item["direction"]]
        rows.append(html.Div([
            html.Span(icon,           style={"color": color, "fontWeight": "bold", "marginRight": "6px", "fontSize": "14px"}),
            html.Span(item["label"],  style={"color": "#888", "fontSize": "11px", "minWidth": "64px", "display": "inline-block"}),
            html.Span(item["value"],  style={"color": "#fafafa", "fontSize": "12px"}),
        ], style={"display": "flex", "alignItems": "center", "padding": "3px 0",
                  "borderBottom": "1px solid #1e2430"}))

    return html.Div([
        html.Div("技術分析總覽", style={"fontSize": "12px", "fontWeight": "bold", "color": "#888", "marginBottom": "6px"}),
        *rows,
    ], style={"padding": "10px 12px", "background": "#161b22", "borderRadius": "6px",
              "border": "1px solid #30363d"})


def build_key_levels(levels: dict) -> html.Div:
    items = [
        ("壓力區", levels["resistance"], "#e74c3c"),
        ("回檔區", levels["pullback"],   "#f39c12"),
        ("支撐區", levels["support"],    "#27ae60"),
        ("跌破防守", f"跌破 {levels['breakdown']:.0f} 轉弱", "#e74c3c"),
        ("強勢關鍵", f"突破 {levels['breakout']:.0f} 才強",  "#27ae60"),
    ]
    rows = [html.Div([
        html.Div(label, style={"backgroundColor": color + "33", "color": color,
                               "fontSize": "11px", "fontWeight": "bold",
                               "padding": "2px 8px", "borderRadius": "3px",
                               "minWidth": "56px", "textAlign": "center"}),
        html.Div(value, style={"color": "#fafafa", "fontSize": "13px", "marginLeft": "8px"}),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"})
            for label, value, color in items]

    return html.Div([
        html.Div("關鍵價位", style={"fontSize": "12px", "fontWeight": "bold", "color": "#888", "marginBottom": "8px"}),
        *rows,
    ], style={"padding": "10px 12px", "background": "#161b22", "borderRadius": "6px",
              "border": "1px solid #30363d"})


def build_pattern_analysis(patterns: dict) -> html.Div:
    def _panel(title: str, p: dict) -> html.Div:
        formed = p["formed"]
        color  = "#27ae60" if formed else "#95a5a6"
        mark   = "✓" if formed else "✗"
        return html.Div([
            html.Div(title, style={"fontSize": "12px", "color": "#888", "marginBottom": "4px"}),
            html.Div([
                html.Span(f"{mark} ", style={"color": color, "fontWeight": "bold"}),
                html.Span("形成標準型態" if formed else "未形成標準型態",
                          style={"color": color, "fontSize": "12px"}),
            ]),
            html.Div(p["reason"], style={"fontSize": "11px", "color": "#666", "marginTop": "3px"}),
        ], style={"flex": "1", "padding": "8px 10px", "background": "#161b22",
                  "borderRadius": "6px", "border": "1px solid #30363d"})

    return html.Div([
        html.Div("型態分析", style={"fontSize": "12px", "fontWeight": "bold",
                                   "color": "#888", "marginBottom": "6px"}),
        html.Div([
            _panel("W底分析", patterns["w_bottom"]),
            _panel("M頭分析", patterns["m_top"]),
        ], style={"display": "flex", "gap": "8px"}),
    ])


def build_operation_suggestion(summary: list, levels: dict) -> html.Div:
    up_count  = sum(1 for i in summary if i["direction"] == "up")
    dn_count  = sum(1 for i in summary if i["direction"] == "down")

    if up_count >= 5:
        strategy = "不追高，等待回檔布局"
        bullets  = [
            f"回檔買點：{levels['pullback']}",
            f"強勢關鍵：突破 {levels['breakout']:.0f} 放量確認",
            f"停損防守：跌破 {levels['breakdown']:.0f} 轉弱出場",
        ]
    elif dn_count >= 5:
        strategy = "弱勢格局，觀望為主"
        bullets  = [
            f"支撐觀察：{levels['support']}",
            f"跌破防守：{levels['breakdown']:.0f} 以下迴避",
            "等待止跌訊號再行動",
        ]
    else:
        strategy = "盤整觀望，等待方向確認"
        bullets  = [
            f"壓力測試：突破 {levels['resistance']} 再追",
            f"支撐守住：{levels['support']} 附近觀察",
            f"跌破 {levels['breakdown']:.0f} 轉弱，謹慎",
        ]

    return html.Div([
        html.Div("操作建議", style={"fontSize": "12px", "fontWeight": "bold",
                                   "color": "#888", "marginBottom": "6px"}),
        html.Div(f"策略：{strategy}", style={"color": "#f39c12", "fontSize": "12px", "marginBottom": "6px"}),
        *[html.Div([html.Span("▶ ", style={"color": "#3498db"}),
                    html.Span(b, style={"fontSize": "12px", "color": "#ddd"})],
                   style={"marginBottom": "4px"})
          for b in bullets],
        html.Div("* 操作建議僅供參考，非投資建議", style={"fontSize": "10px", "color": "#555", "marginTop": "8px"}),
    ], style={"padding": "10px 12px", "background": "#161b22", "borderRadius": "6px",
              "border": "1px solid #30363d"})


def build_prediction_panel(pred: dict) -> html.Div:
    def _prob_card(label: str, pct: float, color: str) -> html.Div:
        return html.Div([
            html.Div(label, style={"fontSize": "11px", "color": "#888", "marginBottom": "4px"}),
            html.Div(f"{pct:.0%}", style={"fontSize": "28px", "fontWeight": "bold", "color": color}),
        ], style={"flex": "1", "textAlign": "center", "padding": "10px 8px",
                  "background": "#0d1117", "borderRadius": "6px", "border": f"1px solid {color}33"})

    error = pred.get("error")
    accuracy = pred.get("accuracy", 0)

    return html.Div([
        html.Div("明日漲跌機率預測（AI模型）",
                 style={"fontSize": "12px", "fontWeight": "bold", "color": "#888", "marginBottom": "8px"}),
        html.Div([
            _prob_card("上漲機率", pred.get("up", 0),       "#e74c3c"),
            _prob_card("下跌機率", pred.get("down", 0),     "#27ae60"),
            _prob_card("震盪機率", pred.get("sideways", 0), "#f39c12"),
        ], style={"display": "flex", "gap": "8px", "marginBottom": "8px"}),
        html.Div(
            f"模型準確率：{accuracy:.0%}" if not error else f"⚠ {error}",
            style={"fontSize": "11px", "color": "#555"},
        ),
    ], style={"padding": "10px 12px", "background": "#161b22", "borderRadius": "6px",
              "border": "1px solid #30363d"})
