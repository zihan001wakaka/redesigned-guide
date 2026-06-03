from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from .config import AppConfig, env
from .http import get_json, get_text, polite_pause, urlencode
from .models import Candidate


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_arxiv(config: AppConfig) -> list[Candidate]:
    candidates: list[Candidate] = []
    per_category = max(5, config.candidate_limit // max(1, len(config.arxiv_categories)))
    for category in config.arxiv_categories:
        query = f"cat:{category}"
        params = urlencode(
            {
                "search_query": query,
                "start": 0,
                "max_results": per_category,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        candidates.extend(parse_arxiv(get_text(f"https://export.arxiv.org/api/query?{params}"), category=category))
        polite_pause()
    return candidates


def fetch_arxiv_china(config: AppConfig) -> list[Candidate]:
    candidates: list[Candidate] = []
    terms = ["China", "Chinese", "Tsinghua", "Peking University", "Beijing", "Shanghai"]
    categories = " OR ".join(f"cat:{category}" for category in config.arxiv_categories)
    for term in terms:
        query = f"all:{term} AND ({categories})"
        params = urlencode(
            {
                "search_query": query,
                "start": 0,
                "max_results": 6,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        candidates.extend(parse_arxiv(get_text(f"https://export.arxiv.org/api/query?{params}"), category=f"china-signal:{term}"))
        polite_pause()
    return candidates


def parse_arxiv(xml_text: str, category: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    root = ET.fromstring(xml_text)
    for entry in root.findall("atom:entry", ATOM_NS):
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        url = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        authors = [
            clean_text(author.findtext("atom:name", default="", namespaces=ATOM_NS))
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        pdf_url = ""
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href", "")
                break
        candidates.append(
            Candidate(
                title=title,
                url=url,
                source="arXiv",
                source_type="preprint",
                published=published,
                authors=[a for a in authors if a],
                abstract=abstract,
                pdf_url=pdf_url,
                extra_links={"category": category},
            )
        )
    return candidates


def fetch_hugging_face_daily(_: AppConfig) -> list[Candidate]:
    html_text = get_text("https://huggingface.co/papers")
    candidates: list[Candidate] = []
    seen: set[str] = set()
    for match in re.finditer(r'href="(/papers/[^"]+)".{0,800}?<h3[^>]*>(.*?)</h3>', html_text, flags=re.S):
        path, raw_title = match.groups()
        title = clean_text(strip_tags(raw_title))
        if not title or title in seen:
            continue
        seen.add(title)
        candidates.append(
            Candidate(
                title=title,
                url=f"https://huggingface.co{path}",
                source="Hugging Face Daily Papers",
                source_type="community_curated",
                abstract="",
            )
        )
    return candidates[:20]


def fetch_news_feeds(config: AppConfig) -> list[Candidate]:
    candidates: list[Candidate] = []
    for feed in config.news_feeds:
        name = feed.get("name", "News Feed")
        url = feed.get("url", "")
        source_type = feed.get("source_type", "news_media")
        if not url:
            continue
        xml_text = get_text(url)
        candidates.extend(parse_rss_or_atom(xml_text, source=name, source_type=source_type))
        polite_pause(0.3)
    return candidates


def parse_rss_or_atom(xml_text: str, source: str, source_type: str) -> list[Candidate]:
    root = ET.fromstring(xml_text)
    candidates: list[Candidate] = []
    if root.tag.endswith("rss"):
        for item in root.findall(".//item"):
            title = clean_text(item.findtext("title", default=""))
            link = clean_text(item.findtext("link", default=""))
            description = clean_text(strip_tags(item.findtext("description", default="")))
            published = clean_text(item.findtext("pubDate", default=""))
            candidates.append(
                Candidate(
                    title=title,
                    url=link,
                    source=source,
                    source_type=source_type,
                    published=published,
                    abstract=description,
                    extra_links={"archive_hint": "news_page_screenshot_if_text_unavailable"},
                )
            )
    else:
        for entry in root.findall("atom:entry", ATOM_NS):
            title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
            link = ""
            for node in entry.findall("atom:link", ATOM_NS):
                if node.attrib.get("href"):
                    link = node.attrib["href"]
                    break
            summary = clean_text(strip_tags(entry.findtext("atom:summary", default="", namespaces=ATOM_NS)))
            published = clean_text(entry.findtext("atom:published", default="", namespaces=ATOM_NS))
            candidates.append(
                Candidate(
                    title=title,
                    url=link,
                    source=source,
                    source_type=source_type,
                    published=published,
                    abstract=summary,
                    extra_links={"archive_hint": "news_page_screenshot_if_text_unavailable"},
                )
            )
    return [candidate for candidate in candidates if candidate.title and candidate.url]


def fetch_semantic_scholar(config: AppConfig) -> list[Candidate]:
    candidates: list[Candidate] = []
    headers = {}
    api_key = env("SEMANTIC_SCHOLAR_API_KEY")
    if not api_key:
        print("[info] SEMANTIC_SCHOLAR_API_KEY 未配置，跳过 Semantic Scholar，避免无 key 限流。")
        return candidates
    headers["x-api-key"] = api_key
    since = (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat()
    for query in config.semantic_scholar_queries:
        params = urlencode(
            {
                "query": query,
                "limit": 10,
                "fields": "title,url,abstract,authors,venue,year,citationCount,publicationDate,openAccessPdf",
                "publicationDateOrYear": f"{since}:",
            }
        )
        data = get_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}", headers=headers)
        for item in data.get("data", []):
            authors = [author.get("name", "") for author in item.get("authors", [])]
            pdf = item.get("openAccessPdf") or {}
            candidates.append(
                Candidate(
                    title=clean_text(item.get("title", "")),
                    url=item.get("url", ""),
                    source="Semantic Scholar",
                    source_type="academic_index",
                    published=item.get("publicationDate") or str(item.get("year") or ""),
                    authors=[a for a in authors if a],
                    abstract=clean_text(item.get("abstract") or ""),
                    pdf_url=pdf.get("url", "") if isinstance(pdf, dict) else "",
                    venue=item.get("venue") or "",
                    citation_count=int(item.get("citationCount") or 0),
                )
            )
        polite_pause(0.5)
    return candidates


SOURCE_FETCHERS = (fetch_arxiv, fetch_arxiv_china, fetch_hugging_face_daily, fetch_news_feeds, fetch_semantic_scholar)


def fetch_all_with_status(config: AppConfig) -> tuple[list[Candidate], list[str]]:
    collected: list[Candidate] = []
    failures: list[str] = []
    for fetcher in SOURCE_FETCHERS:
        try:
            collected.extend(fetcher(config))
        except Exception as exc:
            message = f"{fetcher.__name__}: {exc}"
            failures.append(message)
            print(f"[warn] source failed: {message}")
    return dedupe(collected), failures


def fetch_all(config: AppConfig) -> list[Candidate]:
    candidates, _ = fetch_all_with_status(config)
    return candidates


def dedupe(candidates: list[Candidate]) -> list[Candidate]:
    by_key: dict[str, Candidate] = {}
    for candidate in candidates:
        if not candidate.title:
            continue
        existing = by_key.get(candidate.key)
        if existing is None:
            by_key[candidate.key] = candidate
            continue
        if not existing.pdf_url and candidate.pdf_url:
            existing.pdf_url = candidate.pdf_url
        if not existing.abstract and candidate.abstract:
            existing.abstract = candidate.abstract
        existing.citation_count = max(existing.citation_count, candidate.citation_count)
        if candidate.source not in existing.source:
            existing.source = f"{existing.source} + {candidate.source}"
    return list(by_key.values())


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value or "")
