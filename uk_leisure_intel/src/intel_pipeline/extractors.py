from __future__ import annotations

import re
from typing import Iterable, List

from .models import CollectedDocument


URL_PATTERN = re.compile(r"https?://[^\s\]\)\>\"']+")
REF_PATTERN = re.compile(
    r"(OCID[-\w]*|notice\s*id[:\s]*[\w-]+|planning\s*(application|ref)[:\s]*[\w/-]+|contract\s*award)",
    re.IGNORECASE,
)


def extract_relevant_snippets(
    documents: Iterable[CollectedDocument], council: str, operators: List[str], window: int = 260
) -> List[dict]:
    targets = [council.lower()] + [o.lower() for o in operators]
    findings: List[dict] = []

    for doc in documents:
        text = doc.content or ""
        lowered = text.lower()
        if not lowered:
            continue

        for target in targets:
            for match in re.finditer(re.escape(target), lowered):
                start = max(0, match.start() - window)
                end = min(len(text), match.end() + window)
                snippet = text[start:end].strip()
                refs = list(dict.fromkeys(URL_PATTERN.findall(snippet) + [m[0] for m in REF_PATTERN.findall(snippet)]))

                findings.append(
                    {
                        "document": doc,
                        "snippet": re.sub(r"\s+", " ", snippet),
                        "references": refs,
                        "match_term": target,
                    }
                )

        # fallback: include documents that mention key procurement domains even if target matching is sparse
        key_terms = ["cabinet", "budget", "planning", "tender", "payments"]
        if not any(t in lowered for t in targets) and any(k in lowered for k in key_terms):
            snippet = re.sub(r"\s+", " ", text[: 2 * window])
            refs = list(dict.fromkeys(URL_PATTERN.findall(snippet) + [m[0] for m in REF_PATTERN.findall(snippet)]))
            findings.append(
                {
                    "document": doc,
                    "snippet": snippet,
                    "references": refs,
                    "match_term": "contextual-keyword",
                }
            )

    return findings
