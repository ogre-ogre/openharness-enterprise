"""
测试工具调用解析
"""
import sys
sys.path.insert(0, r'src')
import re

# 测试 LLM 返回的格式
test_text = """<tool_call>read_file<file_path>.oh-enterprise/users/1/uploads/2b2dbf40_子步骤.txt</file_path>"""

# 当前模式
TOOL_PATTERNS = {
    "read_file": r"<read_file>\s*<file_path>([^<]+)</file_path>",
}

print("=== Test Text ===")
print(test_text)
print()

print("=== Pattern Matching ===")
for tool_name, pattern in TOOL_PATTERNS.items():
    match = re.search(pattern, test_text, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"Found {tool_name}!")
        print(f"Path: {match.group(1)}")
    else:
        print(f"No match for {tool_name}")
        
# 尝试不同模式
print("\n=== Alternative Patterns ===")
patterns_to_try = [
    r"<read_file>\s*<file_path>([^<]+)</file_path>",
    r"read_file\s*<file_path>([^<]+)</file_path>",
    r"<read_file><file_path>([^<]+)</file_path>",
    r"read_file.*?file_path>([^<]+)</file_path>",
]

for i, pattern in enumerate(patterns_to_try):
    match = re.search(pattern, test_text, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"Pattern {i+1} matched: {match.group(1)}")
    else:
        print(f"Pattern {i+1} no match")