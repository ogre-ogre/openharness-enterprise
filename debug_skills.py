import os
from pathlib import Path

# 检查 skills 加载路径
from openharness.enterprise.users.workspace import get_shared_root, get_enterprise_root
from openharness.enterprise.users.context import load_user_context
from openharness.enterprise.storage.database import get_database, User

print("=== 路径检查 ===")
print("Shared root:", get_shared_root())
print("Enterprise root:", get_enterprise_root())

shared_skills = get_shared_root() / "skills"
print("\nShared skills path:", shared_skills)
print("Exists:", shared_skills.exists())

if shared_skills.exists():
    print("\n=== Skills 目录 ===")
    for skill_dir in shared_skills.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            print(f"  - {skill_dir.name}: SKILL.md exists = {skill_file.exists()}")

# 测试 LLM client 的 skill 加载
print("\n=== LLM Client Skill 加载测试 ===")
from openharness.enterprise.llm.client import get_llm_client

llm = get_llm_client()
skill_content = llm.load_skill_content("queryZhandianByCity", str(shared_skills))
if skill_content:
    print("Skill loaded successfully, length:", len(skill_content))
    print("First 200 chars:", skill_content[:200])
else:
    print("Failed to load skill!")

# 测试 UserContext 加载
print("\n=== UserContext 加载测试 ===")
db = get_database()
user = db.get_user_by_username("admin")
if user:
    ctx = load_user_context(user)
    print("User ID:", ctx.user_id)
    print("Available skills:", ctx.available_skills)
    print("Skills path:", ctx.skills_path)