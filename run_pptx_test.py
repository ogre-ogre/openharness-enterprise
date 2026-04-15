import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

# Upload Node.js test script
sftp = ssh.open_sftp()
sftp.put('D:/openharness-enterprise/test_pptx_node.js', '/home/ai-app/test_pptx.js')
sftp.close()

# Execute Node.js script
stdin, stdout, stderr = ssh.exec_command('/home/ai-app/node-v10.24.1-linux-x64/bin/node /home/ai-app/test_pptx.js', timeout=30)
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print('Node stdout:', out)
print('Node stderr:', err[:100] if err else 'None')

# Check if file created
stdin, stdout, stderr = ssh.exec_command('ls -la /home/ai-app/.oh-enterprise/users/3/downloads/', timeout=10)
files = stdout.read().decode('utf-8', errors='replace').strip()
print('Downloads:', files)

ssh.close()