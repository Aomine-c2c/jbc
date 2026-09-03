import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.107.114.86', username='sila', password='17012024')

# Check nginx access and error logs
stdin, stdout, stderr = ssh.exec_command('echo 17012024 | sudo -S docker logs --tail 40 $(echo 17012024 | sudo -S docker ps -qf name=nginx)')
print("NGINX LOGS:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
