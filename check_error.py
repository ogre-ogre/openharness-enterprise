import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查完整日志
    print("=== Full server log ===")
    stdin, stdout, stderr = ssh.exec_command("cat ~/.oh-enterprise/logs/server.log")
    print(stdout.read().decode())
    
    # 2. 手动启动测试
    print("\n=== Manual start test ===")
    test_cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
python -c "from openharness.enterprise.server import app; print('Import OK')" 2>&1
'''
    stdin, stdout, stderr = ssh.exec_command(test_cmd, timeout=60)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"Error: {err}")
    
finally:
    ssh.close()