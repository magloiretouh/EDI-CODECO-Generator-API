@echo off
REM EDI CODECO Generator API - Startup Script for Windows

echo ===============================================
echo EDI CODECO Generator API
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Make sure Python is installed and accessible.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo NOTE: .env file not found. Creating from .env.example...
    if exist ".env.example" (
        copy .env.example .env
        echo .env created. Edit it with your SFTP settings if needed.
    ) else (
        echo WARNING: .env.example not found. Using defaults.
    )
)

REM Display startup info
echo.
echo ===============================================
echo Starting API Server...
echo ===============================================
echo.
echo API will be available at:
echo   http://localhost:5000
echo.
echo Interactive API Documentation:
echo   http://localhost:5000/api/docs
echo.
echo Press CTRL+C to stop the server.
echo ===============================================
echo.

REM Start the API
python app.py

pause
