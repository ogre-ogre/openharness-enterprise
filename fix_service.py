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
    if err: print(f"Err: {err[-1500:]}")
    return out, err, stdout.channel.recv_exit_status()

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 检查服务日志
    print("\n=== Checking server log ===")
    run_cmd("tail -50 ~/.oh-enterprise/logs/server.log")
    
    # 2. 检查进程
    print("\n=== Checking processes ===")
    run_cmd("ps aux | grep python | grep -v grep")
    
    # 3. 检查端口
    print("\n=== Checking port ===")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000")
    
    # 4. 修复 server.py（删除重复的导入）
    print("\n=== Fixing server.py ===")
    fix_cmd = f'''
cd {deploy_path}
# 删除最后添加的重复代码
head -n -20 openharness/enterprise/server.py > openharness/enterprise/server_fixed.py
mv openharness/enterprise/server_fixed.py openharness/enterprise/server.py
echo "Fixed server.py"
tail -5 openharness/enterprise/server.py
'''
    run_cmd(fix_cmd)
    
    # 5. 正确添加静态文件挂载
    print("\n=== Adding static files mount ===")
    mount_code = '''

# Static files for frontend
from pathlib import Path
WEB_DIR = Path(__file__).parent.parent.parent / "web"

if WEB_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    
    @app.get("/")
    async def root():
        return FileResponse(str(WEB_DIR / "index.html"))
'''
    
    # 检查是否已有挂载
    check_cmd = f'''grep -q 'app.mount.*web' {deploy_path}/openharness/enterprise/server.py && echo 'Has mount' || echo 'No mount' '''
    stdin, stdout, stderr = ssh.exec_command(check_cmd)
    result = stdout.read().decode().strip()
    print(f"Mount status: {result}")
    
    if "No mount" in result:
        print("Adding static files mount...")
        # 在 main() 函数之前添加
        add_cmd = f'''
cd {deploy_path}
# 找到 main 函数位置并在之前插入
grep -n "def main():" openharness/enterprise/server.py
'''
        run_cmd(add_cmd)
        
        # 直接写入正确的代码
        write_cmd = f'''
cd {deploy_path}
cat >> openharness/enterprise/server.py << 'ENDCODE'


# ============================================================================
# Static Files for Frontend
# ============================================================================
from pathlib import Path as _Path
_WEB_DIR = _Path(__file__).parent.parent.parent / "web"

if _WEB_DIR.exists() and (_WEB_DIR / "index.html").exists():
    from fastapi.staticfiles import StaticFiles as _StaticFiles
    from fastapi.responses import FileResponse as _FileResponse
    
    app.mount("/web", _StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
    
    @app.get("/")
    async def _root():
        return _FileResponse(str(_WEB_DIR / "index.html"))
ENDCODE
echo "Static mount added"
'''
        run_cmd(write_cmd)
    
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
sleep 5
tail -20 ~/.oh-enterprise/logs/server.log
'''
    run_cmd(restart_cmd, 60)
    
    # 7. 测试
    print("\n=== Final testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/ | head -10")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000")
    
finally:
    ssh.close()
    print("\nDone")