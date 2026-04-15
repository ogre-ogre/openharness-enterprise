import paramiko
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

# 检查SKILL.md内容开头
skill_md_path = '/home/ai-app/.oh-enterprise/shared/skills/pptx/SKILL.md'
with sftp.open(skill_md_path) as f:
    content = f.read(3000).decode('utf-8')
    
print('=== SKILL.md开头内容 ===')
print(content[:1500])

# 检查是否包含Python方案
if '## Python直接生成PPT' in content:
    print('\n[OK] Python方案已添加')
else:
    print('\n[ERROR] Python方案未找到')

if '## Creating a new PowerPoint presentation **without a template**' in content:
    print('[INFO] html2pptx部分还存在')

sftp.close()
ssh.close()