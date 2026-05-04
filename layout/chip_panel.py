import pandas as pd
from dash import html, dash_table


def _section(title: str) -> html.Div:
    return html.Div(title, style={
        "fontSize": "12px", "fontWeight": "bold", "color": "#888",
        "padding": "8px 0 4px", "borderTop": "1px solid #30363d", "marginTop": "8px",
    })


def _table(df: pd.DataFrame, color_cols: list) -> dash_table.DataTable:
    style_data_conditional = []
    for col in color_cols:
        style_data_conditional += [
            {"if": {"filter_query": f"{{{col}}} > 0", "column_id": col},
             "color": "#e74c3c", "fontWeight": "bold"},
            {"if": {"filter_query": f"{{{col}}} < 0", "column_id": col},
             "color": "#27ae60", "fontWeight": "bold"},
        ]

    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": "#0d1117", "color": "#fafafa",
            "fontSize": "12px", "padding": "4px 8px",
            "border": "1px solid #30363d", "textAlign": "right",
        },
        style_header={
            "backgroundColor": "#161b22", "color": "#888",
            "fontWeight": "bold", "fontSize": "11px",
            "border": "1px solid #30363d",
        },
        style_data_conditional=style_data_conditional,
        page_size=10,
    )


def build_chip_panel(chip_df: pd.DataFrame) -> html.Div:
    if chip_df.empty:
        return html.Div("三大法人資料不足", style={"color": "#555", "fontSize": "12px"})

    show = chip_df[["日期", "外資", "投信", "自營", "合計"]].tail(5).copy()
    show = show.iloc[::-1].reset_index(drop=True)

    return html.Div([
        _section("三大法人（近5日，張）"),
        _table(show, ["外資", "投信", "自營", "合計"]),
    ])


def build_main_force_table(chip_df: pd.DataFrame) -> html.Div:
    if chip_df.empty:
        return html.Div("主力資料不足", style={"color": "#555", "fontSize": "12px"})

    show = chip_df[["日期", "合計", "10日累計"]].tail(5).copy()
    show = show.rename(columns={"合計": "主力增減", "10日累計": "10日累計"})
    show = show.iloc[::-1].reset_index(drop=True)

    return html.Div([
        _section("主力進出（近5日，張）"),
        _table(show, ["主力增減", "10日累計"]),
    ])
