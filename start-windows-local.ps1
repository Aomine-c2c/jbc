<#
.SYNOPSIS
    Bikita Minerals DWRMS — PowerShell Automated Startup Script for Windows 10/11
.DESCRIPTION
    Verifies environment prerequisites, initializes database, runs migrations,
    and starts both backend and frontend services.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Bikita Minerals DWRMS — Windows Stack Launcher        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check or copy .env
$envPath = Join-Path $ScriptDir ".env"
$envExamplePath = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $envPath)) {
    Write-Host "[DWRMS] Initializing .env from template..." -ForegroundColor Yellow
    Copy-Item $envExamplePath $envPath
}

# 2. Prepare directories
$backendDir = Join-Path $ScriptDir "backend"
$storageDir = Join-Path $backendDir "storage"
$backupsDir = Join-Path $backendDir "backups"
$logsDir = Join-Path $backendDir "logs"

foreach ($dir in @($storageDir, $backupsDir, $logsDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 3. Setup Python venv
$venvActivate = Join-Path $backendDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Host "[DWRMS] Creating Python virtual environment..." -ForegroundColor Yellow
    & python -m venv (Join-Path $backendDir ".venv")
    Write-Host "[DWRMS] Installing backend dependencies..." -ForegroundColor Yellow
    $pipPath = Join-Path $backendDir ".venv\Scripts\pip.exe"
    & $pipPath install -r (Join-Path $backendDir "requirements.txt")
}

# 4. Seed Database
Write-Host "[DWRMS] Initializing database schema..." -ForegroundColor Green
$pythonPath = Join-Path $backendDir ".venv\Scripts\python.exe"
Push-Location $backendDir
& $pythonPath "init_db_all.py"
Pop-Location

# 5. Launch Backend
Write-Host "[DWRMS] Starting FastAPI backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process "cmd.exe" -ArgumentList "/k `"$pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000`"" -WorkingDirectory $backendDir

# 6. Check health
Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 5
    Write-Host "[DWRMS] Backend is ONLINE! Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "[DWRMS] Backend starting in background..." -ForegroundColor Yellow
}

# 7. Start Frontend / Tauri
$frontendDir = Join-Path $ScriptDir "frontend"
Push-Location $frontendDir
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[DWRMS] Installing Node dependencies..." -ForegroundColor Yellow
    & npm install
}

Write-Host "[DWRMS] Starting Frontend server on http://localhost:3000 ..." -ForegroundColor Green
& npm run dev
Pop-Location
