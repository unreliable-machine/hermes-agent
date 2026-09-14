#!/usr/bin/env python3
"""Select the commit that contributor attribution should compare against.

Pull-request runs use the immutable base SHA from the GitHub event. Push runs
retain the historical ``merge-base origin/main HEAD`` behavior.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _pull_request_base(event_path: Path | None) -> str:
    if event_path is None:
        raise ValueError("GITHUB_EVENT_PATH is required for pull_request attribution")
    with event_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    base_sha = ((payload.get("pull_request") or {}).get("base") or {}).get("sha")
    if not isinstance(base_sha, str) or _SHA_RE.fullmatch(base_sha) is None:
        raise ValueError("pull_request.base.sha must be a 40-character hexadecimal commit SHA")
    return base_sha


def comparison_base(event_name: str, event_path: Path | None, repo: Path) -> str:
    """Return a verified comparison commit for the current Actions event."""
    if event_name == "pull_request":
        base = _pull_request_base(event_path)
        return _git(repo, "rev-parse", "--verify", f"{base}^{{commit}}")
    return _git(repo, "merge-base", "origin/main", "HEAD")


def main() -> int:
    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    event_path = Path(event_path_value) if event_path_value else None
    try:
        base = comparison_base(
            os.environ.get("GITHUB_EVENT_NAME", ""),
            event_path,
            Path.cwd(),
        )
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"contributor base selection failed: {exc}", file=sys.stderr)
        return 1
    print(base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
