from openharness.enterprise.server import app
print('Server module loaded OK')

# Test skill loading
from openharness.enterprise.llm.client import get_llm_client
from openharness.enterprise.users.workspace import get_shared_root

llm = get_llm_client()
skill_content = llm.load_skill_content("queryZhandianByCity", str(get_shared_root() / "skills"))
print(f"Skill content loaded: {len(skill_content) if skill_content else 0} chars")
if skill_content:
    print("First 100 chars:", skill_content[:100])