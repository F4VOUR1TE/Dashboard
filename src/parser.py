import re
from calendar import monthrange
from datetime import date
from pathlib import Path

import pandas as pd


FILENAME_RE = re.compile(
    r"Scar__prod_(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{4})_"
)

# Заголовки, по которым ищем нужные колонки (теперь через регулярки).
# Ищем начало строки, а хвост (.*) позволяет ловить добавки типа "без комм надбавок"
COL_QTY_RE = re.compile(r"^кол-во", re.IGNORECASE)
COL_AMOUNT_RE = re.compile(r"^продажа без ндс", re.IGNORECASE)


def parse_filename(filename: str) -> dict:
    match = FILENAME_RE.search(filename)
    if not match:
        raise ValueError(f"Не удалось распарсить имя файла: {filename}")

    sd, sm, ed, em, year = map(int, match.groups())
    start = date(year, sm, sd)
    end = date(year, em, ed)

    if start == end:
        report_type = "daily"
    elif start.day == 1 and end == _last_day_of_month(end):
        report_type = "monthly"
    else:
        report_type = "weekly"

    return {
        "source_file": filename,
        "start_date": start,
        "end_date": end,
        "report_type": report_type,
    }


def _last_day_of_month(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def _find_header_row(df: pd.DataFrame, max_scan: int = 5) -> int:
    """
    Ищет строку, в которой есть одновременно 'Код' и 'Товар'.
    Возвращает индекс строки или бросает исключение.
    """
    for i in range(min(max_scan, len(df))):
        row = df.iloc[i].astype(str).str.strip().str.lower().tolist()
        if "код" in row and "товар" in row:
            return i
    raise ValueError("Не найдена строка с заголовками (Код / Товар)")


def _find_column(df: pd.DataFrame, header_row: int, regex: re.Pattern) -> int:
    """Ищет индекс колонки по регулярному выражению в строке заголовков."""
    headers = df.iloc[header_row].astype(str).str.strip().tolist()
    for idx, h in enumerate(headers):
        if regex.search(h):
            return idx
    raise ValueError(
        f"Не найдена колонка по паттерну '{regex.pattern}'. "
        f"Заголовки в строке {header_row}: {headers}"
    )


def _find_total_row(df: pd.DataFrame) -> int:
    """Ищет строку, где в колонке A написано 'итого'."""
    col_a = df[0].astype(str).str.strip().str.lower()
    mask = col_a == "итого"
    if not mask.any():
        raise ValueError("Не найдена строка 'Итого'")
    return int(mask.idxmax()) # type: ignore


def _to_float(value, default: float = 0.0) -> float:
    """Безопасно приводит значение к float."""
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_totals(file_path: str | Path) -> dict:
    """Читает Excel и вытаскивает итоговые цифры из строки 'Итого'."""
    df = pd.read_excel(file_path, engine="openpyxl", header=None)

    header_row = _find_header_row(df)
    
    # Передаем регулярки вместо строк
    col_qty = _find_column(df, header_row, COL_QTY_RE)
    col_amount = _find_column(df, header_row, COL_AMOUNT_RE)
    
    total_row = _find_total_row(df)

    qty = df.iloc[total_row, col_qty]
    amount = df.iloc[total_row, col_amount]

    return {
        "qty": _to_float(qty),
        "amount_no_vat": _to_float(amount),
    }


def parse_sellout_file(file_path: str | Path) -> dict:
    file_path = Path(file_path)
    result = parse_filename(file_path.name)
    result.update(read_totals(file_path))
    result["amount_with_vat"] = round(result["amount_no_vat"] * 1.22, 2)
    result["source_path"] = str(file_path)
    return result