# 学智画像：教育大数据赋能高校学情可视分析系统

基于Python Flask的大学生计算机能力画像与智能学习分析系统。

## 项目简介

本系统旨在为高校教师和学生提供全方位的计算机能力分析与学习支持，通过数据可视化、智能问答、个性化学习计划等功能，帮助教师精准掌握学生学习状态，帮助学生了解自身能力画像并获得针对性的学习建议。

## 功能特性

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

### 学生端
- **个人画像**：清晰了解自身计算机能力的优势与不足
- **智能问答助手**：24小时在线的AI学习助手，解答学习疑问
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
├── app/                      # 应用主目录
│   ├── __init__.py          # Flask应用工厂
│   ├── models/              # 数据模型
│   │   ├── user.py          # 用户模型
│   │   ├── quiz.py          # 题目与答题模型
│   │   └── extra.py         # 扩展功能模型
│   ├── routes/              # 路由控制器
│   │   ├── analysis.py      # 数据分析路由
│   │   ├── student.py       # 学生相关路由
│   │   ├── intelligent_assistant.py  # 智能问答路由
│   │   └── ...
│   ├── templates/           # Jinja2模板
│   │   ├── index.html       # 首页
│   │   ├── analysis/        # 数据分析页面
│   │   ├── student/         # 学生页面
│   │   └── intelligent_assistant/  # 智能问答页面
│   ├── utils/               # 工具函数
│   └── static/              # 静态资源
├── instance/                 # 实例数据（含数据库）
├── tests/                    # 单元测试
├── run.py                    # 应用入口
├── requirements.txt          # Python依赖
├── Dockerfile                # Docker配置
├── docker-compose.yml         # Docker编排
├── nginx.conf                # Nginx配置
├── start.bat                 # Windows启动脚本
└── install.bat               # Windows安装脚本
```

## 快速部署

### 方式一：Windows本地部署

1. **安装Python**
   - 下载Python 3.9+：https://www.python.org/downloads/
   - 安装时勾选"Add Python to PATH"

2. **克隆/下载项目**
   ```bash
   cd d:\1
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
| 教师 | admin | admin123 |
| 学生 | student1 | password |
| 学生 | student2 | password |

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
# 或
python run_tests.py
```

### 重新构建模板（修改模板后）
```bash
python rebuild_templates.py
```

### 系统检查
```bash
python system_check.py
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
