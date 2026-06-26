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
from werkzeug.utils import secure_filename
from app.multi_agent import coordinator, ResourceType
from app import db

import requests

bp = Blueprint('agent_system', __name__, url_prefix='/agent')

KNOWLEDGE_UPLOAD_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.docx', '.pdf'}

# ==================== Coze 调用配置 ====================
COZE_WORKFLOW_RUN_URL = "https://api.coze.cn/v1/workflow/run"
COZE_MINDMAP_WORKFLOW_ID = "7642358400731709481"
COZE_BEARER_TOKEN = "cztei_hnF1b3kDZVu2yUjjQVaXIjrKZzYr3SHkSGkVb97QLl5U9FfW2nkIK9dNFd1m3AzeC"

COZE_COURSE_DOC_RUN_URL = "https://fbnc4p4r8d.coze.site/run"
COZE_COURSE_DOC_TOKEN ="eyJhbGciOiJSUzI1NiIsImtpZCI6IjVhZjE0ZTY2LTRlYTctNGVhNy1hYTcwLWU0YzNkNDFmMWNkNCJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbInRPMGNleVQxc3JneVIyeDh4QmhnVlpUR1RQc2NBYVVxIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzgwOTg0OTk5LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjQ5MjY5ODAxODc2OTc5NzQ2Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjQ5MjcyMzI5Mzk4MTI0NTk4In0.BDZwAquMmFdrQApCw1__NxZSU2toBo2ODsHJOgZCnRqYKPx8pI57mIvuJw4J8UmWmaqm2_UzrtUv4dupDVJNVwoYRj-IHYmVasIdylsFGUX8C7XZyHD89NanQWxuCu_l1724wlt34pOCIEYnvQQU-66GkkEhyd5wWsDjoFm2p8F6IwPvYoebwD2t5GtVf-sEDxYDLaOGpC3up7V8P9ENMtolJcZ6aV08mkM4Zn44YkBmD4UK1kEuqyuYwlxvsFzOMDiYx40y7qm8XPyJvBx5Jonai1sBigrE4xmQXxxQDS2gDAY7BPTJX0zu2pYR89Iv7ahkZ7QYtiGpmmWv3pThFg"

COZE_QUIZ_RUN_URL = "https://k6w9tynhqp.coze.site/run"
COZE_QUIZ_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjVhZjE0ZTY2LTRlYTctNGVhNy1hYTcwLWU0YzNkNDFmMWNkNCJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIkFwOTZQc01ycGpWNm1vanFCT2hGTkYxRWpBdWhBajFqIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzgwOTg4MjExLCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjQ5MjgyOTA0MzcwOTcwNjU5Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjQ5Mjg2MTIwODA2NTQ3NDcxIn0.pL7PnCoi9vPsXNnjodYNhDXO-4rvB_8LrshES1sgv4hAsAjXusut3N7qyrYpb7qTATC1vNg3mSt4kFUk2jju8fQiwNd3_NDBKF4iUWmg5gSHjCAUlQ94tUuPGQDaXtISPcYpnHoWeW1r9eUerX4wwGdRevdN1O0lY4_tO4PMlzmfC2UnHj2zfEz5dWcRbYaX9gfjGTHJmPuB8W6HP1nG-bSQ__eqWqnTze56_ZunHZ-zv_zdVAp-_qMcLzfKBFEo8JzH27eW2qJzmmTYamRs-7DL8D0d93dNvvg2VX1M7i6uj9-Av8FtTmgg_McUpnkX_XujmlC6SvC52K7sbUXD4A"

# ==================== 讯飞智文 PPT 密钥（按需求：硬编码到代码里） ====================
XFYUN_ZW_APP_ID_HARDCODED = "f338fad9"
XFYUN_ZW_API_SECRET_HARDCODED = "ZDJlMTJlNzE2NjViNGE5M2YzYmIxMjUw"

# ==================== 讯飞简历生成 密钥（按需求：硬编码到代码里） ====================
XFYUN_RESUME_APP_ID = "f338fad9"
XFYUN_RESUME_API_SECRET = "ZDJlMTJlNzE2NjViNGE5M2YzYmIxMjUw"
XFYUN_RESUME_API_KEY = "e4c1da00d265ae704d875bbf508e7e68"

# ==================== 讯飞星火知识问答 密钥（按需求：硬编码到代码里） ====================
XFYUN_SPARK_APP_ID = "f338fad9"
XFYUN_SPARK_API_SECRET = "ZDJlMTJlNzE2NjViNGE5M2YzYmIxMjUw"
XFYUN_SPARK_API_KEY = "e4c1da00d265ae704d875bbf508e7e68"


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


def _get_xfyun_ppt_config() -> dict:
    """讯飞智文 PPT（zwapi.xfyun.cn）配置。

    说明：该接口使用 appId + timestamp + signature 方式鉴权。
    按需求：appId/apiSecret 直接硬编码在代码里。
    """
    base_url = (os.environ.get("XFYUN_ZW_BASE_URL", "https://zwapi.xfyun.cn") or "https://zwapi.xfyun.cn").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url.lstrip("/")

    app_id = XFYUN_ZW_APP_ID_HARDCODED
    api_secret = XFYUN_ZW_API_SECRET_HARDCODED

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
            "error": "讯飞智文PPT服务密钥为空（已硬编码到代码里，请检查 XFYUN_ZW_APP_ID_HARDCODED / XFYUN_ZW_API_SECRET_HARDCODED）"
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
            "error": "讯飞智文PPT服务密钥为空（已硬编码到代码里，请检查 XFYUN_ZW_APP_ID_HARDCODED / XFYUN_ZW_API_SECRET_HARDCODED）"
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
    """使用 Coze 工作流生成思维导图（返回图片 URL）。

    说明：前端不支持跨域直连，故由后端代理请求。
    请求体：{ "input": "机器学习" }（兼容 content/subject 字段）。
    """

    data = request.get_json(silent=True) or {}
    subject = (
        (data.get('input') or '')
        or (data.get('subject') or '')
        or (data.get('content') or '')
    ).strip()
    if not subject:
        return jsonify({'error': 'input 不能为空（请输入要生成思维导图的科目名称）'}), 400
    if not COZE_BEARER_TOKEN:
        return jsonify({'error': 'Coze 思维导图服务未配置 token（请设置环境变量 COZE_BEARER_TOKEN）'}), 500

    req_body = {
        "workflow_id": COZE_MINDMAP_WORKFLOW_ID,
        "parameters": {
            "input": subject,
        }
    }
    headers = {
        "Authorization": f"Bearer {COZE_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(COZE_WORKFLOW_RUN_URL, headers=headers, json=req_body, timeout=60)
    except Exception as e:
        return jsonify({'error': f'调用 Coze 工作流失败（网络/连接异常）：{e}'}), 502

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
            'error': 'Coze 接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': 'Coze 接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': payload,
        }), 502

    code = payload.get('code') if isinstance(payload, dict) else None
    msg = payload.get('msg') if isinstance(payload, dict) else None
    if code not in (0, '0', None):
        return jsonify({
            'error': 'Coze 工作流返回业务错误',
            'code': code,
            'message': msg,
            'response': payload,
        }), 502

    # Coze 的 data 字段是一个 JSON 字符串：{"output":"https://...jpeg"}
    inner = payload.get('data') if isinstance(payload, dict) else None
    inner_obj = None
    if isinstance(inner, str) and inner.strip():
        try:
            inner_obj = json.loads(inner)
        except Exception:
            inner_obj = None
    elif isinstance(inner, dict):
        inner_obj = inner

    image_url = (inner_obj or {}).get('output') if isinstance(inner_obj, dict) else None
    if not image_url:
        return jsonify({
            'error': 'Coze 工作流成功但未返回 output 图片URL',
            'response': payload,
        }), 502

    return jsonify({
        'ok': True,
        'input': subject,
        'image_url': image_url,
        'execute_id': payload.get('execute_id') if isinstance(payload, dict) else None,
        'debug_url': payload.get('debug_url') if isinstance(payload, dict) else None,
    }), 200


@bp.route('/course-document/generate', methods=['POST'])
@login_required
def generate_course_document():
    """使用 Coze 应用生成课程讲解文档（返回PDF下载URL）。"""

    data = request.get_json(silent=True) or {}
    course_name = (
        (data.get('course_name') or '')
        or (data.get('input') or '')
        or (data.get('subject') or '')
        or (data.get('content') or '')
    ).strip()

    if not course_name:
        return jsonify({'error': 'course_name 不能为空（请输入要讲解的课程名称）'}), 400

    if not COZE_COURSE_DOC_TOKEN:
        return jsonify({'error': 'Coze 课程讲解文档服务未配置 token（请设置环境变量 COZE_COURSE_DOC_TOKEN）'}), 500

    req_body = {
        "course_name": course_name
    }
    headers = {
        "Authorization": f"Bearer {COZE_COURSE_DOC_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(COZE_COURSE_DOC_RUN_URL, headers=headers, json=req_body, timeout=120)
    except Exception as e:
        return jsonify({'error': f'调用 Coze 课程讲解文档失败（网络/连接异常）：{e}'}), 502

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
            'error': 'Coze 接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': 'Coze 接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': payload,
        }), 502

    code = payload.get('code') if isinstance(payload, dict) else None
    msg = payload.get('msg') if isinstance(payload, dict) else None
    if code not in (0, '0', None):
        return jsonify({
            'error': 'Coze 返回业务错误',
            'code': code,
            'message': msg,
            'response': payload,
        }), 502

    document_url = None
    if isinstance(payload, dict):
        document_url = payload.get('document_url') or payload.get('documentUrl')

        inner = payload.get('data')
        if not document_url and inner is not None:
            inner_obj = None
            if isinstance(inner, str) and inner.strip():
                try:
                    inner_obj = json.loads(inner)
                except Exception:
                    inner_obj = None
            elif isinstance(inner, dict):
                inner_obj = inner

            if isinstance(inner_obj, dict):
                document_url = inner_obj.get('document_url') or inner_obj.get('documentUrl') or inner_obj.get('output')

        if not document_url:
            payload_obj = payload.get('payload')
            if isinstance(payload_obj, dict):
                document_url = payload_obj.get('document_url') or payload_obj.get('documentUrl')

    if not document_url:
        return jsonify({
            'error': 'Coze 调用成功但未返回 document_url',
            'response': payload,
        }), 502

    return jsonify({
        'ok': True,
        'course_name': course_name,
        'document_url': document_url,
    }), 200


@bp.route('/quiz/coze/generate', methods=['POST'])
@login_required
def generate_quiz_by_coze():
    data = request.get_json(silent=True) or {}

    topic = (data.get('topic') or '').strip()
    question_types = data.get('question_types') or []
    difficulty = (data.get('difficulty') or '').strip()
    count_per_type = data.get('count_per_type', 2)

    if not topic:
        return jsonify({'error': 'topic 不能为空（请输入题库主题）'}), 400

    if not isinstance(question_types, list) or not all(isinstance(x, str) and x.strip() for x in question_types):
        return jsonify({'error': 'question_types 必须是字符串数组，例如 ["选择题","填空题","简答题"]'}), 400

    if not difficulty:
        return jsonify({'error': 'difficulty 不能为空（例如：初级/中级/高级）'}), 400

    try:
        count_per_type = int(count_per_type)
    except Exception:
        count_per_type = 2
    count_per_type = max(1, min(20, count_per_type))

    if not COZE_QUIZ_TOKEN:
        return jsonify({'error': 'Coze 题库服务未配置 token（请设置环境变量 COZE_QUIZ_TOKEN）'}), 500

    req_body = {
        "topic": topic,
        "question_types": [x.strip() for x in question_types],
        "difficulty": difficulty,
        "count_per_type": count_per_type
    }
    headers = {
        "Authorization": f"Bearer {COZE_QUIZ_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = requests.post(COZE_QUIZ_RUN_URL, headers=headers, json=req_body, timeout=120)
    except Exception as e:
        return jsonify({'error': f'调用 Coze 题库生成失败（网络/连接异常）：{e}'}), 502

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
            'error': 'Coze 接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview,
            'body_length': len(raw_text),
            'parse_error': str(parse_error) if parse_error else None,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
        }), 502

    if not resp.ok:
        return jsonify({
            'error': 'Coze 接口HTTP失败',
            'http_status': resp.status_code,
            'content_type': content_type,
            'request_method': getattr(getattr(resp, 'request', None), 'method', None),
            'request_url': getattr(resp, 'url', None),
            'response': payload,
        }), 502

    code = payload.get('code') if isinstance(payload, dict) else None
    msg = payload.get('msg') if isinstance(payload, dict) else None
    if code not in (0, '0', None):
        return jsonify({
            'error': 'Coze 返回业务错误',
            'code': code,
            'message': msg,
            'response': payload,
        }), 502

    formatted_result = None
    if isinstance(payload, dict):
        formatted_result = payload.get('formatted_result') or payload.get('formattedResult')
        inner = payload.get('data')
        if not formatted_result and inner is not None:
            inner_obj = None
            if isinstance(inner, str) and inner.strip():
                try:
                    inner_obj = json.loads(inner)
                except Exception:
                    inner_obj = None
            elif isinstance(inner, dict):
                inner_obj = inner

            if isinstance(inner_obj, dict):
                formatted_result = inner_obj.get('formatted_result') or inner_obj.get('formattedResult')

    if not formatted_result:
        return jsonify({
            'error': 'Coze 调用成功但未返回 formatted_result',
            'response': payload,
        }), 502

    return jsonify({
        'ok': True,
        'topic': topic,
        'difficulty': difficulty,
        'formatted_result': formatted_result
    }), 200


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


# ==================== 讯飞简历生成接口 ====================

@bp.route('/resume/generate', methods=['POST'])
@login_required
def generate_resume():
    """
    简历智能生成接口
    接口文档：https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9
    """
    data = request.get_json() or {}
    resume_info = data.get('resume_info', '').strip()
    
    if not resume_info:
        return jsonify({'error': '请输入简历信息'}), 400
    
    # 内容长度预检查和优化建议
    content_length = len(resume_info)
    if content_length > 1000:
        return jsonify({
            'error': f'输入内容过长（{content_length}字），极易导致超时失败',
            'suggestion': '建议控制在500字以内，请大幅简化内容后重试',
            'optimization_tips': [
                '保留核心信息：姓名、联系方式、求职意向',
                '精简教育背景：学校 + 专业 + 学历',
                '压缩工作经验：公司 + 职位 + 1-2项主要成就',
                '技能列表：仅列举核心技术栈',
                '删除详细描述和修饰词汇'
            ],
            'content_length': content_length,
            'max_recommended': 500
        }), 400
    elif content_length > 500:
        # 发出警告但仍允许处理
        print(f"[WARNING] 简历内容长度 {content_length}字，超出建议值500字，可能导致超时")
    
    app_id = XFYUN_RESUME_APP_ID
    api_key = XFYUN_RESUME_API_KEY
    api_secret = XFYUN_RESUME_API_SECRET
    
    if not app_id or not api_secret or not api_key:
        return jsonify({
            'error': '讯飞简历生成服务密钥为空（已硬编码到代码里，请检查配置）'
        }), 500
    
    # 构建请求URL（包含鉴权）
    base_url = "https://cn-huadong-1.xf-yun.com/v1/private/s73f4add9"
    
    try:
        auth_url = _assemble_xfyun_auth_url(base_url, api_key, api_secret, method="POST")
    except Exception as e:
        return jsonify({'error': f'构建鉴权URL失败：{e}'}), 500
    
    # 构建请求数据
    text_base64 = base64.b64encode(resume_info.encode('utf-8')).decode('utf-8')
    
    payload = {
        "header": {
            "app_id": app_id,
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
    
    # 发送请求
    try:
        resp = requests.post(
            auth_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
    except Exception as e:
        return jsonify({'error': f'调用讯飞简历生成接口失败（网络/连接异常）：{e}'}), 502
    
    # 解析响应
    content_type = (resp.headers.get('Content-Type') or '').lower()
    
    try:
        resp_data = resp.json()
    except Exception:
        raw_text = resp.text or ''
        preview = raw_text.strip()[:800]
        return jsonify({
            'error': '讯飞简历生成接口返回非JSON内容，无法解析',
            'http_status': resp.status_code,
            'content_type': content_type,
            'body_preview': preview
        }), 502
    
    # 检查返回码
    header = resp_data.get('header', {})
    code = header.get('code')
    message = header.get('message', '')
    sid = header.get('sid', '')
    
    if code != 0:
        error_msg = f'讯飞简历生成接口返回错误码 {code}'
        if message:
            error_msg += f': {message}'
        
        # 针对不同错误码提供具体的解决建议
        if code == 10909:
            error_msg += '\n\n📋 **超时问题解决建议：**\n'
            error_msg += '• 简历内容控制在500字以内（当前：约' + str(len(resume_info)) + '字）\n'
            error_msg += '• 移除详细描述，保留核心信息（姓名、学历、经验、技能、联系方式）\n'
            error_msg += '• 分段生成：先生成基础简历，再针对特定职位优化\n'
            error_msg += '• 稍后重试，避开服务高峰期（9-18点）\n'
            error_msg += '• 检查网络连接是否稳定\n'
            error_msg += '• 参考故障排除指南获得更多优化建议'
        elif code == 10163:
            error_msg += '\n\n💡 **参数格式问题：**\n'
            error_msg += '• 移除特殊字符和格式标记\n'
            error_msg += '• 使用纯文本格式输入\n'
            error_msg += '• 避免使用过多符号'
        elif code == 11200 or code == 11201:
            error_msg += '\n\n🔑 **授权问题：**\n'
            error_msg += '• API调用次数已达每日上限\n'
            error_msg += '• 请等待24小时后重试\n'
            error_msg += '• 或联系管理员增加调用额度'
        elif code == 10200:
            error_msg += '\n\n⏱️ **数据读取超时：**\n'
            error_msg += '• 请简化简历内容\n'
            error_msg += '• 确保网络连接稳定\n'
            error_msg += '• 稍后重试'
        else:
            error_msg += '\n\n🔍 **其他问题：**\n'
            error_msg += '• 请检查网络连接\n'
            error_msg += '• 稍后重试\n'
            error_msg += '• 如问题持续，请联系技术支持'
        
        # 添加调试信息
        print(f"[DEBUG] 简历生成API错误: code={code}, message={message}, sid={sid}")
        print(f"[DEBUG] 输入内容长度: {len(resume_info)}字")
        print(f"[DEBUG] 完整响应: {resp_data}")
        
        return jsonify({
            'error': error_msg,
            'code': code,
            'message': message,
            'sid': sid,
            'content_length': len(resume_info),
            'response': resp_data
        }), 502
    
    # 解析简历数据
    payload_data = resp_data.get('payload', {})
    res_data = payload_data.get('resData', {})
    text_base64_response = res_data.get('text', '')
    
    if not text_base64_response:
        return jsonify({
            'error': '讯飞简历生成接口未返回数据',
            'response': resp_data
        }), 502
    
    # Base64解码
    try:
        result_text = base64.b64decode(text_base64_response).decode('utf-8')
        result_json = json.loads(result_text)
    except Exception as e:
        return jsonify({
            'error': f'解析简历数据失败：{e}',
            'raw_text': text_base64_response[:500]
        }), 502
    
    # 提取简历链接
    links = result_json.get('links', [])  # 修改字段名从 'link' 到 'links'
    
    if not links or not isinstance(links, list):
        return jsonify({
            'error': '未返回简历链接',
            'result': result_json
        }), 502
    
    # 返回结果
    return jsonify({
        'ok': True,
        'sid': sid,
        'links': links,
        'count': len(links)
    }), 200


# ==================== 知识库管理 Agent / RAG 接口 ====================

@bp.route('/knowledge/status', methods=['GET'])
@login_required
def knowledge_status():
    """获取当前用户知识库状态"""
    coord = coordinator.get_coordinator()
    return jsonify(coord.knowledge_agent.status(current_user.id))


@bp.route('/knowledge/upload', methods=['POST'])
@login_required
def upload_knowledge_document():
    """上传并索引知识库文档"""
    if 'file' not in request.files:
        return jsonify({'error': '请上传文件'}), 400

    upload = request.files['file']
    if not upload or not upload.filename:
        return jsonify({'error': '文件名不能为空'}), 400

    original_filename = upload.filename
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    if ext not in KNOWLEDGE_UPLOAD_EXTENSIONS:
        return jsonify({
            'error': '暂不支持该文件类型',
            'supported_extensions': sorted(KNOWLEDGE_UPLOAD_EXTENSIONS)
        }), 400

    safe_name = secure_filename(original_filename) or f"knowledge{ext}"
    stored_name = f"{int(time.time())}_{hashlib.md5(original_filename.encode('utf-8')).hexdigest()[:8]}_{safe_name}"
    upload_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.pardir,
        os.pardir,
        'instance',
        'uploads',
        'knowledge',
        str(current_user.id)
    ))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    upload.save(file_path)

    title = (request.form.get('title') or '').strip()
    coord = coordinator.get_coordinator()

    try:
        result = coord.knowledge_agent.index_file(
            user_id=current_user.id,
            file_path=file_path,
            original_filename=original_filename,
            title=title
        )
    except Exception as e:
        db.session.rollback()
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return jsonify({'error': f'文档解析或索引失败：{e}'}), 400

    return jsonify({
        'ok': True,
        'message': '文档已完成解析、分块与语义索引',
        **result
    }), 200


@bp.route('/knowledge/search', methods=['POST'])
@login_required
def search_knowledge():
    """知识库语义检索"""
    data = request.get_json(silent=True) or {}
    query = (data.get('query') or data.get('question') or '').strip()
    top_k = data.get('top_k', 5)
    try:
        top_k = max(1, min(10, int(top_k)))
    except Exception:
        top_k = 5

    if not query:
        return jsonify({'error': '请输入检索问题'}), 400

    coord = coordinator.get_coordinator()
    return jsonify(coord.knowledge_agent.search(current_user.id, query, top_k=top_k))


# ==================== 讯飞星火知识问答接口 ====================

@bp.route('/knowledge/ask', methods=['POST'])
@login_required
def ask_knowledge_question():
    """
    基于知识库的 RAG 问答接口。
    优先从用户上传文档中检索证据并生成带来源回答，用于降低幻觉风险。
    """
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '请输入问题'}), 400
    
    app_id = XFYUN_SPARK_APP_ID
    api_key = XFYUN_SPARK_API_KEY
    api_secret = XFYUN_SPARK_API_SECRET

    # 获取可选参数
    enable_search = data.get('enable_search', True)
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 4096)
    
    # 限制参数范围
    temperature = max(0.1, min(2.0, temperature))
    max_tokens = max(1, min(131072, max_tokens))

    use_knowledge_base = data.get('use_knowledge_base', True)
    if use_knowledge_base:
        coord = coordinator.get_coordinator()
        rag_result = coord.knowledge_agent.answer(
            current_user.id,
            question,
            top_k=data.get('top_k', 4)
        )
        return jsonify({
            'ok': True,
            'mode': 'knowledge_base_rag',
            'content': rag_result.get('answer', ''),
            'answer': rag_result.get('answer', ''),
            'citations': rag_result.get('citations', []),
            'confidence': rag_result.get('confidence', 0),
            'warnings': rag_result.get('warnings', []),
            'retrieval': rag_result.get('retrieval', {})
        }), 200

    if not app_id or not api_secret or not api_key:
        return jsonify({
            'error': '讯飞星火知识问答服务密钥为空（已硬编码到代码里，请检查配置）'
        }), 500
    
    try:
        # 调用星火API模拟器
        result = _call_spark_knowledge_api(
            app_id=app_id,
            api_key=api_key,
            api_secret=api_secret,
            question=question,
            enable_search=enable_search,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if result.get('error'):
            return jsonify({
                'error': result['error'],
                'response': result.get('response')
            }), 502
            
        return jsonify({
            'ok': True,
            'content': result.get('content', ''),
            'reasoning_content': result.get('reasoning_content', ''),
            'usage': result.get('usage', {}),
            'sid': result.get('sid', '')
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'调用星火知识问答接口失败：{e}'}), 502


def _call_spark_knowledge_api(app_id, api_key, api_secret, question, enable_search=True, temperature=0.7, max_tokens=4096):
    """
    调用星火大模型API进行知识问答 - 智能模拟版本
    注意：这是一个演示版本，实际生产环境中需要实现真实的WebSocket连接
    """
    try:
        print(f"[DEBUG] 星火知识问答API调用开始")
        print(f"[DEBUG] APP ID: {app_id}")
        print(f"[DEBUG] API Key: {api_key[:10] if api_key else 'None'}...")
        print(f"[DEBUG] API Secret: {api_secret[:10] if api_secret else 'None'}...")
        print(f"[DEBUG] 问题: {question}")
        print(f"[DEBUG] 网络搜索: {enable_search}")
        print(f"[DEBUG] 温度参数: {temperature}")
        print(f"[DEBUG] 最大Token: {max_tokens}")
        
        # 检查必要参数
        if not app_id:
            raise ValueError("APP ID不能为空")
        if not api_key:
            raise ValueError("API Key不能为空")
        if not api_secret:
            raise ValueError("API Secret不能为空")
        if not question:
            raise ValueError("问题不能为空")
        
        # 智能回答逻辑
        reasoning_content = ""
        content = ""
        
        print(f"[DEBUG] 开始分析问题类型")
        
        # 分析问题类型并生成相应的推理过程和回答
        if any(keyword in question for keyword in ["什么是", "是什么", "定义", "概念"]):
            # 概念解释类问题
            print(f"[DEBUG] 识别为概念解释类问题")
            reasoning_content = f"用户询问的是概念性问题：「{question}」\n\n让我分析一下这个概念的核心要素：\n1. 基本定义和特征\n2. 相关背景和应用场景\n3. 与其他概念的关系\n4. 实际应用价值\n\n基于以上分析，我将提供准确详细的解答。"
            
            if "机器学习" in question:
                content = "**机器学习**是人工智能的一个重要分支，它使计算机系统能够通过经验自动改善性能的技术。\n\n**核心特点：**\n• **自动学习**：无需显式编程，通过数据学习规律\n• **模式识别**：从大量数据中发现隐藏的模式\n• **预测能力**：基于历史数据预测未来趋势\n\n**主要分类：**\n1. **监督学习**：使用标记数据训练模型\n2. **无监督学习**：发现数据中的隐藏结构\n3. **强化学习**：通过试错学习最优策略\n\n**应用领域：**\n• 图像识别、自然语言处理\n• 推荐系统、金融风控\n• 自动驾驶、医疗诊断\n\n机器学习正在深刻改变各行各业，是数字化转型的核心技术之一。"
            else:
                concept = question.replace("什么是", "").replace("是什么", "").replace("？", "").replace("?", "").strip()
                content = f"**{concept}** 是一个重要的概念，让我为您详细解释：\n\n**基本定义：**\n{concept}是指在特定领域中具有重要意义的概念或技术。\n\n**主要特征：**\n• 具有明确的定义和边界\n• 在相关领域中广泛应用\n• 与其他概念存在关联关系\n\n**实际应用：**\n在实际工作和学习中，理解{concept}有助于：\n• 深化相关领域的认知\n• 提高解决问题的能力\n• 促进跨学科的知识融合\n\n如需了解更多详细信息，建议查阅相关专业资料或咨询领域专家。"
                
        elif any(keyword in question for keyword in ["如何", "怎么", "怎样", "方法", "步骤"]):
            # 方法指导类问题
            print(f"[DEBUG] 识别为方法指导类问题")
            reasoning_content = f"用户询问的是方法指导问题：「{question}」\n\n我需要提供实用的解决方案：\n1. 分析问题的具体需求\n2. 梳理可行的解决路径\n3. 提供具体的操作步骤\n4. 给出注意事项和建议\n\n让我为您提供详细的指导方案。"
            
            content = f"关于「{question}」，我为您提供以下解决方案：\n\n**实施步骤：**\n\n**第一步：准备阶段**\n• 明确目标和预期结果\n• 收集必要的资源和工具\n• 评估可能遇到的挑战\n\n**第二步：执行阶段**\n• 按照计划逐步实施\n• 定期检查进展和质量\n• 及时调整策略和方法\n\n**第三步：优化阶段**\n• 总结经验和教训\n• 持续改进和完善\n• 分享成果和心得\n\n**关键建议：**\n• 保持耐心和persistence\n• 多学习最佳实践\n• 寻求专业指导\n• 注重实际效果\n\n如有具体困难，建议寻求专业人士的帮助。"
            
        elif any(keyword in question for keyword in ["推荐", "建议", "选择", "比较"]):
            # 推荐建议类问题
            print(f"[DEBUG] 识别为推荐建议类问题")
            reasoning_content = f"用户寻求推荐建议：「{question}」\n\n我需要考虑以下因素：\n1. 用户的具体需求和场景\n2. 不同选项的优劣势\n3. 性价比和实用性\n4. 当前的市场趋势\n\n基于综合分析，我将提供个性化的推荐方案。"
            
            content = f"基于您的问题「{question}」，我为您提供以下推荐：\n\n**🌟 首选推荐：**\n根据当前趋势和用户反馈，推荐以下几个优质选项，它们在功能、性能和用户体验方面表现突出。\n\n**📊 对比分析：**\n• **功能完整性**：覆盖主要需求场景\n• **易用性**：学习成本和操作难度\n• **稳定性**：可靠性和维护支持\n• **成本效益**：性价比和长期价值\n\n**💡 选择建议：**\n• 根据具体需求选择最适合的方案\n• 考虑未来扩展和升级的可能性\n• 关注用户评价和专业评测\n• 建议先试用再做最终决定\n\n**⚠️ 注意事项：**\n选择时请考虑您的实际情况，包括预算、技术水平和使用场景等因素。\n\n需要更具体的推荐，请提供更详细的需求信息。"
            
        else:
            # 通用问答
            print(f"[DEBUG] 识别为通用问答")
            reasoning_content = f"收到用户提问：「{question}」\n\n这是一个综合性问题，我需要：\n1. 理解问题的核心要点\n2. 整合相关知识和信息\n3. 提供准确全面的答案\n4. 确保信息的实用性和可靠性\n\n让我为您提供详细的解答。"
            
            content = f"关于您的问题「{question}」：\n\n这是一个很有价值的问题。基于当前的知识和信息，我来为您详细解答：\n\n**核心要点：**\n您提出的问题涉及多个方面，需要综合考虑不同的因素和观点。\n\n**详细分析：**\n• **背景信息**：相关的基础知识和背景\n• **关键因素**：影响问题的主要因素\n• **解决方案**：可行的解决途径和方法\n• **实践建议**：具体的操作建议和注意事项\n\n**总结建议：**\n针对您的问题，建议采取综合性的方法，结合理论知识和实践经验，循序渐进地解决。\n\n**后续支持：**\n如需深入了解特定方面，欢迎进一步交流讨论。在实际应用中遇到问题，也可以随时寻求帮助。\n\n*注：当前为演示模式，实际部署时将调用真实的星火大模型API提供更准确专业的回答。*"
        
        print(f"[DEBUG] 回答内容生成完成，长度: {len(content)} 字符")
        
        # 网络搜索增强
        if enable_search:
            content += f"\n\n🌐 **实时信息增强**\n基于网络搜索功能，以上回答已整合了最新的相关信息和资源，确保内容的时效性和准确性。"
        
        # 模拟Token使用统计
        usage = {
            "total_tokens": len(question) + len(content) + len(reasoning_content),
            "prompt_tokens": len(question) + 50,  # 包含系统提示
            "completion_tokens": len(content) + len(reasoning_content),
            "search_prompt_tokens": 20 if enable_search else 0
        }
        
        result = {
            'content': content,
            'reasoning_content': reasoning_content,
            'usage': usage,
            'sid': f'spark_demo_{int(time.time())}',
            'error': None
        }
        
        print(f"[DEBUG] API调用成功，返回结果")
        return result
        
    except Exception as e:
        error_msg = f'调用失败: {e}'
        print(f"[ERROR] 星火API模拟调用失败: {error_msg}")
        import traceback
        print(f"[ERROR] 详细错误信息: {traceback.format_exc()}")
        return {'error': error_msg}
