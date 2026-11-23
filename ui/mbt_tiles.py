"""
UI-блок МБТ - Категории - Бренды:
набор окон с тремя селекторами + 6 показателей.
Окна выводятся по TILES_PER_ROW в ряд, одинаковой высоты.

У каждого окна — стабильный _id, чтобы удаление одного окна
не сдвигало фильтры и ключи виджетов у других.
"""
import streamlit as st

from src.format_utils import format_qty, format_money_full
from src.mbt_dashboard import (
    build_mbt_tile,
    get_available_months,
    get_available_brands,
    get_available_categories4,
    format_month_label,
)


TILES_PER_ROW = 3

SESSION_KEY = "mbt_tiles"
NEXT_ID_KEY = "mbt_next_id"


TILE_CSS = """
<style>
/* Уменьшаем зазоры внутри и вокруг окна */
div[data-testid="stVerticalBlock"] {
    gap: 0.25rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    min-height: 340px;
    height: 100%;
    box-sizing: border-box;
    padding: 10px 12px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    height: 100%;
}

/* Свои метрики вместо st.metric — чтобы числа не обрезались
   и цвета адаптировались под тему Streamlit */
.kpi-row {
    display: flex;
    gap: 10px;
    margin-bottom: 6px;
}
.kpi-cell {
    flex: 1;
    min-width: 0;
}
.kpi-label {
    font-size: 13px;
    color: var(--secondary-text-color);
    margin-bottom: 2px;
    line-height: 1.15;
}
.kpi-value {
    font-size: 22px;
    font-weight: 600;
    color: var(--text-color);
    line-height: 1.2;
    word-break: break-word;
    overflow-wrap: anywhere;
}
.kpi-value-money {
    color: #1a7f37;
}
</style>
"""


def _next_id() -> int:
    if NEXT_ID_KEY not in st.session_state:
        st.session_state[NEXT_ID_KEY] = 0
    nid = st.session_state[NEXT_ID_KEY]
    st.session_state[NEXT_ID_KEY] += 1
    return nid


def _make_default_tile(months, categories4) -> dict:
    return {
        "_id": _next_id(),
        "months": list(months),
        "brands": [],
        "category4": categories4[0] if categories4 else None,
    }


def _init_state(months, categories4):
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = [_make_default_tile(months, categories4)]


def _add_tile(months, categories4):
    st.session_state[SESSION_KEY].append(_make_default_tile(months, categories4))


def _remove_tile_by_id(tile_id: int):
    tiles = st.session_state.get(SESSION_KEY, [])
    if len(tiles) <= 1:
        return
    st.session_state[SESSION_KEY] = [t for t in tiles if t["_id"] != tile_id]


def _fmt_share(value):
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def _kpi_html(label: str, value: str, money: bool = False) -> str:
    cls = "kpi-value kpi-value-money" if money else "kpi-value"
    return (
        f'<div class="kpi-cell">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{cls}">{value}</div>'
        f'</div>'
    )


def render_mbt_tile(
    tile_state: dict,
    mbt_catalog: list[dict],
    months_options: list[tuple[int, int]],
    brands_options: list[str],
    categories4_options: list[str],
    window_number: int,
) -> None:
    tile_id = tile_state["_id"]

    with st.container(border=True):
        col_title, col_del = st.columns([6, 2])
        with col_title:
            st.markdown(f"**Окно {window_number}**")
        with col_del:
            if len(st.session_state[SESSION_KEY]) > 1:
                st.button(
                    "❌",
                    key=f"mbt_del_{tile_id}",
                    on_click=_remove_tile_by_id,
                    args=(tile_id,),
                    use_container_width=True,
                    help="Удалить"
                )

        selected_months = st.multiselect(
            "Период",
            options=months_options,
            default=tile_state["months"],
            format_func=format_month_label,
            key=f"mbt_{tile_id}_months",
        )

        selected_brands = st.multiselect(
            "Бренд",
            options=brands_options,
            default=tile_state["brands"],
            key=f"mbt_{tile_id}_brands",
            placeholder="Выберите один или несколько брендов",
        )

        cat4 = st.selectbox(
            "Категория ур. 4",
            options=categories4_options,
            index=(
                categories4_options.index(tile_state["category4"])
                if tile_state["category4"] in categories4_options
                else 0
            ),
            key=f"mbt_{tile_id}_cat4",
        )

        tile_state["months"] = selected_months
        tile_state["brands"] = selected_brands
        tile_state["category4"] = cat4

        tile = build_mbt_tile(
            mbt_catalog,
            period_months=selected_months,
            brands=selected_brands,
            category4=cat4 or "",
        )

        st.markdown("---")

        # 3 строки × 2 колонки: слева всегда штуки, справа всегда рубли
        html = f"""
        <div class="kpi-row">
            {_kpi_html("штуки", format_qty(tile["qty"]))}
            {_kpi_html("рубли", format_money_full(tile["revenue"]), money=True)}
        </div>
        <div class="kpi-row">
            {_kpi_html("доля, шт.", _fmt_share(tile["share_qty"]))}
            {_kpi_html("доля, руб.", _fmt_share(tile["share_revenue"]), money=True)}
        </div>
        <div class="kpi-row">
            {_kpi_html("кат. 4, шт.", format_qty(tile["cat4_qty"]))}
            {_kpi_html("кат. 4, руб.", format_money_full(tile["cat4_revenue"]), money=True)}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def render_mbt_block(mbt_catalog: list[dict]) -> None:
    st.markdown("### МБТ - Категории - Бренды")
    st.markdown(TILE_CSS, unsafe_allow_html=True)

    if not mbt_catalog:
        st.info("Нет файлов МБТ в выбранной папке.")
        return

    months_options = get_available_months(mbt_catalog)
    brands_options = get_available_brands(mbt_catalog)
    categories4_options = get_available_categories4(mbt_catalog)

    _init_state(months_options, categories4_options)

    col_add, _ = st.columns([1, 5])
    with col_add:
        if st.button("➕", use_container_width=True, help="добавить окно"):
            _add_tile(months_options, categories4_options)
            st.rerun()

    tiles = st.session_state[SESSION_KEY]
    for row_start in range(0, len(tiles), TILES_PER_ROW):
        row_tiles = tiles[row_start:row_start + TILES_PER_ROW]
        cols = st.columns(TILES_PER_ROW, gap="small")
        for i, tile_state in enumerate(row_tiles):
            window_number = row_start + i + 1
            with cols[i]:
                render_mbt_tile(
                    tile_state,
                    mbt_catalog,
                    months_options,
                    brands_options,
                    categories4_options,
                    window_number,
                )