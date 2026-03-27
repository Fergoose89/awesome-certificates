from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen


def fetch_url(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1] or "downloaded_file"
    target = out_dir / filename
    with urlopen(url, timeout=30) as response:
        target.write_bytes(response.read())
    return target
