# Tiny Terminal Agent

Tiny Terminal Agent is a compact, inspectable terminal agent designed for small instruction-tuned language models. It demonstrates structured planning, shell-tool invocation, observation, bounded context management, error repair, and a final answer.

## Why this project

Small models frequently fail at free-form function calling: they add prose, omit arguments, or lose an earlier tool result when a task takes several steps. This implementation makes the control surface deliberately small:

- a two-action JSON protocol (`tool` or `final`), validated before execution;
- a retry message when the model produces malformed JSON;
- a rolling memory buffer that compacts old turns instead of silently dropping all history;
- truncated tool observations (2,000 characters) and a fixed step budget;
- a local Ollama adapter, so a model such as `qwen2.5:3b` can run without a hosted API; and
- a deterministic `demo` provider for reproducible tests and demonstrations.

## Quick start

No third-party Python package is required.

```powershell
python -m tinyagent.cli "show the working directory" --provider demo
python -m unittest discover -s tests -v
```

To use a local model, install and run Ollama separately, then:

```powershell
python -m tinyagent.cli "list files in the current directory" --provider ollama --model qwen2.5:3b
```

## Architecture

```text
User task -> Memory -> model completion -> JSON validator
                                  |             |
                                  | invalid      | tool action
                                  v             v
                              repair prompt   ShellTool -> bounded observation
                                                    |
                                                    +-> Memory -> next model turn
```

The agent has at most six steps by default. A model can return a final answer at any turn. The protocol is intentionally simple enough to fine-tune or use with constrained decoding later.

## Safety scope

`ShellTool` starts subprocesses in the supplied workspace, has a timeout, and rejects several clearly destructive command patterns. It is a classroom prototype, **not a security sandbox**: do not give an untrusted model access to valuable data or a privileged machine. Production use should replace it with a containerised, allowlisted executor.

## Project structure

```text
tinyagent/
  protocol.py  strict action schema and parser
  memory.py    bounded rolling context
  llm.py       Ollama and deterministic demo adapters
  tools.py     terminal tool and safeguards
  agent.py     reason-act-observe loop
  cli.py       command-line interface
tests/         protocol, execution, and safety tests
docs/          academic English submission report
```

## Reproducing the evaluation

The included unit suite verifies protocol rejection, successful tool execution, and rejection of a destructive command pattern. The demo provider exercises an end-to-end model-to-tool-to-final-answer trace without downloading a model. Run the commands in **Quick start**; the expected result is three passing unit tests and one successful `cd` tool call.

## AI assistance disclosure

This project was developed with AI assistance for implementation planning, code drafting, and English technical writing. The code path and tests were executed locally; the report distinguishes validated results from proposed extensions.
