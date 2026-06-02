from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_dotenv, load_json_config
from .assets import download_selected_assets
from .feishu import create_doc_placeholder, send_message
from .ranker import rank_candidates
from .report import build_markdown, write_report
from .sources import fetch_all


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.example.json")
    parser.add_argument("--env", default=".env")
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args()

    load_dotenv(args.env)
    config = load_json_config(args.config)
    candidates = fetch_all(config)
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
    print(f"[ok] report written: {report_path}")

    if config.delivery.get("create_feishu_doc"):
        result = create_doc_placeholder(markdown, config.brief_title)
        print(f"[feishu] {result.message}")
        if result.document_url and config.delivery.get("send_feishu_message"):
            msg = f"{config.brief_title} 已生成：{result.document_url}"
            print(f"[feishu] {send_message(msg).message}")
    elif config.delivery.get("send_feishu_message"):
        print(f"[feishu] {send_message(f'{config.brief_title} 已生成本地报告：{report_path}').message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
