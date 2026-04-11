"""
测试工具调用 - 使用完整路径
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

from openharness.enterprise.tools.registry import get_tool_registry
from pathlib import Path

# 初始化工具注册表
registry = get_tool_registry()

# 使用完整路径
upload_dir = Path.home() / '.oh-enterprise' / 'users' / '1' / 'uploads'
files = list(upload_dir.iterdir())

if files:
    test_file = files[0]
    print(f"=== Testing read_file tool ===")
    print(f"File: {test_file.name}")
    print(f"Full path: {test_file}")
    
    # 使用相对路径
    relative_path = f".oh-enterprise/users/1/uploads/{test_file.name}"
    print(f"Relative path: {relative_path}")
    
    result = registry.execute_tool("read_file", {"path": relative_path})
    
    print(f"\nSuccess: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Output length: {len(result.output) if result.output else 0}")
        if result.output:
            print(f"\nContent (first 500 chars):\n{result.output[:500]}...")
else:
    print("No files found in upload directory")