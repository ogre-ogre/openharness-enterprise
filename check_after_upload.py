import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查 channels 目录
    print("=== Checking channels ===")
    stdin, stdout, stderr = ssh.exec_command("ls -la /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/ 2>&1")
    print(stdout.read().decode())
    
    # 检查服务器日志
    print("\n=== Server log ===")
    stdin, stdout, stderr = ssh.exec_command("tail -30 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 检查进程
    print("\n=== Processes ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep uvicorn | grep -v grep")
    print(stdout.read().decode())
    
    # 测试健康
    print("\n=== Health ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(stdout.read().decode())
    
finally:
    ssh.close()