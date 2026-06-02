from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    brief_title: str
    timezone: str
    max_items: int
    min_china_items: int
    min_news_items: int
    candidate_limit: int
    download_assets: bool
    keywords: list[str]
    arxiv_categories: list[str]
    semantic_scholar_queries: list[str]
    official_blogs: list[str]
    news_feeds: list[dict[str, str]]
    delivery: dict[str, bool]


def load_json_config(path: str | Path) -> AppConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(
        brief_title=raw.get("brief_title", "每日 AI 研究简报"),
        timezone=raw.get("timezone", "Asia/Shanghai"),
        max_items=int(raw.get("max_items", 5)),
        min_china_items=int(raw.get("min_china_items", 1)),
        min_news_items=int(raw.get("min_news_items", 2)),
        candidate_limit=int(raw.get("candidate_limit", 40)),
        download_assets=bool(raw.get("download_assets", True)),
        keywords=list(raw.get("keywords", [])),
        arxiv_categories=list(raw.get("arxiv_categories", ["cs.AI", "cs.LG", "cs.CL"])),
        semantic_scholar_queries=list(raw.get("semantic_scholar_queries", [])),
        official_blogs=list(raw.get("official_blogs", [])),
        news_feeds=list(raw.get("news_feeds", [])),
        delivery=dict(raw.get("delivery", {})),
    )


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def as_dict(config: AppConfig) -> dict[str, Any]:
    return {
        "brief_title": config.brief_title,
        "timezone": config.timezone,
        "max_items": config.max_items,
        "min_china_items": config.min_china_items,
        "min_news_items": config.min_news_items,
        "candidate_limit": config.candidate_limit,
        "download_assets": config.download_assets,
        "keywords": config.keywords,
        "arxiv_categories": config.arxiv_categories,
        "semantic_scholar_queries": config.semantic_scholar_queries,
        "official_blogs": config.official_blogs,
        "news_feeds": config.news_feeds,
        "delivery": config.delivery,
    }
