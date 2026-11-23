import streamlit as st

from src.format_utils import format_qty, format_money


# наконец без наездов!
TILE_CSS = """
<style>
/* --- УМЕНЬШАЕМ ОТСТУП СВЕРХУ --- */
.block-container {
    padding-top: 1.5rem !important; /* было около 6rem, стало в 4 раза меньше */
    padding-bottom: 1rem !important;
}

/* --- УМЕНЬШАЕМ ЗАГОЛОВОК В 2 РАЗА --- */
h1 {
    font-size: 1.4rem !important; /* Уменьшили с ~2.75rem */
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important; /* Прижимаем дату к заголовку */
    padding-top: 0 !important;
}


/* Зазоры между горизонтальными рядами */
div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
    margin-bottom: 0.5rem !important; /* добавил зазор между рядами */
    gap: 0.8rem !important;           /* чуть увеличил горизонтальный зазор */
}

/* Убираем жесткий gap, чтобы не ломать вертикальные блоки внутри колонок */
div[data-testid="stVerticalBlock"] {
    gap: 0.5rem !important;
}


.tile {
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 8px;
    padding: 10px 14px;
    background: var(--secondary-background-color);
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    /* ГЛАВНОЕ ИСПРАВЛЕНИЕ: отступ снизу, чтобы плитки не слипались */
    margin-bottom: 12px;
}
.tile-title {
    font-size: 14px;
    color: var(--secondary-text-color);
    margin-bottom: 6px;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.tile-value {
    font-size: 30px;
    font-weight: 600;
    color: var(--text-color);
    line-height: 1.15;
}
.tile-value-money {
    font-size: 30px;
    font-weight: 600;
    color: #1a7f37;
    line-height: 1.15;
}
.tile-star {
    color: #c00;
    font-weight: bold;
    font-size: 16px;
    margin-left: 4px;
    cursor: help;
    vertical-align: super;
}

/* Строки приростов */
.tile-growth {
    font-size: 15px;
    line-height: 1.3;
    margin-top: 4px;
    font-weight: 500;
}
.tile-growth-up   { color: #1a7f37; }
.tile-growth-down { color: #c0392b; }
.tile-growth-none { color: var(--secondary-text-color); }

.tile-no-data {
    font-size: 18px;
    color: var(--secondary-text-color);
    font-style: italic;
}
.tile-empty {
    min-height: 100px;
    /* Добавляем маргин для пустых ячеек, чтобы они не схлопывались */
    margin-bottom: 12px;
}
</style>
"""
# наконец без наездов!



PERIOD_LABELS = {
    "yesterday":         "вчера",
    "current_week":      "текущая неделя",
    "current_month":     "текущий месяц",
    "current_year_ytd":  "текущий год накопительно",
    "last_week":         "прошлая неделя",
    "last_month":        "прошлый месяц",
    "last_year_ytd":     "прошлый год накопительно",
    "prev_day_year_ago": "прошлый день год назад",
    "week_year_ago":     "неделя год назад",
    "month_year_ago":    "месяц год назад",
}


GRID = [
    ["yesterday", "current_week", "current_month", "current_year_ytd"],
    [None, "last_week", "last_month", "last_year_ytd"],
    ["prev_day_year_ago", "week_year_ago", "month_year_ago", None],
]


def _missing_tooltip(missing_dates: list) -> str:
    if not missing_dates:
        return ""
    from src.format_utils import format_missing_periods
    text = format_missing_periods(missing_dates)
    return text.replace("\n", "&#10;")


def _fmt_growth(value) -> tuple[str, str]:
    """
    Возвращает (текст, css_класс).
      None → ("—", "tile-growth-none")
      >=0 → ("+15.2%", "tile-growth-up")
      <0  → ("-8.4%", "tile-growth-down")
    """
    if value is None:
        return "—", "tile-growth-none"
    pct = value * 100
    if pct >= 0:
        return f"+{pct:.1f}%", "tile-growth-up"
    return f"{pct:.1f}%", "tile-growth-down"


# def _render_growth_line(label: str, growth_value, base_info: dict) -> str:
#     """
#     Возвращает HTML-строку с приростом и (при необходимости) звёздочкой.
#     base_info: {"base_missing_days": [...], "base_no_data": bool}
#     """
#     text, css = _fmt_growth(growth_value)

#     star = ""
#     # Если посчитать нельзя — показываем ★, чтобы объяснить, чего не хватает.
#     if growth_value is None:
#         if base_info.get("base_no_data"):
#             tooltip = "Данных за базовый период нет"
#         else:
#             missing = base_info.get("base_missing_days", [])
#             if missing:
#                 tooltip = f"Пропущено в базовом периоде:&#10;{_missing_tooltip(missing)}"
#             else:
#                 tooltip = "Знаменатель равен 0"
#         star = (
#             f'<span class="tile-star" title="{tooltip}">★</span>'
#         )

#     return (
#         f'<div class="tile-growth {css}">'
#         f'{label}: {text}{star}'
#         f'</div>'
#     )
def _render_growth_line(label: str, growth_value, base_info: dict) -> str:
    """
    Возвращает HTML-строку с приростом и (при необходимости) звёздочкой.
    base_info: {"base_missing_days": [...], "base_no_data": bool}
    """
    text, css = _fmt_growth(growth_value)

    star = ""
    # Если посчитать нельзя — показываем ★, чтобы объяснить, чего не хватает.
    if growth_value is None:
        missing = base_info.get("base_missing_days", [])
        
        if missing:
            # Если есть конкретные дни — показываем их (как на 2-м скрине)
            tooltip = f"Пропущено в базовом периоде:&#10;{_missing_tooltip(missing)}"
        elif base_info.get("base_no_data"):
            # Если дней нет, но данных нет — пишем общую фразу
            tooltip = "Данных за базовый период нет"
        else:
            # Если дни покрыты, но сумма равна нулю
            tooltip = "Знаменатель равен 0"
            
        star = (
            f'<span class="tile-star" title="{tooltip}">★</span>'
        )

    return (
        f'<div class="tile-growth {css}">'
        f'{label}: {text}{star}'
        f'</div>'
    )


def render_tile(period_key: str, tile: dict, mode: str) -> None:
    label = PERIOD_LABELS[period_key]
    value_key = "qty" if mode == "qty" else "amount_with_vat"

    missing = tile.get("missing_days", [])
    tooltip = _missing_tooltip(missing)

    if tile["status"] == "no_data":
        if missing:
            body_html = (
                f'<div class="tile-no-data">нет данных'
                f'<span class="tile-star" title="Пропущено:&#10;{tooltip}">★</span>'
                f'</div>'
            )
        else:
            body_html = '<div class="tile-no-data">нет данных</div>'
    else:
        fmt = format_qty if mode == "qty" else format_money
        value = fmt(tile[value_key])
        css_class = "tile-value" if mode == "qty" else "tile-value-money"
        star = ""
        if tile["status"] == "partial" and missing:
            star = (
                f'<span class="tile-star" '
                f'title="Пропущено:&#10;{tooltip}">★</span>'
            )
        body_html = f'<div class="{css_class}">{value}{star}</div>'

        # Приросты — если у плитки есть ключи growth_prev / growth_prev_year_ago
        if "growth_prev" in tile:
            gp = tile["growth_prev"]
            gp_ya = tile["growth_prev_year_ago"]

            growth_value = gp["growth_qty"] if mode == "qty" else gp["growth_revenue"]
            growth_ya_value = gp_ya["growth_qty"] if mode == "qty" else gp_ya["growth_revenue"]

            # Метка «к чему прирост» — зависит от плитки
            if period_key == "last_week":
                label_prev = "к позапрошл. нед."
                label_ya = "к той же нед. год назад"
            elif period_key == "last_month":
                label_prev = "к позапрошл. мес."
                label_ya = "к тому же мес. год назад"
            else:
                label_prev = "прирост"
                label_ya = "год назад"

            body_html += _render_growth_line(label_prev, growth_value, gp)
            body_html += _render_growth_line(label_ya, growth_ya_value, gp_ya)

    html = f"""
    <div class="tile">
        <div class="tile-title">{label}</div>
        {body_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_cell() -> None:
    st.markdown('<div class="tile-empty"></div>', unsafe_allow_html=True)


def render_dashboard_block(dashboard: dict, mode: str, title: str) -> None:
    st.markdown(f"#### {title}")
    st.markdown(TILE_CSS, unsafe_allow_html=True)

    for row in GRID:
        cols = st.columns(4, gap="small")
        for col, key in zip(cols, row):
            with col:
                if key is None:
                    render_empty_cell()
                else:
                    render_tile(key, dashboard[key], mode)
