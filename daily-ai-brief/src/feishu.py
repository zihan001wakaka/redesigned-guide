from __future__ import annotations

import json
from dataclasses import dataclass

from .config import env
from .http import post_json


@dataclass
class FeishuResult:
    ok: bool
    message: str
    document_url: str = ""


def configured() -> bool:
    required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET"]
    return all(env(name) for name in required)


def tenant_access_token() -> str:
    data = post_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {
            "app_id": env("FEISHU_APP_ID"),
            "app_secret": env("FEISHU_APP_SECRET"),
        },
    )
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError(f"failed to get tenant_access_token: {data}")
    return token


def create_doc_placeholder(markdown: str, title: str) -> FeishuResult:
    if not configured():
        return FeishuResult(False, "飞书凭证未配置，已跳过创建文档。")
    token = tenant_access_token()
    folder_token = env("FEISHU_FOLDER_TOKEN")
    if not folder_token:
        return FeishuResult(False, "缺少 FEISHU_FOLDER_TOKEN，无法确定文档创建位置。")
    # Feishu's document block API needs structured blocks. This MVP creates an online document first;
    # structured Markdown-to-block insertion can be added after app permissions are confirmed.
    payload = {"title": title, "type": "docx"}
    data = post_json(
        f"https://open.feishu.cn/open-apis/drive/explorer/v2/file/{folder_token}",
        payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if data.get("code") != 0:
        return FeishuResult(False, f"创建飞书文档失败：{data}")
    url = ((data.get("data") or {}).get("url")) or ""
    return FeishuResult(True, "飞书文档已创建；正文写入待接入 docx block API。", url)


def send_message(text: str) -> FeishuResult:
    if not configured():
        return FeishuResult(False, "飞书凭证未配置，已跳过发送消息。")
    receive_id = env("FEISHU_RECEIVE_ID")
    if not receive_id:
        return FeishuResult(False, "缺少 FEISHU_RECEIVE_ID，无法发送消息。")
    token = tenant_access_token()
    receive_id_type = env("FEISHU_RECEIVE_ID_TYPE", "open_id")
    data = post_json(
        f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
        {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if data.get("code") != 0:
        return FeishuResult(False, f"发送飞书消息失败：{data}")
    return FeishuResult(True, "飞书消息已发送。")
