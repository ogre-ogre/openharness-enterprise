import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

# 用Python读取日志
cmd = '''/home/ai-app/oh-enterprise-1.0.0/venv/bin/python -c "
import sys
try:
    with open('/home/ai-app/.oh-enterprise/logs/server.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-200:]:
            print(line, end='')
except Exception as e:
    print(f'Error: {e}')
"'''

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
print('=== Server Log (last 200 lines) ===')
print(stdout.read().decode())

# 用Python读取审计日志
cmd2 = '''/home/ai-app/oh-enterprise-1.0.0/venv/bin/python -c "
import sys
try:
    with open('/home/ai-app/.oh-enterprise/logs/audit-2026-04-13.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-50:]:
            print(line, end='')
except Exception as e:
    print(f'Error: {e}')
"'''

stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=15)
print('\n=== Audit Log (last 50 lines) ===')
print(stdout.read().decode())

ssh.close()