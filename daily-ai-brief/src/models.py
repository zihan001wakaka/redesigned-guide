from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Candidate:
    title: str
    url: str
    source: str
    source_type: str
    published: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    pdf_url: str = ""
    venue: str = ""
    citation_count: int = 0
    extra_links: dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    score_reasons: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        normalized = "".join(ch.lower() for ch in self.title if ch.isalnum())
        return normalized[:160]
