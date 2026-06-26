# A3 开源组件与协议说明

## 1. 说明目的

根据赛题要求，项目开发过程中若使用开源项目、前沿 AI 工具或框架，需要在显著位置标注名称、来源与相关协议要求。本文件用于整理当前项目中已明确可识别的主要组件。

## 2. 主要组件清单

| 组件 | 用途 | 来源 | 协议/备注 |
| --- | --- | --- | --- |
| Flask | Web 后端框架 | https://palletsprojects.com/p/flask/ | BSD 风格开源协议，商用友好 |
| Flask-SQLAlchemy | ORM 集成 | https://flask-sqlalchemy.palletsprojects.com/ | 基于 SQLAlchemy 生态 |
| Flask-Login | 登录鉴权 | https://flask-login.readthedocs.io/ | 开源组件 |
| Flask-WTF | 表单与 CSRF | https://flask-wtf.readthedocs.io/ | 开源组件 |
| SQLAlchemy | 数据库 ORM | https://www.sqlalchemy.org/ | MIT License |
| pandas | 数据处理 | https://pandas.pydata.org/ | BSD 3-Clause |
| numpy | 数值计算 | https://numpy.org/ | BSD 3-Clause |
| scikit-learn | 机器学习与 TF-IDF 检索 | https://scikit-learn.org/ | BSD 3-Clause |
| PyPDF2 | PDF 解析 | https://pypdf2.readthedocs.io/ | 开源组件 |
| requests | HTTP 调用 | https://requests.readthedocs.io/ | Apache 2.0 |
| Bootstrap | 页面样式基础 | https://getbootstrap.com/ | MIT License |
| Font Awesome | 图标 | https://fontawesome.com/ | 使用时需按官方说明处理版本和授权 |
| ECharts | 数据可视化图表 | https://echarts.apache.org/ | Apache 2.0 |

## 3. 外部服务与工具说明

| 服务/工具 | 当前用途 | 说明 |
| --- | --- | --- |
| 科大讯飞相关接口 | PPT、视频、问答等多模态能力接入 | 需在正式文档中进一步补充账号来源、调用边界与配置说明 |
| Coze 相关接口 | 课程文档与题库等生成能力 | 需在正式提交文档中明确使用方式与配置要求 |

## 4. 当前处理建议

1. 在最终版开发说明书中保留本表格，并根据实际使用情况补充精确版本号。
2. 对外部服务接口补“调用位置、环境变量、依赖条件、演示环境要求”。
3. 如果最终提交中包含第三方素材、模板或字体，需要单独增加素材来源页。

## 5. 当前未完全补齐项

1. 尚未统一整理所有前端 CDN 的精确版本和官网链接。
2. 尚未补全所有外部接口的授权来源和使用范围说明。
3. 尚未整理最终答辩 PPT 中的“开源与工具声明”页。
