from dash import html


def _card(label: str, value: str, color: str = "#fafafa") -> html.Div:
    return html.Div([
        html.Div(label, style={"fontSize": "11px", "color": "#888", "marginBottom": "2px"}),
        html.Div(value, style={"fontSize": "15px", "fontWeight": "bold", "color": color}),
    ], style={"padding": "0 8px"})


def build_header(stock_id: str, info: dict, quote: dict, df) -> html.Div:
    close = float(df["close"].iloc[-1]) if not df.empty else None
    prev  = float(df["close"].iloc[-2]) if len(df) >= 2 else close
    date  = str(df["date"].iloc[-1])[:10] if not df.empty else "—"

    change     = round(close - prev, 2)         if (close is not None and prev is not None) else None
    change_pct = round(change / prev * 100, 2)  if (change is not None and prev) else None
    color      = "#e74c3c" if (change or 0) > 0 else "#27ae60" if (change or 0) < 0 else "#fafafa"

    arrow  = "▲" if (change or 0) > 0 else "▼"
    volume = df["volume"].iloc[-1] if not df.empty else None

    bid = quote.get("bid") or "—"
    ask = quote.get("ask") or "—"

    return html.Div([
        html.Div([
            html.Div(f"{info.get('name', stock_id)}",
                     style={"fontSize": "22px", "fontWeight": "bold", "color": "#fafafa"}),
            html.Div(f"（{stock_id}）  {info.get('industry', '')}",
                     style={"fontSize": "12px", "color": "#888", "marginTop": "2px"}),
        ], style={"padding": "0 12px", "minWidth": "160px"}),

        html.Div([
            html.Div(f"{close:,.2f}" if close else "—",
                     style={"fontSize": "36px", "fontWeight": "bold", "color": color}),
            html.Div(f"{arrow} {change:+.2f}（{change_pct:+.2f}%）" if change else "—",
                     style={"fontSize": "13px", "color": color}),
        ], style={"padding": "0 16px"}),

        _card("成交量", f"{int(volume):,} 張" if volume else "—"),
        _card("時間",   date),
        _card("買進",   str(bid), "#e74c3c"),
        _card("賣出",   str(ask), "#27ae60"),
    ], style={
        "display": "flex",
        "alignItems": "center",
        "gap": "8px",
        "padding": "14px 16px",
        "background": "#161b22",
        "borderRadius": "8px",
        "marginBottom": "10px",
        "border": "1px solid #30363d",
    })
