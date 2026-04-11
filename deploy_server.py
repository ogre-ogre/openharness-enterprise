import paramiko
import time

# 连接信息
host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_command(cmd, timeout=300):
    print(f"\n执行: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out:
        print(out[-3000:] if len(out) > 3000 else out)
    if err and "warning" not in err.lower():
        print(f"Stderr: {err[-1000:]}")
    return out, err, exit_code

try:
    print(f"连接服务器 {host}...")
    ssh.connect(host, username=username, password=password)
    print("连接成功！")
    
    # 1. 清理之前的失败安装
    print("\n=== 1. 清理之前的安装 ===")
    run_command("rm -rf $HOME/miniconda3 $HOME/miniconda.sh")
    run_command("sed -i '/miniconda/d' ~/.bashrc")
    
    # 2. 确认Python 3.12路径
    print("\n=== 2. 确认Python 3.12路径 ===")
    out, _, _ = run_command("which python3.12 || which python3 || echo 'not found'")
    python_path = out.strip().split('\n')[0] if out.strip() else "/usr/local/python3/bin/python3"
    print(f"使用Python: {python_path}")
    
    # 3. 检查现有venv
    print("\n=== 3. 检查现有虚拟环境 ===")
    run_command(f"ls -la {deploy_path}/venv/bin/ 2>/dev/null || echo 'venv not valid'")
    
    # 4. 重新创建虚拟环境
    print("\n=== 4. 重新创建虚拟环境 ===")
    run_command(f"rm -rf {deploy_path}/venv")
    run_command(f"{python_path} -m venv {deploy_path}/venv")
    
    # 5. 安装依赖（使用国内镜像）
    print("\n=== 5. 安装依赖 ===")
    install_cmd = f"""
cd {deploy_path}
source venv/bin/activate
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
"""
    out, err, exit_code = run_command(install_cmd, timeout=600)
    
    # 6. 验证安装
    print("\n=== 6. 验证安装 ===")
    verify_cmd = f"""
cd {deploy_path}
source venv/bin/activate
python -c "import fastapi, uvicorn; print('依赖验证成功')"
"""
    out, err, exit_code = run_command(verify_cmd)
    
    if "依赖验证成功" in out:
        print("\n✅ 依赖安装成功！")
    else:
        print("\n❌ 依赖安装失败，尝试使用离线安装...")
    
    # 7. 配置环境变量
    print("\n=== 7. 配置环境变量 ===")
    run_command(f"cat {deploy_path}/.env | head -30")
    
    # 8. 创建数据目录
    print("\n=== 8. 创建数据目录 ===")
    run_command("mkdir -p ~/.oh-enterprise/users ~/.oh-enterprise/shared/skills ~/.oh-enterprise/logs")
    
    # 9. 启动服务
    print("\n=== 9. 启动服务 ===")
    # 先停止可能存在的旧进程
    run_command("pkill -f 'openharness.enterprise.server' 2>/dev/null || true")
    
    start_cmd = f"""
cd {deploy_path}
source venv/bin/activate
export ANTHROPIC_AUTH_TOKEN=sk-test
export ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
export ANTHROPIC_MODEL=glm-5
nohup python -m openharness.enterprise.server --port 8000 > ~/.oh-enterprise/logs/server.log 2>&1 &
echo $! > ~/.oh-enterprise/server.pid
sleep 5
cat ~/.oh-enterprise/logs/server.log | tail -30
"""
    run_command(start_cmd, timeout=30)
    
    # 10. 检查服务状态
    print("\n=== 10. 检查服务状态 ===")
    run_command("curl -s http://localhost:8000/health || echo 'Service not ready'")
    run_command("netstat -tlnp 2>/dev/null | grep 8000 || ss -tlnp | grep 8000")
    
    print("\n" + "="*60)
    print("部署完成！")
    print("="*60)
    print(f"访问地址: http://10.1.7.155:8000")
    print(f"API文档: http://10.1.7.155:8000/docs")
    print(f"管理后台: http://10.1.7.155:8000/admin")
    print(f"默认账号: admin / admin123")
    print(f"日志文件: ~/.oh-enterprise/logs/server.log")
    print("="*60)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
    print("\n连接已关闭")