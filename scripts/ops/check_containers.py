import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.107.114.86', username='sila', password='17012024')

stdin, stdout, stderr = ssh.exec_command('echo 17012024 | sudo -S docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')
print("CONTAINERS:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
