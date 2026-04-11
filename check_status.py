import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查进程
    print("=== Check processes ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
    print(stdout.read().decode())
    
    # 2. 检查日志
    print("=== Server log ===")
    stdin, stdout, stderr = ssh.exec_command("tail -20 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 3. 测试 API
    print("\n=== Test API ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    result = stdout.read().decode()
    print(f"Health: {result}")
    
    # 4. 测试 assets
    print("\n=== Test assets ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -5")
    print(stdout.read().decode())
    
    # 5. 如果服务没运行，启动它
    if "healthy" not in result:
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
curl -s http://localhost:8000/health
curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -3
''', timeout=30)
        print(stdout.read().decode())
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()