import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

stdin, stdout, stderr = ssh.exec_command('/home/ai-app/nodejs/bin/node --version', timeout=10)
print('Node:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('/home/ai-app/nodejs/bin/npm --version', timeout=10)
print('npm:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('ls /home/ai-app/.oh-enterprise/node_modules/pptxgenjs/package.json', timeout=10)
print('pptxgenjs files:', stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()