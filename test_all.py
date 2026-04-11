import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 测试所有关键路径
    print("=== Testing all paths ===")
    
    tests = [
        ("Health", "curl -s http://localhost:8000/health"),
        ("Web root", "curl -s http://localhost:8000/web/ | head -20"),
        ("Assets JS", "curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -5"),
        ("Assets CSS", "curl -s -I http://localhost:8000/assets/index-Jmzh3u7K.css | head -5"),
        ("Login API", "curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"),
    ]
    
    for name, cmd in tests:
        print(f"\n--- {name} ---")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode()[:500])
    
    # 2. 检查前端文件
    print("\n\n=== Frontend files ===")
    stdin, stdout, stderr = ssh.exec_command("ls -la /home/ai-app/oh-enterprise-1.0.0/web/assets/ | head -10")
    print(stdout.read().decode())
    
    # 3. 检查 index.html 内容
    print("\n=== index.html ===")
    stdin, stdout, stderr = ssh.exec_command("cat /home/ai-app/oh-enterprise-1.0.0/web/index.html")
    print(stdout.read().decode())
    
finally:
    ssh.close()