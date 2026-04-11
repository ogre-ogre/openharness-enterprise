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
    
    # 1. 安装 bcrypt
    print("\n=== Installing bcrypt ===")
    install_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple bcrypt
'''
    run_cmd(install_cmd, 120)
    
    # 2. 修复静态文件路径
    print("\n=== Fixing static files path ===")
    fix_cmd = f'''
cd {deploy_path}
# 修改 server.py 中的静态文件路径
# 从 web/dist 改为 web
sed -i 's|WEB_DIR / "dist"|WEB_DIR|g' openharness/enterprise/server.py
# 验证修改
grep -n 'WEB_DIR' openharness/enterprise/server.py | head -10
'''
    run_cmd(fix_cmd)
    
    # 3. 确认前端文件结构
    print("\n=== Verifying frontend ===")
    run_cmd(f"ls -la {deploy_path}/web/")
    run_cmd(f"cat {deploy_path}/web/index.html")
    
    # 4. 重启服务
    print("\n=== Restarting service ===")
    restart_cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup python -m openharness.enterprise.server start --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
sleep 5
tail -30 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(restart_cmd, 60)
    
    # 5. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/ | head -20")
    run_cmd("curl -s http://localhost:8000/web/index.html | head -10")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000")
    
    print("\n" + "="*50)
    print("访问地址: http://10.1.7.155:8000")
    print("API文档: http://10.1.7.155:8000/docs")
    print("账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")