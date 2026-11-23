import re
from calendar import monthrange
from datetime import date
from pathlib import Path

from openpyxl import load_workbook


# Русские месяцы в именительном падеже → номер месяца
MONTHS_RU = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}

# Регулярка для имени файла: ...МБТ климат <месяц> <год>.xlsx
FILENAME_RE = re.compile(
    r"МБТ\s+климат\s+(" + "|".join(MONTHS_RU.keys()) + r")\s+(\d{4})",
    re.IGNORECASE,
)

REQUIRED_COLUMNS = (
    "Категория уровень 1",
    "Категория уровень 4",
    "Бренд",
    "Продажи",
    "Продажи SO",
)

CATEGORY_LEVEL_1_VALUE = "04. МБТ"


def parse_mbt_filename(name: str) -> dict | None:
    """
    Разбирает имя файла вида '...МБТ климат июль 2026.xlsx'.
    Возвращает:
        {
            "report_type": "mbt_monthly",
            "month": 7,
            "year": 2026,
            "start_date": date(2026, 7, 1),
            "end_date": date(2026, 7, 31),
            "source_file": name,
        }
    или None, если имя не подходит.
    """
    match = FILENAME_RE.search(name)
    if not match:
        return None

    month_name = match.group(1).lower()
    year = int(match.group(2))
    month = MONTHS_RU[month_name]

    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)

    return {
        "report_type": "mbt_monthly",
        "month": month,
        "year": year,
        "start_date": start,
        "end_date": end,
        "source_file": name,
    }


def _to_float(value) -> float:
    """Аккуратно приводит значение к float. None / '' / '-' → 0.0."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".").replace("\xa0", "").replace(" ", "")
    if not s or s in {"-", "—"}:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def read_mbt_rows(path: Path) -> list[dict]:
    """
    Читает один файл МБТ в read_only-режиме, одним проходом:
      - ищет строку заголовков (по REQUIRED_COLUMNS),
      - после неё собирает строки, где Категория уровень 1 == '04. МБТ'.
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.worksheets[0]

        cols: dict[str, int] | None = None  # {column_name: 0-based index}
        header_row_idx: int | None = None
        rows: list[dict] = []

        # Максимум 50 строк — на поиск заголовка.
        # Если за 50 строк не нашли — считаем, что файл не того формата.
        HEADER_SCAN_LIMIT = 50

        for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
            # --- поиск заголовка ---
            if cols is None:
                # Преобразуем строку в словарь {имя_колонки: индекс}
                row_map: dict[str, int] = {}
                for col_idx, value in enumerate(row):
                    if value is None:
                        continue
                    name = str(value).strip()
                    if name:
                        row_map.setdefault(name, col_idx)

                if all(c in row_map for c in REQUIRED_COLUMNS):
                    cols = {c: row_map[c] for c in REQUIRED_COLUMNS}
                    header_row_idx = row_idx
                elif row_idx >= HEADER_SCAN_LIMIT:
                    return []  # заголовок не найден — файл не подходит
                continue

            # --- сбор данных ---
            cat1 = row[cols["Категория уровень 1"]] if cols["Категория уровень 1"] < len(row) else None
            if cat1 is None:
                continue
            if str(cat1).strip() != CATEGORY_LEVEL_1_VALUE:
                continue

            def _get(name: str):
                idx = cols[name] # type: ignore
                return row[idx] if idx < len(row) else None

            cat4 = _get("Категория уровень 4")
            brand = _get("Бренд")
            qty = _to_float(_get("Продажи"))
            revenue = _to_float(_get("Продажи SO"))

            rows.append({
                "category4": str(cat4).strip() if cat4 is not None else "",
                "brand": str(brand).strip() if brand is not None else "",
                "qty": qty,
                "revenue_vat": revenue,
            })

        return rows
    finally:
        wb.close()


def aggregate_mbt(rows: list[dict]) -> dict:
    by_cat4_brand: dict[tuple[str, str], dict[str, float]] = {}
    by_cat4: dict[str, dict[str, float]] = {}

    for r in rows:
        cat4 = r["category4"]
        brand = r["brand"]
        key = (cat4, brand)
        if key not in by_cat4_brand:
            by_cat4_brand[key] = {"qty": 0.0, "revenue": 0.0}
        by_cat4_brand[key]["qty"] += r["qty"]
        by_cat4_brand[key]["revenue"] += r["revenue_vat"]

        if cat4 not in by_cat4:
            by_cat4[cat4] = {"qty": 0.0, "revenue": 0.0}
        by_cat4[cat4]["qty"] += r["qty"]
        by_cat4[cat4]["revenue"] += r["revenue_vat"]

    return {
        "by_cat4_brand": by_cat4_brand,
        "by_cat4": by_cat4,
    }


def parse_mbt_file(path: Path) -> dict | None:    
    meta = parse_mbt_filename(path.name)
    if meta is None:
        return None

    rows = read_mbt_rows(path)
    aggregates = aggregate_mbt(rows)

    return {
        **meta,
        "source_path": str(path),
        "rows_count": len(rows),
        "by_cat4_brand": aggregates["by_cat4_brand"],
        "by_cat4": aggregates["by_cat4"],
    }