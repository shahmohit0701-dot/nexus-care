@echo off
cd /d "%~dp0"
where python >nul 2>nul || (echo Python is required.&pause&exit /b 1)
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8060
pause
