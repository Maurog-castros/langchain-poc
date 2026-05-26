from __future__ import annotations

from pathlib import Path


class UnsafePathError(ValueError):
    pass


def ensure_child_path(base_dir: Path, candidate: Path) -> Path:
    """Block path traversal for local document/model operations."""

    base = base_dir.resolve()
    target = candidate.resolve()
    if base != target and base not in target.parents:
        raise UnsafePathError(f"path outside allowed directory: {target}")
    return target
