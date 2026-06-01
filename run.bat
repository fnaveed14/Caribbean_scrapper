@echo off
REM ─────────────────────────────────────────────────────────────────
REM  Caribbean Data Scraper — launcher (Windows)
REM  Double-click this file to start
REM ─────────────────────────────────────────────────────────────────

cd /d "%~dp0"

echo ================================================
echo   Caribbean Regional Report Data Scraper
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: Python not found.
    echo Install from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

FOR /F "tokens=*" %%i IN ('python --version') DO SET PYVER=%%i
echo Python found: %PYVER%

REM Create venv if not present
IF NOT EXIST ".venv" (
    echo.
    echo Creating virtual environment (first-time setup)...
    python -m venv .venv
)

REM Activate
call .venv\Scripts\activate.bat

REM Install packages
echo.
echo Installing / checking packages...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo Launching app — your browser will open automatically...
echo (Close this window or press Ctrl+C to stop)
echo.

streamlit run app.py --server.headless false --server.port 8501 --browser.gatherUsageStats false

pause
