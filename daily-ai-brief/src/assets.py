from __future__ import annotations

import re
from pathlib import Path

from .http import get_bytes
from .models import Candidate


def download_selected_assets(selected: list[Candidate], data_dir: str | Path = "data") -> None:
    out_dir = Path(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(selected, start=1):
        if not item.pdf_url:
            continue
        name = f"{index:02d}-{slugify(item.title)}.pdf"
        path = out_dir / name
        if path.exists() and path.stat().st_size > 0:
            item.extra_links["local_pdf"] = str(path)
            continue
        try:
            path.write_bytes(get_bytes(item.pdf_url))
            item.extra_links["local_pdf"] = str(path)
        except Exception as exc:
            item.extra_links["asset_error"] = str(exc)


def slugify(value: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return cleaned[:max_len] or "paper"
