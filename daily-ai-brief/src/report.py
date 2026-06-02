from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import AppConfig
from .models import Candidate
from .ranker import is_china_region
from .ranker import is_news_like


def build_markdown(config: AppConfig, selected: list[Candidate]) -> str:
    now = datetime.now(ZoneInfo(config.timezone))
    lines: list[str] = []
    lines.append(f"# {config.brief_title}｜{now:%Y-%m-%d}")
    lines.append("")
    lines.append("## 今日总览")
    if selected:
        china_note = "已包含至少 1 篇中国/中文地区信号内容。" if any(is_china_region(item) for item in selected) else "本次候选中未识别到明确中国/中文地区信号，未强行补入。"
        lines.append(f"今天筛选出 {len(selected)} 篇候选内容。报告严格基于标题、摘要、来源元信息和可访问链接生成，不做未证实推断。{china_note}")
    else:
        lines.append("今天没有筛选出足够可靠的候选内容。")
    lines.append("")
    lines.append("## 入选内容")
    for index, item in enumerate(selected, start=1):
        lines.extend(render_item(index, item))
    lines.append("## 备注")
    lines.append("- arXiv 内容标注为预印本，不等同于同行评审完成。")
    lines.append("- 产品实践联想只给出谨慎方向；缺少原文依据时不做强判断。")
    return "\n".join(lines).strip() + "\n"


def render_item(index: int, item: Candidate) -> list[str]:
    authors = "、".join(item.authors[:5]) if item.authors else "未获取"
    if len(item.authors) > 5:
        authors += " 等"
    lines = [
        f"### {index}. {item.title}",
        "",
        "#### 原始资料",
        f"- 来源：{item.source}（{item.source_type}）",
        f"- 作者/机构：{authors}",
        f"- 发布时间：{item.published or '未获取'}",
        f"- 原文链接：{item.url or '未获取'}",
        f"- PDF/开放访问：{item.pdf_url or '未获取'}",
    ]
    if is_news_like(item):
        lines.append("- 原始资料类型：网页文章。若正文抓取受限，自动化应保留网页截图/快照作为可追溯资料。")
        lines.append("- 截图/快照：待接入浏览器截图留档。")
    if item.extra_links.get("local_pdf"):
        lines.append(f"- 本地 PDF 资料：{item.extra_links['local_pdf']}")
    if item.extra_links.get("asset_error"):
        lines.append(f"- PDF 下载状态：失败，{item.extra_links['asset_error']}")
    if item.venue:
        lines.append(f"- 发表 venue：{item.venue}")
    if item.citation_count:
        lines.append(f"- 引用量信号：{item.citation_count}")
    lines.extend(
        [
            "",
            "#### 为什么入选",
        ]
    )
    if item.score_reasons:
        for reason in item.score_reasons[:3]:
            lines.append(f"- {reason}")
    else:
        lines.append("- 来源可靠且属于当天候选内容。")
    lines.extend(
        [
            "",
            "#### 行文逻辑图",
            "```mermaid",
            *article_logic_mermaid(item),
            "```",
            "",
            "#### 简练总结",
        ]
    )
    summary = summarize_from_abstract(item)
    lines.extend(f"- {line}" for line in summary)
    lines.extend(
        [
            "",
            "#### 产品实践联想",
            f"- {product_angle(item)}",
            "",
        ]
    )
    return lines


def summarize_from_abstract(item: Candidate) -> list[str]:
    if not item.abstract:
        return [
            "当前只获取到标题和来源信息，未获取到可追溯摘要。",
            "建议后续下载 PDF 后再生成深度总结。",
        ]
    sentences = split_sentences(item.abstract)
    logic = extract_logic(sentences)
    return [
        f"研究问题：{translate_sentence(logic['background'])}",
        f"方法/论证：{translate_sentence(logic['method'])}",
        f"结论/结果：{translate_sentence(logic['conclusion'])}",
        "证据来源：以上内容来自该条目的标题、摘要或元信息；未加入未证实扩写。",
    ]


def article_logic_mermaid(item: Candidate) -> list[str]:
    sentences = split_sentences(item.abstract)
    logic = extract_logic(sentences)
    title = mermaid_label(item.title)
    background = mermaid_label(translate_sentence(logic["background"]))
    method = mermaid_label(translate_sentence(logic["method"]))
    evidence = mermaid_label(translate_sentence(logic["evidence"]))
    conclusion = mermaid_label(translate_sentence(logic["conclusion"]))
    if not item.abstract:
        background = mermaid_label("当前未获取摘要，仅能基于标题保留待读节点")
        method = mermaid_label("待下载或解析 PDF 后补充方法")
        evidence = mermaid_label("待解析实验或论证内容")
        conclusion = mermaid_label("暂不判断结论")
    return [
        "flowchart LR",
        f"  A[\"主题：{title}\"] --> B[\"背景：{background}\"]",
        f"  B --> C[\"方法：{method}\"]",
        f"  C --> D[\"实验/论证：{evidence}\"]",
        f"  D --> E[\"结论：{conclusion}\"]",
    ]


def extract_logic(sentences: list[str]) -> dict[str, str]:
    background = pick_complete_sentence(sentences, 0)
    method = pick_sentence_by_keywords(
        sentences,
        ["we propose", "we present", "we introduce", "we develop", "we design", "to address", "to fill", "we construct", "we build"],
        fallback_index=1,
        avoid={background},
    )
    evidence = pick_sentence_by_keywords(
        sentences,
        ["experiment", "benchmark", "evaluate", "evaluation", "dataset", "manual verification", "results show", "experiments show"],
        fallback_index=2,
        avoid={background, method},
    )
    conclusion = pick_sentence_by_keywords(
        sentences,
        ["outperform", "improve", "achieve", "demonstrate", "superior", "reveal", "find", "indicate", "conclude", "show that"],
        fallback_index=3,
        avoid={background, method},
    )
    if conclusion in {background, method}:
        conclusion = pick_complete_sentence([s for s in sentences if s not in {background, method, evidence}], 0)
    return {
        "background": background,
        "method": method,
        "evidence": evidence,
        "conclusion": conclusion,
    }


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [part.strip() for part in parts if len(part.strip()) > 12]


def pick_complete_sentence(sentences: list[str], index: int) -> str:
    if not sentences:
        return "未获取到可追溯摘要。"
    return sentences[min(index, len(sentences) - 1)]


def pick_sentence_by_keywords(
    sentences: list[str],
    keywords: list[str],
    fallback_index: int,
    avoid: set[str] | None = None,
) -> str:
    avoid = avoid or set()
    for sentence in sentences:
        if sentence in avoid:
            continue
        low = sentence.lower()
        if any(keyword in low for keyword in keywords):
            return sentence
    remaining = [sentence for sentence in sentences if sentence not in avoid]
    return pick_complete_sentence(remaining or sentences, min(fallback_index, max(0, len(remaining) - 1)))


def translate_sentence(sentence: str, max_len: int | None = None) -> str:
    # Deterministic Chinese framing without inventing new facts; keep source wording when precise translation is risky.
    sentence = sentence.strip()
    replacements = [
        ("Recent ", "近期，"),
        ("This paper ", "本文"),
        ("In this paper, ", "本文中，"),
        ("We propose ", "作者提出"),
        ("We present ", "作者提出"),
        ("We introduce ", "作者引入"),
        ("Our results show ", "实验结果显示"),
        ("Results show ", "结果显示"),
        ("The results show ", "结果显示"),
        ("Experiments show ", "实验显示"),
    ]
    for src, dst in replacements:
        if sentence.startswith(src):
            sentence = dst + sentence[len(src):]
            break
    if max_len:
        return shorten(sentence, max_len)
    return sentence


def shorten(text: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rstrip()
    return cut + "…"


def mermaid_label(text: str) -> str:
    return text.replace('"', "'").replace("\n", " ")


def product_angle(item: Candidate) -> str:
    text = f"{item.title} {item.abstract}".lower()
    if "agent" in text or "tool" in text or "gui" in text:
        return "可能关联到办公自动化、浏览器操作代理、客服后台操作、数据录入与质检流程；需读完方法和实验后再判断可落地程度。"
    if "multimodal" in text or "vision" in text or "video" in text:
        return "可能关联到多模态内容理解、图片/视频审核、素材生产、视觉问答或交互式产品体验。"
    if "coding agent" in text or "code generation" in text or "program synthesis" in text:
        return "可能关联到 AI 编程助手、代码审查、研发效率工具和自动化测试。"
    if "retrieval" in text or has_word(text, "rag"):
        return "可能关联到企业知识库、搜索增强问答、客服知识检索和内部文档助手。"
    return "暂不判断。当前元信息不足以推出明确产品实践方向。"


def has_word(text: str, word: str) -> bool:
    import re

    return re.search(rf"\b{re.escape(word.lower())}\b", text) is not None


def write_report(markdown: str, reports_dir: str | Path, title_prefix: str = "daily-ai-brief") -> Path:
    out_dir = Path(reports_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{title_prefix}-{datetime.now():%Y%m%d-%H%M%S}.md"
    path = out_dir / name
    path.write_text(markdown, encoding="utf-8")
    return path
