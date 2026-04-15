import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

# Sync webchat.py
sftp.put('D:/openharness-enterprise/src/openharness/enterprise/channels/webchat.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/webchat.py')
print('webchat.py synced')

# Sync context.py
sftp.put('D:/openharness-enterprise/src/openharness/enterprise/users/context.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/users/context.py')
print('context.py synced')

# Sync workspace.py
sftp.put('D:/openharness-enterprise/src/openharness/enterprise/users/workspace.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/users/workspace.py')
print('workspace.py synced')

# Sync registry.py
sftp.put('D:/openharness-enterprise/src/openharness/enterprise/tools/registry.py', '/home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/tools/registry.py')
print('registry.py synced')

sftp.close()

# Verify sync
stdin, stdout, stderr = ssh.exec_command('/usr/bin/grep "downloads_path" /home/ai-app/oh-enterprise-1.0.0/openharness/enterprise/channels/webchat.py', timeout=10)
grep_result = stdout.read().decode('utf-8', errors='replace').strip()
print('Verify downloads_path:', grep_result[:100] if grep_result else 'NOT FOUND')

ssh.close()