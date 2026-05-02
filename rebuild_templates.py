#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重建所有被损坏的模板文件
"""

import os

# 智能问答页面
intelligent_assistant_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能问答 - 学智画像</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Noto Sans SC', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .chat-container { max-width: 800px; margin: 2rem auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .chat-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; text-align: center; }
        .chat-body { padding: 2rem; min-height: 400px; max-height: 500px; overflow-y: auto; }
        .chat-message { margin-bottom: 1rem; padding: 1rem; border-radius: 15px; animation: fadeIn 0.3s ease; }
        .chat-message.ai { background: #f0f0f0; }
        .chat-message.user { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-left: 20%; }
        .chat-input { padding: 1.5rem; border-top: 1px solid #eee; }
        .quick-questions { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .quick-btn { padding: 0.5rem 1rem; border: 2px solid #667eea; border-radius: 20px; background: white; color: #667eea; cursor: pointer; transition: all 0.3s; }
        .quick-btn:hover { background: #667eea; color: white; }
        .nav-link { color: white; text-decoration: none; padding: 0.5rem 1rem; }
        .nav-link:hover { color: #f0f0f0; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg" style="background: rgba(0,0,0,0.2);">
        <div class="container">
            <a class="navbar-brand text-white" href="/">
                <i class="fas fa-graduation-cap me-2"></i>学智画像
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">首页</a>
                <a class="nav-link" href="/intelligent-assistant">智能问答</a>
                <a class="nav-link" href="/test/assessment">能力测试</a>
                <a class="nav-link" href="/analysis/report">学习报告</a>
            </div>
        </div>
    </nav>

    <div class="chat-container">
        <div class="chat-header">
            <h2><i class="fas fa-robot me-2"></i>AI学习助手</h2>
            <p class="mb-0 opacity-75">基于知识库的智能问答系统</p>
        </div>
        <div class="chat-body" id="chatBody">
            <div class="chat-message ai">
                <strong><i class="fas fa-robot me-2"></i>AI助手：</strong>
                <p class="mb-0">您好！我是您的AI学习助手。我可以帮助您解答学习相关的问题，包括：</p>
                <ul class="mb-0 mt-2">
                    <li>学习规划和时间管理建议</li>
                    <li>知识点理解和记忆技巧</li>
                    <li>考试技巧和复习策略</li>
                    <li>学习方法推荐</li>
                </ul>
                <p class="mb-0 mt-2">请选择或输入您的问题：</p>
            </div>
        </div>
        <div class="chat-input">
            <div class="quick-questions">
                <button class="quick-btn" onclick="askQuestion('如何制定高效的学习计划？')">如何制定学习计划</button>
                <button class="quick-btn" onclick="askQuestion('知识点记不住怎么办？')">知识点记忆技巧</button>
                <button class="quick-btn" onclick="askQuestion('考试前如何有效复习？')">考试复习策略</button>
                <button class="quick-btn" onclick="askQuestion('如何提高学习效率？')">提高学习效率</button>
            </div>
            <div class="input-group">
                <input type="text" class="form-control" id="userInput" placeholder="输入您的问题..." onkeypress="if(event.key==='Enter')sendMessage()">
                <button class="btn btn-primary" onclick="sendMessage()">
                    <i class="fas fa-paper-plane me-2"></i>发送
                </button>
            </div>
        </div>
    </div>

    <script>
        const knowledgeBase = {
            '如何制定高效的学习计划？': '制定高效学习计划的建议：\\n\\n1. **明确目标**：设定清晰的短期和长期学习目标\\n2. **分解任务**：将大目标分解为可执行的小任务\\n3. **时间分配**：根据精力周期合理安排不同难度任务\\n4. **预留缓冲**：为意外情况预留调整时间\\n5. **定期复盘**：每周总结计划执行情况，及时调整',
            '知识点记不住怎么办？': '提高记忆效率的方法：\\n\\n1. **间隔重复**：使用艾宾浩斯遗忘曲线原理复习\\n2. **联想记忆**：将新知识与已知知识建立联系\\n3. **多感官学习**：视觉、听觉、动手结合\\n4. **主动回忆**：不看资料尝试回忆内容\\n5. **教授他人**：尝试向他人讲解来加深理解',
            '考试前如何有效复习？': '高效考试复习策略：\\n\\n1. **制定计划**：提前2-3周开始复习\\n2. **优先级排序**：先复习重点和薄弱环节\\n3. **真题练习**：多做历年考试真题\\n4. **模拟考试**：限时模拟真实考试环境\\n5. **保持状态**：保证充足睡眠和适度运动',
            '如何提高学习效率？': '提高学习效率的技巧：\\n\\n1. **番茄工作法**：25分钟专注学习，5分钟休息\\n2. **清除干扰**：关闭无关应用和通知\\n3. **番茄环境**：选择安静整洁的学习环境\\n4. **交替学习**：不同科目穿插学习\\n5. **及时奖励**：完成任务后给自己奖励'
        };

        function askQuestion(question) {
            document.getElementById('userInput').value = question;
            sendMessage();
        }

        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            const chatBody = document.getElementById('chatBody');
            
            // 添加用户消息
            chatBody.innerHTML += '<div class="chat-message user"><strong>您：</strong>' + message + '</div>';
            
            // 模拟AI思考
            setTimeout(() => {
                let response = '抱歉，我暂时无法回答这个问题。请尝试其他问题或联系管理员。';
                for (const [key, value] of Object.entries(knowledgeBase)) {
                    if (message.includes(key.split('？')[0]) || key.includes(message.split('？')[0])) {
                        response = value;
                        break;
                    }
                }
                
                chatBody.innerHTML += '<div class="chat-message ai"><strong><i class="fas fa-robot me-2"></i>AI助手：</strong><p class="mb-0">' + response.replace(/\\n/g, '<br>') + '</p></div>';
                chatBody.scrollTop = chatBody.scrollHeight;
            }, 500);
            
            input.value = '';
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    </script>
</body>
</html>
'''

# 学习报告页面
learning_report_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学习报告 - 学智画像</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body { font-family: 'Noto Sans SC', sans-serif; background: #f8fafc; }
        .report-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 3rem 0; margin-bottom: 2rem; }
        .stat-card { background: white; border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; transition: all 0.3s; }
        .stat-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.15); }
        .stat-card i { font-size: 2.5rem; color: #667eea; margin-bottom: 0.5rem; }
        .stat-card h3 { font-size: 2rem; font-weight: 700; color: #1e293b; }
        .chart-section { background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .section-title { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1.5rem; border-left: 4px solid #667eea; padding-left: 1rem; }
        .nav-link { color: white; text-decoration: none; padding: 0.5rem 1rem; opacity: 0.9; }
        .nav-link:hover { opacity: 1; color: white; }
        .recommendation { background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); border-left: 4px solid #667eea; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <div class="container">
            <a class="navbar-brand text-white" href="/">
                <i class="fas fa-graduation-cap me-2"></i>学智画像
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">首页</a>
                <a class="nav-link" href="/intelligent-assistant">智能问答</a>
                <a class="nav-link" href="/test/assessment">能力测试</a>
                <a class="nav-link" href="/analysis/report">学习报告</a>
                <a class="nav-link" href="/auth/login">登录</a>
            </div>
        </div>
    </nav>

    <div class="report-header">
        <div class="container text-center">
            <h1><i class="fas fa-chart-bar me-3"></i>学习分析报告</h1>
            <p class="lead opacity-75">全面了解您的学习状态和能力水平</p>
        </div>
    </div>

    <div class="container">
        <div class="row">
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="fas fa-clock"></i>
                    <h3 id="learningTime">0h</h3>
                    <p class="text-muted mb-0">累计学习时长</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="fas fa-check-circle"></i>
                    <h3 id="completionRate">0%</h3>
                    <p class="text-muted mb-0">任务完成率</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="fas fa-bullseye"></i>
                    <h3 id="accuracy">0%</h3>
                    <p class="text-muted mb-0">平均正确率</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card">
                    <i class="fas fa-trophy"></i>
                    <h3 id="rank">Top 0%</h3>
                    <p class="text-muted mb-0">学习排名</p>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-6">
                <div class="chart-section">
                    <h3 class="section-title">学习趋势</h3>
                    <div id="trendChart" style="width: 100%; height: 300px;"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-section">
                    <h3 class="section-title">能力雷达图</h3>
                    <div id="radarChart" style="width: 100%; height: 300px;"></div>
                </div>
            </div>
        </div>

        <div class="chart-section">
            <h3 class="section-title">个性化学习建议</h3>
            <div class="recommendation">
                <h5><i class="fas fa-lightbulb me-2 text-warning"></i>学习规划建议</h5>
                <p class="mb-0">建议您每天安排2-3小时的学习时间，保持规律的学习节奏。可以使用番茄工作法来提高专注度。</p>
            </div>
            <div class="recommendation">
                <h5><i class="fas fa-book me-2 text-info"></i>知识点掌握建议</h5>
                <p class="mb-0">建议加强编程基础和算法方面的练习，每天完成2-3道算法题目，逐步提高难度。</p>
            </div>
            <div class="recommendation">
                <h5><i class="fas fa-chart-line me-2 text-success"></i>考试技巧建议</h5>
                <p class="mb-0">建议考前两周开始系统复习，重点复习高频考点，多做模拟题来熟悉考试节奏。</p>
            </div>
        </div>
    </div>

    <script>
        // 学习趋势图表
        var trendChart = echarts.init(document.getElementById('trendChart'));
        trendChart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['学习时长(h)', '正确率(%)'] },
            xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
            yAxis: [
                { type: 'value', name: '学习时长', axisLabel: { formatter: '{value} h' } },
                { type: 'value', name: '正确率', axisLabel: { formatter: '{value} %' }, max: 100 }
            ],
            series: [
                { name: '学习时长(h)', type: 'bar', data: [2.5, 3.2, 2.8, 3.5, 2.0, 4.2, 3.8] },
                { name: '正确率(%)', type: 'line', yAxisIndex: 1, data: [72, 75, 78, 80, 76, 82, 85] }
            ]
        });

        // 能力雷达图
        var radarChart = echarts.init(document.getElementById('radarChart'));
        radarChart.setOption({
            tooltip: {},
            radar: {
                indicator: [
                    { name: '编程能力', max: 100 },
                    { name: '数学逻辑', max: 100 },
                    { name: '英语水平', max: 100 },
                    { name: '算法思维', max: 100 },
                    { name: '自习效率', max: 100 }
                ]
            },
            series: [{
                type: 'radar',
                data: [{ value: [78, 82, 75, 80, 85], name: '能力评分' }]
            }]
        });

        // 动态更新统计数据
        setTimeout(() => {
            animateNumber('learningTime', 156, 'h');
            animateNumber('completionRate', 87, '%');
            animateNumber('accuracy', 78, '%');
        }, 500);

        function animateNumber(id, target, suffix) {
            const el = document.getElementById(id);
            let current = 0;
            const step = target / 50;
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    el.textContent = target + suffix;
                    clearInterval(timer);
                } else {
                    el.textContent = Math.floor(current) + suffix;
                }
            }, 30);
        }
    </script>
</body>
</html>
'''

# 能力测试页面
assessment_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>能力测试 - 学智画像</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Noto Sans SC', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .test-container { max-width: 900px; margin: 2rem auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .test-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }
        .test-type-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; padding: 2rem; }
        .test-type-card { background: #f8fafc; border: 2px solid transparent; border-radius: 16px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.3s; }
        .test-type-card:hover { border-color: #667eea; transform: translateY(-5px); box-shadow: 0 10px 30px rgba(102,126,234,0.2); }
        .test-type-card i { font-size: 3rem; color: #667eea; margin-bottom: 1rem; }
        .test-type-card h4 { color: #1e293b; margin-bottom: 0.5rem; }
        .test-type-card p { color: #64748b; font-size: 0.9rem; margin-bottom: 0; }
        .nav-link { color: white; text-decoration: none; padding: 0.5rem 1rem; opacity: 0.9; }
        .nav-link:hover { opacity: 1; color: white; }
        .question-card { background: white; border-radius: 16px; padding: 2rem; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .option-btn { width: 100%; padding: 1rem; margin: 0.5rem 0; border: 2px solid #e2e8f0; border-radius: 10px; background: white; text-align: left; cursor: pointer; transition: all 0.3s; }
        .option-btn:hover { border-color: #667eea; background: rgba(102,126,234,0.05); }
        .option-btn.selected { border-color: #667eea; background: rgba(102,126,234,0.1); color: #667eea; }
        .progress-bar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg" style="background: rgba(0,0,0,0.2);">
        <div class="container">
            <a class="navbar-brand text-white" href="/">
                <i class="fas fa-graduation-cap me-2"></i>学智画像
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">首页</a>
                <a class="nav-link" href="/intelligent-assistant">智能问答</a>
                <a class="nav-link" href="/test/assessment">能力测试</a>
                <a class="nav-link" href="/analysis/report">学习报告</a>
            </div>
        </div>
    </nav>

    <div class="test-container" id="testContainer">
        <div class="test-header">
            <h2><i class="fas fa-clipboard-check me-2"></i>基础能力测试</h2>
            <p class="mb-0 opacity-75">选择测试类型，开始评估您的能力水平</p>
        </div>
        
        <div class="test-type-grid" id="testTypeGrid">
            <div class="test-type-card" onclick="startTest('programming')">
                <i class="fas fa-laptop-code"></i>
                <h4>编程基础</h4>
                <p>Python、Java等语言基础知识测试</p>
            </div>
            <div class="test-type-card" onclick="startTest('math')">
                <i class="fas fa-calculator"></i>
                <h4>数学逻辑</h4>
                <p>高数、线代、概率论等数学能力测试</p>
            </div>
            <div class="test-type-card" onclick="startTest('english')">
                <i class="fas fa-language"></i>
                <h4>英语能力</h4>
                <p>词汇、语法、阅读理解能力测试</p>
            </div>
            <div class="test-type-card" onclick="startTest('algorithm')">
                <i class="fas fa-brain"></i>
                <h4>算法思维</h4>
                <p>数据结构、算法设计能力测试</p>
            </div>
        </div>
    </div>

    <script>
        const questions = {
            programming: [
                { question: 'Python中如何定义一个列表？', options: ['list = []', 'list = {}', 'list = ()', 'list = <>'], answer: 0 },
                { question: '哪个不是Python的数据类型？', options: ['int', 'float', 'char', 'str'], answer: 2 },
                { question: '如何输出"Hello World"？', options: ['print("Hello World")', 'echo "Hello World"', 'printf("Hello World")', 'console.log("Hello World")'], answer: 0 }
            ],
            math: [
                { question: ' lim(x->0) sin(x)/x = ?', options: ['0', '1', '2', '无穷'], answer: 1 },
                { question: '矩阵AB=0，则？', options: ['A=0或B=0', 'A和B都为零矩阵', '|A|=0或|B|=0', '无法确定'], answer: 2 },
                { question: '正态分布的标准差为？', options: ['0', '1', '2', '不确定'], answer: 1 }
            ],
            english: [
                { question: '"Hello"的反义词是？', options: ['Hi', 'Goodbye', 'Yes', 'Please'], answer: 1 },
                { question: '"Apple"的中文意思是？', options: ['香蕉', '苹果', '橙子', '葡萄'], answer: 1 },
                { question: 'The quick brown fox jumps over the lazy dog.这句话有多少个单词？', options: ['8', '9', '10', '11'], answer: 2 }
            ],
            algorithm: [
                { question: '二分查找的时间复杂度是？', options: ['O(n)', 'O(log n)', 'O(n^2)', 'O(1)'], answer: 1 },
                { question: '栈的特点是？', options: ['FIFO', 'LIFO', '随机访问', '无特点'], answer: 1 },
                { question: '快速排序的平均时间复杂度是？', options: ['O(n)', 'O(n log n)', 'O(n^2)', 'O(log n)'], answer: 1 }
            ]
        };

        let currentTest = null;
        let currentQuestion = 0;
        let score = 0;

        function startTest(type) {
            currentTest = type;
            currentQuestion = 0;
            score = 0;
            
            const container = document.getElementById('testContainer');
            const qs = questions[type];
            
            container.innerHTML = '<div class="test-header"><h2><i class="fas fa-clipboard-check me-2"></i>' + getTypeName(type) + '测试</h2></div>' +
                '<div class="p-4"><div class="mb-3"><div class="d-flex justify-content-between mb-2"><span>进度</span><span id="progress">1/' + qs.length + '</span></div><div class="progress"><div class="progress-bar" id="progressBar" style="width: 0%"></div></div></div>' +
                '<div class="question-card" id="questionCard"></div></div>';
            
            showQuestion();
        }

        function showQuestion() {
            const qs = questions[currentTest];
            const q = qs[currentQuestion];
            
            document.getElementById('progress').textContent = (currentQuestion + 1) + '/' + qs.length;
            document.getElementById('progressBar').style.width = ((currentQuestion + 1) / qs.length * 100) + '%';
            
            let optionsHtml = q.options.map((opt, i) => 
                '<button class="option-btn" onclick="selectOption(' + i + ')">' + opt + '</button>'
            ).join('');
            
            document.getElementById('questionCard').innerHTML = '<h4 class="mb-4">' + (currentQuestion + 1) + '. ' + q.question + '</h4>' + optionsHtml;
        }

        function selectOption(index) {
            const q = questions[currentTest][currentQuestion];
            if (index === q.answer) score++;
            
            document.querySelectorAll('.option-btn').forEach((btn, i) => {
                btn.classList.remove('selected');
                if (i === q.answer) btn.style.borderColor = '#4ade80';
            });
            
            setTimeout(() => {
                currentQuestion++;
                if (currentQuestion < questions[currentTest].length) {
                    showQuestion();
                } else {
                    showResult();
                }
            }, 1000);
        }

        function showResult() {
            const total = questions[currentTest].length;
            const percentage = Math.round(score / total * 100);
            const level = percentage >= 90 ? '优秀' : percentage >= 70 ? '良好' : percentage >= 60 ? '及格' : '需努力';
            
            document.getElementById('testContainer').innerHTML = '<div class="test-header"><h2><i class="fas fa-trophy me-2"></i>测试完成！</h2></div>' +
                '<div class="text-center p-5"><h1 class="display-1 mb-3" style="color: #667eea;">' + percentage + '%</h1>' +
                '<h3 class="mb-4">您的水平：<span style="color: #667eea;">' + level + '</span></h3>' +
                '<p class="text-muted mb-4">答对 ' + score + ' / ' + total + ' 题</p>' +
                '<button class="btn btn-primary btn-lg me-2" onclick="location.reload()"><i class="fas fa-redo me-2"></i>再测一次</button>' +
                '<a href="/" class="btn btn-outline-primary btn-lg"><i class="fas fa-home me-2"></i>返回首页</a></div>';
        }

        function getTypeName(type) {
            const names = { programming: '编程基础', math: '数学逻辑', english: '英语能力', algorithm: '算法思维' };
            return names[type] || type;
        }
    </script>
</body>
</html>
'''

# 写入文件
files = {
    'd:/桌面/1/app/templates/intelligent_assistant/index.html': intelligent_assistant_html,
    'd:/桌面/1/app/templates/analysis/learning_report.html': learning_report_html,
    'd:/桌面/1/app/templates/test/assessment_pro.html': assessment_html
}

for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'[OK] Rebuilt: {filepath}')

print('\n[SUCCESS] All templates have been rebuilt!')
