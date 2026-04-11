import re

# Test the new regex pattern
pattern = r"execute_command\s*<command>(.+?)</command>(?:\s*<timeout>(\d+)</timeout>)?"

test_cases = [
    'execute_command<command>python shared/skills/ask-zhenxiaowei/zhenxiaowei_query.py "河北有哪些派单接口"</command><timeout>60</timeout>',
    'execute_command<command>python shared/skills/ask-zhenxiaowei/zhenxiaowei_query.py "test"</command>',
    'execute_command<command>dir /s /b *.py</command><timeout>30</timeout>',
]

for test in test_cases:
    match = re.search(pattern, test, re.IGNORECASE | re.DOTALL)
    if match:
        print(f"[OK] Matched: {match.group(1)}")
        if match.group(2):
            print(f"     Timeout: {match.group(2)}")
    else:
        print(f"[FAIL] No match: {test}")