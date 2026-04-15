#!/usr/bin/env python3
import subprocess
import os

os.chdir('D:/openharness-enterprise')

# 获取远程仓库中根目录下的 .py 文件
result = subprocess.run(
    ['git', 'ls-tree', '-r', 'origin/master', '--name-only'],
    capture_output=True, text=True
)
all_files = result.stdout.strip().split('\n')

# 找出根目录下的 .py 文件
root_py_files = [
    f for f in all_files 
    if f.endswith('.py') 
    and not f.startswith('openharness/') 
    and not f.startswith('src/')
]

print(f'Found {len(root_py_files)} root-level .py files in remote:')
for f in root_py_files:
    print(f'  {f}')

# 从 Git 中移除这些文件
if root_py_files:
    for f in root_py_files:
        subprocess.run(['git', 'rm', '--cached', f], capture_output=True)
    
    print(f'\nRemoved {len(root_py_files)} files from Git tracking')
    
    # 显示状态
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    print('\nGit status:')
    print(result.stdout[:500])
else:
    print('No files to remove')