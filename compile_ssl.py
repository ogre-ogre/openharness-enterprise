import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-3000:] if len(out) > 3000 else out)
    if err and 'warning' not in err.lower(): print(f"Err: {err[-1500:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 进入Python源码目录，尝试编译SSL模块
    print("\n=== Compiling SSL module ===")
    
    # 设置编译标志
    compile_cmd = '''
cd /home/ai-app/code/Python-3.12.12
export CFLAGS="-I/usr/include/openssl"
export LDFLAGS="-L/usr/lib64 -lssl -lcrypto"
export LD_LIBRARY_PATH="/usr/lib64:$LD_LIBRARY_PATH"

# 仅编译_ssl模块
cd Modules
gcc -shared -fPIC -I/usr/local/python3/include/python3.12 -I/usr/include/openssl _ssl.c -L/usr/lib64 -lssl -lcrypto -o _ssl.cpython-312-x86_64-linux-gnu.so 2>&1 || echo "Compile failed, trying alternative approach"
'''
    run_cmd(compile_cmd, 120)
    
    # 2. 检查编译结果
    print("\n=== Checking build result ===")
    run_cmd("ls -la /home/ai-app/code/Python-3.12.12/Modules/_ssl*.so 2>/dev/null")
    
    # 3. 尝试复制到Python库目录
    print("\n=== Copying to site-packages ===")
    run_cmd("cp /home/ai-app/code/Python-3.12.12/Modules/_ssl*.so /usr/local/python3/lib/python3.12/lib-dynload/ 2>/dev/null || echo 'Copy failed (permission denied)'")
    
    # 4. 检查是否有build目录
    print("\n=== Checking build directory ===")
    run_cmd("ls -la /home/ai-app/code/Python-3.12.12/build/lib.linux-x86_64-cpython-312/ 2>/dev/null | head -20")
    
    # 5. 尝试完整的模块编译
    print("\n=== Trying make ===")
    run_cmd("cd /home/ai-app/code/Python-3.12.12 && make 2>&1 | tail -30", 300)
    
finally:
    ssh.close()
    print("\nDone")