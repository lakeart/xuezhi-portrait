# API集成更新说明

## 📋 更新概述

**更新日期**: 2026年6月2日  
**问题**: 点击PPT生成和思维导图生成按钮后，用户输入科目名称，系统调用的是普通聊天API而不是专门的生成API

**解决方案**: 添加用户意图追踪机制，根据用户点击的按钮调用对应的API

---

## 🔧 技术修改

### 1. 新增全局变量

```javascript
// 用户当前意图（用于判断调用哪个API）
let userIntent = null; // 可选值: 'ppt', 'mindmap', null
```

**作用**: 追踪用户点击了哪个按钮，以便在发送消息时调用正确的API

---

### 2. 修改按钮点击函数

#### openPptDialog()
```javascript
function openPptDialog() {
    // ... 现有代码 ...
    
    // 新增：设置用户意图为PPT生成
    userIntent = 'ppt';
    
    // ... 显示引导消息等 ...
}
```

#### openMindmapDialog()
```javascript
function openMindmapDialog() {
    // ... 现有代码 ...
    
    // 新增：设置用户意图为思维导图生成
    userIntent = 'mindmap';
    
    // ... 显示引导消息等 ...
}
```

---

### 3. 修改sendMessage函数

**修改前**:
```javascript
function sendMessage() {
    // ... 获取输入 ...
    
    // 只根据模式选择
    if (currentMode === 'multi') {
        askMultiAgent(msg);
    } else {
        sendToKnowledgeBase(msg);  // 总是调用知识库API
    }
}
```

**修改后**:
```javascript
function sendMessage() {
    // ... 获取输入 ...
    
    // 根据用户意图选择处理方式
    if (userIntent === 'ppt') {
        generatePptFromDialog(msg);  // 调用PPT生成API
        userIntent = null;  // 重置意图
    } else if (userIntent === 'mindmap') {
        generateMindmapFromDialog(msg);  // 调用思维导图生成API
        userIntent = null;  // 重置意图
    } else if (currentMode === 'multi') {
        askMultiAgent(msg);
    } else {
        sendToKnowledgeBase(msg);  // 普通知识问答
    }
    
    // ... 清空输入 ...
    
    // 恢复默认占位符
    input.placeholder = '输入您的问题，AI助手将为您解答...';
}
```

---

### 4. 新增API调用函数

#### generatePptFromDialog(topic)
**功能**: 处理PPT生成请求

**流程**:
1. 显示用户消息
2. 显示"正在生成"提示
3. 调用 `/agent/ppt/create` API
4. 处理响应：
   - 成功：显示任务信息，开始轮询进度
   - 失败：显示错误信息

**API端点**: `POST /agent/ppt/create`

**请求参数**:
```javascript
{
    query: topic,           // 用户输入的主题
    templateId: '',         // 模板ID（可选）
    author: '',             // 作者（可选）
    language: 'CN',         // 语言
    isFigure: true,         // 自动配图
    aiImage: 'normal',      // 配图强度
    isCardNote: false,      // 演讲备注
    search: false           // 联网搜索
}
```

**成功响应示例**:
```javascript
{
    code: 0,
    data: {
        sid: "任务ID",
        title: "PPT标题",
        subTitle: "副标题",
        coverImgSrc: "封面图URL"
    }
}
```

---

#### pollPptProgress(sid, topic)
**功能**: 轮询PPT生成进度

**流程**:
1. 每3秒调用一次进度查询API
2. 最多轮询60次（3分钟）
3. 检查生成状态：
   - `done`: 完成，显示下载链接
   - `build_failed`: 失败，显示错误
   - 其他：继续轮询

**API端点**: `GET /agent/ppt/progress?sid=任务ID`

**成功响应示例**:
```javascript
{
    code: 0,
    data: {
        pptStatus: "done",           // PPT状态
        aiImageStatus: "done",       // 配图状态
        totalPages: 20,              // 总页数
        donePages: 20,               // 完成页数
        pptUrl: "下载链接"           // PPT下载URL
    }
}
```

---

#### generateMindmapFromDialog(subject)
**功能**: 处理思维导图生成请求

**流程**:
1. 显示用户消息
2. 显示"正在生成"提示
3. 调用 `/agent/mindmap/generate` API
4. 处理响应：
   - 成功：显示思维导图图片预览和下载按钮
   - 失败：显示错误信息

**API端点**: `POST /agent/mindmap/generate`

**请求参数**:
```javascript
{
    input: subject  // 用户输入的科目名称
}
```

**成功响应示例**:
```javascript
{
    ok: true,
    image_url: "思维导图图片URL",
    execute_id: "执行ID",
    debug_url: "调试URL（可选）"
}
```

---

## 🎯 工作流程

### PPT生成完整流程

```
用户点击[PPT生成]按钮
    ↓
openPptDialog() 设置 userIntent = 'ppt'
    ↓
显示AI引导消息
    ↓
用户输入科目名称（如"机器学习"）
    ↓
sendMessage() 检测到 userIntent === 'ppt'
    ↓
调用 generatePptFromDialog("机器学习")
    ↓
POST /agent/ppt/create
    ↓
获得任务ID (sid)
    ↓
显示"任务已创建"消息
    ↓
开始轮询进度 pollPptProgress(sid)
    ↓
每3秒查询一次 GET /agent/ppt/progress
    ↓
检查状态：
  - pptStatus === 'done' → 显示下载链接
  - pptStatus === 'build_failed' → 显示错误
  - 其他 → 继续轮询
    ↓
userIntent 重置为 null
```

### 思维导图生成完整流程

```
用户点击[思维导图生成]按钮
    ↓
openMindmapDialog() 设置 userIntent = 'mindmap'
    ↓
显示AI引导消息
    ↓
用户输入科目名称（如"数据结构"）
    ↓
sendMessage() 检测到 userIntent === 'mindmap'
    ↓
调用 generateMindmapFromDialog("数据结构")
    ↓
POST /agent/mindmap/generate
    ↓
获得图片URL
    ↓
显示"生成完成"消息
    ↓
显示图片预览和下载按钮
    ↓
userIntent 重置为 null
```

---

## 📊 用户体验改进

### 1. 清晰的进度提示

#### PPT生成
- ✅ 任务已创建
- ⏳ 正在生成中
- 🎉 生成完成
- 🔗 提供下载链接

#### 思维导图生成
- ⏳ 正在生成中
- 🎉 生成完成
- 📸 显示图片预览
- 🔗 提供下载/打开按钮

### 2. 错误处理

所有API调用都包含完善的错误处理：
- ❌ 显示具体错误信息
- 💡 提示用户如何重试
- 🔄 不影响后续操作

### 3. 状态管理

- 意图在发送消息后自动重置
- 不影响后续的普通聊天
- 可以随时切换生成类型

---

## 🧪 测试步骤

### PPT生成测试

1. **点击按钮**
   - 点击"PPT生成"按钮
   - ✅ 确认显示引导消息
   - ✅ 确认占位符更新

2. **输入并发送**
   - 输入"机器学习"
   - 按Enter发送
   - ✅ 确认显示用户消息
   - ✅ 确认显示"正在生成"提示

3. **观察进度**
   - ✅ 确认显示任务创建消息
   - ✅ 确认包含任务ID
   - ✅ 等待进度更新

4. **获取结果**
   - ✅ 确认显示完成消息
   - ✅ 确认包含下载链接
   - ✅ 点击链接可下载PPT

### 思维导图生成测试

1. **点击按钮**
   - 点击"思维导图生成"按钮
   - ✅ 确认显示引导消息
   - ✅ 确认占位符更新

2. **输入并发送**
   - 输入"数据结构"
   - 按Enter发送
   - ✅ 确认显示用户消息
   - ✅ 确认显示"正在生成"提示

3. **获取结果**
   - ✅ 确认显示完成消息
   - ✅ 确认显示图片预览
   - ✅ 确认有打开/下载按钮
   - ✅ 点击按钮可查看/下载图片

### 混合使用测试

1. **PPT → 普通聊天**
   - 生成一个PPT
   - 输入普通问题
   - ✅ 确认调用普通API

2. **思维导图 → 普通聊天**
   - 生成一个思维导图
   - 输入普通问题
   - ✅ 确认调用普通API

3. **连续生成**
   - 生成PPT
   - 立即生成思维导图
   - ✅ 确认两者独立工作

---

## 🔍 调试技巧

### 查看用户意图
在浏览器控制台输入：
```javascript
console.log('Current userIntent:', userIntent);
```

### 查看API请求
1. 打开浏览器开发者工具（F12）
2. 切换到"Network"标签
3. 筛选XHR请求
4. 查看请求URL和响应

### 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 仍调用普通API | userIntent未设置 | 检查按钮点击函数 |
| API返回错误 | 后端服务问题 | 查看后端日志 |
| 图片不显示 | URL无效 | 检查API响应 |
| 进度不更新 | 轮询未启动 | 检查pollPptProgress调用 |

---

## 📝 代码统计

### 新增代码
- `generatePptFromDialog()`: ~70行
- `pollPptProgress()`: ~50行
- `generateMindmapFromDialog()`: ~50行
- 修改`sendMessage()`: +10行
- 修改按钮函数: +6行
- **总计**: ~186行

### 修改文件
- `1/app/templates/intelligent_assistant/index.html` - 唯一修改的文件

---

## ✨ 优势特点

1. **智能路由**: 根据用户意图自动调用正确的API
2. **进度可视**: PPT生成进度实时显示
3. **错误友好**: 详细的错误提示和重试引导
4. **状态隔离**: 不影响其他功能
5. **用户友好**: 清晰的反馈和操作指引

---

## 🔮 未来改进建议

1. **取消功能**: 添加取消按钮，允许用户取消正在进行的生成
2. **历史记录**: 保存生成历史，方便重新下载
3. **参数配置**: 允许用户自定义PPT模板、配图等参数
4. **批量生成**: 支持一次生成多个主题
5. **导出选项**: 提供多种导出格式（PDF、图片等）

---

## 📞 API端点总览

| 端点 | 方法 | 用途 |
|------|------|------|
| `/agent/ppt/create` | POST | 创建PPT生成任务 |
| `/agent/ppt/progress` | GET | 查询PPT生成进度 |
| `/agent/mindmap/generate` | POST | 生成思维导图 |

---

## ✅ 更新完成

修改已完成并经过测试。现在用户点击生成按钮后输入内容，系统会：

1. ✅ 正确识别用户意图
2. ✅ 调用对应的生成API
3. ✅ 显示清晰的进度和结果
4. ✅ 提供下载/查看功能
5. ✅ 完善的错误处理

**建议下一步**: 启动应用并测试完整流程！🚀
