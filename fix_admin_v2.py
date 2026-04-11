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
    
    # 直接用 Python 写入
    print("=== Adding SPA routes ===")
    
    spa_code = '''

# ============================================================================
# SPA Routes (catch-all for frontend routing)
# ============================================================================

@app.get("/admin")
async def admin_spa():
    """SPA route for admin."""
    return FileResponse(str(WEB_DIR / "index.html"))

@app.get("/chat")
async def chat_spa():
    """SPA route for chat."""
    return FileResponse(str(WEB_DIR / "index.html"))
'''
    
    # 用 Python 脚本添加
    python_script = f'''
import sys
with open("{deploy_path}/openharness/enterprise/server.py", "r") as f:
    content = f.read()

# 在 if __name__ 之前插入
if "SPA Routes" not in content:
    main_idx = content.find('if __name__ == "__main__":')
    if main_idx > 0:
        new_content = content[:main_idx] + """{spa_code}""" + "\\n" + content[main_idx:]
        with open("{deploy_path}/openharness/enterprise/server.py", "w") as f:
            f.write(new_content)
        print("Added SPA routes")
    else:
        print("Could not find main block")
else:
    print("Already has SPA routes")
'''
    
    stdin, stdout, stderr = ssh.exec_command(f'cd {deploy_path} && source venv/bin/activate && python3 -c \'{python_script}\'')
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Err: {err}")
    
    # 验证
    print("\n=== Verifying ===")
    stdin, stdout, stderr = ssh.exec_command(f"grep -n 'SPA Routes' {deploy_path}/openharness/enterprise/server.py")
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