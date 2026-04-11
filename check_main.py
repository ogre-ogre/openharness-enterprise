import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 检查 main 函数
    print("=== Checking main function ===")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
grep -A 50 "def main():" openharness/enterprise/server.py | head -60
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 检查启动命令格式
    print("\n=== Testing different commands ===")
    
    # 尝试不带子命令
    print("Test 1: Without subcommand")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
python -m openharness.enterprise.server --help 2>&1 | head -20
'''
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    
    # 尝试直接运行 uvicorn
    print("\nTest 2: Direct uvicorn")
    cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
timeout 10 uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 2>&1 || true
'''
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    print(stdout.read().decode())
    
    # 检查是否运行
    print("\n=== Check if running ===")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health 2>/dev/null || echo 'Not running'")
    print(stdout.read().decode())
    
finally:
    ssh.close()