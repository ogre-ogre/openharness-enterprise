#!/usr/bin/env python3
import subprocess
import os

os.chdir('D:/openharness-enterprise')

# 获取所有已跟踪的 .py 文件
result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
tracked_files = result.stdout.strip().split('\n')

# 找出根目录下的 .py 文件（不在 src/ 或 openharness/ 下）
root_py_files = []
for f in tracked_files:
    if f.endswith('.py') and not f.startswith('src/') and not f.startswith('openharness/'):
        root_py_files.append(f)

print('Root level .py files tracked in git:')
for f in root_py_files:
    print(f'  {f}')

print(f'\nTotal: {len(root_py_files)} files')

# 从 git 中移除这些文件
if root_py_files:
    for f in root_py_files:
        subprocess.run(['git', 'rm', '--cached', f], capture_output=True)
    
    print('\nRemoved from git tracking')
else:
    print('\nNo files to remove')