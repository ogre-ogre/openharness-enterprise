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
    return out

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 安装 websockets
    print("\n=== Installing websockets ===")
    run_cmd(f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple websockets
''')
    
    # 2. 修复 SQLite TRUE 问题
    print("\n=== Fixing SQLite TRUE issue ===")
    run_cmd(f'''
cd {deploy_path}
# 替换 TRUE 为 1, FALSE 为 0
sed -i 's/= TRUE/= 1/g' openharness/enterprise/storage/database.py
sed -i 's/= FALSE/= 0/g' openharness/enterprise/storage/database.py
sed -i 's/ DEFAULT TRUE/ DEFAULT 1/g' openharness/enterprise/storage/database.py
sed -i 's/ DEFAULT FALSE/ DEFAULT 0/g' openharness/enterprise/storage/database.py
echo "Fixed SQLite syntax"
grep -n 'TRUE\\|FALSE' openharness/enterprise/storage/database.py | head -10
''')
    
    # 3. 重启服务
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
    
    # 4. 测试
    print("\n=== Testing ===")
    run_cmd("curl -s http://localhost:8000/health")
    
    print("\n" + "="*50)
    print("修复完成！请刷新页面重试")
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")