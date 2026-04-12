import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

stdin, stdout, stderr = ssh.exec_command('/bin/cat /home/ai-app/.oh-enterprise/users/3/user.md', timeout=10)
user_md = stdout.read().decode('utf-8', errors='replace')
print('user.md content:')
print(user_md)
print('---')

stdin, stdout, stderr = ssh.exec_command('/usr/bin/grep downloads_path /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/webchat.py', timeout=10)
grep_out = stdout.read().decode('utf-8', errors='replace')
print('downloads_path in webchat.py:')
print(grep_out[:200] if grep_out else 'NOT FOUND')

ssh.close()