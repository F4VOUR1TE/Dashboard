from datetime import date
from pathlib import Path
import json
import threading

import streamlit as st

from src.catalog import build_catalog
from src.selector import build_dashboard
from ui.tiles import render_dashboard_block
from ui.mbt_tiles import render_mbt_block


st.set_page_config(
    page_title="Sell-out дашборд",
    layout="wide",
)

DEFAULT_DATA_DIR = "data"
SETTINGS_FILE = Path("settings.json")


# Чтобы протестировать на 18.10.2026 True.
# Чтобы вернуть реальную дату сегодня False.
USE_FAKE_DATE = True 
FAKE_DATE = date(2026, 10, 18)



# Настройки 

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(settings: dict) -> None:
    try:
        SETTINGS_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


#Диалог выбора папки 

def _ask_directory(initial: str) -> str | None:
    result: dict = {"path": None}

    def _run():
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askdirectory(
                initialdir=initial if Path(initial).exists() else ".",
                title="Выберите папку с данными",
            )
            root.destroy()
            result["path"] = path or None
        except Exception as e:
            result["path"] = None
            result["error"] = str(e)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join()
    return result.get("path")


def _on_choose_directory():
    chosen = _ask_directory(st.session_state.selected_dir)
    if chosen:
        st.session_state.selected_dir = chosen
        st.session_state.dir_input = chosen
        settings = load_settings()
        settings["data_dir"] = chosen
        save_settings(settings)


def _on_dir_input_change():
    value = st.session_state.dir_input.strip() or DEFAULT_DATA_DIR
    st.session_state.selected_dir = value
    settings = load_settings()
    settings["data_dir"] = value
    save_settings(settings)


# Загрузка данных 

@st.cache_data(show_spinner=False)
def load_data(data_dir_str: str, files_mtimes: tuple, today_iso: str) -> dict:
    data_dir = Path(data_dir_str)
    files = sorted(
        list(data_dir.glob("Scar__prod_*.xlsx"))
        + list(data_dir.glob("*МБТ*.xlsx"))
    )
    catalog = build_catalog(files)
    today = date.fromisoformat(today_iso)
    dashboard = build_dashboard(catalog["sellout"], today)
    return {
        "dashboard": dashboard,
        "mbt_catalog": catalog["mbt"],
    }


def files_signature(data_dir_str: str) -> tuple:
    data_dir = Path(data_dir_str)
    if not data_dir.exists():
        return ()
    files = (
        list(data_dir.glob("Scar__prod_*.xlsx"))
        + list(data_dir.glob("*МБТ*.xlsx"))
    )
    return tuple(sorted((f.name, f.stat().st_mtime) for f in files))


# Состояние 

if "selected_dir" not in st.session_state:
    settings = load_settings()
    st.session_state.selected_dir = settings.get("data_dir", DEFAULT_DATA_DIR)

if "dir_input" not in st.session_state:
    st.session_state.dir_input = st.session_state.selected_dir


#UI

st.title("Sell-out дашборд")

#дата
today = FAKE_DATE if USE_FAKE_DATE else date.today()

st.caption(f"Данные на {today.strftime('%d.%m.%Y')}")

with st.sidebar:
    st.header("Настройки")
    st.text_input(
        "Папка с данными",
        key="dir_input",
        help="Путь к папке с данными. По умолчанию — data/",
        on_change=_on_dir_input_change,
    )
    st.button(
        "📂 Выбрать папку",
        use_container_width=True,
        on_click=_on_choose_directory,
    )
    if not Path(st.session_state.selected_dir).exists():
        st.error(f"Папка не найдена: {st.session_state.selected_dir}")

col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Обновить", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

data_dir_str = st.session_state.selected_dir
sig = files_signature(data_dir_str)

if not sig:
    st.warning(f"В папке {data_dir_str} нет файлов")
    st.stop()


data = load_data(data_dir_str, sig, today.isoformat())
dashboard = data["dashboard"]
mbt_catalog = data["mbt_catalog"]

# 20 плиток Блок1
render_dashboard_block(dashboard, mode="qty", title="Штуки")
st.markdown("---")
render_dashboard_block(dashboard, mode="money", title="Деньги с НДС, тыс. руб.")

# Блок2
st.markdown("---")
render_mbt_block(mbt_catalog)