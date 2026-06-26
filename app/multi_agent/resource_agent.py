# -*- coding: utf-8 -*-
"""
资源生成智能体
多智能体协同生成5种以上个性化学习资源
"""

import json
import re
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from . import LearningResource, ResourceType, StudentProfile, ContentSafetyFilter, HallucinationDetector
from .llm_client import get_llm_client


class ResourceGeneratorAgent:
    """资源生成智能体 - 专业资源生成"""
    
    SYSTEM_PROMPTS = {
        ResourceType.COURSE_DOCUMENT: """你是一位资深的教育专家，擅长编写清晰、深入的专业课程讲解文档。

## 任务
根据学生画像和指定知识点，生成高质量的课程讲解文档。

## 要求
1. 内容要专业、准确、深入浅出
2. 结构清晰，包含：概述、核心概念、详细讲解、实例、应用场景
3. 使用markdown格式，支持代码块、表格、列表
4. 结合学生认知风格调整表达方式
5. 适当引入前沿知识和拓展内容
6. 内容长度适中（800-1500字）

## 输出格式
```markdown
# [知识点名称]

## 概述
[一句话概括]

## 核心概念
[核心定义和原理]

## 详细讲解
[深入分析]

## 实例解析
[具体例子]

## 应用场景
[实际应用]

## 拓展阅读
[推荐资源]
```""",

        ResourceType.MIND_MAP: """你是一个专业的知识可视化专家，擅长设计思维导图。

## 任务
根据知识点生成Mermaid格式的思维导图代码。

## 要求
1. 涵盖知识点的核心要素和关联关系
2. 层级结构清晰，一般3-4层
3. 每个分支使用简洁关键词
4. 使用Mermaid思维导图语法
5. 包含足够的细节但不过于冗余

## Mermaid语法
```mermaid
mindmap
  root((主题))
    分支1
      子分支1
      子分支2
    分支2
      子分支3
      子分支4
```

## 注意事项
- 根节点是核心主题
- 每个主分支是一个主要类别
- 子分支是具体内容
- 保持简洁，每个节点1-5个词""",

        ResourceType.EXERCISES: """你是一位经验丰富的出题专家，负责生成高质量的练习题目。

## 任务
根据学生画像和知识点，生成针对性的练习题目。

## 要求
1. 题目类型多样化：选择题、填空题、判断题、简答题、编程题
2. 难度分层：基础题、中等题、进阶题
3. 每种类型至少2-3道题
4. 包含详细解析
5. 答案要准确无误
6. 题目要契合学生的认知风格和学习水平

## 输出格式
```json
{
  "exercises": [
    {
      "type": "选择题",
      "difficulty": "中等",
      "question": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "explanation": "解析"
    }
  ]
}
```

## 难度说明
- 基础题：考察基本概念和定义
- 中等题：考察理解和简单应用
- 进阶题：考察综合应用和创新思维""",

        ResourceType.EXTENDED_READING: """你是一位学术导师，负责推荐高质量的拓展阅读材料。

## 任务
根据学生画像和当前学习内容，推荐相关的拓展阅读资源。

## 要求
1. 推荐3-5个高质量资源
2. 每种资源包含：类型、标题、推荐理由、适合程度
3. 类型包括：书籍、论文、文章、视频、在线课程
4. 资源要权威、实用、与时俱进
5. 考虑学生的兴趣方向和学习水平

## 输出格式
```markdown
## 拓展阅读推荐

### 1. [资源1]
- **类型**：书籍/论文/文章/视频
- **推荐理由**：...
- **适合程度**：入门/进阶/深入
- **获取链接**：...

### 2. [资源2]
...
```""",

        ResourceType.VIDEO_SCRIPT: """你是一位专业的教学视频内容策划，擅长创作生动有趣的短视频脚本。

## 任务
根据知识点和学生特点，创作教学视频/动画脚本。

## 要求
1. 时长控制在3-5分钟
2. 脚本要生动有趣，吸引注意力
3. 结构：开场引入 -> 核心讲解 -> 案例演示 -> 总结回顾
4. 配合视觉提示说明
5. 口语化表达，适合讲解
6. 适当使用比喻和类比

## 输出格式
```markdown
# 视频标题

## 基本信息
- 时长：3分钟
- 类型：知识讲解/动画演示/实操展示

## 分镜脚本

### 镜头1：[开场]
- **画面**：...
- **旁白**：...

### 镜头2：[核心概念]
- **画面**：...
- **旁白**：...

### 镜头3：[案例演示]
- **画面**：...
- **旁白**：...

### 镜头4：[总结]
- **画面**：...
- **旁白**：...
```""",

        ResourceType.CODE_PRACTICE: """你是一位资深程序员和教育者，负责设计代码实操案例。

## 任务
根据知识点设计代码实操案例，帮助学生通过实践掌握知识。

## 要求
1. 案例要实用、有趣、有挑战性
2. 提供完整的代码示例
3. 包含详细注释和解释
4. 分步骤指导
5. 提供进阶挑战题目
6. 代码要规范、易读

## 输出格式
```markdown
# 实操案例：[案例名称]

## 案例目标
[学习目标]

## 预备知识
[需要的知识]

## 代码实现
```[语言]
[代码]
```

## 代码解析
[逐行解析]

## 运行结果
[预期输出]

## 进阶挑战
[拓展练习]
```"""
    }
    
    def __init__(self):
        self.llm = get_llm_client()
        self.generated_resources: List[LearningResource] = []
    
    def generate_resource(
        self,
        resource_type: ResourceType,
        topic: str,
        profile: StudentProfile,
        additional_context: Dict = None
    ) -> LearningResource:
        """生成单个资源"""
        
        # 构建提示
        prompt = self._build_prompt(resource_type, topic, profile, additional_context)
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPTS.get(resource_type, "")},
            {"role": "user", "content": prompt}
        ]
        
        try:
            content = self.llm.chat(messages, temperature=0.7)
        except Exception as e:
            content = self._get_fallback_content(resource_type, topic)
        
        # 内容安全检查
        is_safe, reason = ContentSafetyFilter.filter(content)
        if not is_safe:
            content = f"[内容已过滤]{reason}"
        
        # 幻觉检测
        is_factual, warnings = HallucinationDetector.check_factuality(content, topic)
        if not is_factual:
            content += f"\n\n> ⚠️ 注意：{warnings[0]}"
        
        # 清理内容
        content = ContentSafetyFilter.sanitize(content)
        
        # 创建资源对象
        resource = LearningResource(
            resource_id=str(uuid.uuid4()),
            resource_type=resource_type,
            title=f"{topic} - {resource_type.value}",
            content=content,
            target_topics=[topic],
            difficulty=self._estimate_difficulty(profile),
            estimated_time=self._estimate_time(resource_type),
            source_agent=AgentRole.RESOURCE_GENERATOR.value,
            generated_at=datetime.now().isoformat()
        )
        
        self.generated_resources.append(resource)
        return resource
    
    def generate_all_resources(
        self,
        topics: List[str],
        profile: StudentProfile,
        resource_types: List[ResourceType] = None
    ) -> Dict[ResourceType, LearningResource]:
        """生成多种资源"""
        
        if resource_types is None:
            resource_types = list(ResourceType)
        
        results = {}
        
        for topic in topics:
            for resource_type in resource_types:
                try:
                    resource = self.generate_resource(resource_type, topic, profile)
                    results[resource_type] = resource
                except Exception as e:
                    # 单个资源生成失败不影响其他资源
                    pass
        
        return results
    
    def generate_code_practice(
        self,
        topic: str,
        profile: StudentProfile,
        programming_language: str = "Python"
    ) -> LearningResource:
        """专门生成代码实操案例"""
        
        additional_context = {"language": programming_language}
        return self.generate_resource(
            ResourceType.CODE_PRACTICE,
            topic,
            profile,
            additional_context
        )
    
    def _build_prompt(
        self,
        resource_type: ResourceType,
        topic: str,
        profile: StudentProfile,
        additional_context: Dict = None
    ) -> str:
        """构建生成提示"""
        
        context_parts = [
            f"## 学生信息",
            f"- 用户名：{profile.username}",
            f"- 认知风格：{profile.cognitive_style}",
            f"- 学习速度：{profile.learning_speed}",
            f"- 兴趣方向：{', '.join(profile.interests) if profile.interests else '待了解'}",
            f"- 目标：{', '.join(profile.goals) if profile.goals else '待了解'}",
            f"- 薄弱知识点：{', '.join(profile.weak_topics[:3]) if profile.weak_topics else '待评估'}",
            f"",
            f"## 待生成资源",
            f"- 类型：{resource_type.value}",
            f"- 主题：{topic}",
        ]
        
        if additional_context:
            context_parts.append(f"- 附加信息：{json.dumps(additional_context, ensure_ascii=False)}")
        
        return "\n".join(context_parts)
    
    def _estimate_difficulty(self, profile: StudentProfile) -> str:
        """估算难度等级"""
        # 基于认知风格和学习速度估算
        if profile.learning_speed == 'fast':
            return 'hard'
        elif profile.learning_speed == 'slow':
            return 'easy'
        return 'medium'
    
    def _estimate_time(self, resource_type: ResourceType) -> int:
        """估算学习时间（分钟）"""
        time_map = {
            ResourceType.COURSE_DOCUMENT: 15,
            ResourceType.MIND_MAP: 10,
            ResourceType.EXERCISES: 20,
            ResourceType.EXTENDED_READING: 30,
            ResourceType.VIDEO_SCRIPT: 5,
            ResourceType.CODE_PRACTICE: 45
        }
        return time_map.get(resource_type, 20)
    
    def _get_fallback_content(self, resource_type: ResourceType, topic: str) -> str:
        """获取降级内容"""
        fallbacks = {
            ResourceType.COURSE_DOCUMENT: f"""# {topic}

## 概述
本章节将介绍{topic}的核心概念和应用。

## 核心概念
{topic}是计算机科学中的重要基础知识点，涉及理论理解和实践应用。

## 详细讲解
### 基本原理
{topic}的基本原理包括...
### 关键特性
1. 特性一
2. 特性二
3. 特性三

## 实例解析
```python
# {topic} 示例代码
def example():
    pass
```

## 应用场景
{topic}广泛应用于...
""",
            ResourceType.MIND_MAP: """```mermaid
mindmap
  root((主题))
    基础知识
      概念1
      概念2
      概念3
    核心原理
      原理1
      原理2
    实际应用
      应用1
      应用2
    扩展内容
      进阶1
      进阶2
```""",
            ResourceType.EXERCISES: """{
  "exercises": [
    {
      "type": "选择题",
      "difficulty": "中等",
      "question": "关于{topic}，以下说法正确的是？",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "explanation": "详细解析..."
    }
  ]
}""",
            ResourceType.EXTENDED_READING: """## 拓展阅读推荐

### 1. 经典教材
- **推荐理由**：系统性学习
- **适合程度**：入门/进阶

### 2. 在线课程
- **推荐理由**：视频讲解更直观
- **适合程度**：入门
""",
            ResourceType.VIDEO_SCRIPT: """# 视频标题

## 基本信息
- 时长：3分钟
- 类型：知识讲解

## 分镜脚本

### 镜头1：开场
- **画面**：相关图片引入
- **旁白**：今天我们来学习...

### 镜头2：核心概念
- **画面**：图文结合讲解
- **旁白**：核心要点说明...

### 镜头3：总结
- **画面**：回顾要点
- **旁白**：总结今日学习内容
""",
            ResourceType.CODE_PRACTICE: """# 实操案例

## 案例目标
通过实践掌握{topic}

## 代码实现
```python
# 练习代码
def practice():
    # 你的代码
    pass
```

## 进阶挑战
尝试扩展功能...
"""
        }
        
        return fallbacks.get(resource_type, f"关于{topic}的学习内容正在生成中...").format(topic=topic)
    
    def get_generated_resources(self) -> List[Dict]:
        """获取所有已生成的资源"""
        return [r.to_card() for r in self.generated_resources]
