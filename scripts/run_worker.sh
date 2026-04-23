#!/usr/bin/env bash
set -e

if [ -x "./venv/bin/celery" ]; then
    exec ./venv/bin/celery -A app.workers.celery_app.celery_app worker --loglevel=info
fi

exec celery -A app.workers.celery_app.celery_app worker --loglevel=info
