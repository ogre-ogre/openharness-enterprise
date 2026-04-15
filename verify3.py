import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

skill_md_path = '/home/ai-app/.oh-enterprise/shared/skills/pptx/SKILL.md'
with sftp.open(skill_md_path) as f:
    content = f.read(6000).decode('utf-8', errors='replace')

# 检查关键内容
checks = [
    ('Python方案置顶', '⚠️ 重要'),
    ('推荐方案', '✅ 推荐方案'),
    ('python-pptx库', 'python-pptx'),
    ('html2pptx警告', 'html2pptx.js 无法正常运行'),
    ('不要使用', '不要使用 html2pptx'),
]

print('=== SKILL.md Key Checks ===')
for name, keyword in checks:
    found = keyword in content
    status = 'YES' if found else 'NO'
    print(f'{name}: {status}')

sftp.close()
ssh.close()