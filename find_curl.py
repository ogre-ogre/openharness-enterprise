import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

stdin, stdout, stderr = ssh.exec_command('/usr/bin/curl --version', timeout=10)
print('curl:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('/usr/sbin/lsof -i:8000', timeout=10)
print('Port 8000:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('ls /usr/bin/', timeout=10)
print('/usr/bin files:', stdout.read().decode('utf-8', errors='replace').strip()[:300])

stdin, stdout, stderr = ssh.exec_command('/usr/bin/python -c "import urllib.request; print(urllib.request.urlopen(\"http://localhost:8000/health\").read().decode())"', timeout=15)
print('Python health:', stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()