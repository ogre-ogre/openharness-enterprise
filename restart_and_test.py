import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 杀掉所有进程
    print("=== Killing all processes ===")
    stdin, stdout, stderr = ssh.exec_command("pkill -9 -f uvicorn 2>/dev/null; pkill -9 -f python.*server 2>/dev/null; sleep 2")
    stdout.read()
    
    # 2. 启动服务
    print("=== Starting service ===")
    stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
sleep 5
echo "=== Log ==="
tail -10 ~/.oh-enterprise/logs/server.log
''', timeout=30)
    print(stdout.read().decode())
    
    # 3. 快速测试
    print("\n=== Quick tests ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health && echo ''")
    health = stdout.read().decode().strip()
    print(f"Health: {health}")
    
    if "healthy" in health:
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/admin | head -3")
        print(f"Admin: {stdout.read().decode()}")
        
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/web/ | head -3")
        print(f"Web: {stdout.read().decode()}")
    
    print("\n" + "="*50)
    print("前端: http://10.1.7.155:8000/web/")
    print("管理: http://10.1.7.155:8000/admin")
    print("="*50)
    
finally:
    ssh.close()