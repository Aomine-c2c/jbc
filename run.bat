@echo off
setlocal enabledelayedexpansion
REM ==============================================================================
REM BIKITA MINERALS DWRMS — ONE-COMMAND DEVELOPER LAUNCHER (Windows)
REM
REM Double-click this file or run from Command Prompt.
REM Default: Launches full Tauri Desktop App in developer mode.
REM
REM Usage:
REM   run.bat              Default: Tauri desktop dev mode (auto-installs Rust)
REM   run.bat tauri        Same as default
REM   run.bat web          Web only: FastAPI backend + Next.js browser mode
REM   run.bat backend      FastAPI API server only
REM   run.bat frontend     Next.js web frontend only
REM   run.bat deps         Setup/verify dependencies and init database only
REM   run.bat help         Show this help message
REM ==============================================================================

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

title Bikita Minerals DWRMS — Developer Launcher

REM Route to appropriate command
if /i "%1"=="help" goto show_help
if /i "%1"=="--help" goto show_help
if /i "%1"=="-h" goto show_help
if /i "%1"=="deps" goto run_deps_only
if /i "%1"=="backend" goto run_backend_direct
if /i "%1"=="frontend" goto run_frontend_direct
if /i "%1"=="web" goto run_web_direct
if /i "%1"=="tauri" goto run_tauri_direct
REM Default: Tauri desktop dev mode
goto run_tauri_direct

REM ==============================================================================
REM FIND PYTHON HELPER
REM ==============================================================================
:find_python
set "PY_CMD="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    exit /b 0
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    exit /b 0
)
echo.
echo ====================================================================
echo  [ERROR] Python 3 not found in PATH.
echo  Please install Python 3.10+ from https://python.org
echo  During installation, ensure "Add python.exe to PATH" is CHECKED.
echo ====================================================================
pause
exit /b 1

REM ==============================================================================
REM INSTALL RUST IF MISSING
REM ==============================================================================
:ensure_rust
where cargo >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Rust/Cargo found.
    exit /b 0
)
echo.
echo ====================================================================
echo  [DWRMS] Rust not found — required for Tauri Desktop mode.
echo  Auto-installing Rust via rustup.rs...
echo ====================================================================
REM Download and run rustup-init.exe silently
powershell -Command "& { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://win.rustup.rs' -OutFile '%TEMP%\rustup-init.exe' -UseBasicParsing }"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download rustup. Check your internet connection.
    echo  Manual install: https://rustup.rs/
    pause
    exit /b 1
)
echo [DWRMS] Running Rust installer (default toolchain, no interaction needed)...
"%TEMP%\rustup-init.exe" -y --default-toolchain stable --default-host x86_64-pc-windows-msvc
if %errorlevel% neq 0 (
    echo [ERROR] Rust installation failed. Please install manually from https://rustup.rs/
    pause
    exit /b 1
)
REM Update PATH for this session to include newly installed cargo
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
where cargo >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Rust installed but cargo not found in PATH.
    echo  Please CLOSE and REOPEN this terminal, then run run.bat again.
    pause
    exit /b 1
)
echo [SUCCESS] Rust installed successfully!
exit /b 0

REM ==============================================================================
REM PREFLIGHT: ENV, VENV, DB, FRONTEND DEPS
REM ==============================================================================
:preflight
echo.
echo ====================================================================
echo    BIKITA MINERALS DWRMS — DEVELOPER ENVIRONMENT SETUP
echo ====================================================================
echo.
echo [1/4] System ^& Environment Checks...

REM Check Python
call :find_python
if %errorlevel% neq 0 exit /b 1

REM Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org (v18+)
    pause
    exit /b 1
)
echo [OK] Node.js found.

REM Check npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found.
    pause
    exit /b 1
)
echo [OK] npm found.

REM Create .env if missing
if not exist "%SCRIPT_DIR%.env" (
    if exist "%SCRIPT_DIR%.env.example" (
        echo [DWRMS] Creating .env from .env.example...
        copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
        echo [OK] .env created.
    )
)

REM Critical: Ensure ENVIRONMENT is NOT production (disables demo password fallback)
findstr /i "ENVIRONMENT=\"production\"" "%SCRIPT_DIR%.env" >nul 2>&1
if %errorlevel% equ 0 (
    echo [FIX] Overriding ENVIRONMENT=production to 'testing' for dev mode...
    powershell -Command "(Get-Content '%SCRIPT_DIR%.env') -replace 'ENVIRONMENT=\"production\"', 'ENVIRONMENT=\"testing\"' | Set-Content '%SCRIPT_DIR%.env'"
)

REM Ensure SECRET_KEY is populated
findstr /i "^SECRET_KEY=dev-changeme" "%SCRIPT_DIR%.env" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%k in ('%PY_CMD% -c "import secrets; print(secrets.token_hex(32))"') do set "NEWKEY=%%k"
    powershell -Command "(Get-Content '%SCRIPT_DIR%.env') | ForEach-Object { $_ -replace '^SECRET_KEY=.*', 'SECRET_KEY=""!NEWKEY!""' } | Set-Content '%SCRIPT_DIR%.env'"
    echo [OK] SECRET_KEY generated.
)

REM Ensure required directories
if not exist "%BACKEND_DIR%\storage" mkdir "%BACKEND_DIR%\storage"
if not exist "%BACKEND_DIR%\backups" mkdir "%BACKEND_DIR%\backups"
if not exist "%BACKEND_DIR%\logs" mkdir "%BACKEND_DIR%\logs"

echo.
echo [2/4] Backend Virtual Environment ^& Dependencies...
if not exist "%VENV_PYTHON%" (
    echo [DWRMS] Creating Python virtualenv...
    %PY_CMD% -m venv "%VENV_DIR%"
    echo [DWRMS] Installing backend dependencies...
    "%VENV_PIP%" install --upgrade pip >nul 2>&1
    "%VENV_PIP%" install -r "%BACKEND_DIR%\requirements.txt"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
    echo [OK] Backend dependencies installed.
) else (
    echo [OK] Backend virtualenv ready.
)

echo.
echo [3/4] Database Schema ^& Seed Data...
cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" init_db_all.py
"%VENV_PYTHON%" seed_rbac.py
"%VENV_PYTHON%" seed.py
cd /d "%SCRIPT_DIR%"

echo.
echo [4/4] Frontend Dependencies...
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [DWRMS] Installing npm packages...
    cd /d "%FRONTEND_DIR%"
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    cd /d "%SCRIPT_DIR%"
    echo [OK] Frontend dependencies installed.
) else (
    echo [OK] Frontend node_modules ready.
)

echo.
echo [SUCCESS] Environment ready!
echo.
exit /b 0

REM ==============================================================================
REM LAUNCH BACKEND SILENTLY IN BACKGROUND
REM ==============================================================================
:launch_backend_bg
REM Ensure port 8000 is clear before starting
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1
echo [DWRMS] Starting FastAPI backend (hidden) on http://127.0.0.1:8000 ...
REM Start backend in a minimized hidden window — developers won't see it
start /min "" cmd /c "cd /d "%BACKEND_DIR%" && "%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > "%BACKEND_DIR%\logs\dev-backend.log" 2>&1"
REM Wait for backend to be ready (poll up to 20s)
echo [DWRMS] Waiting for backend to initialize...
set RETRIES=0
:wait_backend
timeout /t 2 /nobreak >nul
powershell -Command "try { Invoke-RestMethod http://127.0.0.1:8000/api/v1/health -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is online at http://127.0.0.1:8000
    exit /b 0
)
set /a RETRIES+=1
if %RETRIES% lss 10 goto wait_backend
echo [WARN] Backend did not respond in time — Tauri will connect once it's ready.
exit /b 0

REM ==============================================================================
REM MODES
REM ==============================================================================

:run_tauri_direct
:run_tauri
call :preflight
if %errorlevel% neq 0 exit /b 1

echo [DWRMS] Ensuring Rust/Cargo is available...
call :ensure_rust
if %errorlevel% neq 0 exit /b 1

call :launch_backend_bg

echo.
echo ====================================================================
echo  Launching Tauri Desktop App in Developer Mode
echo  * Next.js hot reload is active
echo  * Backend log: %BACKEND_DIR%\logs\dev-backend.log
echo  * Close the Tauri window to exit
echo ====================================================================
echo.
cd /d "%FRONTEND_DIR%"
call npm run tauri:window
cd /d "%SCRIPT_DIR%"
goto do_exit

:run_web_direct
call :preflight
if %errorlevel% neq 0 exit /b 1

echo [DWRMS] Starting FastAPI Backend on http://127.0.0.1:8000 ...
cd /d "%BACKEND_DIR%"
start "DWRMS Backend (Port 8000)" cmd /k ""%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 /nobreak >nul
echo [DWRMS] Starting Next.js Frontend on http://localhost:3000 ...
cd /d "%FRONTEND_DIR%"
call npm run dev
goto do_exit

:run_backend_direct
call :preflight
if %errorlevel% neq 0 exit /b 1
echo [DWRMS] Starting FastAPI backend only...
cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
goto do_exit

:run_frontend_direct
call :preflight
if %errorlevel% neq 0 exit /b 1
echo [DWRMS] Starting Next.js frontend only...
cd /d "%FRONTEND_DIR%"
call npm run dev
goto do_exit

:run_deps_only
call :preflight
if %errorlevel% neq 0 exit /b 1
echo.
echo [SUCCESS] All dependencies verified and database initialized.
echo Run 'run.bat' again to launch the application.
pause
goto do_exit

:show_help
echo ====================================================================
echo    DWRMS Developer Launcher — Help
echo ====================================================================
echo Usage: run.bat [COMMAND]
echo.
echo Commands:
echo   (default)    Launch Tauri Desktop App in dev mode (auto-installs Rust)
echo   tauri        Same as default
echo   web          Web mode: FastAPI Backend + Next.js browser app
echo   backend      FastAPI backend server only (port 8000)
echo   frontend     Next.js frontend only (port 3000)
echo   deps         Setup/verify environment and database only
echo   help         Show this message
echo.
echo Default credentials for testing/staging:
echo   admin@bikita.com    / password123
echo   tech@bikita.com     / password123
echo   supervisor@bikita.com / password123
echo.
goto do_exit

:do_exit
REM Terminate any running backend process on port 8000 when launcher exits
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1
exit /b 0
