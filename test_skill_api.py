import httpx

# First get a new token
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
print("Login status:", login_resp.status_code)

if login_resp.status_code == 200:
    token = login_resp.json()['token']
    print("Token:", token[:50] + "...")
    
    # Test skills/manage API
    response = httpx.get(
        "http://localhost:8000/api/skills/manage",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print("\nSkills/manage status:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Is Admin:", data.get("is_admin"))
        print("Shared Skills:", len(data.get("shared", [])))
        print("Personal Skills:", len(data.get("personal", [])))
        
        for skill in data.get("shared", []):
            print(f"  - {skill['name']}")
    else:
        print("Error:", response.text)
else:
    print("Login failed:", login_resp.text)