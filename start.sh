#!/bin/bash

ROOT="$(pwd)"
PYTHON="$ROOT/Backend/venv/Scripts/python.exe"

echo "Starting SmartAudit..."

# Backend (FastAPI)
echo "[1/3] Starting Backend..."
(cd "$ROOT/Backend" && "$PYTHON" -m uvicorn main:app --reload) &
BACKEND_PID=$!

# Celery Worker
echo "[2/3] Starting Celery Worker..."
(cd "$ROOT/Backend" && "$PYTHON" -m celery -A celery_worker.celery_app worker --pool=solo --loglevel=info) &
CELERY_PID=$!

# Frontend (Vue)
echo "[3/3] Starting Frontend..."
(cd "$ROOT/Frontend/smart-audit-frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "All services started:"
echo "  Backend  -> http://localhost:8000  (PID $BACKEND_PID)"
echo "  Frontend -> http://localhost:5173  (PID $FRONTEND_PID)"
echo "  Celery   -> worker running         (PID $CELERY_PID)"
echo ""
echo "Press Ctrl+C to stop all services."

trap "echo 'Stopping...'; kill $BACKEND_PID $CELERY_PID $FRONTEND_PID; exit 0" SIGINT SIGTERM

wait
