"""A narrow terminal tool started in the chosen workspace with safety guardrails."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolResult:
    ok: bool
    output: str


class ShellTool:
    BLOCKED = ("rm -rf", "rmdir /s", "del /s", "format ", "shutdown", "reboot", "git reset --hard")

    def __init__(self, workspace: str | Path, timeout: int = 20) -> None:
        self.workspace = Path(workspace).resolve()
        self.timeout = timeout

    def run(self, command: str) -> ToolResult:
        normalized = command.lower().strip()
        if any(token in normalized for token in self.BLOCKED):
            return ToolResult(False, "Rejected by terminal safety policy.")
        try:
            invocation = command if os.name != "nt" else ["powershell.exe", "-NoProfile", "-Command", command]
            proc = subprocess.run(invocation, cwd=self.workspace, shell=os.name != "nt", text=True,
                                  encoding="utf-8", errors="replace", capture_output=True,
                                  timeout=self.timeout, env={**os.environ, "NO_COLOR": "1"})
        except subprocess.TimeoutExpired:
            return ToolResult(False, f"Timed out after {self.timeout} seconds.")
        output = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return ToolResult(proc.returncode == 0, output[:2000] or "(no output)")
