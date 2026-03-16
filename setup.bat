@echo off
setlocal

:: Colors
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "NC=[0m"

echo %GREEN%🚀 EstraConvert Setup Script (Windows)%NC%
echo ============================

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Python is not installed or not in PATH.%NC%
    exit /b 1
)
echo %GREEN%✅ Python found%NC%

:: Check Python version (requires >= 3.10)
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Python version must be 3.10 or higher.%NC%
    exit /b 1
)

:: Check for Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%❌ Node.js is not installed or not in PATH.%NC%
    exit /b 1
)
echo %GREEN%✅ Node.js found%NC%

:: Check for Redis (optional but recommended)
where redis-server >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW%⚠️  Redis server not found. Please install Redis (e.g., via WSL or Memurai) before running the application.%NC%
) else (
    echo %GREEN%✅ Redis server found%NC%
)

:: Check for Tesseract
where tesseract >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %YELLOW%⚠️  Tesseract OCR not found. Please install Tesseract (https://github.com/UB-Mannheim/tesseract/wiki) before processing PDFs.%NC%
) else (
    echo %GREEN%✅ Tesseract OCR found%NC%
)

echo.
echo %YELLOW%📦 Setting up Backend...%NC%
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies...
pip install -r requirements.txt

if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads

if not exist ".env" (
    echo %YELLOW%⚠️  .env file not found. Creating from example...%NC%
    if exist ".env.example" (
        copy .env.example .env
        echo %YELLOW%⚠️  Please edit backend\.env and add your API keys!%NC%
    ) else (
        echo %RED%❌ .env.example not found!%NC%
    )
)

cd ..

echo.
echo %YELLOW%📦 Setting up Frontend...%NC%
cd frontend

echo Installing Node.js dependencies...
call npm install

cd ..

echo.
echo %GREEN%✅ Setup complete!%NC%
echo.
echo To start the application:
echo   start_all.bat
