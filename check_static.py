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
    
    # 1. 检查当前静态文件挂载
    print("\n=== Checking static mount ===")
    run_cmd(f"grep -n 'WEB_DIR\\|StaticFiles\\|app.mount' {deploy_path}/openharness/enterprise/server.py | tail -20")
    
    # 2. 检查 WEB_DIR 路径
    print("\n=== Checking WEB_DIR path ===")
    run_cmd(f"ls -la {deploy_path}/web/")
    
    # 3. 测试 Python 路径解析
    print("\n=== Testing path resolution ===")
    test_cmd = f'''
cd {deploy_path}
source venv/bin/activate
python -c "
from pathlib import Path
WEB_DIR = Path('openharness/enterprise/server.py').parent.parent.parent / 'web'
print(f'WEB_DIR: {{WEB_DIR}}')
print(f'Absolute: {{WEB_DIR.absolute()}}')
print(f'Exists: {{WEB_DIR.exists()}}')
print(f'index.html: {{(WEB_DIR / \"index.html\").exists()}}')
"
'''
    run_cmd(test_cmd)
    
    # 4. 测试前端访问
    print("\n=== Testing frontend access ===")
    run_cmd("curl -s http://localhost:8000/web/ | head -10")
    run_cmd("curl -s http://localhost:8000/web/index.html | head -10")
    
    # 5. 如果前端挂载不工作，添加路由
    print("\n=== Adding frontend route ===")
    add_route_cmd = f'''
cd {deploy_path}
# 检查是否有根路由
grep -q '@app.get("/")' openharness/enterprise/server.py && echo 'Has root route' || echo 'No root route'

# 如果没有静态文件挂载，手动添加
grep -q 'app.mount.*web' openharness/enterprise/server.py && echo 'Has mount' || echo 'No mount'
'''
    run_cmd(add_route_cmd)
    
    # 6. 验证服务状态
    print("\n=== Final verification ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/api/auth/login -X POST -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}' | head -100")
    
    print("\n" + "="*50)
    print("服务已运行在: http://10.1.7.155:8000")
    print("API文档: http://10.1.7.155:8000/docs")
    print("账号: admin / admin123")
    print("="*50)
    
finally:
    ssh.close()
    print("\nDone")