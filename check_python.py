import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    if out: print(out[-2000:] if len(out) > 2000 else out)
    if err: print(f"Err: {err[-500:]}")
    return out

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!\n")
    
    # 1. 检查是否有Anaconda/Miniconda
    print("=== Checking for Anaconda/Miniconda ===")
    run_cmd("find /home /opt -name 'conda' -type f 2>/dev/null | head -5")
    
    # 2. 检查是否有其他Python版本
    print("\n=== Checking for alternative Python ===")
    run_cmd("find /usr /opt -name 'python3*' -type f 2>/dev/null | head -20")
    
    # 3. 检查是否有Docker
    print("\n=== Checking for Docker ===")
    run_cmd("which docker && docker --version")
    
    # 4. 检查openssl库
    print("\n=== Checking OpenSSL libraries ===")
    run_cmd("find /usr -name 'libssl*' 2>/dev/null | head -10")
    run_cmd("ldconfig -p 2>/dev/null | grep ssl")
    
    # 5. 检查Python编译选项
    print("\n=== Python build config ===")
    run_cmd("python3 -c \"import sysconfig; print(sysconfig.get_config_vars())\" 2>/dev/null | grep -i ssl | head -10")
    
    # 6. 尝试从源码目录重新编译SSL模块
    print("\n=== Checking Python source ===")
    run_cmd("ls /home/ai-app/code/Python-3.12.12/ 2>/dev/null | head -20")
    
    print("\n" + "="*60)
    print("需要安装 openssl-devel 并重新编译 Python 的 SSL 模块")
    print("="*60)
    print("请执行以下命令（需要root权限）：")
    print("sudo yum install -y openssl-devel")
    print("cd /home/ai-app/code/Python-3.12.12")
    print("./configure --with-openssl=/usr")
    print("make")
    print("sudo make install")
    print("="*60)
    
finally:
    ssh.close()