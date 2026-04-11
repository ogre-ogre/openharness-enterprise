from openharness.enterprise.tools.registry import get_tool_registry

r = get_tool_registry()
t = r.get_tool('rest_api_call')

if t:
    print('Tool:', t.name)
    print('Description:', t.description[:80])
    print('Parameters:', list(t.parameters.keys()))
else:
    print('Tool not found')

# Test schema
schema = r.get_tool_schema('rest_api_call')
print('\nSchema:')
import json
print(json.dumps(schema, indent=2, ensure_ascii=False))