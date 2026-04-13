from __future__ import annotations

import glob
import json
import re
from html import unescape
from pathlib import Path
from typing import Iterable, List
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import CollectedDocument, SourceItem

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None


def collect_documents(sources: Iterable[SourceItem]) -> List[CollectedDocument]:
    documents: List[CollectedDocument] = []
    for source in sources:
        if not source.enabled:
            continue

        if source.type == "url":
            doc = _collect_from_url(source)
            if doc:
                documents.append(doc)
        elif source.type == "file":
            doc = _collect_from_file(source, source.value)
            if doc:
                documents.append(doc)
        elif source.type == "glob":
            for path in glob.glob(source.value, recursive=True):
                doc = _collect_from_file(source, path)
                if doc:
                    documents.append(doc)
    return documents


def _collect_from_url(source: SourceItem) -> CollectedDocument | None:
    html = ""
    if requests is not None:
        try:
            response = requests.get(source.value, timeout=25)
            response.raise_for_status()
            html = response.text
        except Exception:
            return None
    else:
        try:
            req = Request(source.value, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=25) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except (URLError, ValueError, TimeoutError):
            return None

    title, text = _html_to_text_and_title(html, fallback_title=source.name)
    return CollectedDocument(
        source_name=source.name,
        source_type=source.type,
        source_value=source.value,
        source_url=source.value,
        title=title,
        content=text,
    )


def _collect_from_file(source: SourceItem, file_path: str) -> CollectedDocument | None:
    path = Path(file_path)
    if not path.exists() or path.is_dir():
        return None

    suffix = path.suffix.lower()
    content = ""

    try:
        if suffix in {".txt", ".md", ".csv", ".log"}:
            content = path.read_text(encoding="utf-8", errors="ignore")
        elif suffix in {".json"}:
            parsed = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            content = json.dumps(parsed, ensure_ascii=False)
        elif suffix in {".html", ".htm"}:
            html = path.read_text(encoding="utf-8", errors="ignore")
            title, text = _html_to_text_and_title(html, fallback_title=path.stem)
            return CollectedDocument(
                source_name=source.name,
                source_type=source.type,
                source_value=source.value,
                title=title,
                content=text,
                local_path=str(path),
            )
        elif suffix == ".pdf":
            content = _read_pdf(path)
        else:
            return None
    except Exception:
        return None

    return CollectedDocument(
        source_name=source.name,
        source_type=source.type,
        source_value=source.value,
        title=path.stem,
        content=content,
        local_path=str(path),
    )


def _html_to_text_and_title(html: str, fallback_title: str) -> tuple[str, str]:
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else fallback_title
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
        return title, text

    title_match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = unescape(title_match.group(1).strip()) if title_match else fallback_title
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return title, text


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return "PDF detected but pypdf is unavailable; add pypdf to extract text."

    try:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks).strip()
    except Exception:
        return ""
