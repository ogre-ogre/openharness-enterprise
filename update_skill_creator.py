import paramiko
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.1.7.155', username='ai-app', password='asb#1234', timeout=10)

sftp = ssh.open_sftp()

skill_md_path = '/home/ai-app/.oh-enterprise/shared/skills/skill-creator/SKILL.md'

# 读取完整内容
with sftp.open(skill_md_path) as f:
    content = f.read().decode('utf-8')

print(f'SKILL.md total length: {len(content)}')

# 在开头添加路径限制说明
path_restriction = '''
## ⚠️ 重要：技能保存路径限制

**创建的技能必须保存在用户个人目录下：**

```
~/.oh-enterprise/users/{user_id}/skills/{skill_name}/
```

**绝对禁止保存在以下位置：**
- `~/.oh-enterprise/shared/skills/` （共享技能目录，仅管理员可修改）
- `/home/ai-app/` 根目录
- 其他用户的目录

**正确示例：**
```bash
# 获取用户技能目录
skill_dir = os.path.expanduser(f"~/.oh-enterprise/users/{user_id}/skills/my-skill")
os.makedirs(skill_dir, exist_ok=True)

# 创建SKILL.md
skill_md_path = os.path.join(skill_dir, "SKILL.md")
with open(skill_md_path, 'w') as f:
    f.write(skill_content)
```

**环境变量提示：**
- `OH_USER_ID`: 当前用户ID
- `OH_WORKSPACE_PATH`: 用户工作区路径（包含skills子目录）

使用 `os.environ.get("OH_USER_ID")` 获取用户ID。

---

'''

# 在 "---" 之后插入限制说明
insert_pos = content.find('\n# Skill Creator')
if insert_pos > 0 and '⚠️ 重要' not in content:
    new_content = content[:insert_pos] + path_restriction + content[insert_pos:]
    
    with sftp.open(skill_md_path, 'w') as f:
        f.write(new_content.encode('utf-8'))
    
    print('[OK] SKILL.md updated with path restriction')
else:
    print('[INFO] Already has restriction or marker not found')

# 验证更新
with sftp.open(skill_md_path) as f:
    updated = f.read(1000).decode('utf-8')
    
print('\n=== Updated content preview ===')
print(updated[:600])

sftp.close()
ssh.close()