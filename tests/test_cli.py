"""Tests for CLI helper behavior."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from stagewise_coding_agent_fragility.cli.log_dir import resolve_log_dir


def test_resolve_log_dir_accepts_directory_with_json_files(tmp_path: Path) -> None:
    """A direct run directory should be accepted unchanged."""
    run_dir = tmp_path / "run_a"
    run_dir.mkdir()
    (run_dir / "one.json").write_text("{}", encoding="utf-8")

    assert resolve_log_dir(run_dir) == run_dir


def test_resolve_log_dir_requires_explicit_latest_selection(tmp_path: Path) -> None:
    """A parent directory should fail loudly unless --latest is requested."""
    first = tmp_path / "run_a"
    second = tmp_path / "run_b"
    first.mkdir()
    second.mkdir()
    (first / "one.json").write_text("{}", encoding="utf-8")
    (second / "two.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="--latest"):
        resolve_log_dir(tmp_path)


def test_resolve_log_dir_selects_latest_child_when_requested(tmp_path: Path) -> None:
    """--latest should select the newest eligible child directory."""
    first = tmp_path / "run_a"
    second = tmp_path / "run_b"
    first.mkdir()
    (first / "one.json").write_text("{}", encoding="utf-8")
    time.sleep(0.01)
    second.mkdir()
    (second / "two.json").write_text("{}", encoding="utf-8")

    assert resolve_log_dir(tmp_path, latest=True) == second


def test_resolve_log_dir_rejects_latest_without_eligible_children(tmp_path: Path) -> None:
    """--latest should still fail if no child contains run logs."""
    (tmp_path / "empty_child").mkdir()

    with pytest.raises(ValueError, match="No child directories"):
        resolve_log_dir(tmp_path, latest=True)