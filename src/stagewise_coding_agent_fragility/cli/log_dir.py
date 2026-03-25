"""Helpers for resolving experiment log directories for analysis CLIs."""

from __future__ import annotations

from pathlib import Path


def resolve_log_dir(log_dir: str | Path, latest: bool = False) -> Path:
    """Resolve a directory that directly contains run-log JSON files.

    Args:
        log_dir: User-supplied directory path.
        latest: Whether selecting the newest eligible child directory is allowed.

    Returns:
        A directory path that directly contains ``*.json`` run logs.

    Raises:
        ValueError: If the path cannot be resolved to a direct run-log directory.
    """
    path = Path(log_dir)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Log directory does not exist: {path}")

    if _contains_run_logs(path):
        return path

    if not latest:
        raise ValueError(
            f"{path} does not directly contain run-log JSON files. "
            "Pass the exact timestamped run directory, or add --latest to select "
            "the newest eligible child directory explicitly."
        )

    candidates = [child for child in path.iterdir() if child.is_dir() and _contains_run_logs(child)]
    if not candidates:
        raise ValueError(
            f"No child directories with run-log JSON files were found under {path}."
        )
    return max(candidates, key=lambda child: child.stat().st_mtime)


def _contains_run_logs(path: Path) -> bool:
    """Return whether ``path`` directly contains at least one JSON log file."""
    return any(path.glob("*.json"))