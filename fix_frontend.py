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
    
    # 1. 检查前端目录结构
    print("\n=== Checking frontend structure ===")
    run_cmd(f"ls -la {deploy_path}/web/")
    run_cmd(f"ls -la {deploy_path}/web/assets/ 2>/dev/null | head -10")
    
    # 2. 创建 dist 目录并移动文件（如果需要）
    print("\n=== Fixing frontend directory ===")
    fix_cmd = f'''
cd {deploy_path}/web
# 如果 index.html 在当前目录，创建 dist 并移动
if [ -f index.html ] && [ ! -d dist ]; then
    mkdir -p dist
    cp -r * dist/ 2>/dev/null || true
    echo "Created dist directory"
fi
ls -la dist/ 2>/dev/null || echo "No dist directory"
'''
    run_cmd(fix_cmd)
    
    # 3. 添加根路由重定向
    print("\n=== Adding root route ===")
    patch_cmd = f'''
cd {deploy_path}
# 检查是否已有根路由
grep -n '@app.get("/' openharness/enterprise/server.py | grep -v api | head -5
'''
    run_cmd(patch_cmd)
    
    # 4. 创建一个简单的根路由补丁
    print("\n=== Creating root route patch ===")
    root_route = '''

# ============================================================================
# Root Route - Redirect to Frontend
# ============================================================================

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    """Redirect to web frontend."""
    return RedirectResponse(url="/web/index.html")

'''
    
    # 5. 检查是否需要添加
    check_cmd = f'''grep -q 'RedirectResponse' {deploy_path}/openharness/enterprise/server.py && echo 'Already has redirect' || echo 'Need to add' '''
    stdin, stdout, stderr = ssh.exec_command(check_cmd)
    result = stdout.read().decode().strip()
    print(f"Status: {result}")
    
    if "Need to add" in result:
        print("Adding root route...")
        add_cmd = f'''
cd {deploy_path}
# 在文件末尾添加根路由
cat >> openharness/enterprise/server.py << 'ENDPATCH'


# ============================================================================
# Root Route - Redirect to Frontend  
# ============================================================================

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    """Redirect to web frontend."""
    return RedirectResponse(url="/web/")

ENDPATCH
echo "Root route added"
'''
        run_cmd(add_cmd)
    
    # 6. 重启服务
    print("\n=== Restarting service ===")
    restart_cmd = f'''
pkill -f 'openharness.enterprise.server' 2>/dev/null || true
sleep 2
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup python -m openharness.enterprise.server start --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
sleep 5
echo "=== Server log ==="
tail -20 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(restart_cmd, 60)
    
    # 7. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/ | head -10")
    run_cmd("curl -s http://localhost:8000/health")
    
finally:
    ssh.close()
    print("\nDone")