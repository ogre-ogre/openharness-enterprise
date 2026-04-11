import httpx

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzc1Njk3NjY2LCJleHAiOjE3NzU3ODQwNjZ9.RKzsJDa3i3XkdzN5OtnJtcNYWfXhEF9QU2yYZ29dYhE"

# 获取工具列表
response = httpx.get(
    "http://localhost:8000/api/tools",
    headers={"Authorization": f"Bearer {token}"}
)

tools = response.json().get("tools", [])
print(f"Available tools: {len(tools)}")
for t in tools:
    print(f"  - {t['name']}: {t['description'][:40]}...")
    
# 检查 rest_api_call 是否存在
has_rest = any(t['name'] == 'rest_api_call' for t in tools)
print(f"\n{'[OK]' if has_rest else '[FAIL]'} rest_api_call tool: {'available' if has_rest else 'NOT FOUND'}")