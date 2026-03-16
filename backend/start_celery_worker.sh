#!/bin/bash
# Celery worker startup script for EstraConvert

echo "🚀 Starting Celery worker for EstraConvert..."
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ ERROR: Redis is not running!"
    echo "   Please start Redis first:"
    echo "   brew services start redis"
    echo ""
    exit 1
fi

echo "✅ Redis is running"
echo ""

# Start Celery worker with options:
# -A celery_app: Application module
# --loglevel=info: Log level
# -P threads: Use thread pool (good for I/O bound tasks like OCR/AI)
# -c 4: Use 4 concurrent workers
echo "🔧 Starting Celery worker with 4 threads..."
celery -A celery_app worker --loglevel=info -P threads -c 4

# Alternative: Use prefork pool (process-based) instead of threads
# celery -A celery_app worker --loglevel=info -P prefork -c 4
