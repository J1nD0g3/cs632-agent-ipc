# Progress

| Task | Phase | Priority | Status | Updated | Result | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| T00 Preflight and repo setup | Setup | Must | In progress | 2026-11-18 | | |
| T01 vLLM server and smoke test | Setup | Must | Not started | | | Waiting for a GPU |
| T02 Task data: loaders, samples, key facts | Build | Must | Not started | | | |
| T03 Agent runtime: roles, prompts, tools, logging | Build | Must | Not started | | | |
| T04 Channels A/B/C | Build | Must | Not started | | | |
| T05 Metrics: success, tokens, I/O, information loss | Build | Must | Not started | | | |
| T06 Pilot run and checks | Experiments | Must | Not started | | | |
| T07 Main experiments | Experiments | Must | Not started | | | |
| T08 Sensitivity: workload size, index quality, context limit | Experiments | Should | Not started | | | |
| T09 Analysis and figures | Report | Must | Not started | | | |
| T10 Final report and recommendation | Report | Must | Not started | | | |

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
