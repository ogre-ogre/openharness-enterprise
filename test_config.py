import sys
sys.path.insert(0, r'src')
from dotenv import load_dotenv
load_dotenv('.env')
import os
print('=== Environment Variables ===')
print('OH_PROVIDER:', os.getenv('OH_PROVIDER'))
api_key = os.getenv('OH_API_KEY')
if api_key:
    print('OH_API_KEY:', api_key[:20] + '...')
else:
    print('OH_API_KEY: NOT SET')
print('OH_BASE_URL:', os.getenv('OH_BASE_URL'))
print('OH_MODEL:', os.getenv('OH_MODEL'))

print('\n=== Provider Config ===')
from openharness.enterprise.config.provider import get_provider_config
config = get_provider_config()
print('Provider:', config.provider)
print('API Key:', config.api_key[:20] + '...' if config.api_key else 'NOT SET')
print('Base URL:', config.base_url)
print('Model:', config.model)