import httpx

# Login first
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_resp.json()['token']
print("Token obtained")

# Get tools list
response = httpx.get(
    "http://localhost:8000/api/tools",
    headers={"Authorization": f"Bearer {token}"}
)
tools = response.json().get("tools", [])

print(f"\n=== Available Tools ({len(tools)}) ===")
for t in tools:
    print(f"  - {t['name']}: {t['description'][:40]}...")

# Check if execute_command exists
has_exec = any(t['name'] == 'execute_command' for t in tools)
print(f"\n{'[OK]' if has_exec else '[FAIL]'} execute_command tool: {'available' if has_exec else 'NOT FOUND'}")