"""Behavior tests for the contributor-attribution comparison range."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "contributor_base.py"
_spec = importlib.util.spec_from_file_location("contributor_base", _PATH)
if _spec is None or _spec.loader is None:
    raise ImportError("Failed to load contributor_base.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
comparison_base = _mod.comparison_base


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _commit(repo: Path, name: str, email: str) -> str:
    marker = repo / f"{name}.txt"
    marker.write_text(name, encoding="utf-8")
    _git(repo, "add", marker.name)
    _git(
        repo,
        "-c",
        f"user.name={name}",
        "-c",
        f"user.email={email}",
        "commit",
        "-qm",
        name,
    )
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    root = _commit(path, "root", "root@example.com")
    _git(path, "remote", "add", "origin", path.as_uri())
    _git(path, "update-ref", "refs/remotes/origin/main", root)
    return path


def test_pull_request_uses_event_base_sha_not_origin_main(repo: Path, tmp_path: Path):
    pr_base = _commit(repo, "compatible-base", "base@example.com")
    _git(repo, "switch", "-q", "-c", "feature")
    _commit(repo, "feature", "feature@example.com")
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"pull_request": {"base": {"sha": pr_base, "ref": "compatible-base"}}}),
        encoding="utf-8",
    )

    assert comparison_base("pull_request", event, repo) == pr_base


def test_pull_request_rejects_malformed_event_base_sha(repo: Path, tmp_path: Path):
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"pull_request": {"base": {"sha": "origin/main; echo unsafe"}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="40-character hexadecimal"):
        comparison_base("pull_request", event, repo)


def test_push_keeps_origin_main_merge_base_semantics(repo: Path):
    root = _git(repo, "rev-parse", "refs/remotes/origin/main")
    _commit(repo, "push", "push@example.com")

    assert comparison_base("push", None, repo) == root
