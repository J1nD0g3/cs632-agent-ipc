# Progress

| Task | Phase | Priority | Status | Updated | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T00 Preflight and repo setup | Setup | Must | Done | 2026-11-18 | Repo, Notion sync, Qwen3-8B (16 GB) | |
| T01 vLLM server, smoke test, throughput | Setup | Must | In progress | 2026-11-18 | | GPU 5 |
| T02 Task data: loaders, samples, key facts | Build | Must | In progress | 2026-11-18 | HotpotQA 6947 / 2Wiki 11281 usable dev questions | |
| T03 Agent runtime: roles, prompts, tools, logging | Build | Must | In progress | 2026-11-18 | Mock-tested | Needs a real-model check |
| T04 Channels A1/A2/B/C/D and zero-copy A1 | Build | Must | In progress | 2026-11-18 | A1/B/C mock-tested | A2, D, A1-zc to add |
| T05 Metrics: success, tokens, latency, I/O, loss, failure types | Build | Must | In progress | 2026-11-18 | Lexical fact matching | Judge check pending |
| T06 Pilot run and checks | Experiments | Must | Not started | | | |
| T07 Main experiments: 5 channels x 2 datasets x 3 k | Experiments | Must | Not started | | | Qwen3-8B |
| T08 Sensitivity: k = 8, five agents, zero-copy A1, Qwen3-4B | Experiments | Should | Not started | | | |
| T09 Analysis and figures | Report | Must | Not started | | | |
| T10 Workshop paper and review rounds | Report | Must | Not started | | | 6 pages |

## Key numbers
| Key | Metric | Result | Source |
| --- | --- | --- | --- |
| success | Task success rate: A / B / C | | |
| tokens | Total tokens per task: A / B / C | | |
| file_io | File reads and writes per task: A / B / C | | |
| info_loss | Key facts lost between stages: A / B / C | | |
| recommendation | Which channel, and when | | |

## Log
- 2026-11-18 T00: Repo created from the proposal. Model Qwen3-8B (thinking off) on vLLM v0.33.0;
  datasets HotpotQA (distractor) and 2WikiMultihopQA dev. Deadline 2026-12-02; scope ends at the
  final report (no slides).
- 2026-11-18 T02–T05 plan: tasks bundle k questions (k = 1, 3, 5) so the volume passed between
  agents grows; documents are the union of their paragraphs. The Researcher gets the same input in
  every channel. A copies the whole history (task, documents, notes, draft) forward, as AutoGen group
  chat does; B and C give later agents only the questions and file tools; C adds index.md. Success is
  answer accuracy (EM, F1 >= 0.8, or the gold answer inside a short prediction); information loss is
  the share of supporting facts found in the notes that are missing from the final answer. Fact
  presence is lexical for now and will be checked against an LLM judge in T05.
- 2026-11-18 T02: HotpotQA distractor dev (7405, 6947 usable after dropping yes/no answers and
  questions with fewer than 2 supporting sentences) and 2WikiMultihopQA dev (12576, 11281 usable).
  Documents per task: about 10 / 30 / 50 for k = 1 / 3 / 5 (HotpotQA about 28k characters at k = 5).
- 2026-11-18 Plan (approved): the goal is now a 6-page workshop paper. Working title "Pipes, Files,
  or Handles? Revisiting IPC for LLM Multi-Agent Pipelines". Five channels: A1 broadcast (whole
  history, as now), A2 pipe (previous output only), B files, C files + index, D handles (proposed:
  push a short summary with file locations, pull details from files). Cost is reported three ways:
  logical tokens (API billing), prefill actually computed (self-hosted, after prefix caching), and
  latency. Sensitivity: k = 8, a five-agent pipeline, zero-copy A1 (shared history first, role
  instruction last, so the prefix cache is reused), and Qwen3-4B as a second size of the same model
  family. 150 tasks per condition, the same tasks for every channel, bootstrap 95% CIs. GPU 5 only.
