from datetime import date, timedelta
from calendar import monthrange

MONTHS_RU = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]

def _month_full_days(year: int, month: int) -> set[date]:
    """Все дни месяца."""
    last = monthrange(year, month)[1]
    return {date(year, month, d) for d in range(1, last + 1)}


def _week_full_days(iso_year: int, iso_week: int) -> set[date]:
    """Все 7 дней ISO-недели (пн–вс)."""
    monday = date.fromisocalendar(iso_year, iso_week, 1)
    return {monday + timedelta(days=i) for i in range(7)}


def _fmt_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def format_qty(value: float | None) -> str:
    """Штуки: целое число с разделителями тысяч."""
    if value is None:
        return "нет данных"
    return f"{value:,.0f}".replace(",", " ")


def format_money(value: float | None) -> str:
    """Деньги: округление до тысяч, с разделителями."""
    if value is None:
        return "нет данных"
    thousands = round(value / 1000)
    return f"{thousands:,.0f}".replace(",", " ") + " ₽"


def format_money_full(value) -> str:
    """
    Полные рубли с разделителями, без округления до тысяч.
    12345678.9 -> '12 345 679 ₽'
    """
    if value is None:
        return "—"
    # Округляем до целого рубля, разделитель — пробел
    rounded = round(value)
    return f"{rounded:,} ₽".replace(",", " ")


def format_missing_periods(dates: list[date]) -> str:
    """
    Упрощает список пропущенных дат:
      - целые месяцы → "апрель 2026"
      - целые недели  → "неделя 06.04–12.04.2026"
      - остальное     → "07.04.2026"
    Возвращает строку с переносами (для HTML-тултипа).
    """
    if not dates:
        return ""

    remaining = set(dates)
    parts: list[str] = []

    # 1. Целые месяцы
    months_seen = {}
    for d in sorted(remaining):
        months_seen.setdefault((d.year, d.month), set()).add(d)
    for (y, m), days_in_month in sorted(months_seen.items()):
        if days_in_month == _month_full_days(y, m):
            parts.append(f"{MONTHS_RU[m - 1]} {y}")
            remaining -= days_in_month

    # 2. Целые недели
    weeks_seen = {}
    for d in sorted(remaining):
        iso = d.isocalendar()
        weeks_seen.setdefault((iso[0], iso[1]), set()).add(d)
    for (iso_y, iso_w), days_in_week in sorted(weeks_seen.items()):
        full_week = _week_full_days(iso_y, iso_w)
        if days_in_week == full_week:
            monday = min(full_week)
            sunday = max(full_week)
            parts.append(f"неделя {_fmt_date(monday)}–{_fmt_date(sunday)}")
            remaining -= days_in_week

    # 3. Оставшиеся отдельные дни
    for d in sorted(remaining):
        parts.append(_fmt_date(d))

    return "\n".join(parts)

