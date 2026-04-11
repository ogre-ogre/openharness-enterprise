"""
测试工具调用
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

from openharness.enterprise.tools.registry import get_tool_registry

# 初始化工具注册表
registry = get_tool_registry()

# 测试文件读取
test_path = r".oh-enterprise\users\1\uploads\2b2dbf40_子步骤.txt"

print(f"=== Testing read_file tool ===")
print(f"Path: {test_path}")

result = registry.execute_tool("read_file", {"path": test_path})

print(f"\nSuccess: {result.success}")
print(f"Execution time: {result.execution_time:.3f}s")
if result.error:
    print(f"Error: {result.error}")
else:
    print(f"Output length: {len(result.output) if result.output else 0}")
    if result.output:
        print(f"\nContent (first 500 chars):\n{result.output[:500]}...")