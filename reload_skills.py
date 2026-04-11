import httpx

# Login first
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_resp.json()['token']
print("Token obtained")

# Reload skills
response = httpx.post(
    "http://localhost:8000/api/skills/reload",
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()
print(f"Skills reloaded: {data.get('shared_count')} shared, {data.get('personal_count')} personal")
print(f"Shared skills: {data.get('shared_skills', [])}")