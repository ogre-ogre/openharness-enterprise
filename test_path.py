"""
调试路径解析
"""
import sys
sys.path.insert(0, r'src')

from dotenv import load_dotenv
load_dotenv('.env')

from openharness.enterprise.tools.registry import ToolExecutor
from pathlib import Path

executor = ToolExecutor()

print("=== ALLOWED_PATHS ===")
for p in executor.ALLOWED_PATHS:
    print(f"  {p} -> {p.resolve()}")

test_path = ".oh-enterprise\\users\\1\\uploads\\2b2dbf40_子步骤.txt"
print(f"\n=== Resolving: {test_path} ===")

try:
    resolved = executor._resolve_path(test_path)
    print(f"Resolved: {resolved}")
except Exception as e:
    print(f"Error: {e}")

# 手动解析
print(f"\n=== Manual resolution ===")
p = Path(test_path)
print(f"Is absolute: {p.is_absolute()}")

path_normalized = test_path.replace('\\', '/')
print(f"Normalized: {path_normalized}")
print(f"Starts with .oh-enterprise/: {path_normalized.startswith('.oh-enterprise/')}")

if path_normalized.startswith('.oh-enterprise/'):
    sub_path = path_normalized[14:]
    print(f"Sub path: {sub_path}")
    manual_resolved = Path.home() / '.oh-enterprise' / sub_path
    print(f"Manual resolved: {manual_resolved}")
    print(f"Exists: {manual_resolved.exists()}")
    
    # Check if allowed
    print(f"\n=== Checking if allowed ===")
    for allowed in executor.ALLOWED_PATHS:
        try:
            manual_resolved.resolve().relative_to(allowed.resolve())
            print(f"  Allowed by: {allowed}")
            break
        except ValueError:
            print(f"  NOT under: {allowed}")