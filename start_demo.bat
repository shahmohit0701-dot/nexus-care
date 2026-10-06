@echo off
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r backend\requirements.txt
python backend\train_model.py
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
