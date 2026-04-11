import paramiko
import sys

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    # Read output in real-time
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end='')
        sys.stdout.flush()
    err = stderr.read().decode('utf-8')
    if err: print(f"\nErr: {err[-500:]}")
    return stdout.channel.recv_exit_status()

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 快速检查状态
    print("\n=== Quick status check ===")
    run_cmd("ps aux | grep python | grep -v grep | head -5")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000 || ss -tlnp 2>/dev/null | grep 8000")
    run_cmd("curl -s http://localhost:8000/health || echo 'Not running'")
    
    # 2. 启动服务
    print("\n=== Starting service ===")
    start_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup python -m openharness.enterprise.server --port 8000 --host 0.0.0.0 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
echo "Service starting..."
sleep 5
echo "=== Server log ==="
tail -30 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(start_cmd, 60)
    
    # 3. 检查服务
    print("\n=== Final check ===")
    run_cmd("curl -s http://localhost:8000/health")
    
    print("\n" + "="*50)
    print(f"访问: http://10.1.7.155:8000")
    print(f"账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")