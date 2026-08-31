import paramiko, sys
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('sila', username='sila', password='17012024')
stdin, stdout, stderr = client.exec_command('echo 17012024 | sudo -S docker exec dwrms-db-1 psql -U dwrms_prod -d dwrms -c \"SELECT email FROM users;\"')
stdin.flush()
output = stdout.read().decode('utf-8')
print('DB Users:', output)
client.close()
