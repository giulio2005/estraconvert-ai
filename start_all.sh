#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting EstraConvert...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure log directories exist
mkdir -p backend/logs
mkdir -p backend/uploads

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo -e "${YELLOW}⚠️  Redis is not running. Attempting to start...${NC}"
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes
        echo -e "${GREEN}✅ Redis started${NC}"
    else
        echo -e "${RED}❌ Redis not found. Please install/start Redis manually.${NC}"
        # We don't exit here because maybe it's running on a remote server or different port/name
    fi
else
    echo -e "${GREEN}✅ Redis is running${NC}"
fi

# --- Start Backend ---
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
else
    echo -e "${YELLOW}📦 Starting Backend (FastAPI)...${NC}"
    cd backend
    if [ ! -d "venv" ]; then
        echo -e "${RED}❌ Virtual environment not found. Run ./setup.sh first.${NC}"
        exit 1
    fi
    # Use absolute path to python in venv for reliability
    nohup venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    echo $! > ../backend.pid
    cd ..
    sleep 2
    
    # Check if process is still running
    if kill -0 $(cat backend.pid) 2>/dev/null; then
        echo -e "${GREEN}✅ Backend started (PID: $(cat backend.pid))${NC}"
    else
        echo -e "${RED}❌ Backend failed to start. Check backend/logs/backend.log${NC}"
    fi
fi

# --- Start Celery Worker ---
if pgrep -f "celery.*worker" > /dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Celery worker already running${NC}"
else
    echo -e "${YELLOW}⚙️  Starting Celery Worker...${NC}"
    cd backend
    # Use absolute path to celery in venv
    # Using -P threads for I/O bound tasks (API calls)
    nohup venv/bin/celery -A celery_app worker --loglevel=info -P threads -c 4 -n worker1@%h > logs/celery.log 2>&1 &
    echo $! > ../celery.pid
    cd ..
    sleep 2
    
    if kill -0 $(cat celery.pid) 2>/dev/null; then
        echo -e "${GREEN}✅ Celery worker started (PID: $(cat celery.pid))${NC}"
    else
        echo -e "${RED}❌ Celery worker failed to start. Check backend/logs/celery.log${NC}"
    fi
fi

# --- Start Frontend ---
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
else
    echo -e "${YELLOW}🌐 Starting Frontend (Next.js)...${NC}"
    cd frontend
    # Pass hostname 0.0.0.0 to Next.js dev server
    # Note: npm run dev -- -H 0.0.0.0 passes the host flag to next dev
    nohup npm run dev -- -H 0.0.0.0 > ../frontend.log 2>&1 &
    echo $! > ../frontend.pid
    cd ..
    sleep 5 # Next.js takes a bit longer to start
    
    if kill -0 $(cat frontend.pid) 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend started (PID: $(cat frontend.pid))${NC}"
    else
        echo -e "${RED}❌ Frontend failed to start. Check frontend.log${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ All services initiated!${NC}"
echo ""
echo "📱 Access:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 To stop services: ./stop_all.sh"
echo "📂 Logs are in backend/logs/ and frontend.log"
