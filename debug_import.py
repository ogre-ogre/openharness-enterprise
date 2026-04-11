import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查日志
    print("=== Full server log ===")
    stdin, stdout, stderr = ssh.exec_command("cat ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 测试导入
    print("\n=== Testing import ===")
    stdin, stdout, stderr = ssh.exec_command('''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -c "from openharness.enterprise.server import app; print('OK')" 2>&1
''')
    print(stdout.read().decode())
    
finally:
    ssh.close()