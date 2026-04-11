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
    if out: print(out[-4000:] if len(out) > 4000 else out)
    if err: print(f"Err: {err[-1500:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 创建虚拟环境
    print("\n=== Creating virtual environment ===")
    run_cmd(f"rm -rf {deploy_path}/venv")
    run_cmd(f"export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && /home/ai-app/python3.12-ssl/bin/python3 -m venv {deploy_path}/venv")
    
    # 2. 安装依赖
    print("\n=== Installing dependencies ===")
    install_cmd = f'''
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
cd {deploy_path}
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
'''
    run_cmd(install_cmd, 600)
    
    # 3. 验证安装
    print("\n=== Verifying installation ===")
    run_cmd(f"export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && cd {deploy_path} && source venv/bin/activate && python -c 'import fastapi, uvicorn; print(\"Dependencies OK\")'")
    
    # 4. 创建数据目录
    print("\n=== Creating data directories ===")
    run_cmd("mkdir -p ~/.oh-enterprise/users ~/.oh-enterprise/shared/skills ~/.oh-enterprise/logs")
    
    # 5. 配置环境变量
    print("\n=== Configuring environment ===")
    run_cmd(f"cat {deploy_path}/.env 2>/dev/null || echo 'No .env file'")
    
    # 6. 停止旧服务
    print("\n=== Stopping old service ===")
    run_cmd("pkill -f 'openharness.enterprise.server' 2>/dev/null || true")
    
    # 7. 启动服务
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
cat ~/.oh-enterprise/logs/server.log | tail -30
'''
    run_cmd(start_cmd, 60)
    
    # 8. 检查服务状态
    print("\n=== Checking service status ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000 || ss -tlnp 2>/dev/null | grep 8000")
    
    print("\n" + "="*60)
    print("部署完成！")
    print("="*60)
    print(f"访问地址: http://10.1.7.155:8000")
    print(f"API文档: http://10.1.7.155:8000/docs")
    print(f"管理后台: http://10.1.7.155:8000/admin")
    print(f"默认账号: admin / admin123")
    print("="*60)
    
finally:
    ssh.close()
    print("\nDone")