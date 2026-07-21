"""Strict, compact action protocol designed for small instruction-tuned models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Action:
    kind: str
    command: str = ""
    answer: str = ""


SYSTEM_PROMPT = """You are a terminal agent running in a Windows PowerShell workspace. Return ONLY one JSON object.
Valid actions:
  {\"type\":\"tool\",\"tool\":\"shell\",\"command\":\"...\"}
  {\"type\":\"final\",\"answer\":\"...\"}
Use shell only for a necessary, safe PowerShell command. The current directory
is the workspace: never use an absolute path or a guessed filename. Start by
inspecting unknown files. Useful commands are Get-ChildItem,
Get-Content -Raw FILE, Get-ChildItem -File | Select-String -Pattern 'TOKEN', and
(Get-ChildItem -Filter '*.log').Count. If a user asks which file contains a
token, search file CONTENT using Select-String; do not search file names. Never
invent a tool result. After a
tool result, decide the next action and give the factual answer, not a
placeholder. Never add Markdown, explanation, or keys not shown above."""


def parse_action(text: str) -> Action:
    """Parse and validate a model completion; reject ambiguous outputs."""
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = "\n".join(cleaned.splitlines()[1:-1]).strip()
    try:
        value: Any = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("completion is not valid JSON") from exc
    if not isinstance(value, dict) or set(value) - {"type", "tool", "command", "answer"}:
        raise ValueError("completion has an invalid schema")
    kind = value.get("type")
    if kind == "tool" and value.get("tool") == "shell" and isinstance(value.get("command"), str):
        command = value["command"].strip()
        if command:
            return Action(kind="tool", command=command)
    if kind == "final" and isinstance(value.get("answer"), str):
        return Action(kind="final", answer=value["answer"].strip())
    raise ValueError("completion is not a supported action")
