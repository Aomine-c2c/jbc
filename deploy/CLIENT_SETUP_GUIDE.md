# Bikita Minerals DWRMS - Multi-Device Client Applications Setup & Deployment Guide

Authoritative engineering and deployment guide for rolling out DWRMS across all operational hardware categories:
1. **Desktop Workstations & Control Room Consoles** (Windows 10/11 x64)
2. **Field Maintenance Laptops** (Semi/Fully Rugged Toughbooks, Dell Rugged)
3. **Rugged Field Tablets** (Samsung Galaxy Tab Active4 Pro, Zebra ET51/ET56)
4. **Mobile Handhelds & Field Smartphones** (iOS / Android / Zebra TC-series)

---

## 1. Multi-Device Platform Matrix

| Platform / Form Factor | Target Device Hardware | Distribution Channel | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Desktop Workstations** | 1920x1080+ Monitored PCs, Dual-Screen Control Consoles | Native `.msi` (GPO rollout) or `.exe` setup | Ultra-responsive hardware acceleration, multi-monitor telemetry, batch work-order dispatching, and system administration. |
| **Field Laptops** | Panasonic Toughbook, Dell Latitude Rugged, Lenovo ThinkPad | Native `.exe` / `.msi` or Local Browser via Tailscale | Full offline work-order drafting, batch job card sign-offs, and remote network mesh connectivity via Tailscale. |
| **Rugged Field Tablets** | Samsung Galaxy Tab Active, Zebra ET5x, DT Research | Progressive Web App (PWA) / Native Android APK | 48px+ glove-friendly touch targets, Pre-Start Inspection checklists, capacitive digital signature pads, offline IndexedDB mutation sync. |
| **Mobile Handhelds** | iPhone, Android, Honeywell / Zebra Handheld Computers | Standalone PWA / Mobile Web Browser | Responsive bottom navigation bar, single-tap requisition approvals, instant hazard camera uploads with GPS tagging. |

---

## 2. Automated Multi-Device Packaging Pipeline

Run the unified packaging script from the repository root:
```powershell
.\deploy\build-all-device-setups.ps1
```

### Parameterized Target Packaging:
```powershell
# Package only Desktop Workstations & Field Laptops
.\deploy\build-all-device-setups.ps1 -DevicePlatform desktop

# Package only Rugged Tablets & Mobile PWA assets
.\deploy\build-all-device-setups.ps1 -DevicePlatform pwa

# Generate Android Enterprise build instructions and environment
.\deploy\build-all-device-setups.ps1 -DevicePlatform android
```

### Generated Distribution Directory Structure (`/dist`):
```text
dist/
├── desktop/
│   ├── DWRMS_2.9.0_x64-setup.exe      (Self-contained NSIS Installer - 2.64 MB)
│   └── DWRMS_2.9.0_x64_en-US.msi      (Active Directory GPO Installer - 3.62 MB)
├── tablet-mobile-pwa/
│   ├── manifest.json                  (PWA Web Manifest with 192x192 & 512x512 icons)
│   ├── sw.js                          (Service Worker offline shell & cache engine)
│   ├── icon-192.png                   (High-resolution tablet icon)
│   ├── icon-512.png                   (High-resolution splash icon)
│   └── device-profile.json            (Device configuration metadata)
└── android/
    └── BUILD_INSTRUCTIONS.txt         (Android Enterprise APK build instructions)
```

---

## 3. Workstation & Field Laptop Setup (Windows x64)

### Automated Silent Installation (Active Directory GPO / SCCM):
```powershell
msiexec /i dist\desktop\DWRMS_2.9.0_x64_en-US.msi /quiet /qn
```

### Manual Interactive Installation:
1. Double-click `dist\desktop\DWRMS_2.9.0_x64-setup.exe`.
2. Follow on-screen prompts; desktop shortcut and start menu entries are created automatically.

---

## 4. Rugged Field Tablet Setup (Android / Windows Rugged)

### Deploying PWA on Samsung Galaxy Tab Active / Zebra ET5x:
1. Connect device to the **Bikita-Mine-WLAN** or private mining APN.
2. Launch Google Chrome and browse to `http://dwrms.bikita.com` or local server IP (e.g., `http://192.168.1.100`).
3. Tap **"Install Bikita DWRMS App"** banner or tap Menu (⋮) → **"Install app"** / **"Add to Home screen"**.
4. Launch DWRMS directly from the home screen in standalone immersive fullscreen mode.

### Offline Field Capabilities:
- **Offline Inspection Checklists**: Pre-start machinery checks and meter readings operate without cellular or WiFi coverage.
- **IndexedDB Sync Queue**: Mutations are stored locally in browser IndexedDB.
- **Automatic Reconnection Sync**: The background sync engine automatically flushes queued operations to the central server when the vehicle returns to pit-rim or workshop WiFi range.

---

## 5. Mobile Handheld & Smartphone Setup (iOS & Android)

1. Open Safari (iOS) or Chrome (Android) and navigate to the application URL.
2. **iOS**: Tap the Share button → tap **"Add to Home Screen"** → tap **"Add"**.
3. **Android**: Tap the menu (⋮) → tap **"Add to Home Screen"** or **"Install App"**.
4. The app runs in borderless standalone mode with full mobile bottom-bar navigation.

---

## 6. Native Android Enterprise APK Packaging (Optional)

For managed fleets requiring an `.apk` file for Mobile Device Management (MDM / SOTI / Microsoft Intune):
1. Install Android SDK (Platform 34, Build Tools 34.0.0) and OpenJDK 17+.
2. Add Rust Android targets:
   ```bash
   rustup target add aarch64-linux-android armv7-linux-androideabi x86_64-linux-android
   ```
3. Initialize and build APK via Tauri CLI:
   ```bash
   cd frontend
   npx tauri android init
   npx tauri android build --apk
   ```
4. Output APK is created in `frontend/gen/android/app/build/outputs/apk/release/app-release-unsigned.apk`.
