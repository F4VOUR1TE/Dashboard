@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

set PY_EMBED=python-embed\python.exe
set VENV_PY=venv\Scripts\python.exe
set PTH_FILE=python-embed\python310._pth

REM --- Проверка portable Python ---
if not exist "%PY_EMBED%" (
    echo [ОШИБКА] Не найден portable Python: %PY_EMBED%
    echo Положите embeddable-дистрибутив Python 3.10.11 в папку python-embed\
    pause
    exit /b 1
)

REM --- Настройка portable Python ---
if not exist "python-embed\Lib\site-packages" mkdir "python-embed\Lib\site-packages"
if not exist "python-embed\get-pip.py" (
    echo [0/5] Скачиваю get-pip.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python-embed\get-pip.py'"
)

findstr /r "^import site" "%PTH_FILE%" >nul
if errorlevel 1 (
    echo import site>>"%PTH_FILE%"
)

REM --- Установка pip в portable Python ---
if not exist "python-embed\Lib\site-packages\pip" (
    echo [1/5] Устанавливаю pip в portable Python...
    "%PY_EMBED%" "python-embed\get-pip.py"
)

REM --- Установка virtualenv в portable Python ---
if not exist "python-embed\Lib\site-packages\virtualenv" (
    echo [2/5] Устанавливаю virtualenv в portable Python...
    "%PY_EMBED%" -m pip install virtualenv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить virtualenv
        pause
        exit /b 1
    )
)

REM --- Создание venv через virtualenv ---
if not exist "%VENV_PY%" (
    echo [3/5] Создаю виртуальное окружение...
    "%PY_EMBED%" -m virtualenv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать venv
        pause
        exit /b 1
    )
)

REM --- Установка зависимостей ---
if not exist "venv\.deps_installed" (
    echo [4/5] Устанавливаю зависимости...
    "%VENV_PY%" -m pip install --upgrade pip
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        pause
        exit /b 1
    )
    echo ok > "venv\.deps_installed"
)

REM --- Запуск Streamlit ---
echo [5/5] Запускаю дашборд...
echo Открой в браузере: http://localhost:8501
"%VENV_PY%" -m streamlit run app.py

endlocal