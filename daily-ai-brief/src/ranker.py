from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import Candidate


SOURCE_WEIGHTS = {
    "arXiv": 2.0,
    "Semantic Scholar": 2.5,
    "Hugging Face Daily Papers": 1.5,
    "MIT Technology Review": 2.0,
    "VentureBeat AI": 1.5,
    "The Decoder": 1.5,
    "OpenAI News": 2.5,
}


def rank_candidates(
    candidates: list[Candidate],
    keywords: list[str],
    max_items: int,
    min_china_items: int = 0,
    min_news_items: int = 0,
) -> list[Candidate]:
    for candidate in candidates:
        score = 0.0
        reasons: list[str] = []
        haystack = f"{candidate.title} {candidate.abstract}".lower()
        matches = [kw for kw in keywords if keyword_matches(haystack, kw)]
        if matches:
            score += min(5.0, len(matches) * 1.2)
            reasons.append("关键词匹配：" + "、".join(matches[:5]))
        for name, weight in SOURCE_WEIGHTS.items():
            if name in candidate.source:
                score += weight
                reasons.append(f"来源信号：{name}")
        if candidate.pdf_url:
            score += 1.0
            reasons.append("有 PDF / 开放访问链接")
        if candidate.citation_count:
            citation_score = min(2.0, candidate.citation_count / 50)
            score += citation_score
            reasons.append(f"引用信号：{candidate.citation_count}")
        if is_recent(candidate.published):
            score += 1.0
            reasons.append("近期发布")
        if candidate.abstract:
            score += 0.5
            reasons.append("有可追溯摘要")
        candidate.score = round(score, 2)
        candidate.score_reasons = reasons[:5]
        if is_china_region(candidate):
            candidate.score += 1.5
            candidate.score_reasons.append("中国/中文地区信号")
    ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
    selected = ranked[:max_items]
    if min_china_items > 0 and not any(is_china_region(item) for item in selected):
        china_candidates = [item for item in ranked[max_items:] if is_china_region(item)]
        if china_candidates and selected:
            selected[-1] = china_candidates[0]
    selected = ensure_news_diversity(selected, ranked, max_items, min_news_items)
    return selected


def is_recent(value: str) -> bool:
    if not value:
        return False
    raw = value.replace("Z", "+00:00")
    try:
        date = datetime.fromisoformat(raw)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    delta = datetime.now(timezone.utc) - date.astimezone(timezone.utc)
    return delta.days <= 14


def keyword_matches(haystack: str, keyword: str) -> bool:
    normalized = keyword.lower()
    if len(normalized) <= 4 and normalized.replace("-", "").isalnum():
        return re.search(rf"\b{re.escape(normalized)}\b", haystack) is not None
    return normalized in haystack


def is_china_region(candidate: Candidate) -> bool:
    text = " ".join(
        [
            candidate.title,
            candidate.abstract,
            " ".join(candidate.authors),
            " ".join(candidate.extra_links.values()),
        ]
    ).lower()
    signals = [
        "china",
        "chinese",
        "beijing",
        "shanghai",
        "tsinghua",
        "peking university",
        "zhejiang university",
        "fudan",
        "shanghai jiao tong",
        "university of science and technology of china",
        "香港",
        "中国",
        "北京",
        "上海",
        "清华",
        "北大",
        "复旦",
        "浙江大学",
        "中国科学院",
    ]
    return any(signal in text for signal in signals)


def is_news_like(candidate: Candidate) -> bool:
    return candidate.source_type in {"news_media", "official_blog", "newspaper"}


def ensure_news_diversity(
    selected: list[Candidate],
    ranked: list[Candidate],
    max_items: int,
    min_news_items: int,
) -> list[Candidate]:
    if min_news_items <= 0:
        return selected
    current_news = sum(1 for item in selected if is_news_like(item))
    if current_news >= min_news_items:
        return selected
    news_pool = [item for item in ranked if is_news_like(item) and item not in selected]
    if not news_pool:
        return selected
    result = selected[:]
    for news_item in news_pool:
        if sum(1 for item in result if is_news_like(item)) >= min_news_items:
            break
        replace_index = next((i for i in range(len(result) - 1, -1, -1) if not is_news_like(result[i])), None)
        if replace_index is None:
            break
        result[replace_index] = news_item
    return result[:max_items]
