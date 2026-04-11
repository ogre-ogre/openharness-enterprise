import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=600):
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
    
    # 1. 杀掉旧的pip进程
    print("\n=== Killing old pip process ===")
    run_cmd("pkill -f 'pip install' 2>/dev/null || true")
    
    # 2. 检查虚拟环境
    print("\n=== Checking venv ===")
    run_cmd(f"ls -la {deploy_path}/venv/bin/")
    
    # 3. 安装核心依赖
    print("\n=== Installing core dependencies ===")
    install_cmd = f'''
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
cd {deploy_path}
source venv/bin/activate
pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn pydantic python-multipart aiofiles aiosqlite python-jose passlib anthropic openai python-dotenv pyyaml httpx
'''
    run_cmd(install_cmd, 600)
    
    # 4. 验证安装
    print("\n=== Verifying ===")
    run_cmd(f"export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && source {deploy_path}/venv/bin/activate && python -c 'import fastapi, uvicorn; print(\"OK\")'")
    
    # 5. 启动服务
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
sleep 5
tail -30 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(start_cmd, 60)
    
    # 6. 检查服务
    print("\n=== Checking service ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("ss -tlnp | grep 8000")
    
    print("\n" + "="*50)
    print(f"访问: http://10.1.7.155:8000")
    print(f"账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")