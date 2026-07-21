from __future__ import annotations

import argparse
from pathlib import Path

from .agent import Agent
from .llm import DemoModel, OllamaModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Small-model-friendly terminal agent")
    parser.add_argument("task", help="Natural-language task for the agent")
    parser.add_argument("--provider", choices=("demo", "ollama"), default="demo")
    parser.add_argument("--model", default="qwen2.5:3b", help="Ollama model tag")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args()
    model = DemoModel() if args.provider == "demo" else OllamaModel(args.model)
    result = Agent(model, Path(args.workspace), args.max_steps).run(args.task)
    print(result.answer)
    print("\nTrace:")
    print("\n".join(result.trace) or "(no tool calls)")


if __name__ == "__main__":
    main()
