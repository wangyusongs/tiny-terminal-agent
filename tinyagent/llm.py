"""Minimal model adapters. Ollama keeps inference local and dependency-free."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class Model(Protocol):
    def complete(self, prompt: str) -> str: ...


class OllamaModel:
    def __init__(self, model: str, endpoint: str | None = None) -> None:
        host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
        self.model = model
        self.endpoint = endpoint or f"http://{host.removeprefix('http://').removeprefix('https://').rstrip('/')}/api/generate"

    def complete(self, prompt: str) -> str:
        data = json.dumps({"model": self.model, "prompt": prompt, "stream": False,
                           "think": False,
                           "options": {"temperature": 0, "num_predict": 96}}).encode()
        request = urllib.request.Request(self.endpoint, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read())["response"]


class DemoModel:
    """Deterministic offline demonstrator, useful for CI and the report examples."""
    def complete(self, prompt: str) -> str:
        lower = prompt.lower()
        if "tool_result:" not in lower:
            command = "cd" if "where" in lower or "directory" in lower else "echo tinyagent-demo"
            return json.dumps({"type": "tool", "tool": "shell", "command": command})
        result = prompt.rsplit("TOOL_RESULT:", 1)[-1].strip().split("\n\n", 1)[0]
        return json.dumps({"type": "final", "answer": f"Completed the requested terminal step. Output: {result[:300]}"})
