import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.107.114.86', username='sila', password='17012024')

# Check tailscale serve status
stdin, stdout, stderr = ssh.exec_command('tailscale serve status')
print("TAILSCALE SERVE STATUS:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
