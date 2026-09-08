import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

host = "100.107.114.86"
user = "sila"
password = "password_placeholder"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=password, timeout=15)

def run_cmd(cmd):
    print(f"\n>>> EXECUTING: {cmd}", flush=True)
    stdin, stdout, stderr = ssh.exec_command(f"sudo -n {cmd}", get_pty=False)
    stdin.write(f"{password}\n")
    stdin.flush()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print("STDOUT:", out, flush=True)
    if err:
        print("STDERR:", err, flush=True)
    return out

# 1. Reset Tailscale serve & Funnel to proxy port 80 (Nginx)
run_cmd("tailscale serve reset")
run_cmd("tailscale serve --bg 80")
run_cmd("tailscale funnel --bg 80")
run_cmd("tailscale serve status")

# 2. Re-test POST /api/v1/setup/step/1 via Tailscale domain
run_cmd("curl -k -v -X POST https://sila.tail4ff52b.ts.net/api/v1/setup/step/1 -H 'Content-Type: application/json' -d '{\"step_data\": {\"organization_name\": \"Bikita Minerals\", \"installation_name\": \"Masvingo lithium\", \"server_name\": \"bikita-srv-01\", \"environment\": \"production\", \"timezone\": \"Africa/Harare\"}}'")

ssh.close()
