import os
from openharness.enterprise.tools.registry import get_tool_registry

# Set test token
os.environ['REST_API_TOKEN'] = 'test-token-123'

r = get_tool_registry()

# Test GET request
result = r.execute_tool('rest_api_call', {
    'url': 'https://httpbin.org/get',
    'method': 'GET',
    'query_params': {'foo': 'bar', 'test': '123'}
})

print('GET Test Result:')
print('Success:', result.success)
print('Status:', result.output.get('status') if result.output else None)
if result.output and 'data' in result.output:
    data = result.output['data']
    if isinstance(data, dict):
        print('Response args:', data.get('args'))
        print('Response headers:', data.get('headers', {}).get('Authorization'))