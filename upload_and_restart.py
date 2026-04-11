import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 上传 server.py
    local_file = r"D:\openharness-enterprise\src\openharness\enterprise\server.py"
    remote_file = f"{deploy_path}/openharness/enterprise/server.py"
    
    print(f"\nUploading server.py...")
    sftp = ssh.open_sftp()
    sftp.put(local_file, remote_file)
    sftp.close()
    print("Upload complete!")
    
    # 重启服务
    print("\n=== Restarting service ===")
    stdin, stdout, stderr = ssh.exec_command('''
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
''', timeout=30)
    print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/admin | head -5")
    print(f"Admin: {stdout.read().decode()}")
    
    print("\n" + "="*50)
    print("管理后台: http://10.1.7.155:8000/admin")
    print("="*50)
    
finally:
    ssh.close()