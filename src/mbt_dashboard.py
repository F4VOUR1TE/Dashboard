from typing import Iterable


def _empty_agg() -> dict:
    return {"qty": 0.0, "revenue": 0.0}


def build_mbt_tile(
    mbt_catalog: list[dict],
    period_months: Iterable[tuple[int, int]],
    brands: Iterable[str],
    category4: str,
) -> dict:
    """
    mbt_catalog: список файлов МБТ (dict-ов из parse_mbt_file).
    period_months: iterable of (year, month).
    brands: iterable of brand names.
    category4: одна строка.

    Возвращает:
        {
          "qty": float,
          "revenue": float,
          "share_qty": float | None,
          "share_revenue": float | None,
          "cat4_qty": float,
          "cat4_revenue": float,
        }
    """
    months_set = set(period_months)
    brands_set = set(brands)

    # --- Числители: сумма по (cat4, brand) для выбранных месяцев/брендов ---
    numerator = _empty_agg()

    # --- Знаменатели: сумма по cat4 за выбранные месяцы (все бренды) ---
    denominator = _empty_agg()

    for file_data in mbt_catalog:
        key_month = (file_data["year"], file_data["month"])
        if key_month not in months_set:
            continue

        # Знаменатель: by_cat4
        cat4_agg = file_data["by_cat4"].get(category4)
        if cat4_agg:
            denominator["qty"] += cat4_agg["qty"]
            denominator["revenue"] += cat4_agg["revenue"]

        # Числитель: by_cat4_brand, суммируем по всем выбранным брендам
        by_cb = file_data["by_cat4_brand"]
        for brand in brands_set:
            cell = by_cb.get((category4, brand))
            if cell:
                numerator["qty"] += cell["qty"]
                numerator["revenue"] += cell["revenue"]

    share_qty = (numerator["qty"] / denominator["qty"]) if denominator["qty"] > 0 else None
    share_revenue = (numerator["revenue"] / denominator["revenue"]) if denominator["revenue"] > 0 else None

    return {
        "qty": numerator["qty"],
        "revenue": numerator["revenue"],
        "share_qty": share_qty,
        "share_revenue": share_revenue,
        "cat4_qty": denominator["qty"],
        "cat4_revenue": denominator["revenue"],
    }


def get_available_months(mbt_catalog: list[dict]) -> list[tuple[int, int]]:
    """
    Возвращает отсортированный список доступных (year, month),
    по которым есть файлы МБТ в каталоге.
    """
    months = {(f["year"], f["month"]) for f in mbt_catalog}
    return sorted(months)


def get_available_brands(mbt_catalog: list[dict]) -> list[str]:
    """Все уникальные бренды во всех файлах МБТ."""
    brands: set[str] = set()
    for f in mbt_catalog:
        for (_cat4, brand) in f["by_cat4_brand"].keys():
            if brand:
                brands.add(brand)
    return sorted(brands)


def get_available_categories4(mbt_catalog: list[dict]) -> list[str]:
    """Все уникальные категории ур.4."""
    cats: set[str] = set()
    for f in mbt_catalog:
        for cat4 in f["by_cat4"].keys():
            if cat4:
                cats.add(cat4)
    return sorted(cats)


# === Помощники для UI ===

MONTHS_RU_SHORT = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def format_month_label(ym: tuple[int, int]) -> str:
    """(2026, 7) -> 'июл 2026'."""
    year, month = ym
    return f"{MONTHS_RU_SHORT[month - 1]} {year}"


def format_period_label(months: list[tuple[int, int]]) -> str:
    """
    Список месяцев -> компактная строка.
    Если идут подряд — 'янв–мар 2026'.
    Иначе — перечисление через запятую.
    """
    if not months:
        return "—"
    if len(months) == 1:
        return format_month_label(months[0])

    months_sorted = sorted(months)
    # Проверим, идут ли подряд в одном году
    same_year = all(m[0] == months_sorted[0][0] for m in months_sorted)
    consecutive = same_year and all(
        months_sorted[i + 1][1] - months_sorted[i][1] == 1
        for i in range(len(months_sorted) - 1)
    )
    if consecutive:
        year = months_sorted[0][0]
        m_start = months_sorted[0][1]
        m_end = months_sorted[-1][1]
        return f"{MONTHS_RU_SHORT[m_start - 1]}–{MONTHS_RU_SHORT[m_end - 1]} {year}"

    return ", ".join(format_month_label(m) for m in months_sorted)