import paramiko
import os

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def upload_dir(sftp, local_dir, remote_dir):
    """递归上传目录"""
    try:
        sftp.mkdir(remote_dir)
    except:
        pass
    
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"
        
        if os.path.isfile(local_path):
            print(f"  {item}")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path) and not item.startswith('__pycache__'):
            upload_dir(sftp, local_path, remote_path)

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    sftp = ssh.open_sftp()
    
    # 上传整个 enterprise 目录
    print("\n=== Uploading enterprise modules ===")
    local_enterprise = r"D:\openharness-enterprise\src\openharness\enterprise"
    remote_enterprise = "/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise"
    
    # 只上传目录，不覆盖已有的文件
    for item in os.listdir(local_enterprise):
        local_path = os.path.join(local_enterprise, item)
        remote_path = f"{remote_enterprise}/{item}"
        
        if os.path.isdir(local_path) and not item.startswith('__pycache__'):
            print(f"\n{item}/")
            try:
                sftp.mkdir(remote_path)
            except:
                pass
            
            for f in os.listdir(local_path):
                lf = os.path.join(local_path, f)
                rf = f"{remote_path}/{f}"
                if os.path.isfile(lf):
                    print(f"  {f}")
                    sftp.put(lf, rf)
    
    sftp.close()
    print("\n\nUpload complete!")
    
    # 验证
    print("\n=== Verifying ===")
    stdin, stdout, stderr = ssh.exec_command("ls -la /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/")
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
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()