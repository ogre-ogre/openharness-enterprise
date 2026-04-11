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
    
    sftp = ssh.open_sftp()
    
    # 创建 channels 目录
    channels_dir = f"{deploy_path}/openharness/enterprise/channels"
    try:
        sftp.mkdir(channels_dir)
    except:
        pass  # 目录可能已存在
    
    # 上传 channels 文件
    local_channels = r"D:\openharness-enterprise\src\openharness\enterprise\channels"
    
    for filename in os.listdir(local_channels):
        local_path = os.path.join(local_channels, filename)
        if os.path.isfile(local_path):
            remote_path = f"{channels_dir}/{filename}"
            print(f"Uploading {filename}...")
            sftp.put(local_path, remote_path)
    
    sftp.close()
    print("\nUpload complete!")
    
    # 验证
    print("\n=== Verifying ===")
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {channels_dir}")
    print(stdout.read().decode())
    
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
tail -15 ~/.oh-enterprise/logs/server.log
''', timeout=30)
    print(stdout.read().decode())
    
    # 测试
    print("\n=== Testing ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
    print(f"Health: {stdout.read().decode()}")
    
    print("\n" + "="*50)
    print("WebSocket 已修复！请刷新页面")
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()