import httpx

# Login first
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_resp.json()['token']
print("Token obtained")

# Test audit logs API
response = httpx.get(
    "http://localhost:8000/api/admin/audit-logs",
    headers={"Authorization": f"Bearer {token}"}
)

print("Status:", response.status_code)
if response.status_code == 200:
    data = response.json()
    print(f"Total logs: {data.get('total', 0)}")
    print(f"Logs returned: {len(data.get('logs', []))}")
    for log in data.get('logs', [])[:5]:
        print(f"  - {log['action']} by user {log['user_id']}")
else:
    print("Error:", response.text)