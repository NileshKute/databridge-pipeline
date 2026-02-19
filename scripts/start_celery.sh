#!/bin/bash
source backend/.venv/bin/activate
cd backend
celery -A app.core.celery_app worker -l info -Q scanning,transfer,notifications --concurrency=4
