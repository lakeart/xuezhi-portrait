# -*- coding: utf-8 -*-
"""
多智能体系统路由
为前端提供多智能体协同的API接口
"""

import json
import os
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl, urljoin
from flask import Blueprint, request, jsonify, Response, render_template
from flask_login import login_required, current_user
from app.multi_agent import coordinator, ResourceType
from app import db

import requests

bp = Blueprint('agent_system', __name__, url_prefix='/agent')


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


def _xfyun_hmac_headers(url: str, api_key: str, api_secret: str, method: str = "POST") -> dict:
    """讯飞 HMAC-SHA256 鉴权（HTTP 接口常用）：Authorization/Date/Host 三个头。

    规则与 `_assemble_xfyun_auth_url` 一致，但用于 HTTP header 鉴权场景。
    """
    parsed = urlparse(url)
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
    # 注意：HTTP Header 鉴权通常直接使用明文的 authorization_origin；
    # base64 的是 signature（已在上面处理）。把整个 authorization_origin 再 base64
    # 会导致服务端无法解析/校验，从而报签名无法验证。
    return {
        "Authorization": authorization_origin,
        "Date": date,
        "Host": parsed.netloc,
    }


def _get_xfyun_video_config() -> dict:
    return {
        "app_id": os.environ.get("XFYUN_DH_APP_ID", ""),
        "api_key": os.environ.get("XFYUN_DH_API_KEY", ""),
        "api_secret": os.environ.get("XFYUN_DH_API_SECRET", ""),
        "base_url": os.environ.get("XFYUN_DH_BASE_URL", "https://vms.cn-huadong-1.xf-yun.com").rstrip("/"),
        "generate_path": os.environ.get("XFYUN_DH_GENERATE_PATH", "/v1/private/video/generate"),
        "query_path": os.environ.get("XFYUN_DH_QUERY_PATH", "/v1/private/video/query"),
    }


def _get_xfyun_ppt_config() -> dict:
    """讯飞智文 PPT（zwapi.xfyun.cn）配置。

    说明：该接口使用 appId + timestamp + signature 方式鉴权。
    为避免把密钥写进代码，统一从环境变量读取。
    """
    base_url = (os.environ.get("XFYUN_ZW_BASE_URL", "https://zwapi.xfyun.cn") or "https://zwapi.xfyun.cn").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url.lstrip("/")

    app_id = (
        os.environ.get("XFYUN_ZW_APP_ID", "")
        or os.environ.get("XFYUN_ZW_APPID", "")
        or os.environ.get("XFYUN_PPT_APP_ID", "")
        or os.environ.get("XFYUN_PPT_APPID", "")
    )
    api_secret = (
        os.environ.get("XFYUN_ZW_API_SECRET", "")
        or os.environ.get("XFYUN_ZW_APISECRET", "")
        or os.environ.get("XFYUN_PPT_API_SECRET", "")
        or os.environ.get("XFYUN_PPT_APISECRET", "")
    )

    return {
        "app_id": app_id,
        "api_secret": api_secret,
        "base_url": base_url.rstrip("/"),
    }


def _get_xfyun_tti_config() -> dict:
    """讯飞 Spark 文生图（TTI）配置。

    接口：POST https://spark-api.cn-huabei-1.xf-yun.com/v2.1/tti
    鉴权：HMAC-SHA256（Authorization/Date/Host）
    """
    base_url = (os.environ.get("XFYUN_TTI_BASE_URL", "https://spark-api.cn-huabei-1.xf-yun.com") or "https://spark-api.cn-huabei-1.xf-yun.com").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url.lstrip("/")

    return {
        "app_id": os.environ.get("XFYUN_TTI_APP_ID", "") or os.environ.get("XFYUN_SPARK_APP_ID", ""),
        "api_key": os.environ.get("XFYUN_TTI_API_KEY", "") or os.environ.get("XFYUN_SPARK_API_KEY", ""),
        "api_secret": os.environ.get("XFYUN_TTI_API_SECRET", "") or os.environ.get("XFYUN_SPARK_API_SECRET", ""),
        "url": urljoin(base_url.rstrip("/") + "/", "/v2.1/tti"),
    }


def _zwapi_url(base_url: str, path: str) -> str:
    """生成 zwapi.xfyun.cn 的绝对 API URL。

    说明：使用绝对 path（以 / 开头）避免 base_url 误带路径时拼接出错。
    """
    base = (base_url or "https://zwapi.xfyun.cn").strip()
    if base and not base.startswith(("http://", "https://")):
        base = "https://" + base.lstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return urljoin(base.rstrip("/") + "/", path)


def _safe_uid(max_len: int = 32) -> str:
    try:
        uid = str(getattr(current_user, 'id', '') or '')
    except Exception:
        uid = ''
    uid = uid.strip()
    return uid[:max_len] if uid else ''


def _xfyun_zw_signature(app_id: str, api_secret: str, ts: int) -> str:
    """按文档/官方 demo 规则生成 signature：Base64(HmacSHA1(MD5(appId+ts), apiSecret))"""
    auth = hashlib.md5(f"{app_id}{ts}".encode("utf-8")).hexdigest()
    digest = hmac.new(api_secret.encode("utf-8"), auth.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def _xfyun_zw_headers(app_id: str, api_secret: str, content_type=None) -> dict:
    ts = int(time.time())
    headers = {
        "appId": app_id,
        "timestamp": str(ts),
        "signature": _xfyun_zw_signature(app_id, api_secret, ts),
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


@bp.route('/')
@login_required
def index():
    """多智能体学习系统首页"""
    return render_template('agent_system/learning_agent.html')


@bp.route('/init', methods=['POST'])
@login_required
def init_session():
    """初始化多智能体会话"""
    from app.multi_agent.coordinator import create_new_session
    
    result = create_new_session(current_user.id, current_user.username)
    
    return jsonify(result)


@bp.route('/status', methods=['GET'])
@login_required
def get_status():
    """获取系统状态"""
    coord = coordinator.get_coordinator()
    status = coord.get_system_status()
    
    return jsonify(status)


@bp.route('/reset', methods=['POST'])
@login_required
def reset_session():
    """重置会话"""
    coord = coordinator.get_coordinator()
    result = coord.reset_session()
    
    return jsonify(result)


# ==================== 画像构建接口 ====================

@bp.route('/profile/chat', methods=['POST'])
@login_required
def profile_chat():
    """对话式画像构建"""
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': '请输入内容'}), 400
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    result = coord.build_profile(message)
    
    return jsonify(result)


@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前画像"""
    coord = coordinator.get_coordinator()
    
    if coord.current_profile:
        return jsonify(coord.current_profile.to_dict())
    else:
        return jsonify({'error': '暂无画像'}), 404


@bp.route('/profile/import', methods=['POST'])
@login_required
def import_profile_data():
    """从数据导入画像"""
    data = request.get_json()
    
    coord = coordinator.get_coordinator()
    
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    # 从答题历史等数据构建画像
    if 'quiz_history' in data:
        coord.profile_agent.build_profile_from_data(data)
    
    return jsonify(coord.current_profile.to_dict() if coord.current_profile else {})


# ==================== 资源生成接口 ====================

@bp.route('/resources/generate', methods=['POST'])
@login_required
def generate_resources():
    """协同生成学习资源"""
    data = request.get_json()
    
    topics = data.get('topics', [])
    resource_types = data.get('types', [])
    
    if not topics:
        return jsonify({'error': '请指定知识点'}), 400
    
    # 转换资源类型
    types_enum = []
    if resource_types:
        type_map = {
            'course_document': ResourceType.COURSE_DOCUMENT,
            'mind_map': ResourceType.MIND_MAP,
            'exercises': ResourceType.EXERCISES,
            'extended_reading': ResourceType.EXTENDED_READING,
            'video_script': ResourceType.VIDEO_SCRIPT,
            'code_practice': ResourceType.CODE_PRACTICE
        }
        for t in resource_types:
            if t in type_map:
                types_enum.append(type_map[t])
    else:
        types_enum = None  # 生成所有类型
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    result = coord.generate_learning_resources(topics, types_enum)
    
    return jsonify(result)


@bp.route('/resources', methods=['GET'])
@login_required
def get_resources():
    """获取已生成资源"""
    coord = coordinator.get_coordinator()
    
    return jsonify({
        'resources': coord.generated_resources,
        'count': len(coord.generated_resources)
    })


@bp.route('/resources/<resource_id>', methods=['GET'])
@login_required
def get_resource_detail(resource_id):
    """获取资源详情"""
    coord = coordinator.get_coordinator()
    
    for resource in coord.generated_resources:
        if resource.resource_id == resource_id:
            return jsonify(resource.to_card())
    
    return jsonify({'error': '资源不存在'}), 404


# ==================== 讯飞智文 PPT 生成接口 ====================

@bp.route('/ppt/create', methods=['POST'])
@login_required
def create_ppt_task():
    """创建 PPT 生成任务（返回 sid）。"""

    cfg = _get_xfyun_ppt_config()
    if not cfg["app_id"] or not cfg["api_secret"]:
        return jsonify({
            "error": "未配置讯飞智文PPT服务密钥（请设置环境变量 XFYUN_ZW_APP_ID / XFYUN_ZW_API_SECRET）"
        }), 500

    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'query 不能为空'}), 400

    template_id = (data.get('templateId') or '').strip()
    author = (data.get('author') or '').strip()
    language = (data.get('language') or 'CN').strip() or 'CN'
    is_card_note = bool(data.get('isCardNote', False))
    search = bool(data.get('search', False))
    is_figure = bool(data.get('isFigure', False))
    ai_image = (data.get('aiImage') or 'normal').strip() or 'normal'

    if ai_image not in {'normal', 'advanced'}:
        ai_image = 'normal'

    try:
        from requests_toolbelt.multipart.encoder import MultipartEncoder
    except Exception:
        return jsonify({
            'error': '缺少依赖 requests-toolbelt（请安装后重试：pip install requests-toolbelt）'
        }), 500

    fields = {
        'query': query,
        'language': language,
        'isCardNote': str(is_card_note),
        'search': str(search),
        'isFigure': str(is_figure),
    }
    if template_id:
        fields['templateId'] = template_id
    if author:
        fields['author'] = author
    if is_figure:
        fields['aiImage'] = ai_image

    form_data = MultipartEncoder(fields=fields)

    url = _zwapi_url(cfg['base_url'], "/api/ppt/v2/create")
    headers = _xfyun_zw_headers(cfg['app_id'], cfg['api_secret'], content_type=form_data.content_type)

    try:
        resp = requests.post(
            url,
            data=form_data,
            headers={**headers, "Accept": "application/json"},
            timeout=60,
            allow_redirects=True,
        )
    except Exception as e:
        return jsonify({'error': f'调用讯飞PPT创建接口失败（网络/连接异常）：{e}'}), 502

    content_type = (resp.headers.get('Content-Type') or '').lower()
    raw_text = resp.text or ''

    redirect_chain = []
    try:
        for h in (resp.history or []):
            redirect_chain.append({
                'http_status': h.status_code,
                'url': h.url,
                'location': h.headers.get('Location'),
            })
    except Exception:
        redirect_chain = []

    payload = None
    parse_error = None
    try:
        payload = resp.json()
    except Exception as e:
        parse_error = e
        try:
            payload = json.loads(raw_text)
            parse_error = None
        except Exception as e2:
            parse_error = e2

    if payload is None:
        preview = raw_text.strip()[:800]
        # 某些网关会用 application/json 头但返回纯文本错误（例如 Invalid AppId）
        hint = None
        if resp.status_code == 405 and preview and 'invalid appid' in preview.lower():
            hint = '讯飞返回 Invalid AppId：请确认使用的是“智文PPT(zwapi)”对应的 appId/apiSecret，且服务已开通；并确保 Flask 进程已读取到最新环境变量（重启服务）。'
        return jsonify({
            'error': '讯飞PPT创建接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'hint': hint,
            'used_app_id': cfg.get('app_id'),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'base_url': cfg.get('base_url'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'redirect_chain': redirect_chain,
            'allow_header': resp.headers.get('Allow'),
        }), 502

    if not resp.ok:
        # 透传错误，同时提供HTTP信息辅助排查
        return jsonify({
            'error': '讯飞PPT创建接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'used_app_id': cfg.get('app_id'),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'base_url': cfg.get('base_url'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'redirect_chain': redirect_chain,
            'allow_header': resp.headers.get('Allow'),
            'response': payload,
        }), 502

    return jsonify(payload), 200


@bp.route('/ppt/progress', methods=['GET'])
@login_required
def get_ppt_progress():
    """查询 PPT 生成进度（返回 pptUrl 等）。"""

    cfg = _get_xfyun_ppt_config()
    if not cfg["app_id"] or not cfg["api_secret"]:
        return jsonify({
            "error": "未配置讯飞智文PPT服务密钥（请设置环境变量 XFYUN_ZW_APP_ID / XFYUN_ZW_API_SECRET）"
        }), 500

    sid = (request.args.get('sid') or '').strip()
    if not sid:
        return jsonify({'error': 'sid 不能为空'}), 400

    url = _zwapi_url(cfg['base_url'], "/api/ppt/v2/progress")
    headers = _xfyun_zw_headers(cfg['app_id'], cfg['api_secret'])

    try:
        resp = requests.get(
            url,
            params={'sid': sid},
            headers={**headers, "Accept": "application/json"},
            timeout=30,
            allow_redirects=True,
        )
    except Exception as e:
        return jsonify({'error': f'调用讯飞PPT进度接口失败（网络/连接异常）：{e}'}), 502

    content_type = (resp.headers.get('Content-Type') or '').lower()
    raw_text = resp.text or ''

    redirect_chain = []
    try:
        for h in (resp.history or []):
            redirect_chain.append({
                'http_status': h.status_code,
                'url': h.url,
                'location': h.headers.get('Location'),
            })
    except Exception:
        redirect_chain = []

    payload = None
    parse_error = None
    try:
        payload = resp.json()
    except Exception as e:
        parse_error = e
        try:
            payload = json.loads(raw_text)
            parse_error = None
        except Exception as e2:
            parse_error = e2

    if payload is None:
        preview = raw_text.strip()[:800]
        return jsonify({
            'error': '讯飞PPT进度接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'used_app_id': cfg.get('app_id'),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'base_url': cfg.get('base_url'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'redirect_chain': redirect_chain,
            'allow_header': resp.headers.get('Allow'),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': '讯飞PPT进度接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'used_app_id': cfg.get('app_id'),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'base_url': cfg.get('base_url'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'redirect_chain': redirect_chain,
            'allow_header': resp.headers.get('Allow'),
            'response': payload,
        }), 502

    return jsonify(payload), 200


# ==================== 讯飞 Spark 文生图（思维导图）接口 ====================

@bp.route('/mindmap/generate', methods=['POST'])
@login_required
def generate_mindmap_image():
    """根据文本生成思维导图风格图片（返回 base64）。

    前端不支持跨域直连，故由后端代理请求。
    """
    cfg = _get_xfyun_tti_config()
    if not cfg["app_id"] or not cfg["api_key"] or not cfg["api_secret"]:
        return jsonify({
            "error": "未配置讯飞文生图服务密钥（请设置 XFYUN_TTI_APP_ID / XFYUN_TTI_API_KEY / XFYUN_TTI_API_SECRET）",
            "used_app_id": cfg.get("app_id") or None,
        }), 500

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'error': 'content 不能为空'}), 400

    # 固定为思维导图生成场景：提示词尽量约束为“思维导图风格”。
    prompt = (
        "请根据以下内容生成一张清晰的思维导图图片：白色背景，中文节点，层级结构清楚，线条简洁，"
        "布局均衡，适合教学笔记。内容：\n" + content
    )

    width = int(data.get('width') or 512)
    height = int(data.get('height') or 512)
    # 仅允许文档列出的常见分辨率，防止误填导致计费或接口报错
    allowed = {
        (512, 512), (640, 360), (640, 480), (640, 640), (680, 512), (512, 680),
        (768, 768), (720, 1280), (1280, 720), (1024, 1024)
    }
    if (width, height) not in allowed:
        width, height = 512, 512

    domain = (data.get('domain') or 'general').strip() or 'general'

    body = {
        "header": {
            "app_id": cfg["app_id"],
        },
        "parameter": {
            "chat": {
                "domain": domain,
                "width": width,
                "height": height,
            }
        },
        "payload": {
            "message": {
                "text": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            }
        }
    }

    uid = _safe_uid()
    if uid:
        body["header"]["uid"] = uid

    url = cfg["url"]
    headers = {
        **_xfyun_hmac_headers(url, cfg["api_key"], cfg["api_secret"], method="POST"),
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
    except Exception as e:
        return jsonify({'error': f'调用讯飞文生图接口失败（网络/连接异常）：{e}'}), 502

    content_type = (resp.headers.get('Content-Type') or '').lower()
    raw_text = resp.text or ''

    payload = None
    parse_error = None
    try:
        payload = resp.json()
    except Exception as e:
        parse_error = e
        try:
            payload = json.loads(raw_text)
            parse_error = None
        except Exception as e2:
            parse_error = e2

    if payload is None:
        preview = raw_text.strip()[:1200]
        return jsonify({
            'error': '讯飞文生图接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'used_app_id': cfg.get('app_id'),
            'api_key_length': len(cfg.get('api_key') or ''),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': '讯飞文生图接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'used_app_id': cfg.get('app_id'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': payload,
        }), 502

    header = payload.get('header') if isinstance(payload, dict) else None
    code = header.get('code') if isinstance(header, dict) else None
    message = header.get('message') if isinstance(header, dict) else None
    if code not in (0, '0'):
        return jsonify({
            'error': '讯飞文生图返回业务错误',
            'code': code,
            'message': message,
            'used_app_id': cfg.get('app_id'),
            'response': payload,
        }), 502

    # 提取 base64 图片
    try:
        base64_img = payload['payload']['choices']['text'][0]['content']
    except Exception:
        base64_img = None

    if not base64_img:
        return jsonify({
            'error': '讯飞文生图成功但未返回图片内容',
            'used_app_id': cfg.get('app_id'),
            'response': payload,
        }), 502

    return jsonify({
        'ok': True,
        'width': width,
        'height': height,
        'sid': header.get('sid') if isinstance(header, dict) else None,
        'image_base64': base64_img,
    }), 200


@bp.route('/video/generate', methods=['POST'])
@login_required
def generate_digital_human_video():
    data = request.get_json() or {}

    topic = (data.get('topic') or '').strip()
    prompt = (data.get('prompt') or '').strip()
    word_count = data.get('word_count', 120)

    try:
        word_count = int(word_count)
    except Exception:
        word_count = 120
    word_count = max(50, min(300, word_count))

    if not topic and not prompt:
        return jsonify({'error': '请指定知识点或输入提示词'}), 400

    cfg = _get_xfyun_video_config()
    if not cfg["app_id"] or not cfg["api_key"] or not cfg["api_secret"]:
        return jsonify({'error': '未配置讯飞数字人视频生成服务密钥（请设置环境变量 XFYUN_DH_APP_ID/XFYUN_DH_API_KEY/XFYUN_DH_API_SECRET）'}), 500

    coord = coordinator.get_coordinator()
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)

    if not prompt:
        profile = coord.current_profile
        style_map = {
            "visual": "多用类比和画面感描述，分点说明",
            "verbal": "多用定义与推理，语言表达清晰严谨",
            "auditory": "口语化、节奏清晰，适合听讲",
            "kinesthetic": "强调动手实践与步骤，引导边做边学"
        }
        style_hint = style_map.get(getattr(profile, "cognitive_style", "visual"), style_map["visual"])
        prompt = (
            f"请面向大学生讲解知识点：{topic}。"
            f"要求：结构为“引入-核心概念-例子-常见误区-总结”，{style_hint}。"
        )

    hosturl = f"{cfg['base_url']}{cfg['generate_path']}"
    auth_url = _assemble_xfyun_auth_url(hosturl, cfg["api_key"], cfg["api_secret"], method="POST")

    req_body = {
        "header": {
            "app_id": cfg["app_id"]
        },
        "parameter": {
            "avatar": {
                "prompt": prompt,
                "word_count": word_count
            }
        }
    }

    try:
        resp = requests.post(auth_url, json=req_body, timeout=60)
    except Exception as e:
        return jsonify({'error': f'调用讯飞数字人视频生成服务失败（网络/连接异常）：{e}'}), 502

    content_type = (resp.headers.get('Content-Type') or '').lower()
    raw_text = resp.text or ''

    result = None
    parse_error = None
    try:
        result = resp.json()
    except Exception as e:
        parse_error = e
        try:
            result = json.loads(raw_text)
            parse_error = None
        except Exception as e2:
            parse_error = e2

    if result is None:
        preview = raw_text.strip()[:1200]
        return jsonify({
            'error': '讯飞数字人视频接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'used_app_id': cfg.get('app_id'),
            'api_key_length': len(cfg.get('api_key') or ''),
            'api_secret_length': len(cfg.get('api_secret') or ''),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': '讯飞数字人视频接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'used_app_id': cfg.get('app_id'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': result,
        }), 502

    header = result.get("header") or {}
    code = header.get("code", -1)
    message = header.get("message", "")
    task_id = header.get("task_id", "")

    if code != 0 or not task_id:
        return jsonify({
            'error': f'创建视频任务失败：{message or resp.reason}',
            'code': code,
            'used_app_id': cfg.get('app_id'),
            'request_url': getattr(resp, 'url', None),
            'response': result,
        }), 502

    from app.models.agent_models import DigitalHumanVideoTaskModel

    task = DigitalHumanVideoTaskModel(
        user_id=current_user.id,
        topic=topic,
        prompt=prompt,
        word_count=word_count,
        task_id=task_id,
        task_status=header.get("task_status", "1"),
        code=code,
        message=message
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "id": task.id,
        "task_id": task.task_id,
        "task_status": task.task_status,
        "code": task.code,
        "message": task.message
    })


@bp.route('/video/query', methods=['POST'])
@login_required
def query_digital_human_video():
    data = request.get_json() or {}
    task_id = (data.get('task_id') or '').strip()
    record_id = data.get('id')

    from app.models.agent_models import DigitalHumanVideoTaskModel

    task = None
    if record_id is not None:
        task = DigitalHumanVideoTaskModel.query.filter_by(id=record_id, user_id=current_user.id).first()
    if task is None and task_id:
        task = DigitalHumanVideoTaskModel.query.filter_by(task_id=task_id, user_id=current_user.id).first()

    if task is None:
        return jsonify({'error': '任务不存在'}), 404

    cfg = _get_xfyun_video_config()
    if not cfg["app_id"] or not cfg["api_key"] or not cfg["api_secret"]:
        return jsonify({'error': '未配置讯飞数字人视频生成服务密钥（请设置环境变量 XFYUN_DH_APP_ID/XFYUN_DH_API_KEY/XFYUN_DH_API_SECRET）'}), 500

    hosturl = f"{cfg['base_url']}{cfg['query_path']}"
    auth_url = _assemble_xfyun_auth_url(hosturl, cfg["api_key"], cfg["api_secret"], method="POST")

    req_body = {
        "header": {
            "app_id": cfg["app_id"],
            "task_id": task.task_id
        }
    }

    try:
        resp = requests.post(auth_url, json=req_body, timeout=60)
    except Exception as e:
        return jsonify({'error': f'查询讯飞数字人视频任务失败（网络/连接异常）：{e}'}), 502

    content_type = (resp.headers.get('Content-Type') or '').lower()
    raw_text = resp.text or ''

    result = None
    parse_error = None
    try:
        result = resp.json()
    except Exception as e:
        parse_error = e
        try:
            result = json.loads(raw_text)
            parse_error = None
        except Exception as e2:
            parse_error = e2

    if result is None:
        preview = raw_text.strip()[:1200]
        return jsonify({
            'error': '讯飞数字人视频查询接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'used_app_id': cfg.get('app_id'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': '讯飞数字人视频查询接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'used_app_id': cfg.get('app_id'),
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': result,
        }), 502

    header = result.get("header") or {}
    payload = result.get("payload") or {}

    task.code = header.get("code", task.code)
    task.message = header.get("message", task.message)
    task.task_status = header.get("task_status", task.task_status)

    try:
        task.payload = json.dumps(payload, ensure_ascii=False)
    except Exception:
        task.payload = None

    db.session.commit()

    return jsonify(task.to_dict())


# ==================== 学习规划接口 ====================

@bp.route('/plan/create', methods=['POST'])
@login_required
def create_plan():
    """创建个性化学习计划"""
    data = request.get_json() or {}
    
    goals = data.get('goals', [])
    time_constraint = data.get('weekly_hours', 10)
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    result = coord.create_personalized_plan(goals, time_constraint)
    
    return jsonify(result)


@bp.route('/plan', methods=['GET'])
@login_required
def get_plan():
    """获取当前学习计划"""
    coord = coordinator.get_coordinator()
    
    if coord.current_path:
        return jsonify(coord.current_path.to_dict())
    else:
        return jsonify({'error': '暂无学习计划'}), 404


@bp.route('/plan/recommend', methods=['GET'])
@login_required
def recommend_resources():
    """推荐下一步学习资源"""
    coord = coordinator.get_coordinator()
    
    current_step = request.args.get('current_step', 0, type=int)
    
    if not coord.current_path:
        return jsonify({'error': '暂无学习计划'}), 404
    
    recommendations = coord.planner_agent.recommend_resources(
        coord.current_path,
        current_step
    )
    
    return jsonify({'recommendations': recommendations})


# ==================== 智能问答接口 ====================

@bp.route('/ask', methods=['POST'])
@login_required
def ask_question():
    """智能问答"""
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '请输入问题'}), 400
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    result = coord.ask_question(question)
    
    return jsonify(result)


@bp.route('/ask/stream', methods=['POST'])
@login_required
def ask_question_stream():
    """流式智能问答"""
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '请输入问题'}), 400
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    def generate():
        try:
            for chunk in coord.tutor_agent.stream_answer(question, coord.current_profile):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@bp.route('/explain', methods=['POST'])
@login_required
def explain_concept():
    """详细讲解概念"""
    data = request.get_json()
    concept = data.get('concept', '').strip()
    
    if not concept:
        return jsonify({'error': '请指定概念'}), 400
    
    coord = coordinator.get_coordinator()
    
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    result = coord.tutor_agent.explain_with_examples(concept, coord.current_profile)
    
    return jsonify(result)


# ==================== 学习评估接口 ====================

@bp.route('/evaluate', methods=['POST'])
@login_required
def evaluate_learning():
    """评估学习效果并调整计划"""
    data = request.get_json()
    
    completed_steps = data.get('completed_steps', [])
    assessment_results = data.get('assessments', {})
    
    coord = coordinator.get_coordinator()
    
    if not coord.current_path:
        return jsonify({'error': '暂无学习计划'}), 404
    
    result = coord.evaluate_and_adjust(completed_steps, assessment_results)
    
    return jsonify(result)


@bp.route('/export', methods=['GET'])
@login_required
def export_session():
    """导出会话数据"""
    coord = coordinator.get_coordinator()
    
    data = coord.export_session_data()
    
    return jsonify(data)


# ==================== 详细评估接口 ====================

@bp.route('/assessment/report', methods=['POST'])
@login_required
def generate_assessment_report():
    """生成详细学习评估报告"""
    from app.multi_agent.evaluator_agent import LearningEvaluatorAgent
    
    data = request.get_json() or {}
    
    coord = coordinator.get_coordinator()
    
    # 如果是新会话，先初始化
    if not coord.current_profile:
        coord.initialize_session(current_user.id, current_user.username)
    
    # 获取学习数据
    learning_data = {
        'quiz_results': data.get('quiz_results', []),
        'total_study_time': data.get('total_study_time', 0),
        'study_patterns': data.get('study_patterns', {}),
        'streak': data.get('streak', {}),
        'topic_progress': data.get('topic_progress', {}),
        'score_variance': data.get('score_variance', 0),
        'resource_usage_rate': data.get('resource_usage_rate', 0.5)
    }
    
    # 执行评估
    evaluator = LearningEvaluatorAgent()
    report = evaluator.evaluate(coord.current_profile, learning_data)
    
    # 生成详细报告文本
    report_text = evaluator.generate_detailed_report(report)
    
    return jsonify({
        'report': report.to_dict(),
        'report_text': report_text
    })


@bp.route('/assessment/history', methods=['GET'])
@login_required
def get_assessment_history():
    """获取评估历史"""
    from app.models.agent_models import AssessmentReportModel
    
    reports = AssessmentReportModel.query.filter_by(
        user_id=current_user.id
    ).order_by(
        AssessmentReportModel.assessment_date.desc()
    ).limit(10).all()
    
    return jsonify({
        'reports': [r.to_dict() for r in reports]
    })


@bp.route('/assessment/trend', methods=['GET'])
@login_required
def get_assessment_trend():
    """获取学习评估趋势"""
    from app.models.agent_models import AssessmentReportModel
    
    reports = AssessmentReportModel.query.filter_by(
        user_id=current_user.id
    ).order_by(
        AssessmentReportModel.assessment_date.asc()
    ).limit(10).all()
    
    if not reports:
        return jsonify({'trend': [], 'message': '暂无历史评估数据'})
    
    trend_data = [{
        'date': r.assessment_date.isoformat() if r.assessment_date else None,
        'score': r.overall_score,
        'level': r.level
    } for r in reports]
    
    return jsonify({'trend': trend_data})


# ==================== 画像持久化接口 ====================

@bp.route('/profile/save', methods=['POST'])
@login_required
def save_profile():
    """保存学习画像到数据库"""
    from app.models.agent_models import StudentProfileModel
    import json
    
    coord = coordinator.get_coordinator()
    
    if not coord.current_profile:
        return jsonify({'error': '暂无画像'}), 404
    
    # 查找或创建画像
    profile_model = StudentProfileModel.query.filter_by(
        user_id=current_user.id
    ).first()
    
    if not profile_model:
        profile_model = StudentProfileModel(user_id=current_user.id)
        db.session.add(profile_model)
    
    # 更新数据
    profile_model.profile_data = json.dumps(coord.current_profile.to_dict())
    profile_model.cognitive_style = coord.current_profile.cognitive_style
    profile_model.learning_speed = coord.current_profile.learning_speed
    profile_model.confidence = coord.current_profile.confidence
    
    db.session.commit()
    
    return jsonify({'message': '画像保存成功'})


@bp.route('/profile/load', methods=['GET'])
@login_required
def load_profile():
    """从数据库加载学习画像"""
    from app.models.agent_models import StudentProfileModel
    import json
    
    profile_model = StudentProfileModel.query.filter_by(
        user_id=current_user.id
    ).first()
    
    if not profile_model:
        return jsonify({'error': '暂无保存的画像'}), 404
    
    coord = coordinator.get_coordinator()
    
    # 初始化会话并加载画像
    coord.initialize_session(current_user.id, current_user.username)
    
    if profile_model.profile_data:
        profile_data = json.loads(profile_model.profile_data)
        coord.profile_agent.load_profile(profile_data)
        coord.current_profile = coord.profile_agent.profile
    
    return jsonify(coord.current_profile.to_dict() if coord.current_profile else {})


# ==================== 资源持久化接口 ====================

@bp.route('/resources/save', methods=['POST'])
@login_required
def save_resources():
    """保存资源到数据库"""
    from app.models.agent_models import LearningResourceModel
    import json
    
    coord = coordinator.get_coordinator()
    
    saved_count = 0
    for resource in coord.generated_resources:
        # 检查是否已存在
        existing = LearningResourceModel.query.filter_by(
            resource_id=resource.resource_id
        ).first()
        
        if not existing:
            model = LearningResourceModel(
                resource_id=resource.resource_id,
                user_id=current_user.id,
                resource_type=resource.resource_type.value,
                title=resource.title,
                content=resource.content,
                target_topics=json.dumps(resource.target_topics),
                difficulty=resource.difficulty,
                estimated_time=resource.estimated_time
            )
            db.session.add(model)
            saved_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'成功保存 {saved_count} 个资源',
        'count': saved_count
    })


@bp.route('/resources/saved', methods=['GET'])
@login_required
def get_saved_resources():
    """获取已保存的资源"""
    from app.models.agent_models import LearningResourceModel
    
    resources = LearningResourceModel.query.filter_by(
        user_id=current_user.id
    ).order_by(
        LearningResourceModel.created_at.desc()
    ).limit(50).all()
    
    return jsonify({
        'resources': [r.to_dict() for r in resources],
        'count': len(resources)
    })
