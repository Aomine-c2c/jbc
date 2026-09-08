import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.107.114.86', username='sila', password='17012024')

# Test POST to setup step 1 through port 3000 (Next.js reverse proxy or direct) or whatever port Tailscale hits
cmd = """curl -v -X POST http://localhost:3000/api/v1/setup/step/1 \
  -H "Content-Type: application/json" \
  -H "Origin: https://sila.tail4ff52b.ts.net" \
  -d '{"step_data": {"organization_name": "Bikita Minerals", "installation_name": "Petalite", "server_name": "masvingo-srv-01", "environment": "production", "timezone": "Africa/Harare"}}'
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
