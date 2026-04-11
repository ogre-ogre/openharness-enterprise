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
    if err: print(f"Err: {err[-1500:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 创建新的编译目录
    print("\n=== Setting up build directory ===")
    run_cmd("mkdir -p /home/ai-app/python-build")
    run_cmd("cd /home/ai-app/python-build && rm -rf *")
    
    # 2. 下载Python源码（如果目录中有tar包就直接用）
    print("\n=== Preparing Python source ===")
    run_cmd("ls /home/ai-app/code/Python-3.12.12.tgz 2>/dev/null || ls /home/ai-app/*.tgz 2>/dev/null | head -5")
    
    # 3. 复制源码到用户目录
    print("\n=== Copying source ===")
    run_cmd("cp -r /home/ai-app/code/Python-3.12.12 /home/ai-app/python-build/Python-3.12.12")
    run_cmd("chown -R ai-app:ai-app /home/ai-app/python-build/Python-3.12.12 2>/dev/null || true")
    
    # 4. 配置编译选项
    print("\n=== Configuring Python ===")
    config_cmd = '''
cd /home/ai-app/python-build/Python-3.12.12
make clean 2>/dev/null || true
rm -f config.log config.status Makefile pyconfig.h 2>/dev/null

# 设置OpenSSL 1.1.1路径
export OPENSSL_ROOT=/usr
export CFLAGS="-I/usr/include"
export LDFLAGS="-L/usr/lib64 -Wl,-rpath,/usr/lib64"
export LD_LIBRARY_PATH="/usr/lib64:$LD_LIBRARY_PATH"

# 配置，禁用profile优化加速编译
./configure --prefix=/home/ai-app/python3.12-ssl \
    --with-openssl=/usr \
    --with-openssl-rpath=auto \
    --disable-optimizations \
    --disable-profile \
    2>&1 | grep -i ssl
'''
    run_cmd(config_cmd, 120)
    
    # 5. 检查SSL配置
    print("\n=== Checking SSL config ===")
    run_cmd("grep -i 'ssl' /home/ai-app/python-build/Python-3.12.12/Makefile 2>/dev/null | head -5")
    
    # 6. 编译
    print("\n=== Compiling (this may take a few minutes) ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make -j4 2>&1 | tail -50", 600)
    
    # 7. 检查编译结果
    print("\n=== Checking build result ===")
    run_cmd("ls -la /home/ai-app/python-build/Python-3.12.12/build/lib.*/lib-dynload/_ssl*.so 2>/dev/null")
    
    # 8. 安装
    print("\n=== Installing ===")
    run_cmd("cd /home/ai-app/python-build/Python-3.12.12 && make install 2>&1 | tail -30", 300)
    
    # 9. 验证
    print("\n=== Verifying SSL module ===")
    run_cmd("/home/ai-app/python3.12-ssl/bin/python3 -c 'import ssl; print(\"SSL OK:\", ssl.OPENSSL_VERSION)'")
    
finally:
    ssh.close()
    print("\nDone")