# Data dictionary

Every finished run lives in `results/<exp>/<run_id>/` (`run_id` = start time and code commit). All files below
are committed, so the analyses need no GPU or server.

| File | What it holds |
| --- | --- |
| `config.yaml` | The configuration the run used (a copy of `configs/<exp>.yaml` plus command-line overrides). |
| `env.json` | Code commit, Python and vLLM versions, GPU, model, maximum context, server flags. |
| `task_stats.json` | Per task set (`<dataset>_k<k>_s<seed>`): tasks, questions, mean documents, characters and supporting sentences, question types. |
| `summary.json` | Means with 95% intervals per dataset, k, and channel (written by `agentipc.run`). |
| `run_time.json` | Runs `p05`-`p18` only: wall time of the whole run and, with `scrape_metrics`, the change in vLLM's counters. |
| `replay_source.txt` | Replay runs only: the run and channel whose Researcher output was replayed. |
| `paired.json`, `alignscore.json`, `summary_judge.json`, `entities.json`, `judge_*.json` | Derived summaries (main run and some others). |
| `rows.jsonl.gz` | **One row per pipeline** (task x channel): accuracy, tokens, prefill, file I/O, lexical fact metrics. |
| `judged.jsonl.gz` | Per pipeline, the Qwen3-8B fact judge's labels (`judge_*`, `jq_*`); some runs only. |
| `alignscore_rows.jsonl.gz` | Per pipeline, AlignScore fact coverage (`as_*`, `aq_*`); runs that were scored. |
| `records.jsonl.gz` | **Full record per pipeline**: every model call, every file operation, and each stage's text. |
| `judge_cross.jsonl.gz` | Main run only: the per-fact labels of the judge cross-check (Appendix E). |

`results/_failed/` keeps three smoke runs, a failed pilot, and a discarded first `p02_size_4b` attempt, each with a
`notes.txt` that says why it is not a result.
`results/pro6000*_kv_used.txt` record, per RTX PRO 6000 run, the KV-cache size and memory utilization read from
the vLLM server log.

The agents' workspaces (`workspaces.tar.gz`, about 230 MB over all runs) and the server logs are not in the
repository. They are needed only for the 32B path rescore (`agentipc.rescue`) and a few setup constants.

## Loading

```python
from agentipc.load import experiments, load_rows, load_records

experiments()                    # ['p01_cache_100k', ..., 't09_scope']
df = load_rows("t07_main")       # pandas DataFrame, one row per (task, channel), errors dropped
recs = load_records("t07_main")  # iterator of dicts (see "Records" below)
```

`load_rows` merges `judged.jsonl.gz` and `alignscore_rows.jsonl.gz` into the rows by `(task_id, channel)` and
drops pipelines that ended with an error, as every analysis in the paper does (`errors=True` returns `rows.jsonl.gz` as written, failures included, without the merged columns).

## Keys

| Column | Meaning |
| --- | --- |
| `exp` | Experiment ID (added by `load_rows`; see [experiments.md](experiments.md)). |
| `task_id` | `<dataset>-k<k>-s<seed>-<index>`, e.g. `2wiki-k3-s2-0117`. The same ID in two runs is the same task, so runs pair by task. |
| `dataset` | `hotpotqa` (HotpotQA distractor validation) or `2wiki` (2WikiMultihopQA dev). |
| `k` | Questions per task: 1, 3, 5, 8, or 16. The documents are the union of the questions' paragraphs. |
| `seed` | Seed of the task draw: 2 for k <= 5, 3 for k = 8, 4 for k = 16 (0 and 1 for smoke and pilot runs). |
| `channel` | The channel or arm (codes below). |
| `error` | Empty unless the pipeline failed (such rows are dropped by default). |
| `wall_s` | Wall time of the pipeline, seconds, under the run's concurrency. |

## Channel and arm codes

| Code | Name in the paper | What changes |
| --- | --- | --- |
| `A1` | broadcast | Every prompt copies the task, the notes, and (Reviewer) the draft; role instruction first. |
| `A1zc` | zero-copy broadcast (A1-zc) | A1's messages with the shared history first and the instruction last, so the prefix cache reuses it. |
| `A2` | pipe | Each agent gets only the previous agent's output. |
| `B` | shared files | Documents, notes, and draft are files read with `list_files` / `read_file`; outputs are written with `write_file`. |
| `C` | files with an index | B plus a maintained `index.md` and the heading rule. |
| `D` | handoff channel (excluded) | B plus a short pushed handoff message. |
| `A1r` | reply-written notes, copied | B's Researcher wording, notes in the reply, copied forward as in A1. |
| `A1w` | tool-written notes, copied | Researcher writes notes with `write_file`; their text is copied forward as in A1. |
| `Bs` | stored reply | Reply notes saved by the system as `notes.md`; later agents as in B. |
| `Bt` | told stored reply | Bs plus "The Researcher's notes are in notes.md." in later agents' instructions. |
| `Bs0`, `Bt0` | first-listed stored reply | Bs / Bt with the notes saved as `00_notes.md`. |
| `Br` | reply-output arm | Later agents read files but reply instead of writing files. |
| `A2d`, `Bd` | documents control | A2 / B with the documents in later agents' prompts. |
| `Bn` | write guard (k = 16) | A Researcher's write to a file another Researcher wrote fails. |
| `Bh` | heading rule (k = 16) | B plus the heading rule, without the index. |
| `Bf` | separate folders (k = 8) | Each Researcher writes under `researcher<i>/`. |
| `Bb` | batched reads | B plus a `read_files` tool. |

Runs with `replay_from` in their config (`t09_replay`, `p09_zcreplay_*`) feed one earlier run's broadcast notes to
every channel; their channel codes are unchanged.

## Outcome columns (`rows.jsonl.gz`)

Accuracy columns are shares of the task's k questions (0 to 1). The final answers are the `Q<i>: <answer>` lines
of the Reviewer's final text; a missing line counts as wrong.

| Column | Definition |
| --- | --- |
| `acc` | Share of questions answered correctly: exact match, F1 >= 0.8, or the gold answer inside a prediction at most four words longer (after HotpotQA normalization). **The paper's accuracy.** |
| `em`, `f1` | Exact match and token F1 against the gold answer, averaged over questions. |
| `answered` | Share of questions with a non-empty final answer. |
| `all_correct` | 1 if every question is correct. |
| `prompt_tokens`, `completion_tokens` | Summed over every model call of the pipeline. |
| `total_tokens` | `prompt_tokens + completion_tokens`: **tokens sent**, as an API bills without cache discounts. |
| `prefill_tokens` | Sum over calls of `prompt_tokens - cached_tokens` (vLLM's reported prefix-cache hits): **prefill**, tokens computed. |
| `llm_calls` | Model calls (each tool call is one call). |
| `tokens_<role>` | Tokens sent by one role (`researcher`, `researcher1..3` with parallel Researchers, `writer`, `checker`, `reviewer`). |
| `turn_limit` | 1 if any agent used up its tool budget. |
| `overflow` | 1 if any call exceeded the context length. |
| `file_reads`, `file_writes`, `file_lists`, `file_io` | Workspace operations, summed over agents (`file_io` is their sum). |
| `read_chars`, `write_chars` | Characters read from / written to the workspace. |

A fact is one supporting sentence of a question. The stage texts are `notes` (the Researcher's output),
`writer_input` (what the Writer received: the copied output in message channels, every `read_file` result in
file channels), `draft`, and `final`.

| Column | Definition |
| --- | --- |
| `fact_recall_notes` | Lexical anchors: share of the task's facts whose content words (not in the question, not stop words) are at least half present in the notes. |
| `fact_kept_writer_input`, `fact_kept_draft`, `fact_kept_final` | Of the facts present in the notes, the share also present in that stage. |
| `fact_recall_final` | Share of all facts present in the final text. |
| `info_loss` | `1 - fact_kept_final` (1 when the notes hold no fact). |
| `triple_recall_notes`, `triple_recall_final` | Entity match: share of 2Wiki evidence triples (HotpotQA: supporting titles) whose subject and object appear in the text. |
| `q_<kind>` | Share of questions in each failure kind, the first stage that explains the outcome: `ok`, `reviewer_fixed` (right after a wrong draft), `overflow`, `no_answer`, `reviewer_broke` (wrong after a right draft), `research_miss` (notes lack a fact), `delivery_miss` (Writer's input lacks a fact), `writer_wrong`. Lexical anchors decide fact presence. |
| `as_recall_notes` | **Fact coverage** in the paper: share of facts AlignScore-large (`nli_sp`, threshold 0.5) judges the Researcher's output to state. |
| `as_kept_writer_input` | **Delivery**: of the facts in the Researcher's output, the share the Writer's input also states (absent when the output states none). |
| `aq_<kind>` | The failure kinds with AlignScore deciding fact presence; `aq_right_notes_miss` is the share of correct answers whose notes miss a fact. |
| `judge_recall_notes`, `judge_kept_writer_input`, `judge_kept_final`, `judge_recall_final`, `judge_info_loss` | The same coverage measures with the Qwen3-8B judge deciding fact presence. |
| `jq_<kind>` | Failure kinds with the judge; `jq_overflow` marks texts too long for the judge. |

The paper reports `acc`, `total_tokens`, `prefill_tokens`, `llm_calls`, `turn_limit`, `as_recall_notes`, and
`as_kept_writer_input`; Appendix E explains why fact coverage is a weak measure.

## Records (`records.jsonl.gz`)

One JSON object per pipeline with `task_id`, `channel`, `dataset`, `k`, `seed`, `server`, `wall_s`, `chain` (the
roles in order), `score` (the row's columns plus `preds`, the parsed final answers), and:

- `agents.<role>.calls`: one entry per model call with `turn`, `prompt_tokens`, `completion_tokens`,
  `cached_tokens`, `latency_ms`, `finish_reason`, `tools` (the tools it called), and `forced_write: true` for the
  harness's rescue call; `agents.<role>.reply`, `hit_turn_limit`, `overflow`.
- `io_ops`: every workspace operation in order, `{agent, op: list|read|write, path, chars, error?}`.
- `io`: per-agent counts of reads, writes, lists, and characters.
- `stage`: the texts `notes`, `writer_input`, `draft`, `final`.

The questions and documents themselves are not stored; `agentipc.data.make_tasks` rebuilds every task from the
two public datasets and the seed (README, "Reproduce").
