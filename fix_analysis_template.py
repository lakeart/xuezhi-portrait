#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复 analysis/index.html 的结构问题"""

with open('app/templates/analysis/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到关键位置
# 1. 找到 </style> 标签的位置 (应该在 styles 块内)
style_close_idx = None
for i, line in enumerate(lines):
    if '</style>' in line:
        style_close_idx = i
        break

print("</style> 在行: %d" % (style_close_idx + 1))

# 2. 找到第一个 </style> 之后、多余 endblock 之前的 CSS 样式开始位置
# 这些CSS应该在 </style> 之前（它们是 styles 块的一部分）
css_start = None
for i, line in enumerate(lines):
    if style_close_idx and i > style_close_idx:
        stripped = line.strip()
        # CSS 规则以 . 或 # 开头
        if stripped.startswith('.') or stripped.startswith('#') or stripped.startswith('/*'):
            if css_start is None:
                css_start = i
                print("多余CSS开始于行: %d" % (css_start + 1))
        # 当遇到 {% endblock %} 时停止
        if '{% endblock %}' in line and css_start:
            print("多余 endblock 在行: %d" % (i + 1))
            break

# 3. 重新构建文件
# - styles 块应该在 </style> 之后继续（包含额外CSS）
# - 删除多余的 {% endblock %}

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 如果在 </style> 之后，发现了 {% endblock %} (行1396左右)，跳过它
    if style_close_idx and i > style_close_idx:
        stripped = line.strip()
        # 遇到 {% endblock %} 且下一行是 {% block scripts %} 就跳过
        if stripped == '{% endblock %}' and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if '{% block scripts %}' in next_line:
                i += 1
                continue
    
    # 跳过在 styles 块结束后、多余 endblock 之前的 CSS 行
    if css_start and i >= css_start:
        stripped = line.strip()
        if stripped == '{% endblock %}' or stripped.startswith('.') or stripped.startswith('#') or stripped.startswith('/*') or stripped == '' or stripped == '}':
            i += 1
            continue
        else:
            # 已经过了 CSS 部分，继续正常处理
            css_start = None
    
    new_lines.append(line)
    i += 1

# 写回文件
with open('app/templates/analysis/index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n修复完成！新文件共有 %d 行" % len(new_lines))
