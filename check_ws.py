import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查 WebSocket 路由
    print("=== Checking WebSocket routes ===")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'websocket\\|WebSocket\\|/ws' /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py | head -20")
    print(stdout.read().decode())
    
    # 2. 检查服务器日志
    print("\n=== Server log (last 30 lines) ===")
    stdin, stdout, stderr = ssh.exec_command("tail -30 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 3. 测试 WebSocket 端点
    print("\n=== Testing WebSocket endpoint ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s -i -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Key: test' -H 'Sec-WebSocket-Version: 13' 'http://localhost:8000/ws/chat?token=test' 2>&1 | head -20")
    print(stdout.read().decode())
    
    # 4. 检查端口
    print("\n=== Checking ports ===")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 8000")
    print(stdout.read().decode())
    
finally:
    ssh.close()