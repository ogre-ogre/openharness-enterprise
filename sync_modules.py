import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

print('[1] Installing openpyxl in uv environment...')
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && pip install openpyxl')
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print('Result:', out[:300] if out else 'OK')
if err:
    print('Stderr:', err[:200])

print('[2] Installing pptxgenjs...')
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/.oh-enterprise && npm install pptxgenjs')
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print('Result:', out[:300] if out else 'OK')
if err:
    print('Stderr:', err[:200])

print('[3] Verifying installations...')
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && python -c "import openpyxl; print(openpyxl.__version__)"')
print('openpyxl version:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/.oh-enterprise && npm list pptxgenjs')
print('pptxgenjs:', stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()
print('[Done]')