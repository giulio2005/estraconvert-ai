#!/bin/bash

echo "🛑 Arresto EstraConvert..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Stop Backend
if [ -f backend.pid ]; then
    PID=$(cat backend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo "✅ Backend arrestato"
    fi
    rm backend.pid
fi

# Stop Frontend
if [ -f frontend.pid ]; then
    PID=$(cat frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo "✅ Frontend arrestato"
    fi
    rm frontend.pid
fi

# Stop Celery
if [ -f celery.pid ]; then
    PID=$(cat celery.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo "✅ Celery worker arrestato"
    fi
    rm celery.pid
fi

# Cleanup any remaining processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "celery.*worker" 2>/dev/null
pkill -f "next dev" 2>/dev/null

echo ""
echo "✅ Tutti i servizi sono stati arrestati"
