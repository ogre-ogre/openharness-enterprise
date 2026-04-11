import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out: print(out[-2000:] if len(out) > 2000 else out)
    if err: print(f"Err: {err[-500:]}")
    return out

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # Find correct python path
    print("=== Finding correct Python path ===")
    run_cmd("which python3")
    run_cmd("python3 --version")
    run_cmd("python3 -c 'import sys; print(sys.executable)'")
    
    # Test pip with HTTP (豆瓣镜像支持HTTP)
    print("\n=== Installing with HTTP mirror ===")
    install_cmd = '''
cd /home/ai-app/oh-enterprise-1.0.0
source venv/bin/activate
pip install --index-url http://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com fastapi uvicorn pydantic python-multipart aiofiles aiosqlite python-jose passlib anthropic openai python-dotenv pyyaml httpx
'''
    run_cmd(install_cmd, timeout=300)
    
finally:
    ssh.close()