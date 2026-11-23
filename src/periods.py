# from calendar import monthrange
# from datetime import date, timedelta

# from dateutil.relativedelta import relativedelta


# def _last_day_of_month(d: date) -> date:
#     """Последний день месяца для данной даты."""
#     return date(d.year, d.month, monthrange(d.year, d.month)[1])


# def _monday_of_week(d: date) -> date:
#     """Понедельник недели, содержащей d."""
#     return d - timedelta(days=d.weekday())


# def _sunday_of_week(d: date) -> date:
#     """Воскресенье недели, содержащей d."""
#     return _monday_of_week(d) + timedelta(days=6)


# def get_period_bounds(today: date) -> dict[str, tuple[date, date]]:
#     """
#     Возвращает границы периодов дашборда для заданной даты 'today'.
#     Все периоды — (start_date, end_date) включительно.
#     """
#     yesterday = today - timedelta(days=1)
#     year_ago = today - relativedelta(years=1)
#     yesterday_year_ago = yesterday - relativedelta(years=1)

#     # --- Текущие периоды ---
#     current_day = (today, today)
#     current_week = (_monday_of_week(today), today)
#     current_month = (today.replace(day=1), today)
#     current_year_ytd = (date(today.year, 1, 1), today)

#     # --- Вчера и прошлый день год назад ---
#     yesterday_period = (yesterday, yesterday)
#     prev_day_year_ago = (yesterday_year_ago, yesterday_year_ago)

#     # --- Прошлые периоды ---
#     last_week_monday = _monday_of_week(today) - timedelta(days=7)
#     last_week = (last_week_monday, last_week_monday + timedelta(days=6))

#     first_of_this_month = today.replace(day=1)
#     last_month_end = first_of_this_month - timedelta(days=1)
#     last_month = (last_month_end.replace(day=1), last_month_end)

#     # --- Прошлый год накопительно: 01.01.(year-1) — year_ago ---
#     last_year_ytd = (date(today.year - 1, 1, 1), year_ago)

#     # --- Год назад ---
#     day_year_ago = (year_ago, year_ago)
#     week_year_ago = (_monday_of_week(year_ago), _sunday_of_week(year_ago))
#     month_year_ago = (
#         year_ago.replace(day=1),
#         _last_day_of_month(year_ago),
#     )

#     # --- Позапрошлая неделя / позапрошлый месяц ---
#     prev_week_monday = last_week_monday - timedelta(days=7)
#     prev_week = (prev_week_monday, prev_week_monday + timedelta(days=6))

#     prev_month_end = last_month[0] - timedelta(days=1)
#     prev_month = (prev_month_end.replace(day=1), prev_month_end)

#     # --- Прошлая неделя/месяц ГОД НАЗАД ---
#     # Берем даты ПРОШЛОЙ недели/месяца и вычитаем год.
#     last_week_year_ago_day = last_week_monday - relativedelta(years=1)
#     last_week_year_ago = (
#         _monday_of_week(last_week_year_ago_day),
#         _sunday_of_week(last_week_year_ago_day),
#     )

#     last_month_year_ago_day = last_month[0] - relativedelta(years=1)
#     last_month_year_ago = (
#         last_month_year_ago_day.replace(day=1),
#         _last_day_of_month(last_month_year_ago_day),
#     )

#     return {
#         # Отображаемые в UI
#         "yesterday":           yesterday_period,
#         "prev_day_year_ago":   prev_day_year_ago,
#         "current_week":        current_week,
#         "current_month":       current_month,
#         "current_year_ytd":    current_year_ytd,
#         "last_week":           last_week,
#         "last_month":          last_month,
#         "last_year_ytd":       last_year_ytd,
#         "week_year_ago":       week_year_ago,
#         "month_year_ago":      month_year_ago,

#         # Только для расчёта приростов
#         "prev_week":           prev_week,
#         "prev_month":          prev_month,
#         "last_week_year_ago":  last_week_year_ago,
#         "last_month_year_ago": last_month_year_ago,

#         # Совместимость
#         "current_day":         current_day,
#         "day_year_ago":        day_year_ago,
#     }
from calendar import monthrange
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def _last_day_of_month(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def _monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _sunday_of_week(d: date) -> date:
    return _monday_of_week(d) + timedelta(days=6)


def _get_iso_week_bounds(year: int, week_num: int) -> tuple[date, date]:
    """Возвращает (понедельник, воскресенье) для заданного ISO-года и ISO-номера недели."""
    jan_4 = date(year, 1, 4)
    first_monday = jan_4 - timedelta(days=jan_4.weekday())
    target_monday = first_monday + timedelta(weeks=week_num - 1)
    return target_monday, target_monday + timedelta(days=6)


def get_period_bounds(today: date) -> dict[str, tuple[date, date]]:
    yesterday = today - timedelta(days=1)
    year_ago = today - relativedelta(years=1)
    yesterday_year_ago = yesterday - relativedelta(years=1)

    current_day = (today, today)
    current_week = (_monday_of_week(today), today)
    current_month = (today.replace(day=1), today)
    current_year_ytd = (date(today.year, 1, 1), today)

    yesterday_period = (yesterday, yesterday)
    prev_day_year_ago = (yesterday_year_ago, yesterday_year_ago)

    last_week_monday = _monday_of_week(today) - timedelta(days=7)
    last_week = (last_week_monday, last_week_monday + timedelta(days=6))

    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    last_month = (last_month_end.replace(day=1), last_month_end)

    last_year_ytd = (date(today.year - 1, 1, 1), year_ago)
    day_year_ago = (year_ago, year_ago)
    
    # --- НЕДЕЛЯ ГОД НАЗАД (через ISO) ---
    # year_ago уже имеет год -1, поэтому просто берем его ISO
    iso_ya = year_ago.isocalendar()
    week_year_ago = _get_iso_week_bounds(iso_ya.year, iso_ya.week)

    # --- МЕСЯЦ ГОД НАЗАД ---
    month_year_ago = (
        year_ago.replace(day=1),
        _last_day_of_month(year_ago),
    )

    # --- Позапрошлая неделя / позапрошлый месяц ---
    prev_week_monday = last_week_monday - timedelta(days=7)
    prev_week = (prev_week_monday, prev_week_monday + timedelta(days=6))

    prev_month_end = last_month[0] - timedelta(days=1)
    prev_month = (prev_month_end.replace(day=1), prev_month_end)

    # --- ПРОШЛАЯ НЕДЕЛЯ ГОД НАЗАД (через ISO) ---
    # Берем ISO-номер недели от понедельника прошлой недели (05.10.2026 -> 41)
    # И ищем 41-ю неделю 2025 года.
    iso_lw = last_week_monday.isocalendar()
    last_week_year_ago = _get_iso_week_bounds(iso_lw.year - 1, iso_lw.week)

    # --- ПРОШЛЫЙ МЕСЯЦ ГОД НАЗАД ---
    last_month_year_ago_day = last_month[0] - relativedelta(years=1)
    last_month_year_ago = (
        last_month_year_ago_day.replace(day=1),
        _last_day_of_month(last_month_year_ago_day),
    )

    return {
        "yesterday":           yesterday_period,
        "prev_day_year_ago":   prev_day_year_ago,
        "current_week":        current_week,
        "current_month":       current_month,
        "current_year_ytd":    current_year_ytd,
        "last_week":           last_week,
        "last_month":          last_month,
        "last_year_ytd":       last_year_ytd,
        "week_year_ago":       week_year_ago,
        "month_year_ago":      month_year_ago,
        "prev_week":           prev_week,
        "prev_month":          prev_month,
        "last_week_year_ago":  last_week_year_ago,
        "last_month_year_ago": last_month_year_ago,
        "current_day":         current_day,
        "day_year_ago":        day_year_ago,
    }