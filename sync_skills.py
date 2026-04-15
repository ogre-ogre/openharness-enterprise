import paramiko
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

# 技能列表
skills = ['docx', 'xlsx', 'pptx', 'pdf']

local_base = 'C:/Users/20171/.oh-enterprise/shared/skills'
remote_base = '/home/ai-app/.oh-enterprise/shared/skills'

for skill in skills:
    remote_skill_path = remote_base + '/' + skill
    local_skill_path = os.path.join(local_base, skill)
    
    # 创建本地目录
    os.makedirs(local_skill_path, exist_ok=True)
    
    # 同步SKILL.md
    remote_file = remote_skill_path + '/SKILL.md'
    local_file = os.path.join(local_skill_path, 'SKILL.md')
    
    try:
        sftp.stat(remote_file)
        print(f'[*] Syncing {skill}/SKILL.md...')
        
        # 下载文件
        with sftp.open(remote_file) as remote_f:
            content = remote_f.read()
        
        with open(local_file, 'wb') as local_f:
            local_f.write(content)
        
        print(f'[OK] {skill}/SKILL.md synced ({len(content)} bytes)')
        
    except FileNotFoundError:
        print(f'[WARN] {skill}/SKILL.md not found on remote')
    
    # 同步LICENSE.txt
    remote_license = remote_skill_path + '/LICENSE.txt'
    local_license = os.path.join(local_skill_path, 'LICENSE.txt')
    
    try:
        with sftp.open(remote_license) as remote_f:
            content = remote_f.read()
        with open(local_license, 'wb') as local_f:
            local_f.write(content)
        print(f'[OK] {skill}/LICENSE.txt synced')
    except FileNotFoundError:
        pass

sftp.close()
ssh.close()

print('\n[DONE] Skills synced to local')