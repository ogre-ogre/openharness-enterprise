import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查 WebSocket 路由是否正确
    print("=== WebSocket route ===")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'ws/chat\\|@app.websocket' /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py | head -10")
    print(stdout.read().decode())
    
    # 2. 检查服务器日志
    print("\n=== Server log (last 50 lines) ===")
    stdin, stdout, stderr = ssh.exec_command("tail -50 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 3. 检查 channels 目录是否存在
    print("\n=== Checking channels ===")
    stdin, stdout, stderr = ssh.exec_command("ls -la /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/")
    print(stdout.read().decode())
    
    # 4. 检查 websockets 库
    print("\n=== Checking websockets ===")
    stdin, stdout, stderr = ssh.exec_command("source /home/ai-app/oh-enterprise-1.0.0/venv/bin/activate && pip show websockets")
    print(stdout.read().decode())
    
finally:
    ssh.close()