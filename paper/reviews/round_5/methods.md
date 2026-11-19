# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines" (methods and statistics)

## Summary

The paper compares five ways of passing results between the agents of a Researcher, Writer, Reviewer
pipeline on HotpotQA and 2WikiMultihopQA. The channels are broadcast (A1), zero-copy broadcast (A1-zc,
which orders the prompt so prefix caching applies), a pipe (A2), shared files (B), files with an index (C),
and handles (D). The models are Qwen3 4B to 32B with thinking disabled, served by vLLM. Cost is counted
three ways: tokens sent, prefill tokens computed after prefix caching, and serving time. The headline
findings for Qwen3-8B at k=3 are:

- Copying is the most accurate channel.
- A1-zc keeps A1's accuracy at about 39% of its prefill, but it is not faster.
- File channels send 1.8-4.8x the tokens, take up to 1.97x the time when served alone, and lose
  information both when notes are written and when they are read.

Several controls support the causal story:

- A1r/A1w writing control at four model sizes
- Researcher replay
- Documents in the prompt (A2d, Bd)
- Fan-out
- KV-cache, model-size and tool-budget sweeps
- A zero-copy replay with fixed notes
- A 32B rerun with normalized paths
- An A/A rerun

I checked the paper against `pipeline.py`, `metrics.py`, `alignfacts.py`, `rescue.py`, `analyze.py`,
`run.py`, `paper_numbers.py`, the run configs and env files under `results/`, and the raw records in
`results_raw/`. Every macro in the text has a generated value, and the values I recomputed match. The
remaining issues are about design and interpretation, not transcription.

## Score: 4 / 5 (accept with revisions). Confidence: 4 / 5

For a 6-page workshop paper this is unusually careful. The analysis is paired, uses bootstrap intervals
throughout, includes an A/A control, generates every number from scripts, and reports negative results
honestly. The main problems:

- The writing-side causal claim (A1w vs A1r) is partly a harness truncation artifact, and it rests on
  cross-run comparisons that the A/A control does not cover.
- The serving-time claim rests on one makespan per channel.
- The fact-level measure has unknown validity on real, paraphrased notes, and that validity may differ by
  channel.

None of these overturns the main accuracy and token results. Each one weakens a specific sentence that
the abstract leans on.

## Strengths

1. **Paired design.** Every channel runs the same tasks, with documents shuffled once per task. The
   bootstrap resamples tasks, not questions, so questions in a bundle are correctly treated as clustered.
   Differences are reported as paired intervals (`analyze.paired`).
2. **Controls that separate what is written from what is read.** Each one removes a specific confound:
   - Researcher replay (`fixed_notes`)
   - A2d and Bd (documents in the later prompts)
   - A1r and A1w (wording vs. destination)
   - A zero-copy replay with fixed notes
   - The normalized-path 32B rerun

   Each control is run on 200 paired tasks.
3. **An A/A control exists, and the paper discloses nondeterminism.** 59% of identical Researcher prompts
   give identical output. A1 and B reruns move by -0.3 and +0.5 points, and the B-A1 gap reproduces
   (7.0 vs 7.8).
4. **Honest disclosure of harness interventions.** The paper reports the rescue rate (34-59%), strict
   accuracy (18-41%), the exact-match gap for A1-zc, and the coarseness of stage attribution. The 32B path
   slip is handled with both a rerun and a post-hoc rescore, and the two agree (B: 11.7 vs about 11.3
   points).
5. **Hardware robustness at k=3.** I recomputed tokens computed at k=3 on the RTX 3090 main run
   (34,864-token KV), the PRO 6000 8B run (100k KV), and the PRO 6000 single-channel runs. The ratios are
   essentially identical:

   | Channel | RTX 3090 main run | PRO 6000 8B run | PRO 6000 single-channel run |
   | --- | --- | --- | --- |
   | A1-zc / A1 | 0.39 | 0.39 | n/a |
   | B / A1 | 0.79 | 0.78 | 0.80 |

   The k=3 cost claims therefore do not depend on the cache or the GPU.
6. **Generated numbers.** Every number comes from `paper_numbers.py`, which reads `results/` and
   `results_raw/`. No run in any condition has an error, so `load_rows` silently drops nothing.

## Weaknesses (most important first)

### W1. The writing-side control (A1w vs A1r) is partly a truncation artifact, and its comparisons are cross-run

The abstract and conclusion rest on this: "writing notes through a tool call costs facts and accuracy at
three of four model sizes". A1w differs from A1r in more than "writing through a tool call":

- **The tool loop.** A1w gets `write_file` and up to 12 turns. Tool results carry the nudge "If you are
  finished, reply without calling a tool".
- **A forced-write rescue** when no file is left.
- **Notes inside a JSON string argument**, subject to the 2,048-token `max_tokens` cap. The paper never
  states this cap.

The cap matters. In `p05_a1w_8b`:

- 17 of 200 Researcher runs end with `finish_reason=length`.
- 15 runs leave empty notes, which are copied forward as nothing.

A1r has 4 length stops and no empty notes. On the 17 truncated, empty or forced runs, A1w answers 41% vs
A1r's 69%. Excluding them shrinks the 8B gap from -5.3 [-8.3, -2.3] to -3.3 [-6.2, -0.2]. At 4B the gap
goes from -9.2 to -8.0, and at 32B it is unchanged. The same failure hits B's Researcher in the main run:
22 of 300 k=3 runs hit `length`, and 15 have empty notes.

The design is also cross-run, which the A/A control does not cover:

- A1, A1r and A1w for each size come from three separate runs on different PRO 6000 GPUs. For example,
  4B used GPU 3 for A1, GPU 1 for A1r and GPU 3 for A1w.
- A1r and A1w were single-channel runs, so their batch composition differs from the six-channel `p02` run.
- A1r itself moves accuracy by +5.3 [+2.3, +8.3] at 4B and by -1.7 [-3.7, +0.2] at 8B. So A1r is not a
  neutral reference. Relative to A1, A1w at 4B is -3.8 [-7.5, -0.2], not -9.2.

The claim "Writing through a tool call ... costs accuracy whenever it drops facts from the notes"
generalizes from four correlated points.

**Fixes:**

- (needs new runs) Rerun A1, A1r and A1w interleaved in one run per size, ideally with `max_tokens` raised
  for the Researcher.
- (text/analysis only) Report the truncation and empty-notes rates per channel and role. Report the gap
  with those runs excluded as a sensitivity check, and soften "whenever" and "not the wording".

### W2. The serving-time claim rests on one makespan per channel, in a decode-bound regime

"Prefill savings buy no serving time" and "zero-copy ... takes 1.10x the time" come from a single
`run_time.json` makespan per channel:

- 100 tasks at concurrency 6, run sequentially on GPU 3 in a fixed order (A1, A1-zc, A2, B, C, D).
- No repeats.
- Other experiments were running on other GPUs of the same host at the same time (`p08_norm_32b` on GPU 1
  from 00:10 to 02:01).

Makespan at concurrency 6 is driven by stragglers. Per-task wall times from the same runs tell a weaker
story:

| Channel / A1 | Median per-task ratio | Mean per-task ratio [bootstrap 95%] |
| --- | --- | --- |
| A1-zc | 1.00 | 1.08 [0.99, 1.20] |
| B | 1.58 | 1.87 [1.62, 2.18] |

The makespan ratio for B is 1.97. So the A1-zc slowdown is not distinguishable from zero, and the B
slowdown is overstated.

There is also a confound. A1-zc generates 1.3x the completion tokens (its notes are longer), and the
regime is decode-bound: about 12k prefill tokens vs about 800 generated tokens per task, on a PRO 6000
with 100k KV. The result therefore mixes "prefill does not matter here" with "zero-copy writes more".

Two small biases also enter the timing:

- The makespan includes tarring the workspaces (`run()` tars before returning). This applies only to file
  channels, though the effect is small.
- The token ratios quoted beside the times come from a different run on different hardware.

**Fixes:**

- (needs new runs) At least three repeats per channel in randomized order. Report per-task latency and
  throughput with intervals. Add a load sweep (for example 6, 24 and 64 concurrent tasks, or saturation
  throughput), since prefill savings should matter when the server is prefill-bound. Time the fixed-notes
  replay (as in `p09_zcreplay`) to equalize decode length.
- (text/analysis only) Report per-task medians and CIs now, and scope the heading to "at six concurrent
  tasks on one PRO 6000".

### W3. The fact-level measure has unknown, possibly channel-dependent validity on real notes

AlignScore was validated on synthetic pairs whose contexts are the source sentences verbatim
(AUC 0.996). On 864 real, paraphrased pairs it agrees with the Qwen3-8B judge at kappa 0.29 and with
Llama-3-8B at kappa 0.22, and the two judges agree with each other at kappa 0.24. There are no human
labels, so no measure has a known error rate on real notes.

The worry is channel-dependent bias. File notes are 27% shorter and terser. If AlignScore under-detects
paraphrased facts in terse bullet notes, the gaps "Files lose information when written" (32% vs 45%) and
A1w vs A1r are inflated. The entity match and the LLM judge agree in direction, but their gaps are
smaller:

| Measure | A1 | B |
| --- | --- | --- |
| Entity match | 91% | 82% |
| LLM judge | 73% | 59% |

**Fixes:**

- (needs new annotation, no GPU) Human-label about 300 real (notes, fact) pairs stratified by channel.
  Report AlignScore's per-channel precision and recall, and correct the channel estimates if they differ.
- (text/analysis only) For every fact-level claim, report all three measures side by side (AlignScore,
  judge, entity), and state magnitudes as ranges.

### W4. Comparisons across runs and GPUs are common, but the A/A control covers only one configuration

The A/A rerun covers A1 and B, Qwen3-8B, the RTX 3090 servers, and mixed-channel scheduling. These claims
compare runs beyond that configuration:

- Bb vs B
- Fact-checker (chain4) vs main
- A2d and Bd vs main
- Fan-out vs main
- A1w and A1r vs `p02`
- The normalized 32B rerun vs `p02`'s A1 ("the first run's broadcast")
- The 24-call budget vs the 12-call budget
- The k=16 100k-cache vs RTX 3090 computed-token comparison
- All timing runs

Some of these are single-channel runs on one server (Bb, A1w, A1r, the timing runs), so their batch
composition and cache contention differ from the reference. The largest effects (Bb -12, k=16 B -34)
dwarf any plausible drift. The 3-5 point effects (A1w at 32B, Fact-checker on the pipe, A2d) do not.

The A/A bound is also misreported. "each difference's interval inside ±2 points" is wrong: B's paired
interval is [-1.17, +2.17].

**Fixes:**

- (needs new runs) An A/A on the PRO 6000 for at least one non-8B size. Include the reference channel in
  the same run for every control.
- (text/analysis only) Add a column or footnote marking each comparison as within-run, cross-run or
  cross-GPU. Fix the A/A bound to ±2.2.

### W5. Multiple comparisons, and "settings" that are not independent

The paper reports about 70 bootstrap intervals and counts significant settings without correction. It
says so, but the counts are used as evidence ("significantly in five of six settings", "three of four
model sizes", "four of six settings").

The six settings are also not independent. `make_tasks` draws with the same seed for each k, and I
verified that every HotpotQA k=1 question is among the k=3 questions (150/150), and every k=3 question
is among the k=5 questions (450/450). The k=8 draw shares 54 questions with k=3.

Several null results are underpowered and should be presented as inconclusive, not as absence of an
effect:

- The fan-out difference-in-differences of -4 [-10, +2] on 100 tasks.
- The +3.3 [-0.5, +7.4] effect of the 24-call budget on 60 tasks.

The fan-out run also shows that broadcast itself loses 6 points [-11, -1] with three Researchers. The
text omits this.

**Fixes (text/analysis only):**

- State the nesting.
- Apply Holm correction within each claim family (per channel across cells; across the four sizes for
  A1w-A1r).
- Or fit one mixed-effects or question-clustered model per channel with dataset and k as covariates.
- Phrase underpowered nulls as "we cannot rule out effects up to X".

### W6. At k of 8 or more, tokens computed describes a mixed workload, not a channel

Channels are interleaved on servers that share one KV cache (`run.py` shuffles jobs across channels). The
`cache_salt` prevents cross-channel hits but not cross-channel eviction. At k=3 this does not matter
(see Strength 5). At k=8 and k=16 on the 34,864-token cache, a channel's hit rate depends on what it was
co-scheduled with. For example, `t08_large` also ran Bb, while `p07_k16_kv100k` did not.

Under memory pressure, vLLM also preempts requests and recomputes them. Those recomputed prefills do not
appear in `prompt_tokens - cached_tokens`, so tokens computed undercounts real compute in exactly the
large-payload settings the paper discusses.

**Fixes:**

- (analysis of existing logs) Report vLLM preemption counts for the k=8 and k=16 runs.
- (needs new runs) Run k=8 single-channel, as was done for timing. Otherwise label the k of 8 or more
  numbers as "under a mixed six-channel workload".

### W7. Some mechanism sentences go beyond what the controls separate

- **"At 4B it comes from the prompt order the Writer and Reviewer see."** A1-zc changes both the position
  of the role instruction and its role: it moves from the system prompt to a final user turn
  (`build_messages`). The replay rules out the notes, but not system-vs-user placement.
  - (needs new runs, cheap at 4B) An A1 variant with the instruction as the first user turn instead of
    the system prompt.
- **"its loss at review is specific to that model"** (pipe). This is inferred from one model in four
  sizes of one family, with a non-monotone pattern.
  - (text only) Soften to "we observe it only with Qwen3-8B".
- **The index.** B vs C also differ in C's Researcher instruction ("Start each notes file with a heading
  that says which questions it covers"). That instruction plausibly explains C's zero path clashes at
  k=16, so the index alone does not.
  - (needs new runs) B plus the heading rule, without an index.
- **The clash split at k=16** (43 vs 17 tasks) is observational. The accuracy difference (38 vs 41) is
  within noise.
  - (text only) Present it as descriptive.

### W8. The accuracy metric and harness choices are lenient and partly unreported

- **Lenient containment rule.** Accuracy credits a prediction that contains the gold answer, within gold
  length plus 4 words. Under exact match, A1-zc falls up to 4 points behind on 2Wiki. The paper mentions
  this for A1-zc but not for the other headline comparisons.
- **Rescue rates.** The forced-write rescue applies to 34-59% of B and C Writer and Reviewer runs, and
  strict accuracy would be 18-41%. A reader of Figure 2 sees only the rescued accuracy.
- **Unreported settings.** `max_tokens=2048` (see W1) and thinking-disabled decoding are design choices
  that plausibly hurt tool-using channels more than message channels. Only the second is reported.

**Fixes (text/analysis only):**

- Add an EM/F1 row for every headline gap (one small table).
- Plot strict accuracy as a second marker in Figure 2.
- State the 2,048-token cap and the per-channel truncation rates.

### W9. The stage attribution (Figure 3b) mostly shows a base rate

A wrong answer is charged to the Researcher whenever its notes miss any supporting fact. But in broadcast,
76% of correct answers also come from notes that miss a fact, because the Writer has the documents. So
"Researcher missed" dominates every bar mostly through the AlignScore miss rate.

Delivery is also defined asymmetrically:

- In message channels it means "present in the prompt".
- In file channels it means "returned by a read". This includes reads of source documents (`writer_input`
  concatenates every read), so it measures exposure, not use.

The figure's "Reached Writer" bar multiplies two means (`fig_loss.py`). It is not the mean of the
per-task product.

**Fixes (text/analysis only):**

- Replace the panel with a counterfactual measure, such as the accuracy change under gold-fact notes
  replay, or a per-channel logistic model of correctness on notes recall.
- Otherwise shrink the panel and say it is descriptive.

### W10. Generality is limited

All results come from:

- One model family (Qwen3, with thinking disabled)
- One engine (vLLM 0.33)
- One linear pipeline
- Short-answer multi-hop QA

The prescriptive conclusion ("Long results are better written as plain replies that the system stores")
is stated more broadly than this. Qwen3-14B is already a counterexample: its tool-written notes keep the
facts, B beats C, and A1w equals A1r.

**Fixes:**

- (needs new runs) One cross-family check (another tool-capable 7-9B model) or Qwen3-8B with thinking
  enabled, for A1, A1-zc, B and A1w at k=3 on 200 tasks.
- (text only) Scope the conclusion to the tested family.

## Questions for the authors

1. What are the per-channel, per-role rates of `finish_reason=length` (2,048 tokens)? Why was this cap
   chosen when tool-call arguments must carry the whole notes?
2. How many vLLM preemptions occurred in the k=8 and k=16 runs on the 34,864-token servers? Does tokens
   computed include their recomputation?
3. Were other GPU jobs on the same host during the `p06_alone_*` timing runs? Was the order of the six
   runs randomized?
4. Did Qwen3-4B, 8B or 14B also write prefixed paths (`workspace/...`) that the harness missed, as 32B did?
5. Why does the matched-wording reply (A1r) help Qwen3-4B by 5.3 points? Could part of this be run-to-run
   drift on the PRO 6000, for which there is no A/A?
6. Is "no difference is significant" for A1-zc two-sided? The code (`GapAZcSig`) counts only intervals
   entirely below zero.
7. Fan-out costs broadcast 6 points [-11, -1] at k=3. Since the k=16 headline uses three Researchers, how
   much of the k=16 file collapse is due to fan-out rather than files?
8. Is there any human validation of the fact labels on real notes?

## Sentences that overclaim or mismatch the code or numbers

1. **Abstract:** "With the instruction's wording matched, writing notes through a tool call costs facts
   and accuracy at three of four model sizes."
   - Wording is matched, but the tool loop, forced write and 2,048-token truncation are not. At 8B, 2.0 of
     the 5.3 points come from truncated or empty writes.
   - The comparison is cross-run and uncorrected (W1, W4, W5).
2. **§4 (Results):** "Writing through a tool call, not the wording, costs accuracy whenever it drops facts
   from the notes."
   - "Whenever" is generalized from four sizes.
   - The "fact drop" is measured with kappa of about 0.29 agreement (W1, W3).
3. **Introduction:** "Copying the history with the shared part first (zero-copy broadcast) cuts prefill by
   61% at copying's accuracy but takes 1.10x the time."
   - This is one makespan. The per-task median ratio is 1.00, and the mean is 1.08 [0.99, 1.20] (W2).
4. **§4 heading:** "Prefill savings buy no serving time."
   - This is true only for a decode-bound setting at six concurrent tasks, with one run per channel (W2).
5. **Abstract:** "Served alone, they take up to 1.97x the time."
   - The makespan ratio is 1.97. Per-task mean is 1.87 and median 1.58, with no repeats (W2).
6. **§6 (Run-to-run noise):** "with each difference's interval inside ±2 points"
   - B's A/A interval is [-1.17, +2.17] (W4).
7. **§5 (Model size):** "so its loss at review is specific to that model"
   - The evidence is one family with a non-monotone pattern (W7).
8. **§5 (Model size):** "At 4B it comes from the prompt order the Writer and Reviewer see."
   - Order is confounded with moving the instruction from the system to the user role (W7).
9. **§3 (Methodology):** "Each run gets its own cache namespace (cache_salt), so channels never share
   cached KV."
   - True for hits, but channels share capacity and evict each other's prefixes. This matters for the
     k of 8 or more compute numbers (W6).
10. **§3 (Metrics):** "It is what an API bills without caching and an upper bound when the API discounts
    cached input."
    - This holds for token counts, not cost. APIs price output tokens several times higher than input
      tokens, and file channels generate 1.6-2.2x the output.
11. **§7 (Conclusion):** "Long results are better written as plain replies that the system stores, since
    writing them through a tool call lost facts and accuracy at three of four model sizes."
    - This is prescriptive beyond one model family, and Qwen3-14B is a counterexample (W10).
12. **§5 (Parallel writers):** "With three Researchers on 100 three-question tasks, B's writers clash in
    91%, but B's accuracy change from one to three Researchers, less broadcast's, is -4 points"
    - The interval [-10, +2] is underpowered. The sentence also omits that broadcast itself drops
      6 points with fan-out (W5).

## Minor

- Figure 4 has no error bars, although `fig4_scaling.json` already holds paired intervals. The k=16 B
  point has a 60-task interval of [-39, -29], worth showing. The k axis also mixes sources: k=1, 3, 5
  come from 150 tasks per dataset, k=8 from 100, and k=16 from 30 with fan-out.
- `t08_fanout`, `t09_scope` and the pressure runs were made from a dirty working tree
  (`env.json: git_dirty: true`). The scope control in particular should be rerun or have its diff
  recorded.
- §3 says the main runs use "one RTX 3090 per server". The main run used three servers, while several
  controls used one. Batch composition differs, which matters for nondeterminism (W4).
- The 3090 Qwen3-4B run (`t08_qwen4b`, k=1/3/5) corroborates the 4B zero-copy loss (significant in three
  of four k=3/5 cells). Citing it would strengthen §5.

## Round-6 recommendation

### Constraints

- One server with several 96 GB GPUs, Qwen3 4B/8B/14B/32B, and the same harness.
- About 5,000 pipeline runs in roughly a day, 12 days to the deadline, 6 pages.
- No second model family and no human labels.

The new results should replace existing paragraphs, not add new ones.

### Facts from the existing runs that shape the plan

- **A1 almost never truncates at 2,048 tokens.** Its runs that hit the cap: 1/200 at 4B and 0/200 at 8B,
  14B and 32B (`p02_size_*`). If R1 uses the same tasks, its A1 arm at 4,096 tokens is effectively an A/A
  on the PRO 6000 against `p02`'s A1, at all four sizes.
- **File channels truncate much more.** B: 12/200 (4B) and 15/200 (8B). C: 30/200 (4B). A1-zc: 8/200 (8B).
  The B gap itself may partly be a truncation effect.

### R1: writing-control rerun (keep, but change the design)

Change: put B in the same run, use the first 150 of `p02`'s 200 tasks, and set `normalize_paths: true`.
Same run count (2,400) as the authors' plan.

Config:

- One run per size (4B, 8B, 14B, 32B).
- Channels: A1, A1r, A1w, B, interleaved.
- k=3, seed 2, `n_tasks` 150, `use_tasks` 75 (150 tasks, paired with `p02`).
- `max_tokens` 4096 for all arms.
- Concurrency 6, KV 100k (6,250 blocks).
- `normalize_paths: true` for all arms. It only changes workspace paths, and it removes the 32B path confound.

What this gains:

- The decomposition A1 -> A1r -> A1w -> B is measured within one run at four sizes. That is the table the
  other reviewer asks for (W7).
- A1 vs `p02`'s A1 serves as the PRO 6000 A/A (see R4).
- Report truncation, empty-notes and rescue rates per arm.

Power: 150 tasks costs about 15% wider intervals than 200 (half-width about 3 points), which is still
enough for the 4-9 point effects.

### R2: serving time (keep, but change the second load level and the measurements)

Concurrency 12 is too close to 6 to leave the decode-bound regime.

Config:

- **c=6 repeats.** Two new repeats of all six channels alone. Use `use_tasks` 50 (the same 100 tasks as
  `p06`), KV 100k, a fresh server per run, and a randomized run order. The existing `p06` runs count as
  repeat 1. That is 1,200 runs.
- **c=32.** A1, A1-zc and B, 2 repeats, 100 tasks, with KV at 400k (25,000 blocks), so the higher load
  does not also add eviction. That is 600 runs.
- **Measurements in every run.** Turn on vLLM per-request timing (prefill, decode and queue time), or
  scrape `/metrics` histograms. Also log preemptions. This separates prefill time saved from decode time
  added, with no extra runs. The fixed-notes replay is not suitable for timing, because it skips the
  Researcher call whose prefix A1-zc reuses.
- **Reporting.** Per-task median and mean with bootstrap intervals, throughput, and makespan across
  repeats.

Total: 1,800 runs.

### R3: k=16 no-clobber (keep, and add within-run references)

Config:

- 60 tasks (seed 4, `n_tasks` 30), same tasks as `p07_k16_kv100k`.
- Researchers 3, KV 100k, `max_turns` 12.
- Channels: A1, B, B-noclobber, D-noclobber.
- Make `write_file` return an error when the path was written by another Researcher, so the agent picks
  a new name. This is closer to the real failure than silently namespacing paths.

Total: 240 runs. This is the cheapest test of the clash explanation for the abstract's 34-point number.
Also tabulate what B's Reviewer spends its calls on from the existing `io_ops`; that is analysis only.

### R4: A/A at 14B (drop)

R1's A1 arm against `p02`'s A1 on the same tasks gives an A/A on the PRO 6000 at four sizes for free (A1
truncation is at most 0.5%). The 600 runs are better spent on R2 or E5.

### Missing experiment that outranks R4 and the c=32 part of R2

**E5: k=8 with fan-out.**

Config:

- k=8, seed 3, `n_tasks` 100, `use_tasks` 50 (the same 100 tasks as `p01_cache_100k`).
- Researchers 3. Channels: A1, B, C, D. KV 100k, c=6.

Total: 400 runs.

Claim it tests: whether the k=16 collapse comes from fan-out or from payload size. One Researcher at
k=16 may not fit the 32k context, and k=8 is the largest payload where both topologies run.

Analysis: a difference-in-differences against `p01_cache_100k` (one Researcher), using A1 as the
within-run reference. If B collapses here but not with one Researcher, the abstract should attribute the
34 points to parallel writers on shared files, not to file access at a large k.

**Lower priority: E6, the instruction-role control at 4B.**

- A1 with the role instruction as the first user turn instead of the system prompt.
- Channels A1, A1-zc and the new variant, 200 tasks: 600 runs.
- Claim it tests: "At 4B it comes from the prompt order".
- Rewording the sentence to "prompt order and the instruction's role" is an adequate substitute, so
  this ranks below everything above.

### Full-budget plan (about 4,840 runs)

| Order | Experiment | Runs |
| --- | --- | --- |
| 1 | R1 | 2,400 |
| 2 | R2 c=6 repeats | 1,200 |
| 3 | R3 | 240 |
| 4 | R2 c=32 | 600 |
| 5 | E5 | 400 |

R4 is dropped.

### Minimal set I would accept as sufficient (about 2,400 runs plus text)

1. **R1 without B:** A1, A1r, A1w x 4 sizes x 150 tasks, `max_tokens` 4096 (1,800 runs).
2. **R2 c=6 repeats for A1, A1-zc and B only:** 2 new repeats x 100 tasks, randomized, with per-request
   prefill/decode timing (600 runs).
3. **Text changes:**
   - Scope the timing claims to "six concurrent tasks on one PRO 6000".
   - Qualify the k=16 number as "with three parallel Researchers that overwrite each other's files"
     unless R3 or E5 runs.
   - Fix the overclaims listed above.

### Priority if only half the budget is available (about 2,500 runs)

1. **R1 core** (A1, A1r, A1w; 4 sizes; 150 tasks; 4,096 tokens): 1,800 runs.
2. **R2 c=6 repeats for A1, A1-zc and B,** with per-request timing: 600 runs.
3. **R3 reduced to B and B-noclobber** (60 tasks each): 120 runs.

Drop B from R1, R2 at c=32, E5 and R4.
