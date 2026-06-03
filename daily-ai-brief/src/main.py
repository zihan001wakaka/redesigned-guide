from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_dotenv, load_json_config
from .assets import download_selected_assets
from .feishu import create_doc_placeholder, send_message
from .ranker import rank_candidates
from .report import build_markdown, write_report
from .sources import fetch_all_with_status
from .models import Candidate
from scripts.export_outputs import export_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.example.json")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--outputs-dir", default="outputs")
    args = parser.parse_args()

    load_dotenv(args.env)
    config = load_json_config(args.config)
    candidates, fetch_failures = fetch_all_with_status(config)
    selected = rank_candidates(
        candidates,
        config.keywords,
        config.max_items,
        config.min_china_items,
        getattr(config, "min_news_items", 0),
    )
    if config.download_assets:
        download_selected_assets(selected)
    markdown = build_markdown(config, selected)
    report_path = write_report(markdown, Path(args.reports_dir))
    exported_files = export_report(report_path, Path(args.outputs_dir))
    markdown = with_export_links(markdown, report_path, exported_files)
    report_path.write_text(markdown, encoding="utf-8")
    exported_files = export_report(report_path, Path(args.outputs_dir))
    print(f"[ok] report written: {report_path}")
    print(f"[ok] selected items: {len(selected)}")
    print(f"[ok] html export: {exported_files[0]}")
    print(f"[ok] word export: {exported_files[1]}")

    delivery_failures: list[str] = []
    if config.delivery.get("create_feishu_doc"):
        result = create_doc_placeholder(markdown, config.brief_title)
        print(f"[feishu] {result.message}")
        if not result.ok:
            delivery_failures.append(result.message)
        if result.document_url and config.delivery.get("send_feishu_message"):
            msg = build_delivery_message(config.brief_title, selected, report_path, result.document_url, exported_files)
            message_result = send_message(msg)
            print(f"[feishu] {message_result.message}")
            if not message_result.ok:
                delivery_failures.append(message_result.message)
    elif config.delivery.get("send_feishu_message"):
        message_result = send_message(build_delivery_message(config.brief_title, selected, report_path, exported_files=exported_files))
        print(f"[feishu] {message_result.message}")
        if not message_result.ok:
            delivery_failures.append(message_result.message)

    if not selected and fetch_failures:
        print("[error] no selected items and at least one source fetch failed; treating this run as failed.")
        for failure in fetch_failures:
            print(f"[error] fetch failure: {failure}")
        return 2

    if delivery_failures:
        print("[error] feishu delivery failed; treating this run as failed.")
        for failure in delivery_failures:
            print(f"[error] feishu failure: {failure}")
        return 3

    return 0


def with_export_links(markdown: str, report_path: Path, exported_files: tuple[Path, Path]) -> str:
    html_path, docx_path = exported_files
    lines = [
        "",
        "## 导出文件",
        f"- Markdown 报告：{report_path.resolve()}",
        f"- HTML 文件：{html_path.resolve()}",
        f"- Word 文件：{docx_path.resolve()}",
    ]
    return markdown.rstrip() + "\n" + "\n".join(lines) + "\n"


def build_delivery_message(
    title: str,
    selected: list[Candidate],
    report_path: Path,
    document_url: str = "",
    exported_files: tuple[Path, Path] | None = None,
) -> str:
    lines = [
        f"{title} 已生成",
        f"入选数量：{len(selected)}",
    ]
    if document_url:
        lines.append(f"飞书文档：{document_url}")
    else:
        lines.append(f"本地报告：{report_path}")
    if exported_files:
        html_path, docx_path = exported_files
        lines.append(f"HTML 文件：{html_path.resolve()}")
        lines.append(f"Word 文件：{docx_path.resolve()}")
    if selected:
        lines.append("")
        lines.append("今日入选：")
        for index, item in enumerate(selected[:5], start=1):
            lines.append(f"{index}. {item.title}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
