# Bikita Minerals DWRMS - Local Client Applications Setup Guide

Comprehensive guide for deploying and configuring local client applications (Desktop & Rugged Mobile Tablets) across Bikita Minerals mining operations.

---

## 1. Supported Client Platforms

| Platform | Deployment Target | Key Features | Recommended Use Case |
| :--- | :--- | :--- | :--- |
| **Windows Desktop App** | Native `.exe` / `.msi` (Tauri) | Multi-window, hardware acceleration, zero-browser clutter, direct printer integration | Workshop PCs, Control Room consoles, Engineering & Planning offices |
| **Rugged Tablet / Phone (PWA)** | Android / iOS / Windows Rugged (Chrome / Edge PWA) | Offline IndexedDB storage, Camera barcode & QR scanning, background mutation sync | Open pit operators, field artisans, underground mobile technicians |
| **Local LAN Web Browser** | Standard modern web browser (`http://dwrms-server.local`) | Zero-install, instant access, live WebSocket telemetry | Guest terminals, supervisor inspection laptops |

---

## 2. Windows Desktop App Setup (Workshop & Office PCs)

### Automated Installation:
1. Obtain the installer package `DWRMS_2.9.0_x64_en-US.msi` from IT distribution share (`\\dwrms-server\dist\desktop`).
2. Run the installer with administrator privileges:
   ```powershell
   msiexec /i DWRMS_2.9.0_x64_en-US.msi /quiet /qn
   ```
3. A desktop shortcut **"Bikita Minerals DWRMS"** will be created automatically.

### First-Launch Server Configuration:
1. Open the DWRMS application.
2. If the application is unable to reach the default address (`http://dwrms-server.local`), the **Server Configuration Dialog** will appear automatically.
3. Select **"Local Mine LAN Server"** or enter the server static IP (e.g. `http://192.168.1.100:8000`).
4. Click **"Test Connection"** to verify roundtrip latency (< 15 ms on LAN).
5. Click **"Save & Connect"**. The endpoint is saved to encrypted local storage.

---

## 3. Rugged Field Tablet & Smartphone Setup (PWA)

### Installation on Android / Samsung Active Rugged Tablets:
1. Connect the tablet to the **Bikita-Mine-WLAN** or field private APN.
2. Open Google Chrome and navigate to `http://dwrms-server.local` or `http://192.168.1.100`.
3. Tap the **"Install DWRMS App"** banner at the bottom or open Chrome menu (⋮) → **"Install app"** / **"Add to Home Screen"**.
4. The DWRMS icon will appear on the tablet home screen with standalone fullscreen display mode.

### Offline Field Capabilities:
- **Offline Fault Logging**: If WiFi signal drops underground or in the open pit, operators can continue creating faults, completing inspection checklists, and recording meter hours.
- **Queued Mutations**: Requests are queued into IndexedDB (`dwrms_offline_db`).
- **Auto-Sync**: As soon as the tablet re-enters workshop or relay WiFi coverage, the background sync engine transmits all queued records to the server without data loss.

---

## 4. Server Auto-Discovery & QR Code Setup

To instantly connect a new device without typing IP addresses:
1. On any active Supervisor/Admin console, navigate to `/admin/system`.
2. Click **"Configure Server Node"** to display the **Quick-Connect QR Code**.
3. On the field tablet or desktop app, click **"Scan Server QR"** to automatically bind the client to the active production node.

---

## 5. Troubleshooting & Diagnostic Commands

| Issue | Resolution Steps |
| :--- | :--- |
| **"Unable to connect to authentication server"** | 1. Verify PC is connected to the mine LAN.<br>2. Open `/admin/system` (or press `Ctrl+Shift+S`) to open the Server Config dialog.<br>3. Test ping to `http://dwrms-server.local:8000/api/v1/health`. |
| **App shows old cache after server update** | Click **"Refresh Telemetry"** or press `Ctrl+F5` (Desktop: press `Ctrl+R` to force reload runtime). |
| **Tauri Desktop build from source** | Run `deploy/build-desktop-apps.ps1` in PowerShell with Rust toolchain installed. |
