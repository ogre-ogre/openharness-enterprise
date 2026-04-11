import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out: print(out[-3000:] if len(out) > 3000 else out)
    if err: print(f"Err: {err[-1000:]}")
    return out, err, stdout.channel.recv_exit_status()

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 杀掉旧进程
    print("\n=== Killing old processes ===")
    run_cmd("pkill -f 'openharness.enterprise.server' 2>/dev/null || true")
    run_cmd("pkill -f 'oh-enterprise' 2>/dev/null || true")
    
    # 2. 启动服务（正确的命令）
    print("\n=== Starting service ===")
    start_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5

# 使用正确的命令
nohup python -m openharness.enterprise.server start --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
echo "Started with PID: $(cat ~/.oh-enterprise/server.pid)"
sleep 5
tail -30 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(start_cmd, 60)
    
    # 3. 检查服务
    print("\n=== Checking service ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/docs | head -5")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000 || lsof -i :8000 2>/dev/null | head -5")
    
    # 4. 如果还是不行，尝试其他启动方式
    print("\n=== Alternative check ===")
    run_cmd("ps aux | grep python | grep -v grep | grep -v pip")
    
    print("\n" + "="*50)
    print(f"访问: http://10.1.7.155:8000")
    print(f"账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")