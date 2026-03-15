#!/bin/sh
set -e
PYTHONPATH=. alembic upgrade head
exec gunicorn app.main:app --config gunicorn.conf.py
