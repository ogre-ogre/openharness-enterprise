import paramiko
import os
import time

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

# 连接SSH和SFTP
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password)
sftp = ssh.open_sftp()

def run_cmd(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-2000:] if len(out) > 2000 else out)
    if err: print(f"Err: {err[-500:]}")
    return out, err, exit_code

def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} -> {remote_path}")
    sftp.put(local_path, remote_path)
    print("Done")

try:
    print("Connected!\n")
    
    # 1. 检查服务器是否有现成的wheel文件
    print("=== Checking for existing wheels ===")
    run_cmd("find /home -name '*.whl' 2>/dev/null | head -20")
    
    # 2. 检查/opt或其他位置是否有缓存的包
    print("\n=== Checking for package cache ===")
    run_cmd("find /opt -name 'site-packages' -type d 2>/dev/null")
    
    # 3. 检查是否有conda-forge或其他包管理器
    print("\n=== Checking for alternative package managers ===")
    run_cmd("which conda mamba pipx 2>/dev/null")
    run_cmd("ls /opt/ 2>/dev/null")
    
    # 4. 创建packages目录
    print("\n=== Creating packages directory ===")
    run_cmd(f"mkdir -p {deploy_path}/packages")
    
    # 5. 尝试使用本地文件安装
    print("\n=== Preparing offline installation ===")
    print("需要上传whl文件到服务器。请确认服务器是否有网络访问内网PyPI镜像？")
    
    # 6. 检查网络连接
    print("\n=== Checking network ===")
    run_cmd("curl -I http://mirrors.aliyun.com/pypi/simple/ 2>&1 | head -5")
    
    print("\n" + "="*50)
    print("服务器状态检查完成")
    print("="*50)
    print("问题: Python缺少SSL模块，无法使用HTTPS")
    print("解决方案:")
    print("1. 联系管理员安装 openssl-devel 并重新编译Python")
    print("2. 或使用离线安装包")
    print("="*50)
    
finally:
    sftp.close()
    ssh.close()
    print("\nConnection closed")