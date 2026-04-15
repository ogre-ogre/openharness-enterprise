import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

# 检查 node 是否存在
stdin, stdout, stderr = ssh.exec_command('which node')
node_path = stdout.read().decode('utf-8', errors='replace').strip()
print('Node path:', node_path if node_path else 'Not installed')

# 测试 Python openpyxl
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && python -c "import openpyxl; print(openpyxl.__version__)"')
print('openpyxl:', stdout.read().decode('utf-8', errors='replace').strip())

# 检查 pptxgenjs 文件
stdin, stdout, stderr = ssh.exec_command('ls /home/ai-app/.oh-enterprise/node_modules/pptxgenjs/package.json')
pkg = stdout.read().decode('utf-8', errors='replace').strip()
print('pptxgenjs package.json:', pkg[:50] if pkg else 'Not found')

ssh.close()