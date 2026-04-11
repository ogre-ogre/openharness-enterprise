import paramiko
import time

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 检查pip进程
    print("\n=== Checking pip process ===")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep pip | grep -v grep")
    print(stdout.read().decode())
    
    # 等待pip完成
    print("Waiting for pip to finish...")
    for i in range(60):
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'pip install' | grep -v grep | wc -l")
        count = int(stdout.read().decode().strip())
        if count == 0:
            print(f"\nPip finished after {i} seconds")
            break
        print(f".", end="", flush=True)
        time.sleep(5)
    else:
        print("\nTimeout waiting for pip")
    
    # 检查安装结果
    print("\n=== Checking installed packages ===")
    stdin, stdout, stderr = ssh.exec_command("source /home/ai-app/oh-enterprise-1.0.0/venv/bin/activate && pip list | grep -E 'fastapi|uvicorn|pydantic'")
    print(stdout.read().decode())
    
finally:
    ssh.close()
    print("\nDone")