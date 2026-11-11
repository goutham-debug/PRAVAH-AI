#!/bin/bash
# Development start. Production: gunicorn -w 2 -b 127.0.0.1:5000 app:app (from backend/)
set -e
cd "$(dirname "$0")/backend"
[ -f .env ] || { echo "Missing backend/.env. Copy .env.example and fill it in."; exit 1; }
python3 -m pip install -r requirements.txt
python3 app.py
