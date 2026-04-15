import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

# 上传修改后的文件
files_to_upload = [
    ('src/openharness/enterprise/channels/webchat.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/webchat.py'),
    ('src/openharness/enterprise/tools/registry.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/tools/registry.py'),
]

for local, remote in files_to_upload:
    local_path = os.path.join('D:/openharness-enterprise', local)
    
    # 读取本地文件
    with open(local_path, 'rb') as f:
        content = f.read()
    
    # 通过SSH写入远程文件
    cmd = f'''
/home/ai-app/oh-enterprise-1.0.0/venv/bin/python3 << 'PYEOF'
import os
os.makedirs(os.path.dirname("{remote}"), exist_ok=True)
with open("{remote}", "wb") as f:
    f.write({len(content)})
PYEOF
'''
    
    # 使用SFTP传输
    sftp = ssh.open_sftp()
    
    # 确保目录存在
    remote_dir = os.path.dirname(remote)
    try:
        sftp.stat(remote_dir)
    except:
        # 创建目录
        ssh.exec_command(f'mkdir -p {remote_dir}', timeout=10)
    
    # 上传文件
    sftp.put(local_path, remote)
    print(f'Uploaded: {local} -> {remote}')
    
    sftp.close()

print('\n[OK] Files uploaded')

# 重启服务
stdin, stdout, stderr = ssh.exec_command('/usr/sbin/lsof -i:8000', timeout=10)
lsof = stdout.read().decode()
print('\n=== Current service ===')
print(lsof[:500])

# 终止进程
for line in lsof.split('\n'):
    if 'python' in line:
        parts = line.split()
        if len(parts) > 1:
            pid = parts[1]
            ssh.exec_command(f'/bin/kill -9 {pid}', timeout=5)
            print(f'Killed PID: {pid}')

import time
time.sleep(3)

# 启动服务
start_cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0 && \
source venv/bin/activate && \
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && \
nohup python -m openharness.enterprise.server --host 0.0.0.0 --port 8000 > /home/ai-app/.oh-enterprise/logs/server.log 2>&1 &
'''
stdin, stdout, stderr = ssh.exec_command(start_cmd, timeout=10)
print('\n[OK] Service restarted')

ssh.close()