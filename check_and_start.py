import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查日志
    print("=== Server log ===")
    stdin, stdout, stderr = ssh.exec_command("tail -20 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 检查进程
    print("\n=== Processes ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
    print(stdout.read().decode())
    
    # 如果没运行，启动
    print("\n=== Starting if not running ===")
    stdin, stdout, stderr = ssh.exec_command('''
if ! pgrep -f "uvicorn.*openharness" > /dev/null; then
    echo "Starting service..."
    cd /home/ai-app/oh-enterprise-1.0.0
    source venv/bin/activate
    export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
    export ANTHROPIC_AUTH_TOKEN=sk-test
    export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
    export ANTHROPIC_MODEL=glm-5
    nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
    sleep 5
    echo "Started"
else
    echo "Already running"
fi
tail -10 ~/.oh-enterprise/logs/server.log
''', timeout=30)
    print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/admin | head -5")
    print(f"Admin: {stdout.read().decode()}")
    
finally:
    ssh.close()