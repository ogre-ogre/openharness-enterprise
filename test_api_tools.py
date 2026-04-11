import httpx

# First login to get token
login_resp = httpx.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = login_resp.json()['token']

# Test tools API with auth
response = httpx.get('http://localhost:8000/api/tools', headers={
    'Authorization': f'Bearer {token}'
})
data = response.json()

print('Available tools:', len(data.get('tools', [])))
for tool in data.get('tools', []):
    print(f"  - {tool['name']}: {tool['description'][:40]}...")
    if tool['name'] == 'rest_api_call':
        print('\n--- rest_api_call tool found ---')
        print('Name:', tool['name'])
        print('Description:', tool['description'])
        print('Category:', tool['category'])
        print('Parameters:', list(tool['parameters'].keys()))