#!/usr/bin/env bash
set -e

python scripts/wait_for_db.py
python scripts/init_db.py

uvicorn app.main:app --host 0.0.0.0 --port 8000
