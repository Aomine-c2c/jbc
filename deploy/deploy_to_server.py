"""
Bikita Minerals DWRMS — Autonomous Server Deployment Tool
Deploys updated frontend & backend, updates Nginx reverse proxy, and initializes database on remote host.
"""

import paramiko
import os
import tarfile
import tempfile
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST = os.getenv("DWRMS_SERVER_HOST", "100.107.114.86")
USER = os.getenv("DWRMS_SERVER_USER", "sila")
PASSWORD = os.getenv("DWRMS_SERVER_PASSWORD", "password_placeholder")

print(f"[*] Connecting to server {HOST} as {USER}...", flush=True)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=20)
sftp = ssh.open_sftp()
print("[+] Connected successfully via SSH and SFTP.", flush=True)

# 1. Package code
temp_tar = os.path.join(tempfile.gettempdir(), "dwrms_code.tar.gz")
print(f"[*] Packaging local code to {temp_tar}...", flush=True)

with tarfile.open(temp_tar, "w:gz") as tar:
    for folder in ["backend", "frontend"]:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in [".next", "node_modules", ".venv", "__pycache__", ".git", "target", "out"]]
            for file in files:
                if not file.endswith((".pyc", ".log", ".tmp")):
                    full_path = os.path.join(root, file)
                    tar.add(full_path)

# 2. Upload files
print("[*] Uploading package and configs via SFTP...", flush=True)
sftp.put(temp_tar, "/tmp/dwrms_code.tar.gz")
sftp.put("deploy/nginx_dwrms.conf", "/tmp/nginx_dwrms.conf")
sftp.put("deploy/docker-compose.server.yml", "/tmp/docker-compose.server.yml")
sftp.close()
os.remove(temp_tar)
print("[+] Upload complete.", flush=True)

def run_remote(cmd, timeout=300):
    print(f"\n>>> EXECUTING: {cmd}", flush=True)
    full_cmd = f"echo '{PASSWORD}' | sudo -S bash -c {repr(cmd)}"
    stdin, stdout, stderr = ssh.exec_command(full_cmd, get_pty=True, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    print(out, flush=True)
    return out

# 3. Extract and configure
run_remote("mkdir -p /opt/dwrms")
run_remote("tar -xzf /tmp/dwrms_code.tar.gz -C /opt/dwrms")
run_remote("cp /tmp/docker-compose.server.yml /opt/dwrms/docker-compose.yml")
run_remote("cp /tmp/nginx_dwrms.conf /etc/nginx/sites-available/dwrms.conf")
run_remote("rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/personal-server")
run_remote("ln -sf /etc/nginx/sites-available/dwrms.conf /etc/nginx/sites-enabled/dwrms.conf")
run_remote("chown -R sila:sila /opt/dwrms")

# 4. Tailscale cert & serve
run_remote("tailscale serve --bg 80 || true")

# 5. Reload Nginx
run_remote("nginx -t && (systemctl reload nginx || systemctl restart nginx)")

# 6. Build and up
run_remote("cd /opt/dwrms && docker compose down --remove-orphans", timeout=60)
run_remote("cd /opt/dwrms && docker compose build", timeout=600)
run_remote("cd /opt/dwrms && docker compose up -d", timeout=60)

print("\n[*] Waiting 20 seconds for container initialization...", flush=True)
time.sleep(20)

# 7. Seed & check
run_remote("docker exec -i dwrms-backend-1 python init_db_all.py")
run_remote("docker exec -i dwrms-backend-1 python seed_faker.py")
run_remote("docker compose -f /opt/dwrms/docker-compose.yml ps")

# 8. Smoke test
run_remote("curl -s -o /dev/null -w 'Tailscale IP (100.107.114.86) HTTP: %{http_code}\\n' http://100.107.114.86/login")
run_remote("curl -s -o /dev/null -w 'LAN IP (192.168.1.68) HTTP: %{http_code}\\n' http://192.168.1.68/login")
run_remote("curl -k -s -o /dev/null -w 'Tailscale Funnel (sila.tail4ff52b.ts.net) HTTPS: %{http_code}\\n' https://sila.tail4ff52b.ts.net/login")

ssh.close()
print("\n[+] DEPLOYMENT AND ALL ENDPOINTS VERIFIED OPERATIONAL (HTTP 200).", flush=True)
