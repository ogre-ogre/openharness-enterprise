"""
测试用户目录权限检查
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

from openharness.enterprise.tools.registry import get_tool_registry

# 初始化工具注册表
registry = get_tool_registry()

# 测试用户 1 访问自己的目录
print("=== User 1 accessing their own directory ===")
result = registry.execute_tool("read_file", {"path": ".oh-enterprise/users/1/uploads/2b2dbf40_子步骤.txt"}, user_id=1)
print(f"Success: {result.success}")
if result.error:
    print(f"Error: {result.error}")
else:
    print(f"Output length: {len(result.output) if result.output else 0}")

# 测试用户 2 访问用户 1 的目录（应该被拒绝）
print("\n=== User 2 accessing User 1's directory (should be denied) ===")
result = registry.execute_tool("read_file", {"path": ".oh-enterprise/users/1/uploads/2b2dbf40_子步骤.txt"}, user_id=2)
print(f"Success: {result.success}")
if result.error:
    print(f"Error: {result.error}")

# 测试用户 1 访问用户 2 的目录（应该被拒绝）
print("\n=== User 1 accessing User 2's directory (should be denied) ===")
result = registry.execute_tool("list_files", {"path": ".oh-enterprise/users/2/uploads"}, user_id=1)
print(f"Success: {result.success}")
if result.error:
    print(f"Error: {result.error}")

# 测试访问 shared 目录（应该允许）
print("\n=== User 1 accessing shared directory (should be allowed) ===")
result = registry.execute_tool("list_files", {"path": ".oh-enterprise/shared"}, user_id=1)
print(f"Success: {result.success}")
if result.error:
    print(f"Error: {result.error}")