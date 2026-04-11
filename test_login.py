import httpx

# Test login
try:
    response = httpx.post(
        'http://localhost:8000/api/auth/login',
        json={'username': 'admin', 'password': 'admin123'}
    )
    print('Status:', response.status_code)
    print('Response:', response.json())
except Exception as e:
    print('Error:', e)