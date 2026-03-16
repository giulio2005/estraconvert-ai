@echo off
setlocal

:: Colors
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "NC=[0m"

echo %GREEN%🚀 Starting EstraConvert...%NC%
cd /d "%~dp0"

:: Start Redis (Assuming it's installed and in PATH)
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo %YELLOW%⚠️  Redis server is already running.%NC%
) else (
    echo %GREEN%✅ Starting Redis...%NC%
    start "Redis Server" redis-server --daemonize yes
)

:: Start Backend
cd backend
if not exist "venv" (
    echo %RED%❌ Virtual environment not found. Run setup.bat first.%NC%
    exit /b 1
)
call venv\Scripts\activate.bat

echo %YELLOW%📦 Starting Backend (FastAPI)...%NC%
start "Backend" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

:: Start Celery Worker
echo %YELLOW%⚙️  Starting Celery Worker...%NC%
:: Note: Celery on Windows requires 'solo' or 'threads' pool due to limitations
start "Celery Worker" celery -A celery_app worker --loglevel=info -P threads

cd ..

:: Start Frontend
cd frontend
echo %YELLOW%🌐 Starting Frontend (Next.js)...%NC%
start "Frontend" npm run dev

cd ..

echo.
echo %GREEN%✅ All services initiated!%NC%
echo.
echo 📱 Access:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo 📝 Close the command prompt windows to stop services.
