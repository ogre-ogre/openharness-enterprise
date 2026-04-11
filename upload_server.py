import paramiko
import os

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 上传正确的 server.py
    local_file = r"D:\openharness-enterprise\src\openharness\enterprise\server.py"
    remote_file = f"{deploy_path}/openharness/enterprise/server.py"
    
    print(f"\nUploading {local_file}...")
    sftp = ssh.open_sftp()
    sftp.put(local_file, remote_file)
    sftp.close()
    print("Upload complete!")
    
    # 验证语法
    print("\n=== Verifying syntax ===")
    stdin, stdout, stderr = ssh.exec_command(f'''
cd {deploy_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -c "from openharness.enterprise.server import app; print('Import OK')"
''')
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Error: {err[-500:]}")
    
    # 启动服务
    print("\n=== Starting service ===")
    stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
sleep 5
tail -15 ~/.oh-enterprise/logs/server.log
''', timeout=30)
    print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -I http://localhost:8000/assets/index-CVVycQ94.js | head -5")
    print(stdout.read().decode())
    
    print("\n" + "="*50)
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()