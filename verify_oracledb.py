import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234')

stdin, stdout, stderr = ssh.exec_command('cd /home/ai-app/oh-enterprise-1.0.0 && source venv/bin/activate && python -c "import oracledb; print(oracledb.__version__)"', timeout=15)
ver = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()

if ver:
    print('oracledb installed:', ver)
else:
    print('oracledb NOT installed')
    print('Error:', err[:80] if err else '')

ssh.close()