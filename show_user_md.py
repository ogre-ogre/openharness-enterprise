import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)
stdin, stdout, stderr = ssh.exec_command('/bin/cat /home/ai-app/.oh-enterprise/users/3/user.md', timeout=10)
print(stdout.read().decode('utf-8', errors='replace').strip())
ssh.close()