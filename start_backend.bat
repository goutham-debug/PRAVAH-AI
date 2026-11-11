@echo off
cd /d "%~dp0backend"
if not exist .env (echo Missing backend\.env. Copy .env.example and fill it in. & exit /b 1)
python -m pip install -r requirements.txt
python app.py
