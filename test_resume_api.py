#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历生成API测试脚本
"""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

import requests


# 硬编码的讯飞API密钥（与后端保持一致）
XFYUN_RESUME_APP_ID = "f338fad9"
XFYUN_RESUME_API_SECRET = "ZDJlMTJlNzE2NjViNGE5M2YzYmIxMjUw"
XFYUN_RESUME_API_KEY = "e4c1da00d265ae704d875bbf508e7e68"


def _rfc1123_utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')


def _assemble_xfyun_auth_url(hosturl: str, api_key: str, api_secret: str, method: str = "POST") -> str:
    parsed = urlparse(hosturl)
    date = _rfc1123_utc_now()

    signature_origin = "\n".join([
        f"host: {parsed.netloc}",
        f"date: {date}",
        f"{method.upper()} {parsed.path} HTTP/1.1",
    ])

    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", '
        f'signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({
        "host": parsed.netloc,
        "date": date,
        "authorization": authorization
    })

    return urlunparse(parsed._replace(query=urlencode(query)))


def test_resume_generation():
    """测试简历生成功能"""
    
    # 测试简历信息
    resume_info = """
    张小明，25岁，计算机科学与技术专业本科毕业。
    联系方式：手机13812345678，邮箱zhangming@example.com
    
    教育背景：
    - 2018-2022 北京大学计算机科学与技术学士学位
    - GPA 3.8/4.0，获得优秀学生奖学金
    
    工作经验：
    - 2022-2024 阿里巴巴集团 Java开发工程师
      * 参与电商平台后端系统开发，使用Spring Boot、MyBatis等技术栈
      * 优化系统性能，将接口响应时间降低30%
      * 负责微服务架构设计和实现
    
    技能特长：
    - 编程语言：Java、Python、JavaScript
    - 框架技术：Spring Boot、Vue.js、React
    - 数据库：MySQL、Redis、MongoDB
    - 工具：Git、Docker、Jenkins
    
    求职意向：高级Java开发工程师
    期望薪资：20-25K
    工作地点：北京、上海
    """
    
    # 构建请求URL
    base_url = "https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9"
    
    try:
        auth_url = _assemble_xfyun_auth_url(base_url, XFYUN_RESUME_API_KEY, XFYUN_RESUME_API_SECRET, method="POST")
        print(f"[INFO] 鉴权URL构建成功")
        print(f"[DEBUG] 认证URL: {auth_url[:100]}...")
    except Exception as e:
        print(f"[ERROR] 构建鉴权URL失败：{e}")
        return
    
    # 构建请求数据
    text_base64 = base64.b64encode(resume_info.encode('utf-8')).decode('utf-8')
    
    payload = {
        "header": {
            "app_id": XFYUN_RESUME_APP_ID,
            "status": 3  # 一次传完
        },
        "parameter": {
            "ai_resume": {
                "resData": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "reqData": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 3,
                "text": text_base64
            }
        }
    }
    
    print(f"[INFO] 请求载荷构建完成")
    print(f"[DEBUG] APP ID: {XFYUN_RESUME_APP_ID}")
    print(f"[DEBUG] 文本长度: {len(resume_info)} 字符")
    print(f"[DEBUG] Base64编码长度: {len(text_base64)} 字符")
    
    # 发送请求
    try:
        print(f"[INFO] 发送请求到讯飞简历生成接口...")
        resp = requests.post(
            auth_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        print(f"[INFO] 请求发送完成，HTTP状态码: {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] 调用讯飞简历生成接口失败（网络/连接异常）：{e}")
        return
    
    # 打印响应详细信息
    content_type = (resp.headers.get('Content-Type') or '').lower()
    print(f"[DEBUG] 响应Content-Type: {content_type}")
    print(f"[DEBUG] 响应头: {dict(resp.headers)}")
    
    # 尝试解析响应
    try:
        resp_data = resp.json()
        print(f"[INFO] 响应JSON解析成功")
        print(f"[DEBUG] 完整响应: {json.dumps(resp_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        raw_text = resp.text or ''
        print(f"[ERROR] JSON解析失败: {e}")
        print(f"[DEBUG] 原始响应文本: {raw_text[:1000]}")
        return
    
    # 检查返回码
    header = resp_data.get('header', {})
    code = header.get('code')
    message = header.get('message', '')
    sid = header.get('sid', '')
    
    print(f"[INFO] 返回码: {code}")
    print(f"[INFO] 返回消息: {message}")
    print(f"[INFO] 会话ID: {sid}")
    
    if code != 0:
        print(f"[ERROR] 接口返回错误码: {code}, 消息: {message}")
        return
    
    # 解析简历数据
    payload_data = resp_data.get('payload', {})
    res_data = payload_data.get('resData', {})
    text_base64_response = res_data.get('text', '')
    
    print(f"[INFO] 返回数据Base64长度: {len(text_base64_response)}")
    
    if not text_base64_response:
        print(f"[ERROR] 未返回数据")
        return
    
    # Base64解码
    try:
        result_text = base64.b64decode(text_base64_response).decode('utf-8')
        result_json = json.loads(result_text)
        print(f"[INFO] 数据解码成功")
        print(f"[DEBUG] 解码结果: {json.dumps(result_json, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"[ERROR] 解析简历数据失败：{e}")
        print(f"[DEBUG] 原始Base64: {text_base64_response[:500]}")
        return
    
    # 提取简历链接
    links = result_json.get('links', [])  # 修改字段名从 'link' 到 'links'
    
    print(f"[INFO] 简历链接数量: {len(links) if links else 0}")
    if links:
        for i, link in enumerate(links):
            print(f"[INFO] 简历 {i+1}:")
            print(f"  - 图片URL: {link.get('img_url', 'N/A')}")
            print(f"  - Word URL: {link.get('word_url', 'N/A')}")
    else:
        print(f"[WARNING] 未返回简历链接")
    
    print(f"[SUCCESS] 简历生成测试完成！")


if __name__ == '__main__':
    test_resume_generation()