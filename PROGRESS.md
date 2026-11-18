# Progress

| Task | Phase | Priority | Status | Updated | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T00 Preflight and repo setup | Setup | Must | Done | 2026-11-18 | Repo, Notion sync, Qwen3-8B (16 GB) | |
| T01 vLLM server, smoke test, throughput | Setup | Must | Done | 2026-11-18 | results/t01_smoke/20261118-205929-9eaaec7 | GPUs 5, 1, 2; 20 runs/min |
| T02 Task data: loaders, samples, key facts | Build | Must | Done | 2026-11-18 | HotpotQA 6947 / 2Wiki 11281 usable dev questions | |
| T03 Agent runtime: roles, prompts, tools, logging | Build | Must | Done | 2026-11-18 | Checked on Qwen3-8B in the pilot | |
| T04 Channels A1/A2/B/C/D and zero-copy A1 | Build | Must | Done | 2026-11-18 | Six channels, per-run cache_salt | Five-agent chain ready |
| T05 Metrics: success, tokens, latency, I/O, loss, failure types | Build | Must | Done | 2026-11-18 | LLM judge for facts (lexical agrees 87.5%, kappa 0.72) | |
| T06 Pilot run and checks | Experiments | Must | Done | 2026-11-18 | results/t06_pilot/20261118-210200-08f1221 | 360 runs, 0 errors |
| T07 Main experiments: 5 channels x 2 datasets x 3 k | Experiments | Must | In progress | 2026-11-18 | | 5400 runs, about 4.5 h |
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
- 2026-11-18 T01: vLLM v0.33.0 with Qwen3-8B on GPU 5 (KV pool 34,864 tokens), later also GPUs 1
  and 2 (lent by the cs506 runs). Smoke runs showed file-channel agents looping on tools until the
  12-turn limit; fixes: the Researcher only writes, repeated identical calls end the loop, a write
  result tells the agent it may stop, an agent that ends without its output gets one forced
  write_file turn, and C's index.md is kept by the workspace (author, size, first line per file).
  Superseded smoke runs are in results/_failed with notes.
- 2026-11-18 T04: each run gets its own cache_salt so channels never reuse each other's KV;
  checked on the server (same salt: 608 of 613 tokens cached; other salt: 0).
- 2026-11-18 T06 pilot (10 tasks per cell, 360 runs, 0 errors, 18 min on 3 GPUs): logical tokens
  in B and C are 2-4x A1, but prefill actually computed is close to A1 because tool turns reuse the
  cache; A1zc computes about the same prefill as A2 while carrying A1's content. The judge says
  delivery to the Writer is near 1.0 for message channels, 0.9-1.0 for C and 0.6-0.75 for D and
  (at k = 1-3) B. Researchers write sparser notes when they write files. Lexical fact matching
  under-counts against the judge, so the judge (batched per question and stage, about 3 min for
  the pilot) is the primary fact measure. Main run started (seed 2, 150 tasks per cell).
