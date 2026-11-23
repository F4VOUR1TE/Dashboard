from datetime import date, timedelta

from src.periods import get_period_bounds


SOFT_PERIODS = {
    "current_day", "current_week", "current_month",
    "current_year_ytd", "last_year_ytd",
}


def _covers_fully(file_start: date, file_end: date,
                  period_start: date, period_end: date) -> bool:
    return file_start >= period_start and file_end <= period_end


def _days_range(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def select_sources(catalog: list[dict],
                   period_start: date,
                   period_end: date) -> dict:
    all_days = set(_days_range(period_start, period_end))
    remaining_days = set(all_days)
    chosen_files = []

    # 1. Monthly
    for item in catalog:
        if item["report_type"] != "monthly":
            continue
        if _covers_fully(item["start_date"], item["end_date"],
                         period_start, period_end):
            chosen_files.append(item)
            remaining_days -= set(_days_range(item["start_date"], item["end_date"]))

    # 2. Weekly 
    for item in catalog:
        if item["report_type"] != "weekly":
            continue
        if not _covers_fully(item["start_date"], item["end_date"],
                             period_start, period_end):
            continue
        item_days = set(_days_range(item["start_date"], item["end_date"]))
        if item_days.issubset(remaining_days):
            chosen_files.append(item)
            remaining_days -= item_days

    # 3. Daily
    for item in catalog:
        if item["report_type"] != "daily":
            continue
        if item["start_date"] == item["end_date"] and item["start_date"] in remaining_days:
            chosen_files.append(item)
            remaining_days.discard(item["start_date"])

    return {
        "files": chosen_files,
        "covered_days": all_days - remaining_days,
        "missing_days": remaining_days,
    }


def _empty_tile() -> dict:
    return {
        "qty": 0.0,
        "amount_no_vat": 0.0,
        "amount_with_vat": 0.0,
        "status": "no_data",
        "missing_days": [],
        "sources": [],
    }


def build_tile(catalog: list[dict],
               period_start: date,
               period_end: date,
               period_name: str) -> dict:
    selection = select_sources(catalog, period_start, period_end)
    files = selection["files"]
    missing = selection["missing_days"]

    qty = sum(f["qty"] for f in files)
    amount_no_vat = sum(f["amount_no_vat"] for f in files)
    amount_with_vat = round(amount_no_vat * 1.22, 2)

    if not files:
        status = "no_data"
    elif missing and period_name not in SOFT_PERIODS:
        status = "no_data"
    elif missing:
        status = "partial"
    else:
        status = "ok"

    return {
        "qty": qty,
        "amount_no_vat": amount_no_vat,
        "amount_with_vat": amount_with_vat,
        "status": status,
        "missing_days": sorted(missing),
        "sources": [f["source_file"] for f in files],
    }


# def build_growth(tile: dict, base_tile: dict) -> dict:
#     base_missing = list(base_tile.get("missing_days", []))
#     base_no_data = base_tile["status"] == "no_data"

#     if base_no_data:
#         return {
#             "growth_qty": None,
#             "growth_revenue": None,
#             "base_missing_days": [],
#             "base_no_data": True,
#         }

#     base_qty = base_tile["qty"]
#     base_rev = base_tile["amount_with_vat"]

#     growth_qty = (
#         (tile["qty"] - base_qty) / base_qty
#         if base_qty > 0 else None
#     )
#     growth_rev = (
#         (tile["amount_with_vat"] - base_rev) / base_rev
#         if base_rev > 0 else None
#     )

#     return {
#         "growth_qty": growth_qty,
#         "growth_revenue": growth_rev,
#         "base_missing_days": base_missing,
#         "base_no_data": False,
#     }
def build_growth(tile: dict, base_tile: dict) -> dict:
    base_missing = list(base_tile.get("missing_days", []))
    base_no_data = base_tile["status"] == "no_data"

    if base_no_data:
        return {
            "growth_qty": None,
            "growth_revenue": None,
            "base_missing_days": base_missing, # <-- ТЕПЕРЬ ПЕРЕДАЕМ ДНИ СЮДА
            "base_no_data": True,
        }

    base_qty = base_tile["qty"]
    base_rev = base_tile["amount_with_vat"]

    growth_qty = (
        (tile["qty"] - base_qty) / base_qty
        if base_qty > 0 else None
    )
    growth_rev = (
        (tile["amount_with_vat"] - base_rev) / base_rev
        if base_rev > 0 else None
    )

    return {
        "growth_qty": growth_qty,
        "growth_revenue": growth_rev,
        "base_missing_days": base_missing,
        "base_no_data": False,
    }


def build_dashboard(catalog: list[dict], today: date) -> dict:
    periods = get_period_bounds(today)

    dashboard: dict[str, dict] = {}
    for name, (start, end) in periods.items():
        dashboard[name] = build_tile(catalog, start, end, name)

    # Приросты — только для last_week и last_month.
    # Обновили кортежи, чтобы использовать новые ключи *_year_ago
    for tile_name, base_name, base_ya_name in (
        ("last_week",  "prev_week",  "last_week_year_ago"),
        ("last_month", "prev_month", "last_month_year_ago"),
    ):
        tile = dashboard[tile_name]
        base = dashboard[base_name]
        base_ya = dashboard[base_ya_name]

        tile["growth_prev"] = build_growth(tile, base)
        tile["growth_prev_year_ago"] = build_growth(tile, base_ya)

    return dashboard