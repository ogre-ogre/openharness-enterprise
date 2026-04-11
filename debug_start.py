import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查完整日志
    print("=== Full server log ===")
    stdin, stdout, stderr = ssh.exec_command("cat ~/.oh-enterprise/logs/server.log 2>&1")
    out = stdout.read().decode()
    print(out)
    
    # 检查端口
    print("\n=== Checking port 8000 ===")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 8000 || lsof -i :8000 2>/dev/null | head -5")
    print(stdout.read().decode())
    
    # 检查进程
    print("\n=== Checking uvicorn process ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'uvicorn|python.*server' | grep -v grep")
    print(stdout.read().decode())
    
    # 直接启动服务看输出
    print("\n=== Starting service directly ===")
    stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
timeout 10 uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 2>&1 || true
''', timeout=30)
    print(stdout.read().decode())
    
finally:
    ssh.close()