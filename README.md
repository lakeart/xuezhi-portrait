# 学智画像：教育大数据赋能高校学情可视分析系统

基于 Python Flask 的大学生计算机能力画像与智能学习分析系统。

## 项目简介

本系统面向高校教师、学生和管理员三类用户，通过数据可视化、智能问答、个性化学习计划等功能，帮助教师精准掌握学生学习状态，帮助学生了解自身能力画像并获得针对性的学习建议。

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
- **个性化学习计划**：基于个人能力画像的定制化学习路径
- **学习中心**：知识点学习、专项练习、错题复习

## 技术栈

- **后端**：Python 3.9+ / Flask
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **前端**：HTML5 / CSS3 / JavaScript / Bootstrap 5
- **数据可视化**：Chart.js / ECharts
- **机器学习**：scikit-learn（学习风格聚类、预测模型）

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

1. **深色科技风UI**：采用现代深色主题，配合蓝色渐变，营造专业的技术氛围
2. **响应式设计**：适配桌面端和移动端，提供一致的用户体验
3. **实时数据更新**：图表数据自动刷新，随时掌握最新动态
4. **智能推荐**：基于机器学习的个性化学习建议
5. **全中文界面**：符合国内用户习惯，无需切换语言

## 参赛信息

- **赛事**：中国大学生计算机设计大赛（2026）
- **类别**：大数据应用
- **作品名称**：大学生计算机能力画像与智能学习分析系统

## 许可证

本项目仅供学习交流使用。

## 联系方式

如有问题，请通过以下方式联系：
- 提交Issue
- 发送邮件至项目维护者
