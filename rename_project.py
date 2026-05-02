#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量替换项目名称"""

import os

# 替换规则
replacements = [
    ('学智画像：教育大数据赋能高校学情可视分析系统', '学智画像：教育大数据赋能高校学情可视分析系统'),
    ('学智画像：教育大数据赋能高校学情可视分析系统', '学智画像：教育大数据赋能高校学情可视分析系统'),
    ('学智画像', '学智画像'),
]

# 统计
total_replaced = 0
files_modified = []

for root, dirs, filenames in os.walk('.'):
    # 跳过不需要的目录
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'instance', 'node_modules']]
    
    for filename in filenames:
        # 只处理文本文件
        if not filename.endswith(('.py', '.html', '.md', '.txt', '.bat', '.js', '.json', '.yml', '.yaml')):
            continue
        
        filepath = os.path.join(root, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                count = sum(1 for old, _ in replacements if old in original)
                files_modified.append(filepath)
                total_replaced += 1
                print('已修改: %s' % filepath)
        except Exception as e:
            print('跳过 %s: %s' % (filepath, e))

print('\n完成！共修改 %d 个文件' % len(files_modified))
