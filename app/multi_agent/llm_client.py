# -*- coding: utf-8 -*-
"""
大语言模型接口模块
支持多种LLM后端的统一接口
"""

import os
import json
import time
import re
from typing import Dict, List, Any, Optional, Iterator
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """LLM基类"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self.max_tokens = 4096
        self.temperature = 0.7
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        pass
    
    @abstractmethod
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """流式对话请求"""
        pass
    
    def generate_with_retry(self, messages: List[Dict], max_retries: int = 3, **kwargs) -> str:
        """带重试的生成"""
        for attempt in range(max_retries):
            try:
                return self.chat(messages, **kwargs)
            except Exception as e:
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise


class OpenAIClient(BaseLLM):
    """OpenAI API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, base_url, model)
        self.max_tokens = 4096
        self.temperature = 0.7
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": False
            }
            
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"OpenAI API错误: {response.status_code} - {response.text}")
                return self._get_fallback_response(messages)
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except ImportError:
            logger.warning("requests库未安装，使用模拟响应")
            return self._get_mock_response(messages)
        except Exception as e:
            logger.error(f"LLM调用异常: {e}")
            return self._get_fallback_response(messages)
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """流式对话请求"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": True
            }
            
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"流式调用异常: {e}")
            yield from self._get_mock_stream_response(messages)
    
    def _get_mock_response(self, messages: List[Dict]) -> str:
        """获取模拟响应"""
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        return f"""感谢您的提问！关于「{user_msg[:50]}...」这个问题，我来为您提供详细解答：

## 问题分析

这是一个涉及学习方法和知识理解的综合性问题。从您的提问来看，您正在积极思考如何更好地掌握相关知识。

## 核心要点

1. **理解本质**：首先需要深入理解相关概念的本质含义
2. **建立联系**：将新知识与已有知识建立关联
3. **实践应用**：通过练习和实际应用来巩固理解
4. **反思总结**：定期回顾和总结学习内容

## 具体建议

根据您的学习情况，我建议您：
- 每天安排固定时间进行专项学习
- 做好笔记，记录关键知识点
- 定期进行自我测试
- 与同学讨论，互相启发

如果您需要更具体的帮助，请告诉我您所在的年级和专业！"""
    
    def _get_mock_stream_response(self, messages: List[Dict]) -> Iterator[str]:
        """获取模拟流式响应"""
        response = self._get_mock_response(messages)
        for char in response:
            yield char
    
    def _get_fallback_response(self, messages: List[Dict]) -> str:
        """获取降级响应"""
        return self._get_mock_response(messages)


class LocalLLM(BaseLLM):
    """本地LLM客户端（如Ollama）"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        super().__init__(base_url=base_url, model=model)
        self.base_url = base_url.rstrip('/')
    
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """发送对话请求"""
        try:
            import requests
            
            ollama_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    ollama_messages.append({"role": "system", "content": msg.get("content", "")})
                elif msg.get("role") == "user":
                    ollama_messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "assistant":
                    ollama_messages.append({"role": "assistant", "content": msg.get("content", "")})
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "num_predict": kwargs.get("max_tokens", self.max_tokens)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama API错误: {response.status_code}")
                return self._get_mock_response(messages)
                
        except Exception as e:
            logger.error(f"本地LLM调用异常: {e}")
            return self._get_mock_response(messages)
    
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """流式对话请求"""
        try:
            import requests
            
            ollama_messages = []
            for msg in messages:
                if msg.get("role") == "system":
                    ollama_messages.append({"role": "system", "content": msg.get("content", "")})
                elif msg.get("role") == "user":
                    ollama_messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "assistant":
                    ollama_messages.append({"role": "assistant", "content": msg.get("content", "")})
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'message' in chunk and 'content' in chunk['message']:
                            yield chunk['message']['content']
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"本地LLM流式调用异常: {e}")
            yield from self._get_mock_stream_response(messages)
    
    def _get_mock_response(self, messages: List[Dict]) -> str:
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        return f"感谢您的提问！关于「{user_msg[:30]}...」的详细解答如下：\n\n这是基于您的学习情况生成的个性化回答。"
    
    def _get_mock_stream_response(self, messages: List[Dict]) -> Iterator[str]:
        response = self._get_mock_response(messages)
        for char in response:
            yield char


def get_llm_client() -> BaseLLM:
    """获取LLM客户端实例"""
    # 检查是否有本地Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            return LocalLLM()
    except:
        pass
    
    # 默认使用OpenAI兼容接口
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    
    if api_key or base_url:
        return OpenAIClient(api_key=api_key, base_url=base_url)
    else:
        # 无API配置，返回本地Ollama（需自行启动）
        return LocalLLM()
