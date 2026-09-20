<#
.SYNOPSIS
    Bikita Minerals DWRMS — One-Command Developer Launcher (PowerShell)
.DESCRIPTION
    Default mode: Launches the Tauri Desktop App in developer mode.
    Automatically installs Rust if missing, sets up .venv, initialises the database,
    installs npm packages, then opens the native desktop window with hot reload.
.EXAMPLE
    .\run.ps1               # Default: Tauri desktop dev (auto-installs Rust)
    .\run.ps1 tauri         # Same as default
    .\run.ps1 web           # Web mode: FastAPI + Next.js in browser
    .\run.ps1 backend       # FastAPI only
    .\run.ps1 frontend      # Next.js only
    .\run.ps1 deps          # Setup/verify env and database
#>

[CmdletBinding()]
param (
    [Parameter(Position=0)]
    [ValidateSet("tauri", "web", "backend", "frontend", "deps", "help")]
    [string]$Mode = "tauri"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

# ── Helpers ───────────────────────────────────────────────────────────────────

function Find-PythonCmd {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $ver = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) { return "python" }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $ver = & py -3 --version 2>&1
        if ($LASTEXITCODE -eq 0) { return "py -3" }
    }
    throw "Python 3.10+ not found. Install from https://python.org and check 'Add to PATH'."
}

function Write-Header {
    Write-Host "`n====================================================================" -ForegroundColor Cyan
    Write-Host "   BIKITA MINERALS DWRMS — DEVELOPER LAUNCHER" -ForegroundColor Cyan
    Write-Host "   Mode: $Mode" -ForegroundColor Cyan
    Write-Host "====================================================================`n" -ForegroundColor Cyan
}

function Ensure-Rust {
    if (Get-Command cargo -ErrorAction SilentlyContinue) {
        $v = & cargo --version 2>&1
        Write-Host "[OK] Rust/Cargo: $v" -ForegroundColor Green
        return
    }

    Write-Host "`n[DWRMS] Rust not found — required for Tauri Desktop mode." -ForegroundColor Yellow
    Write-Host "[DWRMS] Auto-installing Rust via rustup.rs..." -ForegroundColor Yellow

    $rustupExe = Join-Path $env:TEMP "rustup-init.exe"
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri "https://win.rustup.rs" -OutFile $rustupExe -UseBasicParsing
    } catch {
        throw "Failed to download rustup: $_. Check your internet connection or install manually from https://rustup.rs/"
    }

    Write-Host "[DWRMS] Running Rust installer (no interaction needed)..." -ForegroundColor Yellow
    & $rustupExe -y --default-toolchain stable --default-host x86_64-pc-windows-msvc
    if ($LASTEXITCODE -ne 0) {
        throw "Rust installation failed. Please install manually from https://rustup.rs/"
    }

    # Add cargo to PATH for this session
    $cargoPath = Join-Path $env:USERPROFILE ".cargo\bin"
    $env:PATH = "$cargoPath;$env:PATH"

    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        throw "Rust installed but cargo not found. Please close and reopen PowerShell, then run .\run.ps1 again."
    }

    Write-Host "[SUCCESS] Rust installed!" -ForegroundColor Green
}

function Run-Preflight {
    Write-Host "[1/4] System & Environment Checks..." -ForegroundColor White

    $pyCmd = Find-PythonCmd
    Write-Host "[OK] Python: $(& $pyCmd.Split()[0] --version 2>&1)" -ForegroundColor Green

    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw "Node.js not found. Install from https://nodejs.org (v18+)"
    }
    Write-Host "[OK] Node: $(& node --version)" -ForegroundColor Green

    # .env setup
    $envFile = Join-Path $ScriptDir ".env"
    $envExample = Join-Path $ScriptDir ".env.example"
    if (-not (Test-Path $envFile)) {
        if (Test-Path $envExample) {
            Copy-Item $envExample $envFile
            Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
        } else {
            throw ".env and .env.example both missing. Re-clone the repository."
        }
    }

    # Fix ENVIRONMENT if production
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match 'ENVIRONMENT="production"') {
        Write-Host "[FIX] Overriding ENVIRONMENT=production -> testing (needed for demo logins)" -ForegroundColor Yellow
        $envContent = $envContent -replace 'ENVIRONMENT="production"', 'ENVIRONMENT="testing"'
        Set-Content -Path $envFile -Value $envContent
    }

    # Generate SECRET_KEY if missing/placeholder
    if ($envContent -match 'SECRET_KEY=\s*$' -or $envContent -match 'SECRET_KEY=dev-changeme') {
        $pyExe = if ($pyCmd -eq "python") { "python" } else { "py" }
        $newKey = & $pyExe -c "import secrets; print(secrets.token_hex(32))"
        $envContent = $envContent -replace 'SECRET_KEY=.*', "SECRET_KEY=`"$newKey`""
        Set-Content -Path $envFile -Value $envContent
        Write-Host "[OK] SECRET_KEY generated." -ForegroundColor Green
    }

    # Directories
    foreach ($d in @("storage", "backups", "logs")) {
        $p = Join-Path $BackendDir $d
        if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
    }

    # Frontend .env.local
    $frontendEnv = Join-Path $FrontendDir ".env.local"
    if (-not (Test-Path $frontendEnv)) {
        @"
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_ENABLE_DEMO_LOGINS=true
BACKEND_URL=http://127.0.0.1:8000
"@ | Set-Content -Path $frontendEnv
        Write-Host "[OK] Created frontend/.env.local" -ForegroundColor Green
    }

    Write-Host "`n[2/4] Backend Virtualenv & Dependencies..." -ForegroundColor White
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[DWRMS] Creating virtualenv..." -ForegroundColor Yellow
        $pyExe = if ($pyCmd -eq "python") { "python" } else { "py" }
        & $pyExe -m venv $VenvDir
        Write-Host "[DWRMS] Installing backend dependencies..." -ForegroundColor Yellow
        & $VenvPip install --upgrade pip | Out-Null
        & $VenvPip install -r (Join-Path $BackendDir "requirements.txt")
    } else {
        Write-Host "[OK] Backend virtualenv ready." -ForegroundColor Green
    }

    Write-Host "`n[3/4] Database Schema & Seed Data..." -ForegroundColor White
    Push-Location $BackendDir
    & $VenvPython "init_db_all.py"
    & $VenvPython "seed_rbac.py"
    & $VenvPython "seed.py"
    Pop-Location

    Write-Host "`n[4/4] Frontend Dependencies..." -ForegroundColor White
    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Host "[DWRMS] Installing npm packages..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        & npm install
        Pop-Location
    } else {
        Write-Host "[OK] node_modules ready." -ForegroundColor Green
    }

    Write-Host "`n[SUCCESS] Environment ready!`n" -ForegroundColor Green
}

function Start-BackendSilent {
    Write-Host "[DWRMS] Starting FastAPI backend (hidden) on http://127.0.0.1:8000 ..." -ForegroundColor Cyan

    $logFile = Join-Path $BackendDir "logs\dev-backend.log"
    $cmd = "`"$VenvPython`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

    # Start minimized hidden process
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/c cd /d `"$BackendDir`" && $cmd > `"$logFile`" 2>&1"
    $psi.WorkingDirectory = $BackendDir
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
    $psi.CreateNoWindow = $false
    [System.Diagnostics.Process]::Start($psi) | Out-Null

    # Wait for backend (poll up to 20s)
    Write-Host "[DWRMS] Waiting for backend to initialize..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 0; $i -lt 10; $i++) {
        Start-Sleep -Seconds 2
        try {
            Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {}
    }
    if ($ready) {
        Write-Host "[OK] Backend is online." -ForegroundColor Green
    } else {
        Write-Host "[WARN] Backend not responding yet — Tauri will connect once it starts." -ForegroundColor Yellow
        Write-Host "       Check log: $logFile" -ForegroundColor DarkGray
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Header

switch ($Mode.ToLower()) {
    "tauri" {
        Run-Preflight
        Ensure-Rust
        Start-BackendSilent

        Write-Host "====================================================================" -ForegroundColor Cyan
        Write-Host "  Launching Tauri Desktop App — Developer Mode (hot reload active)" -ForegroundColor Cyan
        Write-Host "  Backend log: $(Join-Path $BackendDir 'logs\dev-backend.log')" -ForegroundColor DarkGray
        Write-Host "  Close the desktop window to exit." -ForegroundColor DarkGray
        Write-Host "====================================================================`n" -ForegroundColor Cyan

        Push-Location $FrontendDir
        & npm run tauri dev
        Pop-Location
    }

    "web" {
        Run-Preflight
        Write-Host "[DWRMS] Launching Backend in separate window..." -ForegroundColor Cyan
        Start-Process "cmd.exe" -ArgumentList "/k `"$VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`"" -WorkingDirectory $BackendDir
        Start-Sleep -Seconds 2
        Write-Host "[DWRMS] Launching Next.js on http://localhost:3000..." -ForegroundColor Cyan
        Push-Location $FrontendDir
        & npm run dev
        Pop-Location
    }

    "backend" {
        Run-Preflight
        Push-Location $BackendDir
        & $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
        Pop-Location
    }

    "frontend" {
        Run-Preflight
        Push-Location $FrontendDir
        & npm run dev
        Pop-Location
    }

    "deps" {
        Run-Preflight
        Write-Host "All dependencies verified. Run '.\run.ps1' to launch." -ForegroundColor Green
    }

    "help" {
        Write-Host "Usage: .\run.ps1 [tauri|web|backend|frontend|deps|help]"
        Write-Host ""
        Write-Host "  (default / tauri)  Tauri desktop dev mode (auto-installs Rust if missing)"
        Write-Host "  web                FastAPI + Next.js in web browser"
        Write-Host "  backend            FastAPI backend only (port 8000)"
        Write-Host "  frontend           Next.js frontend only (port 3000)"
        Write-Host "  deps               Setup/verify environment and database"
        Write-Host ""
        Write-Host "Default credentials (testing mode):"
        Write-Host "  admin@bikita.com       / password123"
        Write-Host "  tech@bikita.com        / password123"
        Write-Host "  supervisor@bikita.com  / password123"
    }
}
