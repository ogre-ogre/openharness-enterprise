import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=600):
    print(f"\n>>> {cmd[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-4000:] if len(out) > 4000 else out)
    if err: print(f"Err: {err[-1000:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 创建目录
    print("\n=== Creating build directory ===")
    run_cmd("mkdir -p /home/ai-app/openssl-build")
    
    # 2. 尝试使用国内镜像下载
    print("\n=== Downloading OpenSSL 1.1.1w from mirror ===")
    # 使用清华镜像或直接检查是否已下载
    run_cmd("ls /home/ai-app/openssl-build/*.tar.gz 2>/dev/null || echo 'No tarball yet'")
    
    # 尝试从清华镜像下载
    download_cmd = '''
cd /home/ai-app/openssl-build
# 尝试多个镜像
curl -L --connect-timeout 10 -o openssl-1.1.1w.tar.gz "https://mirrors.tuna.tsinghua.edu.cn/openssl/source/openssl-1.1.1w.tar.gz" 2>&1 || \
curl -L --connect-timeout 10 -o openssl-1.1.1w.tar.gz "https://www.openssl.org/source/openssl-1.1.1w.tar.gz" 2>&1 | tail -5 || \
echo "Download failed"
'''
    run_cmd(download_cmd, 300)
    
    # 3. 检查下载结果
    print("\n=== Checking download ===")
    run_cmd("ls -la /home/ai-app/openssl-build/openssl*.tar.gz 2>/dev/null")
    
    # 4. 解压
    print("\n=== Extracting ===")
    run_cmd("cd /home/ai-app/openssl-build && tar xzf openssl-1.1.1w.tar.gz 2>&1")
    run_cmd("ls /home/ai-app/openssl-build/")
    
    # 5. 配置OpenSSL
    print("\n=== Configuring OpenSSL ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && ./config --prefix=/home/ai-app/openssl-1.1.1 --openssldir=/home/ai-app/openssl-1.1.1/ssl shared 2>&1 | tail -20", 120)
    
    # 6. 编译OpenSSL
    print("\n=== Compiling OpenSSL (5-10 minutes) ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && make -j4 2>&1 | tail -20", 900)
    
    # 7. 安装OpenSSL
    print("\n=== Installing OpenSSL ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && make install 2>&1 | tail -20", 120)
    
    # 8. 验证OpenSSL
    print("\n=== Verifying OpenSSL ===")
    run_cmd("ls -la /home/ai-app/openssl-1.1.1/bin/")
    run_cmd("LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib /home/ai-app/openssl-1.1.1/bin/openssl version")
    
    # 9. 重新配置Python
    print("\n=== Reconfiguring Python ===")
    python_cmd = '''
cd /home/ai-app/python-build/Python-3.12.12
make clean 2>/dev/null || true
rm -f config.log config.status Makefile pyconfig.h 2>/dev/null

export PATH="/home/ai-app/openssl-1.1.1/bin:$PATH"
export LD_LIBRARY_PATH="/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH"
export CFLAGS="-I/home/ai-app/openssl-1.1.1/include"
export LDFLAGS="-L/home/ai-app/openssl-1.1.1/lib -Wl,-rpath,/home/ai-app/openssl-1.1.1/lib"

./configure --prefix=/home/ai-app/python3.12-ssl \
    --with-openssl=/home/ai-app/openssl-1.1.1 \
    --with-openssl-rpath=auto \
    --disable-optimizations \
    --disable-profile \
    2>&1 | grep -E "(ssl|SSL|OpenSSL|checking)"
'''
    run_cmd(python_cmd, 120)
    
    # 10. 编译Python
    print("\n=== Compiling Python (5-10 minutes) ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make -j4 2>&1 | tail -30", 900)
    
    # 11. 检查SSL模块
    print("\n=== Checking SSL module ===")
    run_cmd("ls -la /home/ai-app/python-build/Python-3.12.12/build/lib.*/lib-dynload/_ssl*.so 2>/dev/null")
    
    # 12. 安装Python
    print("\n=== Installing Python ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make install 2>&1 | tail -20", 300)
    
    # 13. 验证SSL
    print("\n=== Final verification ===")
    run_cmd("export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && /home/ai-app/python3.12-ssl/bin/python3 -c 'import ssl; print(\"SSL OK:\", ssl.OPENSSL_VERSION)'")
    
finally:
    ssh.close()
    print("\nDone")