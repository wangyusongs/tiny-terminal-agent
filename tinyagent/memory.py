"""Bounded context manager: retain recent turns and compact older observations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Memory:
    max_chars: int = 5000
    messages: list[tuple[str, str]] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append((role, content))
        self._compact()

    def _compact(self) -> None:
        while sum(len(x[1]) for x in self.messages) > self.max_chars and len(self.messages) > 2:
            role, content = self.messages.pop(0)
            compact = content.replace("\n", " ")[:240]
            self.summary.append(f"{role}: {compact}")
        self.summary = self.summary[-8:]

    def render(self) -> str:
        parts: list[str] = []
        if self.summary:
            parts.append("COMPACTED HISTORY:\n" + "\n".join(self.summary))
        parts.extend(f"{role.upper()}: {content}" for role, content in self.messages)
        return "\n\n".join(parts)
