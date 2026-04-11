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
    if err: print(f"Err: {err[-500:]}")
    return out

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 检查 index.html 内容
    print("\n=== Checking index.html ===")
    run_cmd(f"cat {deploy_path}/web/index.html")
    
    # 2. 检查 assets 目录
    print("\n=== Checking assets ===")
    run_cmd(f"ls -la {deploy_path}/web/assets/ | head -10")
    
    # 3. 方案：添加 /assets 路由指向 web/assets
    print("\n=== Adding /assets route ===")
    patch_cmd = f'''
cd {deploy_path}
# 检查是否已有 /assets 挂载
grep -q 'app.mount.*assets' openharness/enterprise/server.py && echo 'Has assets mount' || echo 'No assets mount'
'''
    run_cmd(patch_cmd)
    
    # 4. 添加 assets 挂载
    print("\n=== Patching server.py ===")
    add_assets = f'''
cd {deploy_path}
# 在 WEB_DIR 挂载后添加 assets 挂载
cat >> openharness/enterprise/server.py << 'ENDPATCH'

# Mount assets directory for frontend
if _WEB_DIR.exists() and (_WEB_DIR / "assets").exists():
    app.mount("/assets", _StaticFiles(directory=str(_WEB_DIR / "assets")), name="assets")
ENDPATCH
echo "Assets mount added"
'''
    run_cmd(add_assets)
    
    # 5. 重启服务
    print("\n=== Restarting service ===")
    restart_cmd = '''
pkill -f 'uvicorn.*openharness' 2>/dev/null || true
sleep 2
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
sleep 5
tail -10 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(restart_cmd, 30)
    
    # 6. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/assets/index-CVVycQ94.js | head -5")
    run_cmd("curl -s http://localhost:8000/web/ | head -10")
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")