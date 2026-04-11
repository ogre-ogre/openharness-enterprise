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
    return out

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 杀掉旧进程
    print("\n=== Killing old processes ===")
    run_cmd("pkill -f 'uvicorn.*openharness' 2>/dev/null || true")
    run_cmd("pkill -f 'openharness.enterprise' 2>/dev/null || true")
    
    # 2. 使用 uvicorn 启动
    print("\n=== Starting with uvicorn ===")
    start_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
echo "Started with PID: $(cat ~/.oh-enterprise/server.pid)"
sleep 5
tail -20 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(start_cmd, 30)
    
    # 3. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/ | head -20")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000")
    
    # 4. 测试登录
    print("\n=== Testing login ===")
    run_cmd("curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'")
    
    print("\n" + "="*60)
    print("✅ 部署完成!")
    print("="*60)
    print(f"访问地址: http://10.1.7.155:8000")
    print(f"API文档: http://10.1.7.155:8000/docs")
    print(f"管理后台: http://10.1.7.155:8000/admin")
    print(f"账号: admin / admin123")
    print("="*60)
    
finally:
    ssh.close()
    print("\nDone")