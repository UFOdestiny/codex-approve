#!/usr/bin/env python3
"""Apply the configured policy to Codex PermissionRequest events."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

SANDBOX_KEYWORD = re.compile(r"沙盒|sandbox", re.IGNORECASE)
LEVELS = {"codex", "retry_without_sandbox", "all"}
DEFAULT_LEVEL = "all"


def _config_path() -> Path | None:
    explicit = os.environ.get("CODEX_AUTO_APPROVE_CONFIG")
    if explicit:
        return Path(explicit)
    data = os.environ.get("PLUGIN_DATA")
    if data and (Path(data) / "config.json").is_file():
        return Path(data) / "config.json"
    root = os.environ.get("PLUGIN_ROOT")
    if root and (Path(root) / "config.json").is_file():
        return Path(root) / "config.json"
    return None


def _load_config() -> dict:
    path = _config_path()
    if path is None:
        return {"default_level": DEFAULT_LEVEL, "projects": {}}
    with path.open(encoding="utf-8") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError("config must be an object")
    default = config.get("default_level", DEFAULT_LEVEL)
    projects = config.get("projects", {})
    if default not in LEVELS or not isinstance(projects, dict):
        raise ValueError("invalid default_level or projects")
    for project, level in projects.items():
        if not isinstance(project, str) or not Path(project).is_absolute() or level not in LEVELS:
            raise ValueError("project rules need absolute paths and valid levels")
    return {"default_level": default, "projects": projects}


def _level(config: dict, cwd: object) -> str:
    override = os.environ.get("CODEX_AUTO_APPROVE_LEVEL")
    if override is not None:
        if override not in LEVELS:
            raise ValueError("invalid CODEX_AUTO_APPROVE_LEVEL")
        return override
    level = config["default_level"]
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        return level
    current = Path(cwd).resolve()
    best_depth = -1
    for project, project_level in config["projects"].items():
        root = Path(project).resolve()
        if current == root or root in current.parents:
            depth = len(root.parts)
            if depth > best_depth:
                best_depth = depth
                level = project_level
    return level


def _mentions_sandbox(description: str) -> bool:
    return SANDBOX_KEYWORD.search(description) is not None


def _log_approval(payload: dict, description: str | None, level: str) -> None:
    """Write a best-effort audit record without affecting the decision."""
    data_dir = os.environ.get("PLUGIN_DATA")
    if not data_dir:
        return
    try:
        path = Path(data_dir)
        path.mkdir(parents=True, exist_ok=True)
        record = {
            "time_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "level": level,
            "tool_name": payload.get("tool_name"),
            "cwd": payload.get("cwd"),
            "description": description,
        }
        with (path / "approvals.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, TypeError, ValueError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "PermissionRequest":
            return 0
        level = _level(_load_config(), payload.get("cwd"))
    except (OSError, ValueError, TypeError, RuntimeError):
        # Invalid input or configuration: leave the decision to Codex.
        return 0

    if level == "codex":
        return 0

    tool_input = payload.get("tool_input")
    description = tool_input.get("description") if isinstance(tool_input, dict) else None
    if level == "retry_without_sandbox" and (
        not isinstance(description, str) or not _mentions_sandbox(description)
    ):
        return 0

    _log_approval(payload, description if isinstance(description, str) else None, level)
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}},
        sys.stdout,
        separators=(",", ":"),
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
