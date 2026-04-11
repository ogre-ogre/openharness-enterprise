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
    
    # 1. 解压OpenSSL
    print("\n=== Extracting OpenSSL ===")
    run_cmd("cd /home/ai-app/openssl-build && tar xzf openssl-1.1.1w.tar.gz")
    run_cmd("ls /home/ai-app/openssl-build/")
    
    # 2. 配置OpenSSL
    print("\n=== Configuring OpenSSL ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && ./config --prefix=/home/ai-app/openssl-1.1.1 --openssldir=/home/ai-app/openssl-1.1.1/ssl shared 2>&1 | tail -20", 120)
    
    # 3. 编译OpenSSL
    print("\n=== Compiling OpenSSL (5-10 min) ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && make -j4 2>&1 | tail -10", 900)
    
    # 4. 安装OpenSSL
    print("\n=== Installing OpenSSL ===")
    run_cmd("cd /home/ai-app/openssl-build/openssl-1.1.1w && make install 2>&1 | tail -10", 120)
    
    # 5. 验证OpenSSL
    print("\n=== Verifying OpenSSL ===")
    run_cmd("LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib /home/ai-app/openssl-1.1.1/bin/openssl version")
    
    # 6. 配置Python
    print("\n=== Configuring Python ===")
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
    2>&1 | grep -E "(ssl|SSL|OpenSSL)"
'''
    run_cmd(python_cmd, 120)
    
    # 7. 编译Python
    print("\n=== Compiling Python (5-10 min) ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make -j4 2>&1 | tail -20", 900)
    
    # 8. 检查SSL模块
    print("\n=== Checking SSL module ===")
    run_cmd("ls -la /home/ai-app/python-build/Python-3.12.12/build/lib.*/lib-dynload/_ssl*.so 2>/dev/null")
    
    # 9. 安装Python
    print("\n=== Installing Python ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make install 2>&1 | tail -10", 300)
    
    # 10. 验证SSL
    print("\n=== Final verification ===")
    run_cmd("export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH && /home/ai-app/python3.12-ssl/bin/python3 -c 'import ssl; print(\"SSL OK:\", ssl.OPENSSL_VERSION)'")
    
finally:
    ssh.close()
    print("\nDone")