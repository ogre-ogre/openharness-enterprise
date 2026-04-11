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
    
    # 1. 修复 WEB_DIR 路径
    # 原来是 4 个 parent，应该是 3 个
    print("\n=== Fixing WEB_DIR path ===")
    fix_cmd = f'''
cd {deploy_path}
# 替换路径计算
sed -i 's|WEB_DIR = Path(__file__).parent.parent.parent.parent / "web"|WEB_DIR = Path(__file__).parent.parent.parent / "web"|g' openharness/enterprise/server.py

# 验证修改
grep -n 'WEB_DIR' openharness/enterprise/server.py | head -5
'''
    run_cmd(fix_cmd)
    
    # 2. 重启服务
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
    
    # 3. 测试前端访问
    print("\n=== Testing frontend ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/web/ | head -10")
    run_cmd("curl -s http://localhost:8000/ | head -10")
    
    # 4. 检查服务
    print("\n=== Final check ===")
    run_cmd("netstat -tlnp 2>/dev/null | grep 8000")
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000")
    print("账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")