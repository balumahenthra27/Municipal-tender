@echo off
echo ===================================================
echo   MUNICIPAL TENDER WATCHDOG - BACKEND SERVER
echo ===================================================
cd /d "%~dp0backend"

echo [1/3] Checking dependencies...
py -m pip install -r requirements.txt

echo [2/3] Verifying database and importing dataset...
py importer.py

echo [3/3] Launching FastAPI server on http://localhost:8000 ...
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause
