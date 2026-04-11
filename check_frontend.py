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
    
    # 1. 检查前端文件是否存在
    print("\n=== Checking frontend files ===")
    run_cmd(f"ls -la {deploy_path}/web/")
    run_cmd(f"ls -la {deploy_path}/web/index.html 2>/dev/null || echo 'No index.html'")
    
    # 2. 检查API是否正常
    print("\n=== Testing API endpoints ===")
    run_cmd("curl -s http://localhost:8000/health")
    run_cmd("curl -s http://localhost:8000/api/auth/login -X POST -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'")
    
    # 3. 检查根路由配置
    print("\n=== Checking server routes ===")
    run_cmd(f"grep -n 'StaticFiles\\|@app.get.*\\/' {deploy_path}/openharness/enterprise/server.py | head -20")
    
    # 4. 如果前端文件存在，测试访问
    print("\n=== Testing frontend access ===")
    run_cmd("curl -s http://localhost:8000/web/ | head -20")
    run_cmd("curl -s http://localhost:8000/admin/ | head -10")
    
finally:
    ssh.close()
    print("\nDone")