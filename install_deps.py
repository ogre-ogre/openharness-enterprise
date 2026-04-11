import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-3000:] if len(out) > 3000 else out)
    if err and 'warning' not in err.lower(): 
        print(f"Err: {err[-1000:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 使用阿里云HTTP镜像
    print("\n=== Installing with Aliyun HTTP mirror ===")
    
    install_cmd = f'''
cd {deploy_path}
source venv/bin/activate
pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com fastapi uvicorn pydantic python-multipart aiofiles aiosqlite python-jose passlib anthropic openai python-dotenv pyyaml httpx
'''
    
    out, err, exit_code = run_cmd(install_cmd, 600)
    
    if exit_code == 0:
        print("\n=== Success! Verifying installation ===")
        verify_cmd = f'''
cd {deploy_path}
source venv/bin/activate
python -c "import fastapi, uvicorn; print('Dependencies installed successfully!')"
'''
        run_cmd(verify_cmd)
        
        print("\n=== Starting server ===")
        start_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup python -m openharness.enterprise.server --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
sleep 5
cat ~/.oh-enterprise/logs/server.log | tail -20
'''
        run_cmd(start_cmd, 30)
        
        print("\n=== Checking service ===")
        run_cmd("curl -s http://localhost:8000/health || echo 'Not ready'")
        run_cmd("netstat -tlnp 2>/dev/null | grep 8000 || ss -tlnp 2>/dev/null | grep 8000")
    else:
        print("\n=== Installation failed, trying alternative approach ===")
        
        # 尝试逐个安装
        packages = [
            "fastapi", "uvicorn", "pydantic", "python-multipart",
            "aiofiles", "aiosqlite", "python-jose", "passlib",
            "anthropic", "openai", "python-dotenv", "pyyaml", "httpx"
        ]
        
        for pkg in packages:
            print(f"\n--- Installing {pkg} ---")
            run_cmd(f'''
cd {deploy_path}
source venv/bin/activate
pip install --index-url http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com {pkg}
''', 120)
    
finally:
    ssh.close()
    print("\nDone")