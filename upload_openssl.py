import paramiko
import os

host = "10.1.7.155"
username = "ai-app"
password = "asb#1234"

# 本地文件路径
local_file = r"D:\openharness-enterprise\deploy\openssl-1.1.1w.tar.gz"
remote_file = "/home/ai-app/openssl-build/openssl-1.1.1w.tar.gz"

print(f"Connecting to {host}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=username, password=password)

print("Creating remote directory...")
ssh.exec_command("mkdir -p /home/ai-app/openssl-build")

print(f"Uploading {local_file}...")
sftp = ssh.open_sftp()
sftp.put(local_file, remote_file)
sftp.close()

print("Upload complete!")

# 验证文件
stdin, stdout, stderr = ssh.exec_command(f"ls -la {remote_file}")
print(stdout.read().decode())

ssh.close()
print("Done")