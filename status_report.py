import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

print('=== Remote Environment Status ===')
print()

# Check service
stdin, stdout, stderr = ssh.exec_command('/usr/sbin/lsof -i:8000')
print('1. Service on port 8000:', stdout.read().decode().strip()[:50])

# Check openpyxl
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && python -c "import openpyxl"')
err = stderr.read().decode().strip()
print('2. openpyxl:', 'OK' if not err else 'ERROR: ' + err[:50])

# Check Node.js
stdin, stdout, stderr = ssh.exec_command('/home/ai-app/node-v10.24.1-linux-x64/bin/node --version')
print('3. Node.js:', stdout.read().decode().strip())

# Check downloads_path in webchat.py
stdin, stdout, stderr = ssh.exec_command('/usr/bin/grep -c downloads_path /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/webchat.py')
print('4. downloads_path in webchat.py:', stdout.read().decode().strip(), 'lines')

# Check downloads directory
stdin, stdout, stderr = ssh.exec_command('/bin/ls -la /home/ai-app/.oh-enterprise/users/3/')
print('5. User 3 home:', stdout.read().decode().strip()[:100])

# Check user.md
stdin, stdout, stderr = ssh.exec_command('/bin/cat /home/ai-app/.oh-enterprise/users/3/user.md')
user_md = stdout.read().decode()
print('6. user.md exists:', 'YES' if user_md else 'NO')
if 'downloads' in user_md:
    print('   downloads path configured: YES')
else:
    print('   downloads path configured: NO')

# Check pptxgenjs
stdin, stdout, stderr = ssh.exec_command('/bin/ls /home/ai-app/.oh-enterprise/node_modules/pptxgenjs/')
print('7. pptxgenjs files:', stdout.read().decode().strip()[:50])

ssh.close()