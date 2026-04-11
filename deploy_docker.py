import paramiko

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"
deploy_path = "/home/ai-app/oh-enterprise-1.0.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def run_cmd(cmd, timeout=300):
    print(f"\n>>> {cmd[:80]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    if out: print(out[-3000:] if len(out) > 3000 else out)
    if err: print(f"Err: {err[-1500:]}")
    return out, err, exit_code

try:
    ssh.connect(host, username=username, password=password)
    print("Connected!")
    
    # 1. 创建Dockerfile
    print("\n=== Creating Dockerfile ===")
    dockerfile = '''FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy application
COPY openharness/ ./openharness/
COPY web/ ./web/

# Create data directories
RUN mkdir -p /root/.oh-enterprise/users /root/.oh-enterprise/shared/skills /root/.oh-enterprise/logs

# Environment variables
ENV ANTHROPIC_AUTH_TOKEN=sk-test
ENV ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ENV ANTHROPIC_MODEL=glm-5

EXPOSE 8000

CMD ["python", "-m", "openharness.enterprise.server", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    # 通过SFTP写入Dockerfile
    sftp = ssh.open_sftp()
    with sftp.file(f"{deploy_path}/Dockerfile", 'w') as f:
        f.write(dockerfile)
    sftp.close()
    print("Dockerfile created")
    
    # 2. 构建Docker镜像
    print("\n=== Building Docker image ===")
    out, err, exit_code = run_cmd(f"cd {deploy_path} && docker build -t oh-enterprise:latest .", 600)
    
    if exit_code != 0:
        print("Build failed, checking error...")
    else:
        print("Build successful!")
    
    # 3. 检查镜像
    print("\n=== Checking images ===")
    run_cmd("docker images | grep oh-enterprise")
    
    # 4. 停止旧容器
    print("\n=== Stopping old container ===")
    run_cmd("docker stop oh-enterprise 2>/dev/null || true")
    run_cmd("docker rm oh-enterprise 2>/dev/null || true")
    
    # 5. 运行新容器
    print("\n=== Starting container ===")
    run_cmd(f"docker run -d --name oh-enterprise -p 8000:8000 -v /home/ai-app/.oh-enterprise:/root/.oh-enterprise oh-enterprise:latest")
    
    # 6. 检查容器状态
    print("\n=== Checking container status ===")
    run_cmd("docker ps | grep oh-enterprise")
    
    # 7. 查看日志
    print("\n=== Container logs ===")
    run_cmd("docker logs oh-enterprise 2>&1 | tail -30")
    
    # 8. 测试服务
    print("\n=== Testing service ===")
    run_cmd("sleep 3 && curl -s http://localhost:8000/health")
    
    print("\n" + "="*60)
    print("部署完成!")
    print("="*60)
    print(f"访问地址: http://10.1.7.155:8000")
    print(f"API文档: http://10.1.7.155:8000/docs")
    print(f"管理后台: http://10.1.7.155:8000/admin")
    print(f"默认账号: admin / admin123")
    print("="*60)
    
finally:
    ssh.close()
    print("\nDone")