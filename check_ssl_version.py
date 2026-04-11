import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:100]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-3000:] if len(out) > 3000 else out)
    if err: print(f"Err: {err[-1000:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 检查OpenSSL版本
    print("\n=== Checking OpenSSL versions ===")
    run_cmd("ls -la /usr/lib64/libssl*")
    run_cmd("openssl version")
    run_cmd("/usr/bin/openssl version")
    
    # 2. 查找OpenSSL 1.1.1的头文件
    print("\n=== Finding OpenSSL 1.1.1 headers ===")
    run_cmd("find /usr -name 'opensslconf.h' 2>/dev/null")
    run_cmd("ls -la /usr/include/openssl/ 2>/dev/null | head -20")
    
    # 3. 检查是否有OpenSSL 1.1.1的pkg-config
    print("\n=== Checking pkg-config ===")
    run_cmd("pkg-config --modversion openssl 2>/dev/null || echo 'No pkg-config'")
    run_cmd("ls -la /usr/lib64/pkgconfig/openssl* 2>/dev/null")
    
    # 4. 检查Python源码目录是否有已编译的模块
    print("\n=== Checking for compiled modules ===")
    run_cmd("find /home/ai-app/code/Python-3.12.12 -name '_ssl*.so' 2>/dev/null")
    run_cmd("ls -la /home/ai-app/code/Python-3.12.12/build/lib.*/lib-dynload/ 2>/dev/null")
    
    # 5. 尝试使用OpenSSL 1.1.1编译
    print("\n=== Trying to compile with OpenSSL 1.1.1 ===")
    compile_cmd = '''
cd /home/ai-app/code/Python-3.12.12
# 清理之前的编译
make clean 2>/dev/null

# 使用OpenSSL 1.1.1重新配置
export OPENSSL_ROOT=/usr
export CFLAGS="-I/usr/include"
export LDFLAGS="-L/usr/lib64"
export LD_LIBRARY_PATH="/usr/lib64"

# 仅重新配置并编译ssl模块
./configure --with-openssl=/usr --with-openssl-rpath=auto 2>&1 | tail -20
'''
    run_cmd(compile_cmd, 120)
    
    # 6. 检查配置结果
    print("\n=== Checking configure result ===")
    run_cmd("grep -i ssl /home/ai-app/code/Python-3.12.12/Makefile 2>/dev/null | head -20")
    run_cmd("cat /home/ai-app/code/Python-3.12.12/pyconfig.h 2>/dev/null | grep -i ssl | head -10")
    
finally:
    ssh.close()
    print("\nDone")