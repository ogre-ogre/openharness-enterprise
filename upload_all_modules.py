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
    
    # 检查缺失的目录
    print("\n=== Checking directories ===")
    dirs_to_check = ["channels", "users", "auth", "llm", "tools", "storage"]
    
    for d in dirs_to_check:
        remote_dir = f"{deploy_path}/openharness/enterprise/{d}"
        try:
            sftp.stat(remote_dir)
            print(f"[OK] {d}/")
        except FileNotFoundError:
            print(f"[MISSING] {d}/")
            
            # 创建目录并上传文件
            local_dir = f"D:\\openharness-enterprise\\src\\openharness\\enterprise\\{d}"
            if os.path.exists(local_dir):
                try:
                    sftp.mkdir(remote_dir)
                except:
                    pass
                
                for f in os.listdir(local_dir):
                    local_file = os.path.join(local_dir, f)
                    if os.path.isfile(local_file):
                        remote_file = f"{remote_dir}/{f}"
                        print(f"  Uploading {f}...")
                        sftp.put(local_file, remote_file)
                
                print(f"  [UPLOADED] {d}/")
    
    sftp.close()
    
    # 验证
    print("\n=== Verifying all directories ===")
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {deploy_path}/openharness/enterprise/")
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
    print("所有模块已上传！请刷新页面")
    print("访问: http://10.1.7.155:8000/web/")
    print("="*50)
    
finally:
    ssh.close()