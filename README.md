# 学智画像：基于大模型的个性化资源生成与学习多智能体系统

面向中国大学生计算机设计大赛的高校计算机能力画像、知识库 RAG 与智能学习资源生成系统。

## 项目简介

本系统面向高校教师、学生和管理员三类用户，通过对话式学习画像、多智能体协同、知识库 RAG、个性化学习计划与学习资源生成，帮助教师精准掌握学生学习状态，帮助学生获得可信、可追溯、可执行的学习支持。

## 功能特性

### 管理员端
- 与教师端功能一致，可管理所有学生数据、题库和系统设置
- 适合系统管理维护角色使用

### 教师端
- **数据分析仪表盘**：实时查看学生参与度、正确率、用时等核心指标
- **学生群像分析**：可视化展示学生群体的能力分布与学习特征
- **知识点掌握分析**：掌握各知识点的学习情况，识别薄弱环节
- **高级分析功能**：
  - 学习风格聚类分析
  - 能力雷达图
  - 学习效率分析
  - 预测预警系统
- **学生管理**：查看学生答题详情，追踪学习轨迹
- **题库管理**：添加、编辑、删除题目

### 学生端
- **个人画像**：清晰了解自身计算机能力的优势与不足
- **智能问答助手**：AI 学习助手，解答学习疑问
- **知识库 RAG 问答**：支持 TXT/Markdown/CSV/JSON/DOCX/PDF 上传，自动解析、分块、语义检索，并生成带来源引用的可信回答
- **个性化学习计划**：基于个人能力画像的定制化学习路径
- **学习中心**：知识点学习、专项练习、错题复习

### 多智能体系统
- **ProfileBuilderAgent**：通过自然语言对话构建 10 维学习画像
- **KnowledgeBaseAgent**：管理课程资料上传、分块索引、TF-IDF 语义检索和 RAG 问答
- **ResourceGeneratorAgent**：生成课程讲义、思维导图、练习题、拓展阅读、视频脚本、代码实操
- **LearningPlannerAgent**：生成阶段化学习路径、周计划、甘特图/日历视图和动态调整建议
- **TutorAgent**：提供多轮问答、追问纠错和个性化解释
- **LearningEvaluatorAgent**：输出多维学习评估报告并反向更新画像/路径

## 技术栈

- **后端**：Python 3.9+ / Flask
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **前端**：HTML5 / CSS3 / JavaScript / Bootstrap 5
- **数据可视化**：Chart.js / ECharts
- **机器学习**：scikit-learn（学习风格聚类、预测模型）
- **知识库检索**：文档解析 + 分块索引 + TF-IDF 语义检索，可扩展到 ChromaDB/Milvus

## 目录结构

```
.
├── app/                       # 应用主目录
│   ├── __init__.py           # Flask应用工厂
│   ├── models/               # 数据模型 (User / Quiz / Feature)
│   ├── routes/               # 路由控制器 (auth / analysis / student / quiz / assistant)
│   ├── templates/            # Jinja2 模板
│   ├── utils/                # 工具函数
│   └── static/               # 静态资源
├── demo/                      # 讯飞智文PPT接口示例与诊断脚本
├── tests/                     # 单元测试
├── instance/                  # 实例数据（含 SQLite 数据库）
├── run.py                     # 开发环境入口
├── wsgi.py                    # 生产环境 WSGI 入口
├── set_db.py                  # 数据库初始化与测试数据生成
├── deploy.py                  # 部署脚本（支持 Gunicorn / Waitress）
├── take_screenshots.py        # 页面截图工具（供文档使用）
├── requirements.txt           # 完整 Python 依赖
├── requirements_light.txt     # 精简 Python 依赖（不含重型包）
├── Dockerfile                 # Docker 镜像配置
├── docker-compose.yml         # Docker 编排
├── nginx.conf                 # Nginx 反向代理配置
├── install.bat                # Windows 一键安装脚本
└── start.bat                  # Windows 一键启动脚本
```

## 快速部署

### 方式一：Windows本地部署

1. **安装Python**
   - 下载Python 3.9+：https://www.python.org/downloads/
   - 安装时勾选"Add Python to PATH"

2. **克隆/下载项目**
   ```bash
   cd 项目目录
   ```

3. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **初始化数据库**
   ```bash
   python set_db.py
   ```

6. **启动应用**
   ```bash
   python run.py
   ```

7. **访问应用**
   打开浏览器访问：http://127.0.0.1:5000

8. **查看赛题契合度演示页**
   打开：http://127.0.0.1:5000/competition-readiness
   该页面集中展示 A3 赛题要求、完成度、实现证据与下一步提升点，适合答辩和项目验收时快速说明优势。

### 方式二：使用启动脚本（Windows）

双击运行 `start.bat`，脚本会自动：
- 检查Python环境
- 安装依赖
- 初始化数据库
- 启动服务器

### 方式三：Docker部署（推荐生产环境）

1. **安装Docker**
   - 下载Docker Desktop：https://www.docker.com/products/docker-desktop

2. **构建并启动**
   ```bash
   docker-compose up -d
   ```

3. **访问应用**
   打开浏览器访问：http://localhost:80

## 默认账号

部署完成后可使用以下测试账号登录：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher | teacher123 |
| 学生 | student | student123 |

> 运行 `python set_db.py` 后会额外生成 50 个模拟学生账号（学号即密码）。

## 生产环境部署

### 使用Nginx反向代理

1. 修改 `nginx.conf` 中的配置（域名、SSL证书等）
2. 运行部署脚本：
   ```bash
   python deploy.py
   ```

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SECRET_KEY | Flask密钥 | dev-secret-key |
| FLASK_ENV | 运行环境 | development |
| DATABASE_URL | 数据库连接 | sqlite:///instance/quiz_system.db |

## 开发指南

### 运行测试
```bash
pytest tests/
```

### 使用精简依赖
如果不需要完整功能（如机器学习分析），可安装精简依赖：
```bash
pip install -r requirements_light.txt
```

## 项目特色

1. **赛题高度契合**：围绕 A3 赛题的对话式画像、多智能体协同、个性化资源生成、反幻觉问答展开
2. **知识库 RAG 闭环**：完成文件上传、文档解析、分块索引、语义检索、带引用回答的完整链路
3. **可视化学习规划**：学习路径支持时间线、甘特图、周日历三种视图，便于答辩演示与教学执行
4. **画像动态演进**：对话式画像更新后展示置信度、知识点覆盖、薄弱点、学习目标的前后变化
5. **移动端知识卡片**：自动将生成资源切片为手机端复习卡片，强化个性化资源生成的体验亮点
6. **数据智能优势明显**：融合 KMeans 聚类、雷达图、随机森林预警、学习行为画像等分析能力
7. **深色科技风 UI**：采用现代深色主题，突出多智能体节点、数据可视化与智能学习体验

## 参赛信息

- **赛事**：中国大学生计算机设计大赛
- **赛题**：A3 赛题
- **作品名称**：学智画像：基于大模型的个性化资源生成与学习多智能体系统

## 许可证

本项目仅供学习交流使用。

## 联系方式

如有问题，请通过以下方式联系：
- 提交Issue
- 发送邮件至项目维护者
