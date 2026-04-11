"""
测试工具调用解析 - 使用新模式
"""
import sys
sys.path.insert(0, r'src')
import re

# 测试 LLM 返回的格式
test_text = """<tool_call>read_file<file_path>.oh-enterprise/users/1/uploads/2b2dbf40_子步骤.txt</file_path>"""

# 新模式
TOOL_PATTERNS = {
    "read_file": r"read_file\s*<file_path>([^<]+)</file_path>",
    "write_file": r"write_file\s*<file_path>([^<]+)</file_path>\s*<content>([^<]+)</content>",
    "list_files": r"list_files\s*<path>([^<]+)</path>",
}

print("=== Test Text ===")
print(test_text)
print()

print("=== Pattern Matching ===")
for tool_name, pattern in TOOL_PATTERNS.items():
    match = re.search(pattern, test_text, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"Found {tool_name}!")
        print(f"Groups: {match.groups()}")
    else:
        print(f"No match for {tool_name}")