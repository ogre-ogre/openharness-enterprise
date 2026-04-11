import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查进程
    print("=== Processes ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
    processes = stdout.read().decode()
    print(processes)
    
    # 如果没有运行，启动
    if not processes.strip():
        print("\n=== Starting service ===")
        stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
sleep 5
tail -15 ~/.oh-enterprise/logs/server.log
''', timeout=30)
        print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/web/ | head -10")
    print(f"Web: {stdout.read().decode()}")
    
    print("\n" + "="*50)
    print("服务地址: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()