#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量生成演示视频片段"""

import subprocess
import time
import json

token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJteWZFenA3ODNLaV9KQ3g4Vm5jM1hfaXg2alpyYjZDZjVPTWtHWk1QSTNzIn0.eyJleHAiOjE4MDg2NTM5NTQsImlhdCI6MTc3Nzc5NjA0NCwiYXV0aF90aW1lIjoxNzc3MTE3OTU0LCJqdGkiOiI2ODU3NzA5Ny1kNDNkLTQ1YjctOTZlMy0xMGVkNTAzMWI2ZjEiLCJpc3MiOiJodHRwczovL3d3dy5jb2RlYnVkZHkuY24vYXV0aC9yZWFsbXMvY29waWxvdCIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI4ZGYzYmYyNi04ZWZhLTRlZTQtYWQ1Mi04NzBmZTllNGFhNjgiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJjb25zb2xlIiwic2lkIjoiODEzOTViZWItZDlmZC00YzRhLWJjZGQtNzdjM2I2ZWNiNDlkIiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgb2ZmbGluZV9hY2Nlc3MgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5pY2tuYW1lIjoiTGFrZWFydCIsInByZWZlcnJlZF91c2VybmFtZSI6IjEzODY3NzU4MDU1In0.tKsOjaTjI-hmz-JWzXNE1EeRU4XuAPTjhch0THIjxjk-i6rd8Hb_kLWRXLpA7oof8IUkwHcCe4-bKcX87S6rDGAwcfREN0XMdmaxe1bqs76W_B0X3fsYca2O5quyRjVuRStj35mohC2xuiS2_aMWjGpyuci0_jtgThc-63Br1Ne_JjxmaafwtasiTQf01gFPaWO8S2TL5_t_ahFB8GE3CPELMxrtQx8N277F06jfNVaO74og3W0wsEoWsudC6oD3Tu7rcV3w94kmgOrVk7wBFqdXtD_WANyXfC_VrQMDaNdaFwA6GzvQ716SpIHCZ6JuIZg2cSjslFcNPYSvt_SRxA'

script = r'd:\Program Files\CodeBuddy CN\resources\app\extensions\genie\out\extension\builtin\buddy-multimodal-generation\scripts\buddy-cloud.py'

prompts = [
    ('视频片段1-科技仪表盘', '深色界面上的教育数据可视化仪表盘，彩色图表和统计数据动画，深蓝色科技风格界面'),
    ('视频片段2-雷达图', '炫酷的学生能力雷达图在深色背景上慢慢展开动画，不同颜色标注各维度，科技感十足'),
    ('视频片段3-智能问答', '现代AI智能问答界面，对话气泡动画，智能助手回复效果，深色科技风格'),
    ('视频片段4-学习计划', '个性化学习计划界面，时间轴和进度条动画，学生学习路径可视化'),
]

results = []

for name, prompt in prompts:
    print(f'\n正在生成 {name}...')
    print(f'提示词: {prompt[:30]}...')
    
    # 提交任务
    result = subprocess.run(
        ['python', script, 'video', prompt, '--token', token],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    output = result.stdout + result.stderr
    print(f'提交响应: {output[:200]}')
    
    # 提取 job_id
    job_id = None
    for line in output.split('\n'):
        if '"job_id"' in line:
            try:
                data = json.loads(line.strip())
                job_id = data.get('job_id')
            except:
                pass
    
    if job_id:
        print(f'Job ID: {job_id}')
        # 等待完成
        for i in range(60):
            time.sleep(5)
            status_result = subprocess.run(
                ['python', script, 'status', job_id, '--type', 'video', '--token', token],
                capture_output=True,
                text=True
            )
            status_output = status_result.stdout + status_result.stderr
            
            if 'DONE' in status_output:
                # 提取 URL
                for line in status_output.split('\n'):
                    if 'result_url' in line:
                        try:
                            data = json.loads(line.strip())
                            url = data.get('result_url', '')
                            results.append({'name': name, 'url': url})
                            print(f'成功: {name}')
                            print(f'URL: {url[:80]}...')
                        except:
                            pass
                break
            elif 'FAIL' in status_output:
                print(f'失败: {name}')
                break
            print(f'等待中... {(i+1)*5}秒')
    else:
        print(f'未能获取 Job ID')

print('\n========== 生成结果 ==========')
for r in results:
    print(f'{r["name"]}: {r["url"]}')

print(f'\n共生成 {len(results)} 个视频片段')
