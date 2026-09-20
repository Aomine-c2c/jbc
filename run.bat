@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM BIKITA MINERALS DWRMS — AUTHORITATIVE WINDOWS DEVELOPER STACK LAUNCHER
REM
REM Usage:
REM   run.bat                  Interactive selection menu
REM   run.bat all              Launch full stack (FastAPI Backend + Next.js Frontend)
REM   run.bat backend          Launch Backend API only (FastAPI with reload)
REM   run.bat frontend         Launch Frontend Web only (Next.js dev server)
REM   run.bat tauri            Launch Desktop environment (Tauri + Backend - Requires Rust)
REM   run.bat deps             Verify and install dependencies & init DB
REM   run.bat help             Display usage instructions
REM ==============================================================================

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

title Bikita Minerals DWRMS Launcher

if "%1"=="help" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="deps" goto run_deps_only
if "%1"=="backend" goto run_backend_direct
if "%1"=="frontend" goto run_frontend_direct
if "%1"=="tauri" goto run_tauri_direct
if "%1"=="all" goto run_all_direct

:show_menu
cls
echo ======================================================================
echo    BIKITA MINERALS DWRMS -- WINDOWS DEVELOPER LAUNCHER
echo    Authoritative Operations and Mining Resource Management
echo ======================================================================
echo.
echo Select execution mode:
echo.
echo   [1] Full Stack (Web) - FastAPI Backend + Next.js Frontend (RECOMMENDED)
echo                          *No Rust required! Only Python and Node.js.
echo.
echo   [2] Backend Only     - FastAPI API server with live reload (:8000)
echo   [3] Frontend Only    - Next.js web application dev server (:3000)
echo   [4] Tauri Desktop    - Run Native Desktop App (*Requires Rust / Cargo*)
echo   [5] Setup / Deps     - Verify/install dependencies and initialize database
echo   [6] Exit
echo.
set /p "CHOICE=Enter choice [1-6] (default: 1): "
if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="1" goto run_all
if "%CHOICE%"=="2" goto run_backend
if "%CHOICE%"=="3" goto run_frontend
if "%CHOICE%"=="4" goto run_tauri
if "%CHOICE%"=="5" goto run_deps_only
if "%CHOICE%"=="6" goto do_exit
if /i "%CHOICE%"=="q" goto do_exit

echo [ERROR] Invalid selection.
pause
goto show_menu

:find_python
REM Detect python executable (either 'python' or 'py -3')
set "PY_CMD="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :eof
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto :eof
)
echo [ERROR] Python is not found in PATH. Please install Python 3.10+ from python.org
echo (Make sure to check 'Add python.exe to PATH' during installation).
pause
exit /b 1

:preflight
echo.
echo [1/3] System & Environment Verification...
call :find_python
if %errorlevel% neq 0 exit /b 1

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH. Please install Node.js 18+.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        echo [DWRMS] Initializing .env from .env.example...
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
    )
)

if not exist "%BACKEND_DIR%\storage" mkdir "%BACKEND_DIR%\storage"
if not exist "%BACKEND_DIR%\backups" mkdir "%BACKEND_DIR%\backups"
if not exist "%BACKEND_DIR%\logs" mkdir "%BACKEND_DIR%\logs"

echo.
echo [2/3] Backend & Database Verification...
if not exist "%VENV_PYTHON%" (
    echo [DWRMS] Creating Python virtual environment in %VENV_DIR%...
    %PY_CMD% -m venv "%VENV_DIR%"
    echo [DWRMS] Installing backend dependencies...
    "%VENV_PIP%" install --upgrade pip
    "%VENV_PIP%" install -r "%BACKEND_DIR%\requirements.txt"
)

echo [DWRMS] Initializing database schema and seed data...
cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" init_db_all.py
"%VENV_PYTHON%" seed_rbac.py
"%VENV_PYTHON%" seed.py
cd /d "%SCRIPT_DIR%"

echo.
echo [3/3] Frontend Dependencies Verification...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [DWRMS] Installing frontend dependencies via npm...
    cd /d "%FRONTEND_DIR%"
    call npm install
    cd /d "%SCRIPT_DIR%"
)

echo [SUCCESS] Dependencies and environment are verified!
echo.
exit /b 0

:run_all_direct
:run_all
call :preflight
echo [DWRMS] Launching FastAPI Backend on http://127.0.0.1:8000 ...
cd /d "%BACKEND_DIR%"
start "DWRMS Backend API (Port 8000)" cmd /k ""%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [DWRMS] Launching Next.js Frontend on http://localhost:3000 ...
cd /d "%FRONTEND_DIR%"
call npm run dev
goto do_exit

:run_backend_direct
:run_backend
call :preflight
echo [DWRMS] Launching FastAPI Backend with hot reload on http://127.0.0.1:8000 ...
cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
goto do_exit

:run_frontend_direct
:run_frontend
call :preflight
echo [DWRMS] Launching Next.js Frontend on http://localhost:3000 ...
cd /d "%FRONTEND_DIR%"
call npm run dev
goto do_exit

:run_tauri_direct
:run_tauri
call :preflight

REM Tauri requires Rust and Cargo
where cargo >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Rust / Cargo was not found on this computer!
    echo ======================================================================
    echo Tauri Desktop mode requires the Rust compiler.
    echo.
    echo  Option A (Recommended):
    echo    Run the web version instead! Select Option [1] (Full Stack Web).
    echo    The web version has all the exact same features and requires NO RUST.
    echo.
    echo  Option B:
    echo    If you really want to build the native Windows desktop shell,
    echo    install Rust from https://rustup.rs/ and restart your terminal.
    echo ======================================================================
    echo.
    pause
    goto show_menu
)

echo [DWRMS] Launching Backend for Tauri...
cd /d "%BACKEND_DIR%"
start "DWRMS Backend API" cmd /k ""%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 /nobreak >nul
echo [DWRMS] Launching Tauri Desktop Dev Application...
cd /d "%FRONTEND_DIR%"
call npm run tauri dev
goto do_exit

:run_deps_only
call :preflight
echo [SUCCESS] Setup and dependency checks completed.
pause
goto do_exit

:show_help
echo ======================================================================
echo    BIKITA MINERALS DWRMS -- WINDOWS LAUNCHER HELP
echo ======================================================================
echo Usage: run.bat [COMMAND]
echo.
echo Commands:
echo   all        Start full stack (FastAPI Backend + Next.js Frontend) - NO Rust required
echo   backend    Start FastAPI backend server on :8000
echo   frontend   Start Next.js frontend server on :3000
echo   tauri      Start Tauri desktop application environment (Requires Rust)
echo   deps       Verify and install dependencies and initialize database
echo   help       Show this help message
echo.
echo If no command is provided, an interactive menu is displayed.
exit /b 0

:do_exit
exit /b 0
