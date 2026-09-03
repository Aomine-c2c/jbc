import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('100.107.114.86', username='sila', password='17012024')

# Check containers and run db query
stdin, stdout, stderr = ssh.exec_command('echo 17012024 | sudo -S docker exec -i $(echo 17012024 | sudo -S docker ps -qf name=db) psql -U postgres -d dwrms -c "SELECT id, job_number, title, status FROM job_cards LIMIT 10;"')
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
