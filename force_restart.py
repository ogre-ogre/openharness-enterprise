import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

stdin, stdout, stderr = ssh.exec_command('/bin/kill -9 3107364', timeout=5)
stdout.read()
print('Killed 3107364')

stdin, stdout, stderr = ssh.exec_command('/bin/kill -9 3107727', timeout=5)
stdout.read()
print('Killed 3107727')

time.sleep(5)

stdin, stdout, stderr = ssh.exec_command('/usr/sbin/lsof -i:8000 -i:8001', timeout=5)
print('Ports:', stdout.read().decode('utf-8', errors='replace').strip())

time.sleep(5)

# 启动服务
stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && python -m uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000', timeout=15)
time.sleep(15)

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:8000/health', timeout=5)
print('Health:', stdout.read().decode('utf-8', errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command('/usr/sbin/lsof -i:8000', timeout=5)
print('Port 8000:', stdout.read().decode('utf-8', errors='replace').strip())

ssh.close()