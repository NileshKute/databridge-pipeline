#!/bin/bash
echo "=== Starting DataBridge Pipeline ==="

# Build frontend if dist doesn't exist
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend && npm run build && cd ..
fi

# Activate venv
source backend/.venv/bin/activate

# Start Celery worker in background
echo "Starting Celery worker..."
cd backend
celery -A app.core.celery_app worker -l info -Q scanning,transfer,notifications &
CELERY_PID=$!
cd ..

# Start FastAPI server
echo "Starting FastAPI server on port ${PORT:-8000}..."
cd backend
uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --workers 4
cd ..

# Cleanup on exit
trap "kill $CELERY_PID 2>/dev/null" EXIT
