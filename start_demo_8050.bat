@echo off
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r backend\requirements.txt
if not exist data\triage_model.joblib python backend\train_model.py
start "NEXUS CARE" http://127.0.0.1:8050
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8050
