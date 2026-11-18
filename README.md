# Shared Files vs. Message Passing for Multi-Agent Communication

CS632 term project. We replay the operating-systems comparison of IPC styles with LLM agents: a
Researcher, a Writer and a Reviewer solve the same task with the same model in the same order, and
only the channel between them changes.

| Channel | How agents exchange results |
| --- | --- |
| A · Message passing | The previous agent's whole output is copied into the next prompt. |
| B · Shared file workspace | Agents write files and read what they need through file tools. |
| C · Shared workspace + index | B plus an index file that says what each file holds. |

We measure task success, total tokens, workspace file I/O, and information loss (key facts
dropped between stages).

## Setup

```bash
source env.local.sh                       # local paths (not committed)
uv venv $STORE/venv && ln -sfn $STORE/venv .venv
uv pip install -p .venv -e ".[dev]"
pytest -q
```

Model: `Qwen/Qwen3-8B` served by vLLM v0.33.0 on one RTX 3090.

## Layout

```
configs/        experiment configs (every run starts from one)
src/agentipc/   datasets, agents, channels, metrics, analysis
tests/
results/<exp>/<run_id>/   config.yaml, env.json, summary.json
figures/        png and the csv each one plots
reports/        final report
```
