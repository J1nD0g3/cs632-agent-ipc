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
| T07 Main experiments: 5 channels x 2 datasets x 3 k | Experiments | Must | Done | 2026-11-19 | results/t07_main/20261118-212337-5d6c70f | 5400 runs, 0 errors, judged |
| T08 Sensitivity: k = 8, five agents, zero-copy A1, Qwen3-4B | Experiments | Should | In progress | 2026-11-19 | Bb, 24-turn done | k8, chain4, 4B, k16, pressure, fan-out queued |
| T09 Analysis and figures | Report | Must | In progress | 2026-11-19 | Figs. 1-4 | paper/figs/out |
| T10 Workshop paper and review rounds | Report | Must | In progress | 2026-11-19 | paper/main.pdf, round 7: 3/5, 3/5; rounds 6 and 8 runs added | AlignScore is the fact measure; scope controls added |

## Key numbers
| Key | Metric | Result | Source |
| --- | --- | --- | --- |
| success | Task success rate: A / B / C | k=3 pooled: A1 72.3%, A1-zc 71.6%, A2 62.1%, B 62.8%, C 66.3%, D 65.1% | results/t07_main/20261118-212337-5d6c70f |
| tokens | Total tokens per task: A / B / C | k=3 sent / computed: A1 13.3k/12.4k, A1-zc 13.6k/4.8k, A2 5.6k/4.7k, B 38.2k/9.8k, C 37.4k/9.8k, D 17.5k/7.2k | results/t07_main/20261118-212337-5d6c70f |
| file_io | File reads and writes per task: A / B / C | k=3 file I/O ops: B 13.4-15.3, C 12.1-14.4, D 5.6-5.8 (message channels 0) | results/t07_main/20261118-212337-5d6c70f |
| info_loss | Key facts lost between stages: A / B / C | k=3 AlignScore, facts in Researcher output / share delivered: A1 45%/100%, A1-zc 50%/100%, A2 45%/100%, B 32%/91%, C 30%/95%, D 25%/51% | results/t07_main/20261118-212337-5d6c70f/alignscore.json |
| recommendation | Which channel, and when | History fits in context: copy it with the shared prefix first (zero-copy; saves prefill, not serving time). Pipe is cheap but drops the documents. Write long results as plain replies. With parallel writers, give each its own folder (or guard writes / head files with their questions). | paper/main.tex (Conclusion) |

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
- 2026-11-19 T07 main run (150 paired tasks per cell, 5400 runs, 0 errors, 3.7 h on GPUs 5/1/2):
  zero-copy broadcast matches broadcast's accuracy while computing 38-40% of its prefill, the same
  as the pipe. The pipe loses 3-15 points because its Reviewer, without the facts, changes right
  answers (15-16% of 2Wiki questions). File channels send 2-4x the tokens of broadcast; B loses 6-14
  points; the index (C) keeps delivery at 91-97% and accuracy within 1-8 points of broadcast. Writing
  to files makes the Researcher's notes 25-30% shorter, and with handles (D) the Writer rarely opens
  the files (delivery 61-76%).
- 2026-11-19 T08 so far: batched reads (Bb) cut round trips (13 vs 16-19 calls) and tokens but did
  not help accuracy on 64 paired tasks; a 24-turn budget adds 24-36% tokens to B and C with no
  accuracy change, so the 12-turn limit does not drive the results. Same-prompt Researcher outputs
  are identical only 72-77% of the time (vLLM batch nondeterminism), a noise floor for small gaps.
  k=16 (partial): the prefix cache stops helping (computed close to sent) and B drops sharply while C
  holds. Queue rescheduled so that k=8, four agents, Qwen3-4B, k=16, cache pressure (1/2 concurrent
  runs) and fan-out (50 tasks) all finish by about 10:00.
- 2026-11-19 T08 results: k=8 and k=16 show the cache savings fade under six concurrent runs per server
  (zero-copy 0.83x and 1.00x of broadcast's compute; files above broadcast), and the cache-pressure runs
  (1-2 concurrent runs, k=16) bring them back (B computes 0.23 of what it sends instead of 0.83) with
  accuracy unchanged. At k=16 the pipe matches broadcast at 0.37x compute and plain files lose 34 points
  (index 5). Four agents: broadcast +38% compute, zero-copy +6%; the pipe gains 5.5 points, B loses 7.8.
  Qwen3-4B: files lose 19-35 points even with an index and zero-copy costs 3-11 points at k=3-5.
- 2026-11-19 T10: draft at 6 pages with Figs. 1-4 and 253 generated macros. Round-1 reviews (systems
  3/5, methods 3/5) in paper/reviews/round_1. Text fixes applied (18 mismatches, harness rescue rates,
  latency, concurrency, missing related work). Revision runs queued: A1w (Researcher writes via a tool
  call, then copied), Researcher replay into A1/A2/B/C, and an A/A repeat; main run being re-judged with
  per-question judge results for Fig. 3b.
- 2026-11-19 T10: Fact presence switched to AlignScore throughout (validated on 450 synthetic pairs; kappa 0.29
  with the LLM judge on real outputs, reported as a caveat). Cache-pressure runs show the k=16 savings loss
  comes from six concurrent runs per server. Round-2 reviews (3/5, 3/5) asked whether only the channel varies;
  scope controls answer it: a pipe that also passes the documents (A2d) gains 6.8 points at 0.96x broadcast's
  compute, while files with the documents in the prompt (Bd) gain 0.5 (n.s.), so files lose through their notes.
  Since 11:49 only GPU 5 is used (GPUs 1, 2, 6 returned to cs506).
- 2026-11-19 T10: Style pass in the voice of the style guide, with meaning audits after each step (round 3):
  detector 6/10 -> 4/10 machine-like; body semicolons 35 -> 0; three meaning audits found 8, 6 and 7 issues
  (dropped scopes and intervals, overclaims), all fixed. Still 6 pages.
- 2026-11-20 T10: Round 4. Reviews (3/5, 3/5) asked for causal controls; ran 4,020 runs on the PRO 6000 (KV 100k):
  writing control at 4 sizes (the tool call, not the wording, shortens notes and costs accuracy at 4B/8B/32B; not at
  14B), 32B with normalized paths (files still 8-17 points behind), serving time per channel (zero-copy saves no
  time; files 1.3-2.0x), k=16 with a 100k cache and 24 calls (neither closes B's 34-point gap), zero-copy with fixed
  notes (4B loss is from prompt order). Paper revised; meaning audit found 12 issues, all fixed. Still 6 pages.

- 2026-11-20 T10: Rounds 5-8. Fresh reviewers each round (3/5-4/5). PRO 6000 round 6 (4,740 runs) and round 8
  (2,300 runs): in-run writing control at 4 sizes (tool-call writing costs at 4B/8B after Holm), serving time in
  three repeats (zero-copy 1.09x at six tasks at a time, 1.00x at 32), k=16 write guard and heading rule, and a
  same-server k=8 fan-out (three Researchers cost B 21.2 points; per-Researcher folders recover 19.8). Paper cut
  to four channels (D, batched reads and the fact-checker removed), retitled "Messages or Files?", Fig. 3 now
  splits writing from the rest of the file channel. Meaning audits after each pass (22 and 19 fixes). 6 pages.
