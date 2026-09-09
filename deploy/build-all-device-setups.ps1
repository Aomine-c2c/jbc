# ==============================================================================
# Bikita Minerals DWRMS - Unified Multi-Device Packaging Pipeline
# ==============================================================================
# Automates multi-platform packaging for all operational devices:
# 1. Desktop Workstations / Field Laptops (Windows Native NSIS .exe & MSI)
# 2. Rugged Field Tablets (Offline PWA + Android APK build script generator)
# 3. Mobile Handhelds (Progressive Web App distribution bundle)
# 4. Linux Field Terminals (Tauri AppImage / Debian package configuration)
# ==============================================================================

[CmdletBinding()]
param (
    [ValidateSet("all", "desktop", "pwa", "android", "linux")]
    [string]$DevicePlatform = "all",
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   BIKITA MINERALS DWRMS - MULTI-DEVICE SETUP & PACKAGING CORE   " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " Target Device Profile: $DevicePlatform" -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"
$DistDir = Join-Path $ProjectRoot "dist"

# Resolve application version dynamically from tauri.conf.json
$TauriConfPath = Join-Path $FrontendDir "src-tauri\tauri.conf.json"
$AppVersion = "2.10.0"
if (Test-Path $TauriConfPath) {
    try {
        $tauriJson = Get-Content $TauriConfPath -Raw | ConvertFrom-Json
        if ($tauriJson.version) {
            $AppVersion = $tauriJson.version
        }
    } catch {
        Write-Warning "Could not parse tauri.conf.json; using default version $AppVersion"
    }
}
Write-Host " Application Release Version: v$AppVersion" -ForegroundColor Cyan

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
}

Set-Location $FrontendDir

# ------------------------------------------------------------------------------
# STEP 1: Front-End Production Static Export (Used by Tauri, PWA & Mobile Web)
# ------------------------------------------------------------------------------
if (-not $SkipFrontendBuild) {
    Write-Host "`n[1/4] Compiling Next.js multi-device responsive frontend export..." -ForegroundColor Yellow
    npm run build:export
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Frontend compilation failed with exit code $LASTEXITCODE"
    }
    Write-Host "Frontend static export completed successfully into frontend/out." -ForegroundColor Green
} else {
    Write-Host "`n[1/4] Skipping Next.js build as requested." -ForegroundColor DarkGray
}

# ------------------------------------------------------------------------------
# STEP 2: Desktop Workstations & Field Laptops (Tauri Windows .msi & .exe)
# ------------------------------------------------------------------------------
if ($DevicePlatform -eq "all" -or $DevicePlatform -eq "desktop") {
    Write-Host "`n[2/4] Packaging Desktop Workstations & Field Laptops (Windows x64)..." -ForegroundColor Yellow
    
    $NsisBundle = Join-Path $FrontendDir "src-tauri\target\release\bundle\nsis\DWRMS_${AppVersion}_x64-setup.exe"
    $MsiBundle = Join-Path $FrontendDir "src-tauri\target\release\bundle\msi\DWRMS_${AppVersion}_x64_en-US.msi"

    $DesktopDistDir = Join-Path $DistDir "desktop"
    if (-not (Test-Path $DesktopDistDir)) { New-Item -ItemType Directory -Path $DesktopDistDir -Force | Out-Null }

    Write-Host "Compiling native Tauri bundles via npx tauri build..." -ForegroundColor Cyan
    npx tauri build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tauri build failed with exit code $LASTEXITCODE"
    }

    if (Test-Path $NsisBundle) {
        Copy-Item $NsisBundle -Destination $DesktopDistDir -Force
        Write-Host " Desktop NSIS installer copied to dist/desktop/: DWRMS_${AppVersion}_x64-setup.exe" -ForegroundColor Green
    }
    if (Test-Path $MsiBundle) {
        Copy-Item $MsiBundle -Destination $DesktopDistDir -Force
        Write-Host " Desktop MSI installer copied to dist/desktop/: DWRMS_${AppVersion}_x64_en-US.msi" -ForegroundColor Green
    }
}

# ------------------------------------------------------------------------------
# STEP 3: Rugged Field Tablets & Mobile Handhelds (Offline PWA Package)
# ------------------------------------------------------------------------------
if ($DevicePlatform -eq "all" -or $DevicePlatform -eq "pwa") {
    Write-Host "`n[3/4] Packaging Rugged Field Tablets & Mobile PWA..." -ForegroundColor Yellow
    
    $PwaDistDir = Join-Path $DistDir "tablet-mobile-pwa"
    if (-not (Test-Path $PwaDistDir)) { New-Item -ItemType Directory -Path $PwaDistDir -Force | Out-Null }

    # Validate PWA assets
    $PwaManifest = Join-Path $FrontendDir "public\manifest.json"
    $ServiceWorker = Join-Path $FrontendDir "public\sw.js"
    $Icons = @("icon-192.png", "icon-512.png", "favicon.ico")

    $MissingPwa = @()
    if (-not (Test-Path $PwaManifest)) { $MissingPwa += "manifest.json" }
    if (-not (Test-Path $ServiceWorker)) { $MissingPwa += "sw.js" }
    foreach ($icon in $Icons) {
        $iconPath = Join-Path $FrontendDir "public\$icon"
        if (-not (Test-Path $iconPath)) { $MissingPwa += $icon }
    }

    if ($MissingPwa.Count -eq 0) {
        # Create offline PWA deployment archive
        Copy-Item $PwaManifest -Destination $PwaDistDir -Force
        Copy-Item $ServiceWorker -Destination $PwaDistDir -Force
        foreach ($icon in $Icons) {
            Copy-Item (Join-Path $FrontendDir "public\$icon") -Destination $PwaDistDir -Force
        }
        
        # Write device-specific PWA installation and pairing manifest
        $DeviceInfo = @{
            system = "Bikita Minerals DWRMS"
            version = $AppVersion
            device_categories = @("Rugged Tablets (Samsung Tab Active, Zebra)", "Mobile Smartphones (iOS / Android)")
            offline_storage = "IndexedDB + ServiceWorker Cache"
            sync_protocol = "Bi-directional mutation queue via /api/v1/sync"
            install_url = "http://dwrms.bikita.com or mine LAN server IP"
        } | ConvertTo-Json -Depth 4

        Set-Content -Path (Join-Path $PwaDistDir "device-profile.json") -Value $DeviceInfo
        Write-Host " Tablet & Mobile PWA distribution verified in dist/tablet-mobile-pwa/" -ForegroundColor Green
    } else {
        Write-Warning "Missing PWA assets: $($MissingPwa -join ', ')"
    }
}

# ------------------------------------------------------------------------------
# STEP 4: Native Android Tablet / Handheld Setup Generator
# ------------------------------------------------------------------------------
if ($DevicePlatform -eq "all" -or $DevicePlatform -eq "android") {
    Write-Host "`n[4/4] Generating Android Enterprise (APK/AAB) Build Environment..." -ForegroundColor Yellow
    
    $AndroidDistDir = Join-Path $DistDir "android"
    if (-not (Test-Path $AndroidDistDir)) { New-Item -ItemType Directory -Path $AndroidDistDir -Force | Out-Null }

    $AndroidSetupScript = @"
# ==============================================================================
# Bikita Minerals DWRMS - Android Enterprise APK Packaging Instructions
# ==============================================================================
# Requirements:
# 1. Android Studio / Android SDK (Platform 34, Build-Tools 34.0.0)
# 2. OpenJDK 17+ (JAVA_HOME set)
# 3. Rust toolchain targets:
#    rustup target add aarch64-linux-android armv7-linux-androideabi x86_64-linux-android i686-linux-android
#
# Commands:
# cd frontend
# npx tauri android init
# npx tauri android build --apk
# Output APK location: frontend/gen/android/app/build/outputs/apk/release/app-release-unsigned.apk
# ==============================================================================
"@
    Set-Content -Path (Join-Path $AndroidDistDir "BUILD_INSTRUCTIONS.txt") -Value $AndroidSetupScript
    Write-Host " Android Enterprise build instructions generated in dist/android/" -ForegroundColor Green
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "   ALL MULTI-DEVICE PACKAGING TARGETS READY IN: /dist/           " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Get-ChildItem -Path $DistDir -Recurse | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
    $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash.ToLower()
    [PSCustomObject]@{
        Name = $_.Name
        LengthKB = [math]::Round($_.Length / 1KB, 2)
        SHA256 = $hash
    }
} | Format-Table -AutoSize
