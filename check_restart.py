import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查日志
    print("=== Server log ===")
    stdin, stdout, stderr = ssh.exec_command("tail -50 ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 2. 测试 Python 导入
    print("\n=== Testing import ===")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -c "from openharness.enterprise.server import app; print('Import OK')" 2>&1
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 3. 测试路径
    print("\n=== Testing WEB_DIR ===")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
python -c "
from pathlib import Path
WEB_DIR = Path('/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/server.py').parent.parent.parent / 'web'
print(f'WEB_DIR: {WEB_DIR}')
print(f'Exists: {WEB_DIR.exists()}')
print(f'Files: {list(WEB_DIR.iterdir()) if WEB_DIR.exists() else []}')
"
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 4. 手动启动服务
    print("\n=== Starting service ===")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $!
sleep 5
curl -s http://localhost:8000/health
curl -s http://localhost:8000/web/ | head -5
'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(stdout.read().decode())
    
finally:
    ssh.close()