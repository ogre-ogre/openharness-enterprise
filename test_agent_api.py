"""
测试创建 Agent API
"""
import requests
import json

# 登录获取 token
login_url = "http://localhost:8000/api/auth/login"
login_data = {"username": "admin", "password": "admin123"}

response = requests.post(login_url, json=login_data)
print("Login response:", response.status_code)

if response.status_code == 200:
    token = response.json()["access_token"]
    print("Token:", token[:20] + "...")
    
    # 创建 agent
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    agent_data = {
        "id": "test-agent-001",
        "name": "测试Agent",
        "role": "custom",
        "description": "这是一个测试Agent",
        "system_prompt": "你是一个测试助手。",
        "model": "glm-5",
        "temperature": 0.7
    }
    
    create_url = "http://localhost:8000/api/agents"
    response = requests.post(create_url, headers=headers, json=agent_data)
    print("\nCreate agent response:", response.status_code)
    print("Response:", response.text)
    
    # 列出 agents
    list_url = "http://localhost:8000/api/agents"
    response = requests.get(list_url, headers=headers)
    print("\nList agents response:", response.status_code)
    agents = response.json().get("agents", [])
    print(f"Found {len(agents)} agents")
    for a in agents[-3:]:
        print(f"  - {a['id']}: {a['name']}")
else:
    print("Login failed:", response.text)