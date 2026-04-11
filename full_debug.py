import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 查看完整日志
    print("=== Full log ===")
    stdin, stdout, stderr = ssh.exec_command("cat ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 检查进程
    print("\n=== Current processes ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'python|uvicorn' | grep -v grep | head -10")
    print(stdout.read().decode())
    
    # 检查端口
    print("\n=== Port 8000 ===")
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep 8000")
    print(stdout.read().decode())
    
    # 测试连接
    print("\n=== Testing connection ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>&1")
    print(stdout.read().decode())
    
finally:
    ssh.close()