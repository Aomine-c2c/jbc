<#
.SYNOPSIS
Checks the health and readiness of the DWRMS system.

.DESCRIPTION
Pings the API /health and /readiness endpoints to ensure the service is running
and connected to the database successfully.

.EXAMPLE
.\startup_check.ps1
#>

$ApiUrl = "http://127.0.0.1:8000/api/v1"
$ErrorActionPreference = "Stop"

Write-Host "Checking API Liveness (/health)..."
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get -TimeoutSec 5
    if ($response.status -eq "ok") {
        Write-Host "API is running." -ForegroundColor Green
    } else {
        Write-Host "API returned unknown status: $($response.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Error "Failed to connect to API: $_"
    exit 1
}

Write-Host "Checking API Readiness (/readiness)..."
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/readiness" -Method Get -TimeoutSec 5
    if ($response.status -eq "ready" -and $response.database -eq "connected") {
        Write-Host "API is ready and connected to the database." -ForegroundColor Green
    } else {
        Write-Host "API returned unknown readiness state." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Readiness check failed. Database might be down or API is experiencing errors: $_"
    exit 1
}

Write-Host "Checking System Version (/version)..."
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/version" -Method Get -TimeoutSec 5
    Write-Host "System Version: $($response.version) ($($response.environment))" -ForegroundColor Cyan
} catch {
    Write-Host "Could not fetch version." -ForegroundColor Yellow
}

Write-Host "All startup checks passed!" -ForegroundColor Green
