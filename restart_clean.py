import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 杀掉所有旧进程
    print("=== Killing old processes ===")
    stdin, stdout, stderr = ssh.exec_command("pkill -9 -f 'uvicorn' 2>/dev/null; pkill -9 -f 'openharness' 2>/dev/null; sleep 2; echo 'Done'")
    print(stdout.read().decode())
    
    # 启动服务
    print("\n=== Starting service ===")
    stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
echo "Started PID: $(cat ~/.oh-enterprise/server.pid)"
sleep 5
echo "=== Log ==="
tail -20 ~/.oh-enterprise/logs/server.log
echo "=== Health ==="
curl -s http://localhost:8000/health
echo ""
echo "=== Port ==="
netstat -tlnp 2>/dev/null | grep 8000
''', timeout=30)
    print(stdout.read().decode())
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()