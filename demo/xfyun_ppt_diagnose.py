# -*- coding: utf-8 -*-
"""讯飞智文 PPT 接口连通性诊断脚本

用法（推荐 Anaconda 解释器）：
    D:/AnacondaEnvs/pytorch/python.exe demo/xfyun_ppt_diagnose.py

前置：在项目根目录放置 .env，并设置：
  XFYUN_ZW_APP_ID=...
  XFYUN_ZW_API_SECRET=...

输出：不会打印密钥明文，只打印长度与响应预览。
"""

import os
import json
import time
import base64
import hashlib
import hmac
from urllib.parse import urljoin

import requests

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except Exception as e:
    raise SystemExit("缺少依赖 requests-toolbelt，请先安装：pip install requests-toolbelt") from e


def load_env():
    if not load_dotenv:
        return
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    load_dotenv(os.path.join(project_root, ".env"), override=False)


def signature(app_id: str, api_secret: str, ts: int) -> str:
    auth = hashlib.md5(f"{app_id}{ts}".encode("utf-8")).hexdigest()
    digest = hmac.new(api_secret.encode("utf-8"), auth.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


def main():
    load_env()

    app_id = os.environ.get("XFYUN_ZW_APP_ID", "") or os.environ.get("XFYUN_PPT_APP_ID", "")
    api_secret = (
        os.environ.get("XFYUN_ZW_API_SECRET", "")
        or os.environ.get("XFYUN_ZW_APISECRET", "")
        or os.environ.get("XFYUN_PPT_API_SECRET", "")
    )

    base_url = (os.environ.get("XFYUN_ZW_BASE_URL", "https://zwapi.xfyun.cn") or "https://zwapi.xfyun.cn").strip()
    if base_url and not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url.lstrip("/")
    base_url = base_url.rstrip("/")

    if not app_id or not api_secret:
        raise SystemExit("未读取到 XFYUN_ZW_APP_ID / XFYUN_ZW_API_SECRET，请先配置 .env 或环境变量")

    print("base_url:", base_url)
    print("app_id:", app_id)
    print("api_secret_length:", len(api_secret))

    url = urljoin(base_url + "/", "/api/ppt/v2/create")
    ts = int(time.time())

    query = "请生成一份PPT：介绍线性回归的核心概念、推导、一个例题与总结。"

    form = MultipartEncoder(
        fields={
            "query": query,
            "language": "CN",
            "isCardNote": "false",
            "search": "false",
            "isFigure": "true",
            "aiImage": "normal",
        }
    )

    headers = {
        "appId": app_id,
        "timestamp": str(ts),
        "signature": signature(app_id, api_secret, ts),
        "Content-Type": form.content_type,
        "Accept": "application/json",
    }

    print("POST:", url)
    try:
        resp = requests.post(url, data=form, headers=headers, timeout=60, allow_redirects=True)
    except Exception as e:
        print("REQUEST_ERROR:", repr(e))
        return

    ct = (resp.headers.get("Content-Type") or "").lower()
    text = resp.text or ""
    print("HTTP_STATUS:", resp.status_code)
    print("CONTENT_TYPE:", ct)
    print("REQUEST_METHOD:", getattr(getattr(resp, "request", None), "method", None))
    print("FINAL_URL:", getattr(resp, "url", None))
    if resp.history:
        chain = []
        for h in resp.history:
            chain.append({
                "http_status": h.status_code,
                "url": h.url,
                "location": h.headers.get("Location"),
            })
        print("REDIRECT_CHAIN:", json.dumps(chain, ensure_ascii=False))
    allow_hdr = resp.headers.get("Allow")
    if allow_hdr:
        print("ALLOW_HEADER:", allow_hdr)

    payload = None
    try:
        payload = resp.json()
    except Exception:
        try:
            payload = json.loads(text)
        except Exception:
            payload = None

    if payload is not None:
        print("JSON_OK: true")
        # 仅打印关键字段，避免输出过大
        code = payload.get("code")
        desc = payload.get("desc")
        flag = payload.get("flag")
        sid = (payload.get("data") or {}).get("sid") if isinstance(payload.get("data"), dict) else None
        print("code:", code)
        print("desc:", desc)
        print("flag:", flag)
        print("sid:", sid)
    else:
        print("JSON_OK: false")
        preview = text.strip()[:800]
        print("BODY_PREVIEW:\n" + preview)


if __name__ == "__main__":
    main()
