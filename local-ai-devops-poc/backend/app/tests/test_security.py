"""
Tests for core utilities: config and security.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from app.core.security import UnsafePathError, ensure_child_path


class TestEnsureChildPath:
    def test_child_is_allowed(self, tmp_path: Path) -> None:
        child = tmp_path / "subdir" / "file.txt"
        child.parent.mkdir()
        child.touch()
        result = ensure_child_path(tmp_path, child)
        assert result == child.resolve()

    def test_base_itself_is_allowed(self, tmp_path: Path) -> None:
        result = ensure_child_path(tmp_path, tmp_path)
        assert result == tmp_path.resolve()

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        evil = tmp_path / ".." / "etc" / "passwd"
        with pytest.raises(UnsafePathError):
            ensure_child_path(tmp_path, evil)

    def test_sibling_directory_blocked(self, tmp_path: Path) -> None:
        sibling = tmp_path.parent / "other_dir"
        sibling.mkdir(exist_ok=True)
        with pytest.raises(UnsafePathError):
            ensure_child_path(tmp_path, sibling)
