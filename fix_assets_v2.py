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
    
    # 1. 查看当前的静态文件挂载代码
    print("\n=== Current static mount code ===")
    run_cmd(f"grep -n -A5 'WEB_DIR = ' {deploy_path}/openharness/enterprise/server.py")
    
    # 2. 删除末尾添加的错误代码
    print("\n=== Removing incorrect code ===")
    run_cmd(f'''
cd {deploy_path}
# 删除文件末尾的错误代码（从最后一个空行开始）
head -n -10 openharness/enterprise/server.py > openharness/enterprise/server_fixed.py
mv openharness/enterprise/server_fixed.py openharness/enterprise/server.py
echo "Removed last 10 lines"
tail -5 openharness/enterprise/server.py
''')
    
    # 3. 在正确的位置添加 assets 挂载
    print("\n=== Adding assets mount correctly ===")
    run_cmd(f'''
cd {deploy_path}
# 在 app.mount("/web" 后面添加 assets 挂载
# 找到那一行的行号
LINE_NUM=$(grep -n 'app.mount.*web.*StaticFiles' openharness/enterprise/server.py | cut -d: -f1)
echo "Line number: $LINE_NUM"

# 在该行后插入 assets 挂载
sed -i "${{LINE_NUM}}a\\
if (WEB_DIR / \\"assets\\").exists():\\
    app.mount(\\"/assets\\", StaticFiles(directory=str(WEB_DIR / \\"assets\\")), name=\\"assets\\")
" openharness/enterprise/server.py

echo "Done"
grep -n -A3 'app.mount.*web' openharness/enterprise/server.py | head -10
''')
    
    # 4. 重启服务
    print("\n=== Restarting service ===")
    run_cmd('''
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
''', 30)
    
    # 5. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -5")
    run_cmd("curl -s http://localhost:8000/web/ | head -10")
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")