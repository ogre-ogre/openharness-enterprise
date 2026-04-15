import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

skill_md_path = '/home/ai-app/.oh-enterprise/shared/skills/pptx/SKILL.md'
with sftp.open(skill_md_path) as f:
    content = f.read(5000).decode('utf-8', errors='replace')
    
print('=== SKILL.md First 800 chars ===')
print(content[:800])

print('\n=== Key checks ===')
if 'Python' in content:
    print('Python keyword: YES')
else:
    print('Python keyword: NO')

if 'python-pptx' in content:
    print('python-pptx: YES')
else:
    print('python-pptx: NO')

if 'html2pptx' in content[:2000]:
    print('html2pptx in first 2000: YES')
else:
    print('html2pptx in first 2000: NO')

sftp.close()
ssh.close()