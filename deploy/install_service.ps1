<#
.SYNOPSIS
Installs the FastAPI application as a Windows Service using NSSM.

.DESCRIPTION
This script downloads NSSM (if not present) and configures the backend to run as a Windows service,
ensuring it starts automatically on system boot.

.EXAMPLE
.\install_service.ps1
#>

$ErrorActionPreference = "Stop"

$ServiceName = "DWRMS_API"
$ProjectRoot = Resolve-Path "..\backend"
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"
$UvicornModule = "uvicorn"
$UvicornArgs = "app.main:app --host 127.0.0.1 --port 8000"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at $VenvPython. Please set up the environment first."
    exit 1
}

$NssmPath = ".\nssm.exe"
if (-not (Test-Path $NssmPath)) {
    Write-Host "NSSM not found locally. Please download nssm.exe and place it in the deploy folder." -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing Windows Service: $ServiceName" -ForegroundColor Cyan

# Stop and remove existing service if present
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service exists. Stopping and removing..."
    Stop-Service -Name $ServiceName -Force
    & $NssmPath remove $ServiceName confirm
}

# Install service
& $NssmPath install $ServiceName $VenvPython "-m" $UvicornModule $UvicornArgs
& $NssmPath set $ServiceName AppDirectory $ProjectRoot
& $NssmPath set $ServiceName Description "DWRMS Enterprise API Backend"
& $NssmPath set $ServiceName Start SERVICE_AUTO_START
& $NssmPath set $ServiceName AppStdout "$ProjectRoot\logs\service.log"
& $NssmPath set $ServiceName AppStderr "$ProjectRoot\logs\service-error.log"

Write-Host "Starting service..."
Start-Service -Name $ServiceName

Write-Host "Service $ServiceName installed and started successfully!" -ForegroundColor Green
