"""Reason-act-observe loop with validation repair and compacted context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .llm import Model
from .memory import Memory
from .protocol import SYSTEM_PROMPT, parse_action
from .tools import ShellTool


@dataclass
class AgentResult:
    answer: str
    steps: int
    trace: list[str]


class Agent:
    def __init__(self, model: Model, workspace: str | Path, max_steps: int = 6) -> None:
        self.model, self.tool, self.max_steps = model, ShellTool(workspace), max_steps

    def run(self, task: str) -> AgentResult:
        memory = Memory()
        memory.add("user", task)
        trace: list[str] = []
        for step in range(1, self.max_steps + 1):
            completion = self.model.complete(f"{SYSTEM_PROMPT}\n\n{memory.render()}")
            try:
                action = parse_action(completion)
            except ValueError as exc:
                memory.add("repair", f"Your last output was rejected ({exc}). Return valid JSON only.")
                trace.append(f"step {step}: schema repair")
                continue
            if action.kind == "final":
                return AgentResult(action.answer, step, trace)
            result = self.tool.run(action.command)
            observation = f"TOOL_RESULT: ok={result.ok}; output={result.output}"
            memory.add("tool_result", observation)
            trace.append(f"step {step}: shell `{action.command}` -> {result.ok}")
        return AgentResult("Stopped because the step budget was exhausted.", self.max_steps, trace)
