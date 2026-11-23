from pathlib import Path
import traceback

from src.parser import parse_sellout_file
from src.parser_mbt import parse_mbt_file, parse_mbt_filename


def build_catalog(files: list[Path]) -> dict:
    
    sellout_parsed: list[dict] = []
    mbt_parsed: list[dict] = []

    for f in files:
        name = f.name

        # МБТ
        if parse_mbt_filename(name) is not None:
            try:
                item = parse_mbt_file(f)
                if item is not None:
                    mbt_parsed.append(item)
            except Exception as e:
                print(f"[!] МБТ: не удалось обработать {name}: "
                      f"{type(e).__name__}: {e}")
                traceback.print_exc()
            continue

        # sell-out
        if name.startswith("Scar__prod_"):
            try:
                item = parse_sellout_file(f)
                sellout_parsed.append(item)
            except Exception as e:
                print(f"[!] Sell-out: не удалось обработать {name}: "
                      f"{type(e).__name__}: {e}")
                traceback.print_exc()
            continue

        # всё остальное игнорируем 
        print(f"[i] Пропущен файл (не МБТ и не Scar__prod_): {name}")

    return {
        "sellout": _dedup_sellout(sellout_parsed),
        "mbt": _dedup_mbt(mbt_parsed),
    }


def _dedup_sellout(parsed: list[dict]) -> list[dict]:
    """Дедупликация sell-out по (start_date, end_date)."""
    grouped: dict[tuple, list[dict]] = {}
    for item in parsed:
        key = (item["start_date"], item["end_date"])
        grouped.setdefault(key, []).append(item)

    catalog: list[dict] = []
    for key, items in grouped.items():
        if len(items) == 1:
            catalog.append(items[0])
            continue
        items_sorted = sorted(
            items,
            key=lambda x: (Path(x["source_path"]).stat().st_mtime, x["source_file"]),
            reverse=True,
        )
        chosen = items_sorted[0]
        catalog.append(chosen)
        dropped = [x["source_file"] for x in items_sorted[1:]]
        print(f"[i] Sell-out дубль за {key[0]}..{key[1]}: оставлен "
              f"{chosen['source_file']}, отброшены: {dropped}")

    catalog.sort(key=lambda x: (x["start_date"], x["end_date"]))
    return catalog


def _dedup_mbt(parsed: list[dict]) -> list[dict]:
    """Дедупликация МБТ по (year, month)."""
    grouped: dict[tuple, list[dict]] = {}
    for item in parsed:
        key = (item["year"], item["month"])
        grouped.setdefault(key, []).append(item)

    catalog: list[dict] = []
    for key, items in grouped.items():
        if len(items) == 1:
            catalog.append(items[0])
            continue
        items_sorted = sorted(
            items,
            key=lambda x: (Path(x["source_path"]).stat().st_mtime, x["source_file"]),
            reverse=True,
        )
        chosen = items_sorted[0]
        catalog.append(chosen)
        dropped = [x["source_file"] for x in items_sorted[1:]]
        print(f"[i] МБТ дубль за {key[1]:02d}.{key[0]}: оставлен "
              f"{chosen['source_file']}, отброшены: {dropped}")

    catalog.sort(key=lambda x: (x["year"], x["month"]))
    return catalog


def catalog_report(catalog: dict) -> None:
    """Печатает краткий отчёт по каталогу (sell-out + МБТ)."""
    sellout = catalog["sellout"]
    mbt = catalog["mbt"]

    print()
    print("=== КАТАЛОГ ===")
    print(f"Sell-out файлов: {len(sellout)}")
    print(f"МБТ файлов:      {len(mbt)}")

    if sellout:
        print(f"\nПериод sell-out: {sellout[0]['start_date']} — "
              f"{sellout[-1]['end_date']}")
        by_type: dict[str, int] = {}
        for item in sellout:
            by_type[item["report_type"]] = by_type.get(item["report_type"], 0) + 1
        print("По типам sell-out:")
        for t, n in by_type.items():
            print(f"  {t:8s}: {n}")
        print("\nSell-out список:")
        for item in sellout:
            print(f"  {item['start_date']} — {item['end_date']}  "
                  f"({item['report_type']:8s})  {item['source_file']}")

    if mbt:
        print("\nМБТ список:")
        for item in mbt:
            print(f"  {item['year']}-{item['month']:02d}  "
                  f"({item['start_date']} — {item['end_date']})  "
                  f"{item['source_file']}  "
                  f"[строк: {item['rows_count']}, "
                  f"категорий: {len(item['by_cat4'])}]")