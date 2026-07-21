"""Run a transparent baseline-vs-optimised evaluation on a local Ollama model.

The suite uses a disposable workspace and non-destructive read-only terminal
tasks. It produces JSON, so the report can quote only measured values.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from tinyagent.agent import Agent
from tinyagent.llm import OllamaModel
from tinyagent.tools import ShellTool

ROOT = Path(__file__).parent / "eval_workspace"

@dataclass
class Record:
    condition: str
    task_id: str
    valid_action: bool
    completed: bool
    steps: int
    detail: str

TASKS = [
    ("find_token", "Find the file that contains the token BLUE-CEDAR-91 and report its file name and the token."),
    ("count_logs", "Count how many .log files are in the current directory and report only the number."),
    ("read_config", "Read config.txt and report the value assigned to mode."),
]

def setup_workspace() -> None:
    if ROOT.exists(): shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    (ROOT / "notes.txt").write_text("ordinary note\n", encoding="utf-8")
    (ROOT / "target.txt").write_text("token=BLUE-CEDAR-91\n", encoding="utf-8")
    (ROOT / "config.txt").write_text("mode=compact\nretries=2\n", encoding="utf-8")
    (ROOT / "first.log").write_text("a\n", encoding="utf-8")
    (ROOT / "second.log").write_text("b\n", encoding="utf-8")

def is_complete(task_id: str, answer: str) -> bool:
    text = answer.lower()
    return {
        "find_token": "target.txt" in text and "blue-cedar-91" in text,
        "count_logs": bool(re.search(r"\b2\b", text)),
        "read_config": "compact" in text,
    }[task_id]

def baseline(model: OllamaModel, task_id: str, task: str) -> Record:
    prompt = ("You can operate a Windows PowerShell terminal. Solve this task. "
              "If you need a command, answer exactly COMMAND: <one command>. "
              "Otherwise answer FINAL: <answer>.\nTASK: " + task)
    first = model.complete(prompt).strip()
    match = re.fullmatch(r"COMMAND:\s*(.+)", first, flags=re.S)
    if not match:
        final = re.fullmatch(r"FINAL:\s*(.+)", first, flags=re.S)
        answer = final.group(1) if final else first
        return Record("baseline", task_id, bool(final), is_complete(task_id, answer), 1, answer[:300])
    result = ShellTool(ROOT).run(match.group(1).strip())
    second = model.complete(prompt + "\nCOMMAND_OUTPUT: " + result.output + "\nNow answer FINAL: <answer>. ").strip()
    final = re.fullmatch(r"FINAL:\s*(.+)", second, flags=re.S)
    answer = final.group(1) if final else second
    return Record("baseline", task_id, bool(final), is_complete(task_id, answer), 2, answer[:300])

def optimised(model: OllamaModel, task_id: str, task: str) -> Record:
    try:
        result = Agent(model, ROOT, max_steps=4).run(task)
        return Record("optimised", task_id, True, is_complete(task_id, result.answer), result.steps, result.answer[:300])
    except Exception as exc:
        return Record("optimised", task_id, False, False, 0, f"ERROR: {type(exc).__name__}: {exc}"[:300])

def safe_baseline(model: OllamaModel, task_id: str, task: str) -> Record:
    try:
        return baseline(model, task_id, task)
    except Exception as exc:
        return Record("baseline", task_id, False, False, 0, f"ERROR: {type(exc).__name__}: {exc}"[:300])

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", default="benchmarks/results.json")
    parser.add_argument("--endpoint", default=None, help="Optional Ollama /api/generate endpoint")
    args = parser.parse_args()
    setup_workspace(); model = OllamaModel(args.model, endpoint=args.endpoint)
    records = []
    for condition, runner in (("baseline", safe_baseline), ("optimised", optimised)):
        for task_id, task in TASKS:
            records.append(runner(model, task_id, task))
            Path(args.out).write_text(json.dumps([asdict(r) for r in records], indent=2), encoding="utf-8")
    for condition in ("baseline", "optimised"):
        group = [r for r in records if r.condition == condition]
        print(condition, "valid_action_rate=", sum(r.valid_action for r in group)/len(group),
              "completion_rate=", sum(r.completed for r in group)/len(group))

if __name__ == "__main__": main()
