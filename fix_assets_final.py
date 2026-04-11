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
    
    # 1. 查看日志
    print("=== Server log ===")
    stdin, stdout, stderr = ssh.exec_command("tail -50 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 2. 检查 Python 语法
    print("\n=== Checking Python syntax ===")
    cmd = f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -m py_compile openharness/enterprise/server.py 2>&1 || echo "Syntax error"
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 3. 查看当前静态文件挂载代码
    print("\n=== Current code ===")
    stdin, stdout, stderr = ssh.exec_command(f"tail -20 {deploy_path}/openharness/enterprise/server.py")
    print(stdout.read().decode())
    
    # 4. 直接重写静态文件挂载部分
    print("\n=== Rewriting static mount ===")
    fix_cmd = f'''
cd {deploy_path}
# 找到 Static Files 注释的位置，然后替换整个部分
LINE_START=$(grep -n '# Static Files (Frontend)' openharness/enterprise/server.py | head -1 | cut -d: -f1)
echo "Start line: $LINE_START"

# 删除从该行到文件末尾的内容
if [ -n "$LINE_START" ]; then
    head -n $((LINE_START - 1)) openharness/enterprise/server.py > openharness/enterprise/server_temp.py
    
    # 添加正确的静态文件挂载代码
    cat >> openharness/enterprise/server_temp.py << 'ENDCODE'

# ============================================================================
# Static Files (Frontend)
# ============================================================================

# Get web directory path
WEB_DIR = Path(__file__).parent.parent.parent / "web"

# Mount static files if web directory exists
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    
    # Mount assets for frontend (CSS, JS)
    if (WEB_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")
    
    @app.get("/")
    async def root():
        from fastapi.responses import FileResponse
        return FileResponse(str(WEB_DIR / "index.html"))
ENDCODE

    mv openharness/enterprise/server_temp.py openharness/enterprise/server.py
    echo "Done"
fi

# 验证
tail -20 openharness/enterprise/server.py
'''
    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=30)
    print(stdout.read().decode())
    
    # 5. 测试语法
    print("\n=== Testing syntax ===")
    stdin, stdout, stderr = ssh.exec_command(f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -c "from openharness.enterprise.server import app; print('Import OK')"
''')
    print(stdout.read().decode())
    
    # 6. 启动服务
    print("\n=== Starting service ===")
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
tail -15 ~/.oh-enterprise/logs/server.log
''', timeout=30)
    print(stdout.read().decode())
    
    # 7. 测试
    print("\n=== Final testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health && echo '' && curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -3")
    print(stdout.read().decode())
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()