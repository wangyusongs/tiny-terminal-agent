import json
import tempfile
import unittest
from pathlib import Path

from tinyagent.agent import Agent
from tinyagent.protocol import parse_action
from tinyagent.tools import ShellTool


class ScriptedModel:
    def __init__(self, replies): self.replies = iter(replies)
    def complete(self, prompt): return next(self.replies)


class AgentTests(unittest.TestCase):
    def test_protocol_rejects_prose(self):
        with self.assertRaises(ValueError): parse_action("I will run a command")

    def test_protocol_accepts_fenced_json_from_small_model(self):
        action = parse_action("```json\n{\"type\":\"final\",\"answer\":\"done\"}\n```")
        self.assertEqual(action.answer, "done")

    def test_agent_executes_and_finishes(self):
        model = ScriptedModel([
            json.dumps({"type":"tool","tool":"shell","command":"echo hello"}),
            json.dumps({"type":"final","answer":"done"}),
        ])
        with tempfile.TemporaryDirectory() as directory:
            result = Agent(model, directory).run("say hello")
        self.assertEqual(result.answer, "done")
        self.assertEqual(len(result.trace), 1)

    def test_safety_policy_blocks_destructive_command(self):
        with tempfile.TemporaryDirectory() as directory:
            result = ShellTool(Path(directory)).run("rm -rf /")
        self.assertFalse(result.ok)


if __name__ == "__main__": unittest.main()
