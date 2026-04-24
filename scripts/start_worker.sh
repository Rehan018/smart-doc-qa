#!/usr/bin/env bash
set -e

python scripts/wait_for_db.py

celery -A app.workers.celery_app.celery_app worker --loglevel=info
