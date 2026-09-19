@echo off
REM ==============================================================================
REM Bikita Minerals DWRMS — Windows Local Startup Script
REM Automatically launches FastAPI Backend and Next.js / Desktop Environment
REM ==============================================================================

echo [DWRMS] Starting Bikita Minerals DWRMS Local Stack...

REM 1. Verify .env file exists
if not exist "%~dp0.env" (
    echo [DWRMS] .env not found. Copying from .env.example...
    copy "%~dp0.env.example" "%~dp0.env"
)

REM 2. Create local storage & backup directories
if not exist "%~dp0backend\storage" mkdir "%~dp0backend\storage"
if not exist "%~dp0backend\backups" mkdir "%~dp0backend\backups"
if not exist "%~dp0backend\logs" mkdir "%~dp0backend\logs"

REM 3. Check Python Virtual Environment
cd /d "%~dp0backend"
if exist ".venv\Scripts\activate.bat" (
    echo [DWRMS] Activating Python virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [DWRMS] Python virtual environment not detected in backend\.venv.
    echo [DWRMS] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [DWRMS] Installing backend dependencies...
    pip install -r requirements.txt
)

REM 4. Initialize Database
echo [DWRMS] Checking database tables and demo seed...
python init_db_all.py

REM 5. Start Backend Server in a dedicated window
echo [DWRMS] Starting FastAPI backend on http://127.0.0.1:8000 ...
start "DWRMS Backend Server" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM 6. Wait for backend to be ready
echo [DWRMS] Waiting for backend initialization...
timeout /t 3 /nobreak >nul

REM 7. Return to project root and launch Frontend
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [DWRMS] Installing frontend dependencies...
    call npm install
)

echo [DWRMS] Launching Frontend Development Server...
call npm run dev

pause
