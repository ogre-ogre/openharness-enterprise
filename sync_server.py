import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

sftp.put('D:/openharness-enterprise/src/openharness/enterprise/server.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py')
print('server.py synced')

sftp.close()

stdin, stdout, stderr = ssh.exec_command('grep -n "UNDELETABLE" /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py', timeout=10)
print('Verify:', stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()