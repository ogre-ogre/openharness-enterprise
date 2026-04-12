import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

stdin, stdout, stderr = ssh.exec_command('/bin/cat /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py | /usr/bin/head -n 1880 | /usr/bin/tail -n 10', timeout=10)
print('Lines 1870-1880:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('/bin/wc -l /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py', timeout=10)
print('Lines count:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('/usr/bin/grep UNDELETABLE /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py', timeout=10)
print('UNDELETABLE grep:', stdout.read().decode('utf-8', errors='replace').strip())
err = stderr.read().decode('utf-8', errors='replace').strip()
if err:
    print('grep stderr:', err)

ssh.close()