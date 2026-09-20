<#
.SYNOPSIS
    Bikita Minerals DWRMS — Authoritative Windows PowerShell Developer Launcher
.DESCRIPTION
    Checks system dependencies, initializes virtual environment, database schema,
    node dependencies, and launches the development environment.
.EXAMPLE
    .\run.ps1
    .\run.ps1 all
    .\run.ps1 backend
    .\run.ps1 frontend
    .\run.ps1 tauri
    .\run.ps1 deps
#>

[CmdletBinding()]
param (
    [Parameter(Position=0)]
    [ValidateSet("all", "backend", "frontend", "tauri", "deps", "help", "menu")]
    [string]$Mode = "menu"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

function Write-DWRMSHeader {
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "   BIKITA MINERALS DWRMS — POWERSHELL DEVELOPER LAUNCHER             " -ForegroundColor Cyan
    Write-Host "   Authoritative Operations & Mining Resource Management               " -ForegroundColor Cyan
    Write-Host "======================================================================" -ForegroundColor Cyan
}

function Run-Preflight {
    Write-Host "`n[1/3] System & Environment Verification..." -ForegroundColor Cyan

    # Check python
    if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command py -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Python 3.10+ from python.org (check 'Add to PATH')." -ForegroundColor Yellow
        exit 1
    }
    $pyVer = & python --version 2>$null
    if (-not $pyVer) { $pyVer = & py -3 --version }
    Write-Host "[OK] Detected $pyVer" -ForegroundColor Green

    # Check node & npm
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Node.js is not installed or not in PATH. Install Node.js 18+." -ForegroundColor Red
        exit 1
    }
    $nodeVer = & node --version
    Write-Host "[OK] Detected Node $nodeVer" -ForegroundColor Green

    # Verify .env
    $envPath = Join-Path $ScriptDir ".env"
    $envExample = Join-Path $ScriptDir ".env.example"
    if (-not (Test-Path $envPath)) {
        if (Test-Path $envExample) {
            Write-Host "[DWRMS] Initializing .env from .env.example..." -ForegroundColor Yellow
            Copy-Item $envExample $envPath
        }
    }

    # Directories
    foreach ($dir in @("storage", "backups", "logs")) {
        $fullPath = Join-Path $BackendDir $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        }
    }

    Write-Host "`n[2/3] Backend & Database Verification..." -ForegroundColor Cyan
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[DWRMS] Creating virtualenv in $VenvDir..." -ForegroundColor Yellow
        if (Get-Command python -ErrorAction SilentlyContinue) {
            & python -m venv $VenvDir
        } else {
            & py -3 -m venv $VenvDir
        }
        Write-Host "[DWRMS] Installing backend dependencies..." -ForegroundColor Yellow
        & $VenvPip install --upgrade pip | Out-Null
        & $VenvPip install -r (Join-Path $BackendDir "requirements.txt")
    }

    Write-Host "[DWRMS] Initializing database schema & seed data..." -ForegroundColor Yellow
    Push-Location $BackendDir
    & $VenvPython "init_db_all.py"
    & $VenvPython "seed_rbac.py"
    & $VenvPython "seed.py"
    Pop-Location

    Write-Host "`n[3/3] Frontend Dependencies Verification..." -ForegroundColor Cyan
    $nodeModules = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Host "[DWRMS] Installing frontend dependencies..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        & npm install
        Pop-Location
    }

    Write-Host "[SUCCESS] Pre-flight checks and dependencies are ready!`n" -ForegroundColor Green
}

function Show-InteractiveMenu {
    Write-DWRMSHeader
    Write-Host "Select execution mode:`n" -ForegroundColor White
    Write-Host "  [1] Full Stack (Web) - FastAPI Backend + Next.js (RECOMMENDED - No Rust required)" -ForegroundColor Green
    Write-Host "  [2] Backend Only     - FastAPI API server with live reload (:8000)" -ForegroundColor Cyan
    Write-Host "  [3] Frontend Only    - Next.js web application dev server (:3000)" -ForegroundColor Cyan
    Write-Host "  [4] Tauri Desktop    - Native Desktop App (*Requires Rust / Cargo*)" -ForegroundColor Yellow
    Write-Host "  [5] Setup / Deps     - Verify and install all dependencies and init DB" -ForegroundColor Cyan
    Write-Host "  [6] Exit`n" -ForegroundColor White

    $choice = Read-Host "Enter choice [1-6] (default: 1)"
    if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

    switch ($choice) {
        "1" { Run-Preflight; Start-FullStack }
        "2" { Run-Preflight; Start-BackendOnly }
        "3" { Run-Preflight; Start-FrontendOnly }
        "4" { Run-Preflight; Start-TauriDesktop }
        "5" { Run-Preflight; Write-Host "[SUCCESS] Preflight complete." -ForegroundColor Green }
        "6" { exit 0 }
        default { Write-Host "Invalid choice." -ForegroundColor Red; exit 1 }
    }
}

function Start-FullStack {
    Write-Host "[DWRMS] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    Push-Location $BackendDir
    Start-Process "cmd.exe" -ArgumentList "/k `"$VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`"" -WorkingDirectory $BackendDir
    Pop-Location

    Start-Sleep -Seconds 2
    Write-Host "[DWRMS] Launching Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    & npm run dev
    Pop-Location
}

function Start-BackendOnly {
    Write-Host "[DWRMS] Launching FastAPI Backend with hot reload on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    Push-Location $BackendDir
    & $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    Pop-Location
}

function Start-FrontendOnly {
    Write-Host "[DWRMS] Launching Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Cyan
    Push-Location $FrontendDir
    & npm run dev
    Pop-Location
}

function Start-TauriDesktop {
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        Write-Host "`n======================================================================" -ForegroundColor Red
        Write-Host "[ERROR] Rust / Cargo was not found on this computer!" -ForegroundColor Red
        Write-Host "======================================================================" -ForegroundColor Red
        Write-Host "Tauri Desktop mode requires the Rust compiler." -ForegroundColor Yellow
        Write-Host "`nOption A (Recommended):" -ForegroundColor White
        Write-Host "  Run the web version instead! Run: .\run.ps1 all" -ForegroundColor Green
        Write-Host "  The web version has all the exact same features and requires NO RUST." -ForegroundColor Green
        Write-Host "`nOption B:" -ForegroundColor White
        Write-Host "  Install Rust from https://rustup.rs/ and restart PowerShell." -ForegroundColor Yellow
        Write-Host "======================================================================`n" -ForegroundColor Red
        return
    }

    Write-Host "[DWRMS] Launching Backend and Tauri..." -ForegroundColor Cyan
    Push-Location $BackendDir
    Start-Process "cmd.exe" -ArgumentList "/k `"$VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`"" -WorkingDirectory $BackendDir
    Pop-Location

    Start-Sleep -Seconds 2
    Push-Location $FrontendDir
    & npm run tauri dev
    Pop-Location
}

# Entrypoint routing
switch ($Mode.ToLower()) {
    "menu"     { Show-InteractiveMenu }
    "all"      { Write-DWRMSHeader; Run-Preflight; Start-FullStack }
    "backend"  { Write-DWRMSHeader; Run-Preflight; Start-BackendOnly }
    "frontend" { Write-DWRMSHeader; Run-Preflight; Start-FrontendOnly }
    "tauri"    { Write-DWRMSHeader; Run-Preflight; Start-TauriDesktop }
    "deps"     { Write-DWRMSHeader; Run-Preflight }
    "help"     {
        Write-DWRMSHeader
        Write-Host "Usage: .\run.ps1 [all|backend|frontend|tauri|deps|help]"
        exit 0
    }
}
