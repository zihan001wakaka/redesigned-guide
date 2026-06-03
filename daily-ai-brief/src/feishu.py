from __future__ import annotations

import json
import re
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


def feishu_doc_url(document_id: str) -> str:
    if not document_id:
        return ""
    return f"https://my.feishu.cn/docx/{document_id}"


def markdown_to_text_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    in_code_block = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not line:
            continue
        text = normalize_markdown_line(line, in_code_block)
        for chunk in chunk_text(text):
            blocks.append(
                {
                    "block_type": 2,
                    "text": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": chunk,
                                }
                            }
                        ]
                    },
                }
            )
    return blocks


def normalize_markdown_line(line: str, in_code_block: bool) -> str:
    if in_code_block:
        return line
    heading = re.match(r"^(#{1,6})\s+(.*)$", line)
    if heading:
        level = len(heading.group(1))
        return f"{'  ' * max(0, level - 1)}{heading.group(2)}"
    line = re.sub(r"^\s*-\s+", "• ", line)
    line = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"`([^`]+)`", r"\1", line)
    return line


def chunk_text(text: str, max_chars: int = 1500) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def write_doc_content(document_id: str, markdown: str, token: str) -> None:
    blocks = markdown_to_text_blocks(markdown)
    for start in range(0, len(blocks), 50):
        batch = blocks[start : start + 50]
        post_json(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            {"children": batch},
            headers={"Authorization": f"Bearer {token}"},
        )


def create_doc_placeholder(markdown: str, title: str) -> FeishuResult:
    if not configured():
        return FeishuResult(False, "飞书凭证未配置，已跳过创建文档。")
    try:
        token = tenant_access_token()
        folder_token = env("FEISHU_FOLDER_TOKEN")
        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        data = post_json(
            "https://open.feishu.cn/open-apis/docx/v1/documents",
            payload,
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception as exc:
        return FeishuResult(False, f"创建飞书文档失败：{exc}")
    if data.get("code") != 0:
        return FeishuResult(False, f"创建飞书文档失败：{data}")
    document = ((data.get("data") or {}).get("document")) or {}
    document_id = document.get("document_id", "")
    url = document.get("url") or feishu_doc_url(document_id)
    if document_id:
        try:
            write_doc_content(document_id, markdown, token)
        except Exception as exc:
            return FeishuResult(False, f"飞书文档已创建，但正文写入失败：{exc}", url)
    return FeishuResult(True, "飞书文档已创建并写入正文。", url)


def send_message(text: str) -> FeishuResult:
    if not configured():
        return FeishuResult(False, "飞书凭证未配置，已跳过发送消息。")
    receive_id = env("FEISHU_RECEIVE_ID")
    if not receive_id:
        return FeishuResult(False, "缺少 FEISHU_RECEIVE_ID，无法发送消息。")
    try:
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
    except Exception as exc:
        return FeishuResult(False, f"发送飞书消息失败：{exc}")
    if data.get("code") != 0:
        return FeishuResult(False, f"发送飞书消息失败：{data}")
    return FeishuResult(True, "飞书消息已发送。")
