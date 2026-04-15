import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('D:/openharness-enterprise/src/openharness/enterprise/server.py', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 /api/agents 路由
for i, line in enumerate(lines):
    if '/api/agents' in line and '@app' in line:
        print(f'Found at line {i+1}')
        # 打印接下来的30行
        for j in range(i, min(i+30, len(lines))):
            print(f'{j+1}: {lines[j]}')
        print('\n---\n')