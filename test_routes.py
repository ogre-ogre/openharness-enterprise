import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 测试所有路由
    tests = [
        ("Health", "curl -s http://localhost:8000/health"),
        ("Root /", "curl -s http://localhost:8000/ | head -5"),
        ("Web /web/", "curl -s http://localhost:8000/web/ | head -5"),
        ("Admin /admin", "curl -s http://localhost:8000/admin | head -5"),
        ("Chat /chat", "curl -s http://localhost:8000/chat | head -5"),
    ]
    
    for name, cmd in tests:
        print(f"\n=== {name} ===")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode()[:300])
    
    # 检查 WEB_DIR 和路由
    print("\n\n=== Checking WEB_DIR in server.py ===")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'WEB_DIR\\|@app.get.*admin\\|@app.get.*chat' /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py | tail -20")
    print(stdout.read().decode())
    
    # 检查 web 目录
    print("\n=== Checking web directory ===")
    stdin, stdout, stderr = ssh.exec_command("ls -la /home/ai-app/oh-enterprise-1.0.0/web/ | head -10")
    print(stdout.read().decode())
    
finally:
    ssh.close()