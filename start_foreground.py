import paramiko
import time

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 直接在前台启动，捕获所有输出
    print("=== Starting server in foreground (15 seconds) ===")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
timeout 15 python -m openharness.enterprise.server start --port 8000 2>&1 || true
'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    
    # 实时读取输出
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end='')
    
    print("\n\n=== Checking if running ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo 'Not running'")
    print(stdout.read().decode())
    
finally:
    ssh.close()