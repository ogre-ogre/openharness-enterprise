import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 添加 SPA 路由支持（所有前端路由返回 index.html）
    print("=== Adding SPA routes ===")
    
    # 读取 server.py 末尾
    stdin, stdout, stderr = ssh.exec_command(f"tail -30 {deploy_path}/openharness/enterprise/server.py")
    print(stdout.read().decode())
    
    # 添加 catch-all 路由
    print("\n=== Adding catch-all route ===")
    fix_cmd = f'''
cd {deploy_path}
# 在文件末尾添加 catch-all 路由（用于 SPA）
cat >> openharness/enterprise/server.py << 'ENDCODE'


# ============================================================================
# SPA Routes (catch-all for frontend routing)
# ============================================================================

@app.get("/admin")
@app.get("/admin/{path:path}")
async def admin_spa(path: str = ""):
    """SPA catch-all for admin routes."""
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/chat")
async def chat_spa():
    """SPA catch-all for chat route."""
    return FileResponse(str(WEB_DIR / "index.html"))
ENDCODE
echo "Added SPA routes"
'''
    stdin, stdout, stderr = ssh.exec_command(fix_cmd)
    print(stdout.read().decode())
    
    # 重启服务
    print("\n=== Restarting service ===")
    stdin, stdout, stderr = ssh.exec_command('''
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
''', timeout=30)
    print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/admin | head -5")
    print(f"Admin: {stdout.read().decode()}")
    
    print("\n" + "="*50)
    print("管理后台: http://10.1.7.155:8000/admin")
    print("="*50)
    
finally:
    ssh.close()