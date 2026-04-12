import paramiko
import subprocess
import sys

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
server_path = "/home/ai-app/oh-enterprise-1.0.0"

print("=" * 60)
print("OpenHarness Enterprise 同步部署脚本")
print("=" * 60)

# Step 1: 提交本地代码到 GitHub
print("\n[1/5] 提交本地代码到 GitHub...")
local_result = subprocess.run(
    ["git", "status", "--porcelain"],
    cwd="D:\\openharness-enterprise",
    capture_output=True,
    text=True
)

if local_result.stdout.strip():
    print("  发现未提交的更改，正在提交...")
    subprocess.run(["git", "add", "-A"], cwd="D:\\openharness-enterprise")
    subprocess.run(
        ["git", "commit", "-m", "sync: 同步到服务器"],
        cwd="D:\\openharness-enterprise"
    )
else:
    print("  无待提交更改")

# 推送到 GitHub
push_result = subprocess.run(
    ["git", "push", "origin", "master"],
    cwd="D:\\openharness-enterprise",
    capture_output=True,
    text=True,
    timeout=60
)

if push_result.returncode == 0:
    print("  [OK] GitHub 推送成功")
else:
    print(f"  [WARN] GitHub 推送失败: {push_result.stderr}")
    print("  将继续尝试同步服务器...")

# Step 2: SSH 连接服务器
print("\n[2/5] 连接服务器...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=username, password=password, timeout=10)
    print("  [OK] 已连接到服务器")
except Exception as e:
    print(f"  [FAIL] 连接失败: {e}")
    sys.exit(1)

try:
    # Step 3: 同步代码
    print("\n[3/5] 同步代码到服务器...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {server_path} && git pull origin master",
        timeout=60
    )
    pull_output = stdout.read().decode()
    pull_error = stderr.read().decode()
    
    if "Already up to date" in pull_output or pull_output.strip() == "":
        print("  [OK] 代码已是最新")
    elif pull_error:
        print(f"  [WARN] 同步警告: {pull_error}")
    else:
        print(f"  [OK] 代码已更新: {pull_output.strip()}")
    
    # Step 4: 构建前端并重启服务
    print("\n[4/5] 构建前端并重启服务...")
    
    # 杀掉所有进程
    stdin, stdout, stderr = ssh.exec_command(
        "pkill -9 -f uvicorn 2>/dev/null; "
        "pkill -9 -f python.*server 2>/dev/null; "
        "sleep 2"
    )
    stdout.read()
    print("  [OK] 已停止旧服务")
    
    # 启动服务（包含前端构建）
    stdin, stdout, stderr = ssh.exec_command(f'''
cd {server_path}
source venv/bin/activate
export LD_LIBRARY_PATH=/home/ai-app/openssl-1.1.1/lib:$LD_LIBRARY_PATH
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5

# 更新依赖
uv sync --extra dev 2>/dev/null

# 构建前端
cd web
npm run build 2>/dev/null
cd ..

# 启动服务
nohup uvicorn openharness.enterprise.server:app --host 0.0.0.0 --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
sleep 5

echo "=== 服务日志 ==="
tail -15 ~/.oh-enterprise/logs/server.log
''', timeout=120)
    
    output = stdout.read().decode()
    print(output)
    
    # Step 5: 测试服务
    print("\n[5/5] 测试服务状态...")
    
    # Health check
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost:8000/health",
        timeout=10
    )
    health = stdout.read().decode().strip()
    
    if "healthy" in health:
        print(f"  [OK] 健康检查: {health}")
    else:
        print(f"  [WARN] 健康检查: {health or '无响应'}")
    
    # API docs check
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost:8000/docs | grep -o '<title>.*</title>' | head -1",
        timeout=10
    )
    docs_title = stdout.read().decode().strip()
    
    if docs_title:
        print(f"  [OK] API 文档: {docs_title}")
    
    # Web UI check
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s http://localhost:8000/web/ | grep -o '<title>.*</title>' | head -1",
        timeout=10
    )
    web_title = stdout.read().decode().strip()
    
    if web_title:
        print(f"  [OK] 前端页面: {web_title}")
    
    # 打印访问地址
    print("\n" + "=" * 60)
    print("部署完成!")
    print("=" * 60)
    print(f"前端地址: http://{host}:8000/web/")
    print(f"管理后台: http://{host}:8000/admin")
    print(f"API 文档: http://{host}:8000/docs")
    print(f"健康检查: http://{host}:8000/health")
    print("=" * 60)

except Exception as e:
    print(f"\n[FAIL] 执行失败: {e}")
    
    # 打印错误日志
    stdin, stdout, stderr = ssh.exec_command(
        "tail -20 ~/.oh-enterprise/logs/server.log"
    )
    print("\n错误日志:")
    print(stdout.read().decode())

finally:
    ssh.close()
    print("\n连接已关闭")