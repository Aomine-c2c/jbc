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

run_cmd("tailscale serve status")
run_cmd("cat /etc/nginx/sites-enabled/*")

ssh.close()
