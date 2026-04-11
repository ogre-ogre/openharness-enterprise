import httpx
import json

# Login first
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_resp.json()['token']
print("Token obtained")

# 1. Test skills/manage API
response = httpx.get(
    "http://localhost:8000/api/skills/manage",
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()
print(f"\n=== Skills List ===")
print(f"Is Admin: {data['is_admin']}")
print(f"Shared Skills: {data['shared_skills'] if 'shared_skills' in str(data) else [s['name'] for s in data['shared']]}")

# 2. Test reload API
response = httpx.post(
    "http://localhost:8000/api/skills/reload",
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()
print(f"\n=== Reload Skills ===")
print(f"Message: {data['message']}")
print(f"Personal: {data.get('personal_skills', [])}")
print(f"Shared: {data.get('shared_skills', [])}")

# 3. Test context loading (simulate WebSocket connection)
from openharness.enterprise.users.context import load_user_context
from openharness.enterprise.storage.database import get_database

db = get_database()
user = db.get_user_by_username("admin")
ctx = load_user_context(user)

print(f"\n=== User Context ===")
print(f"Available skills: {ctx.available_skills}")
print(f"Skills path: {ctx.skills_path}")

# 4. Test system prompt building
from openharness.enterprise.llm.client import get_llm_client

llm = get_llm_client()
system_prompt = llm.build_system_prompt(
    base_prompt="You are a helpful assistant.",
    skills=ctx.available_skills,
    skills_base_path=ctx.skills_path
)

print(f"\n=== System Prompt ===")
print(f"Length: {len(system_prompt)}")

# Check if each skill is in the prompt
for skill in ctx.available_skills:
    if skill in system_prompt:
        print(f"[OK] {skill} is in system prompt")
    else:
        print(f"[FAIL] {skill} is NOT in system prompt!")

# Check if skill content is present
if "queryStation" in system_prompt:
    print("[OK] queryStation content found in prompt")
if "rest_api_call" in system_prompt:
    print("[OK] rest_api_call instruction found in prompt")