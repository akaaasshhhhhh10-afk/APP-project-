@echo off
REM Starts the Flask (5000) and FastAPI (8000) services in two windows.
cd /d "%~dp0backend"
if not exist .venv ( python -m venv .venv && .venv\Scripts\python -m pip install -r requirements.txt )
start "Alumni Connect - Flask :5000" cmd /k ".venv\Scripts\python flask_service\app.py"
start "Alumni Connect - FastAPI :8000" cmd /k ".venv\Scripts\python -m uvicorn fastapi_service.main:app --port 8000 --reload"
