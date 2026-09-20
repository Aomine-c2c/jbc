@echo off
setlocal enabledelayedexpansion
REM ==============================================================================
REM BIKITA MINERALS DWRMS — Login Diagnostic & Self-Repair Tool
REM Run this script from the project root to diagnose and fix login failures.
REM Usage: fix-login.bat
REM ==============================================================================

echo ======================================================================
echo    DWRMS Login Diagnostic ^& Self-Repair Tool
echo    Run this from the project root directory.
echo ======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "ENV_FILE=%SCRIPT_DIR%.env"
set "VENV_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"

REM ── Step 1: Find Python ──────────────────────────────────────────────────────
echo [1/6] Checking Python availability...
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY=py -3"
    ) else (
        echo [FAIL] Python not found. Please install Python 3.10+ from python.org.
        goto end
    )
)
echo [OK] Python found.

REM ── Step 2: Check .env exists ────────────────────────────────────────────────
echo.
echo [2/6] Checking .env configuration file...
if not exist "%ENV_FILE%" (
    echo [FAIL] .env file not found!
    if exist "%SCRIPT_DIR%.env.example" (
        echo [FIX] Creating .env from .env.example...
        copy "%SCRIPT_DIR%.env.example" "%ENV_FILE%" >nul
        echo [OK] .env created.
    ) else (
        echo [FAIL] .env.example also not found. Please re-clone the repository.
        goto end
    )
) else (
    echo [OK] .env file exists.
)

REM ── Step 3: Check ENVIRONMENT setting ────────────────────────────────────────
echo.
echo [3/6] Checking ENVIRONMENT setting in .env...
findstr /i "ENVIRONMENT=\"production\"" "%ENV_FILE%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [FAIL] ENVIRONMENT is set to 'production'!
    echo.
    echo  ROOT CAUSE FOUND: This is why you cannot login.
    echo  When ENVIRONMENT=production, the demo password fallback is DISABLED.
    echo  Any user with 'password123' in the database cannot authenticate.
    echo.
    echo [FIX] Changing ENVIRONMENT to 'testing'...
    powershell -Command "(Get-Content '%ENV_FILE%') -replace 'ENVIRONMENT=\"production\"', 'ENVIRONMENT=\"testing\"' | Set-Content '%ENV_FILE%'"
    echo [OK] ENVIRONMENT updated to 'testing'.
) else (
    findstr /i "^ENVIRONMENT=" "%ENV_FILE%" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARN] ENVIRONMENT not set in .env. Adding ENVIRONMENT="testing"...
        echo ENVIRONMENT="testing">> "%ENV_FILE%"
        echo [OK] ENVIRONMENT set to 'testing'.
    ) else (
        for /f "tokens=2 delims==" %%v in ('findstr /i "^ENVIRONMENT=" "%ENV_FILE%"') do set ENV_VAL=%%v
        echo [OK] ENVIRONMENT = !ENV_VAL! (compatible with demo logins).
    )
)

REM ── Step 4: Check SECRET_KEY ─────────────────────────────────────────────────
echo.
echo [4/6] Checking SECRET_KEY...
findstr /r "^SECRET_KEY=$" "%ENV_FILE%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARN] SECRET_KEY is empty. Generating a secure key...
    for /f "delims=" %%k in ('%PY% -c "import secrets; print(secrets.token_hex(32))"') do set "NEW_KEY=%%k"
    powershell -Command "(Get-Content '%ENV_FILE%') -replace '^SECRET_KEY=$', 'SECRET_KEY=\"!NEW_KEY!\"' | Set-Content '%ENV_FILE%'"
    echo [OK] SECRET_KEY generated and saved.
) else (
    echo [OK] SECRET_KEY is set.
)

REM ── Step 5: Check database and users ─────────────────────────────────────────
echo.
echo [5/6] Checking database and user accounts...
if not exist "%VENV_PYTHON%" (
    echo [WARN] Python virtualenv not found. Run 'run.bat deps' first to set up the environment.
    goto end
)
cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" -c "
import asyncio, sys
sys.path.insert(0, '.')
async def check():
    from app.db.session import async_session_factory
    from app.modules.iam.models import User
    from sqlalchemy import select
    from app.core.security import verify_password
    async with async_session_factory() as db:
        users = (await db.execute(select(User))).scalars().all()
        if not users:
            print('[FAIL] No users found in database! Run: run.bat deps')
            return
        print(f'[OK] Found {len(users)} users in database.')
        for u in users:
            ok = verify_password('password123', u.hashed_password)
            dept = 'HAS_DEPT' if u.department_id else 'NO_DEPT'
            active = 'ACTIVE' if u.is_active else 'INACTIVE'
            print(f'  {u.email}: password123={ok} | {active} | {dept}')
            if not ok:
                print(f'    ^ WARNING: Password does not match password123. User may need re-seeding.')
            if not u.department_id:
                print(f'    ^ WARNING: No department assigned -- login will return 403 Account pending approval.')
asyncio.run(check())
" 2>&1
cd /d "%SCRIPT_DIR%"

REM ── Step 6: Quick login test ──────────────────────────────────────────────────
echo.
echo [6/6] Quick Login Simulation (requires backend to be running)...
powershell -Command "
try {
    $body = '{\"username\":\"admin@bikita.com\",\"password\":\"password123\"}'
    $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/iam/auth/login' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    Write-Host '[OK] Login SUCCESSFUL! Token received.' -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host \"[FAIL] Login failed with HTTP $code: $($_.Exception.Message)\" -ForegroundColor Red
    if ($code -eq 400) {
        Write-Host '  -> Incorrect email or password. Database may not be seeded, or ENVIRONMENT is wrong.' -ForegroundColor Yellow
    } elseif ($code -eq 403) {
        Write-Host '  -> Account pending approval (no department_id). Run: run.bat deps to reseed.' -ForegroundColor Yellow
    } elseif (!$code) {
        Write-Host '  -> Backend not reachable. Make sure run.bat all is running first.' -ForegroundColor Yellow
    }
}" 2>&1

echo.
echo ======================================================================
echo  Diagnosis complete.
echo  If issues were found and auto-fixed, restart the stack: run.bat all
echo  If database had no users, run: run.bat deps (to reseed)
echo ======================================================================
:end
pause
