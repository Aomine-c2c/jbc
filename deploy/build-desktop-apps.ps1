# ==============================================================================
# Bikita Minerals DWRMS - Desktop & Client Packaging Script (Windows PowerShell)
# ==============================================================================
# Builds Next.js frontend static assets and compiles native Tauri Windows .exe / .msi
# ==============================================================================

[CmdletBinding()]
param (
    [switch]$SkipFrontendBuild,
    [string]$Target = "msi"
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   BIKITA MINERALS DWRMS - WINDOWS DESKTOP PACKAGING PIPELINE   " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"

Set-Location $FrontendDir

# 1. Environment Verification
Write-Host "[1/4] Checking Node.js and Rust build tools..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js is not found on PATH. Please install Node.js 20+."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm is not found on PATH."
}

# 2. Frontend Production Build
if (-not $SkipFrontendBuild) {
    Write-Host "[2/4] Compiling Next.js production frontend..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Next.js build failed with exit code $LASTEXITCODE"
    }
    Write-Host "Frontend build completed successfully." -ForegroundColor Green
} else {
    Write-Host "[2/4] Skipping Next.js build as requested." -ForegroundColor DarkGray
}

# 3. Tauri Desktop Compilation
Write-Host "[3/4] Compiling Tauri Native Windows Application..." -ForegroundColor Yellow

if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Write-Host "Building Tauri release binary via cargo-tauri..." -ForegroundColor Cyan
    npx tauri build --target $Target
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tauri build completed successfully!" -ForegroundColor Green
    } else {
        Write-Warning "Tauri packaging completed with warning/status code $LASTEXITCODE."
    }
} else {
    Write-Warning "Rust / Cargo is not installed on this host. Skipping binary compilation step."
    Write-Host "To produce .msi/.exe installers, install Rust from https://rustup.rs and run this script again." -ForegroundColor DarkYellow
}

# 4. Output Summary
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   PACKAGING SUMMARY & DISTRIBUTION ARTIFACTS                    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " • Static Web / PWA Build: $FrontendDir/out" -ForegroundColor Green
Write-Host " • Tauri Release Bundle:   $FrontendDir/src-tauri/target/release/bundle/" -ForegroundColor Green
Write-Host " • PWA Manifest:           $FrontendDir/public/manifest.json" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
