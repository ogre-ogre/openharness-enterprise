import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

# 用Python读取xlsx技能的SKILL.md
cmd = r'''
/home/ai-app/oh-enterprise-1.0.0/venv/bin/python3 << 'EOF'
import os

skill_path = '/home/ai-app/.oh-enterprise/shared/skills/xlsx'
for f in os.listdir(skill_path):
    full_path = os.path.join(skill_path, f)
    print(f'\n=== {f} ===')
    if os.path.isfile(full_path) and f.endswith('.md') or f.endswith('.py') or f.endswith('.txt'):
        with open(full_path) as file:
            content = file.read()
            print(content[:2000])
EOF
'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
print(stdout.read().decode())

ssh.close()