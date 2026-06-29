from pathlib import Path

import pytest
from paper_to_deck.security import (
    PathTraversalError,
    UnsafeAssetError,
    safe_join,
    escape_text,
    safe_asset_src,
)


def test_safe_join_allows_child(tmp_path):
    result = safe_join(tmp_path, "assets", "f1.png")
    assert str(result).startswith(str(tmp_path.resolve()))


def test_safe_join_blocks_traversal(tmp_path):
    with pytest.raises(PathTraversalError):
        safe_join(tmp_path, "..", "..", "etc", "passwd")


def test_escape_text_neutralizes_markup():
    assert escape_text("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_safe_asset_src_accepts_local_image():
    assert safe_asset_src("assets/fig_1.png") == "assets/fig_1.png"


@pytest.mark.parametrize("bad", [
    "javascript:alert(1)",
    "https://evil.com/x.png",
    "assets/../../etc/passwd",
    "/etc/passwd",
    "assets/note.txt",
])
def test_safe_asset_src_rejects_dangerous(bad):
    with pytest.raises(UnsafeAssetError):
        safe_asset_src(bad)
