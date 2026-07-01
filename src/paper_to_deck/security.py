from __future__ import annotations

"""Security guardrails for filesystem access and HTML rendering.

Prevents path traversal and XSS via strict validation functions.
"""

import html
import re
from pathlib import Path

_IMAGE_RE = re.compile(r"^assets/[A-Za-z0-9_\-]+\.(png|jpg|jpeg)$")


class PathTraversalError(Exception):
    pass


class UnsafeAssetError(Exception):
    pass


def safe_join(base: Path, *parts: str) -> Path:
    # Guarantees that the resolved path must stay under the sandbox root
    base_resolved = Path(base).resolve()
    candidate = base_resolved.joinpath(*parts).resolve()
    if base_resolved != candidate and base_resolved not in candidate.parents:
        raise PathTraversalError(f"path escapes sandbox: {candidate}")
    return candidate


def escape_text(value: str) -> str:
    return html.escape(value, quote=True)


def safe_asset_src(src: str) -> str:
    # Only allows assets/<name>.(png|jpg|jpeg) to block path traversal and non-image src injection
    if ".." in src or src.startswith("/") or not _IMAGE_RE.match(src):
        raise UnsafeAssetError(f"unsafe asset src: {src!r}")
    return src
