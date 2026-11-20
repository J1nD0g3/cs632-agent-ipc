# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (methods / statistics)

## Summary

The paper compares five ways of passing results through a Researcher -> Writer -> Reviewer pipeline:
broadcast (A1), zero-copy broadcast (A1-zc, shared history first so the prefix cache reuses it), pipe (A2),
shared files (B), and files with an auto-maintained index (C). It uses Qwen3 (4B-32B) on vLLM with
HotpotQA and 2Wiki tasks that bundle k questions. Every channel runs the same tasks, so differences are
paired by task, and intervals come from a task-level bootstrap. The headline results with Qwen3-8B are:

- Broadcast is the most accurate channel.
- Zero-copy cuts prefill by 51-62% without a detectable loss in accuracy (-0.8, CI -2.9 to 1.4 at k=3). It
  saves no wall time at 6 concurrent tasks, because its agents generate 1.2x the tokens.
- Files send 2-5x the tokens and take 1.6-1.8x the time.

To explain the file channel's accuracy loss, the paper adds several controls:

- An in-run split of the loss into wording, tool-call write, and the rest of the channel, at four model
  sizes, with a 12-test Holm family.
- Documents-in-prompt arms, a replay of broadcast's notes into every channel, and a reply-output variant.
- At k=8, one vs three Researchers run back to back with a per-Researcher-folder arm.
- At k=16, a write guard and a heading-rule arm.
- Sweeps of cache size, tool budget, and model size.
- An A/A rerun on the RTX 3090s.

I checked the macros against `paper_numbers.py`, the pipeline and workspace code, and the raw records. Almost
every number in the text matches what the code computes. The main problems are in interpretation:

- The step decomposition depends on the order of the steps.
- The serving-time conclusion at 32 concurrent tasks does not match the per-task latencies the authors
  already logged.
- The fan-out mechanism is under-analyzed, although the data to analyze it exists.
- Several prompt and harness asymmetries are as large as the effects being attributed.

## Score

**3 / 5** (borderline accept for a workshop). The controls are unusually careful for a 6-page paper and the
claims are mostly hedged. However, several causal sentences go beyond what their arms isolate, and two
analyses that need no new runs would change how readers interpret the serving-time and fan-out claims.

**Confidence: 4 / 5.** I read the code that produces the numbers and recomputed several statistics from
`results_raw/`.

## Strengths

1. **Paired design throughout, with task-level clustering.** Accuracy is averaged within a task before the
   bootstrap (`analyze.paired`, `stats.ci`), so the k questions of one task are not treated as independent.
   Every channel runs the same task IDs, and almost no runs failed: the error rate is 0 in every run I
   checked except one `Bh` task at k=16. So dropping errored rows does not bias the pairing.
2. **In-run controls where they matter most.**
   - The writing split (p10) puts A1, A1r, A1w, and B in one interleaved run per size.
   - The fan-out repair arm (Bf) shares a run with the three-Researcher B.
   - The guard and heading arms (Bn, Bh) share a run with their B and A1.
   - The replay control is within-run.
   - Job order is shuffled across channels (`run.py`), so server drift falls on every arm alike.
3. **Replication across runs.** The earlier cross-run write effects (p05: -9.2, -5.3, 0.0, -4.3 points) are
   close to the in-run ones (p10: -8.7, -5.6, -0.2, -4.4). The path-normalized 32B rerun (B -11.7) agrees
   with the in-run p10 32B total (-12.7). This triangulation is convincing.
4. **Honest disclosure of limits.** The paper states which comparisons cross runs, that significance counts
   are uncorrected, how often the harness rescue fires (34-59%), the strict-scoring bound, AlignScore's weak
   agreement with a judge (kappa 0.29), and that the k=1/3/5 question sets overlap.
5. **Multiple-comparison control where the central causal claim is made.** The Holm correction over the 12
   writing-control tests uses a sign-flip permutation test on per-task differences. I reproduced the
   p-values exactly.
6. **The serving-time measurement is cleanly isolated at the GPU level.** Each channel runs alone, the order
   of the p11 runs is randomized (`pro6000_round6_timing_order.txt`), and vLLM counters are scraped before
   and after each run. The A1 wall time is very stable (246-248 s over three runs).

## Weaknesses (most important first)

### W1. The step decomposition depends on order, and the two estimates of "the rest of the file channel" at 8B disagree. *(text/analysis only; ideally needs new runs)*

The decomposition is sequential: wording, then the tool-call write, then the rest. "The rest" is estimated
as B - A1w, which is the rest of the channel applied to tool-written notes. The replay control estimates the
rest of the channel applied to broadcast's reply notes instead.

At 8B the two estimates disagree:

- In p10, B - A1w = **-1.6 (-5.3 to 2.2)**, which is not significant.
- In t09_replay, B - A1 with the same notes = **-5 (-8 to -2)**, which is significant.

So the rest of the channel may cost more when the notes are better, which is an interaction. If it does,
the order "write first, then rest" moves loss from the rest to the write at 8B, and that is exactly where
the paper says the write effect survives Holm. The conclusion that the write "cost accuracy at two of four
sizes" depends on this order.

- **Fix (text/analysis):** state that the split is sequential and order-dependent. Report the replay
  estimate next to B - A1w at 8B and discuss the gap. Do not rank the steps at 8B (the paper already avoids
  this partly).
- **Fix (needs new runs):** add the missing cell of a 2x2 design (reply notes vs tool-written notes, crossed
  with copy-forward vs files) inside the same p10 run. This is "A1r notes stored as a file and read through
  B" at each size. It gives main effects and an interaction instead of a path-dependent split.

### W2. The serving-time conclusion at 32 concurrent tasks is contradicted by the per-task latencies already in the records. *(text/analysis only)*

The conclusion says zero-copy "saved no serving time at six or 32 tasks at a time". Here "serving time" is
the makespan: the time until the last of 100 tasks finishes. At concurrency 32 that is only about three
waves of tasks, so one straggler sets the result. From the `wall_s` field of the p11_c32 rows:

| Channel | Run | Median task latency | p90 | Max | Makespan |
| --- | --- | --- | --- | --- | --- |
| A1 | r1 | 34.6 s | 45.9 s | 68 s | 126 s |
| A1 | r2 | 34.1 s | 45.4 s | 62 s | 124 s |
| A1-zc | r1 | 28.8 s | 39.6 s | 87 s | 126 s |
| A1-zc | r2 | 27.7 s | 42.5 s | 90 s | 125 s |

So zero-copy lowers the median task latency by about 17% and the summed latency by about 13%. This matches
the paper's own summed request time of 0.87x. The equal makespan comes from one 87-90 s straggler.

At concurrency 6 (about 17 waves) the median is unchanged (13.5 vs 13.6 s), but the p90 rises from 18.1 to
22.8 s. This fits the extra generation being concentrated in a few long tasks.

A likely source of those long tasks is degenerate generation in the Researcher. In the main run, A1-zc's
Researcher hits the 2,048-token cap in 3.0% of k=3 tasks, against 0.3% for A1.

- **Fix:** report median and p90 task latency, plus a throughput figure (tasks per second over a long
  closed-loop run), next to makespan.
- Drop "or 32" from the conclusion, or reword it to say that at 32 tasks at a time zero-copy finishes the
  typical task faster but not the batch.
- Report how much of the 1.2x extra generation comes from cap-hit calls.
- (Optional, new runs) A run with several hundred tasks at concurrency 32 would remove the makespan
  artifact.

### W3. The fan-out mechanism is asserted rather than shown, although the records support it directly. *(text/analysis only)*

"B's fan-out loss at eight questions thus comes from sharing one folder" rests on Bf. But Bf changes two
things at once: it prevents overwrites, and it changes the paths the Writer sees (the paper says so). It
also changes how much tool budget is used. In p15_k8_three, B's Reviewer hits the 12-call limit in **67%**
of tasks, against 12% in Bf. The Writer hits it in 32% vs 29%, and the rescue fires for 70% of B's Reviewers
vs 28% in Bf. A reader cannot tell whether overwritten notes or budget exhaustion during the search for
notes cause the loss.

The data can separate these. I split B's three-Researcher questions by whether the Researcher covering each
question still had its notes in the workspace (the same ownership replay as `REightOneLeftB`):

- Questions whose Researcher's notes **survived**: **57.8%** accuracy (n=427).
- Questions whose notes were **overwritten**: **22.8%** accuracy (n=373).
- One-Researcher B: 62.7%.

This within-task contrast is far stronger evidence for the overwrite mechanism than the Bf arm.

- **Fix:** add this per-question split, and report Writer and Reviewer turn-limit rates for B, Bf, Bn, and
  Bh.
- Soften "thus comes from" to "is mostly explained by". The Bf vs one-Researcher-B interval (-5.8 to 3.0)
  does not exclude a residual loss of several points.
- (Optional, new runs) Run the write guard (Bn) at k=8 in the p15 three-Researcher run. It prevents
  overwrites without changing paths.

### W4. Prompt and harness asymmetries are as large as the attributed effects, and each channel has only one prompt. *(needs new runs for the fix; text for the caveat)*

The introduction says the study changes "only how results reach the next agent". It does not:

- The channels differ in instruction wording.
- They differ in call budget: 1 call for message channels, up to 12 calls plus a forced rescue call for
  file channels.
- Zero-copy moves the role instruction after the documents.
- The main run caps each call at 2,048 tokens, which tool-call writes hit more often. In the main run at
  k=3, B's Researcher hits the cap in 7.3% of tasks and leaves **empty notes in 5.0%**. A1 has 0.3% cap
  hits and 0% empty notes.

The wording control shows that wording alone moves 4B accuracy by **+6.2 points**. That is larger than the
8B write effect (-5.6) and the 32B write effect (-4.4). At 8B, 14B, and 32B the wording interval of ±3.1
does not exclude effects about as large as the 32B write effect.

With one wording per channel and per model, the results may depend on that wording rather than on the
channel.

- **Fix (text):** replace "change only how results reach the next agent" with a list of what else
  changes. Report the main-run B gap without cap-hit tasks, as the paper already does for p10.
- **Fix (new runs):** run two or three paraphrases of each channel's instructions at one size (8B, k=3,
  about 150 tasks) and report the spread across paraphrases next to the gap between channels.

### W5. The "two of four sizes after correction" result is on a knife edge. *(text/analysis only)*

I reproduced the Holm procedure:

- 8B write: p = 0.00625 against a step threshold of 0.00714, so it passes.
- 32B write: p = 0.0097 against 0.00833, so it fails.
- 8B write without the 7 cap-hit tasks: CI -7.5 to -0.2, which would very likely fail.

The abstract and conclusion state "two of four" as a finding. The evidence is closer to this: write effects
of 4-9 points at three sizes, all with uncorrected intervals excluding zero, of which two clear Holm by a
narrow margin.

- **Fix:** report Holm-adjusted p-values for the write effects at 4B, 8B, and 32B (a small table or a
  sentence). Phrase the abstract as "at three of four sizes (two after Holm correction)". Say that the 8B
  effect partly depends on cap-hit tasks.

### W6. Cross-run and cross-GPU comparisons have no A/A control on the RTX PRO 6000. *(analysis only for the caveat; new runs for the fix)*

Several claims compare runs on the PRO 6000:

- the k=8 one- vs three-Researcher runs (p15, back to back);
- the path-normalized 32B rerun against p02's broadcast;
- the heading-rule result against C from t08_large, which ran on a 3090;
- the earlier p05 write effects.

The A/A rerun covers only the 3090s. The broadcast arm in p15 (-0.9, CI -3.9 to 2.0) is a useful in-design
drift check and should be presented as such for the k=8 claim. The others have none.

Also, the first of the three timing repeats (p06) ran on a different commit, without counter scraping, and
alongside another job on a different GPU of the same host (p08_norm_32b). It is not exchangeable with the
two p11 repeats. For B its makespan is 484 s against 415 and 438 s.

- **Fix (text):** label the p06 repeat as such. Report B's time ratio with and without it.
- **Fix (new runs, cheap):** one A1/B A/A pair on the PRO 6000 at k=3 with 100 tasks.

### W7. The fact-level measures support several causal sentences without having the validity to bear them. *(text/analysis only)*

AlignScore at 0.5 says broadcast's notes state only 45% of the supporting facts, yet broadcast answers 72%
of the questions. Its agreement with an LLM judge on real notes is kappa = 0.29.

Even so, the text uses it for directional claims such as "Writing through a tool call drops supporting facts
from the notes at 4B, 8B, and 32B", with no intervals and with empty notes included (5% at 8B in p10). The
"delivery" metric counts document reads, so for files it measures exposure, not whether the notes arrived;
the paper says so. The "opened the notes" measure is more direct and should carry those claims.

- **Fix:** add bootstrap intervals for the notes-fact numbers in Figure 3a. Report the base rate of
  correct answers whose notes "miss" a fact (the code already computes it as `aq_right_notes_miss`). Back up
  the tool-write fact drop with a cheaper, more valid measure: note length, or the share of the task's
  questions that the notes mention.

### W8. Some results do not generalize, and the text does not say so. *(text only)*

- **C vs B depends on model size.** At 14B, C trails broadcast by 16 points and B by 8, so the index *hurts*.
  The section "Readers without an index skip the notes" and the guidance in the conclusion rest on 8B.
- **The pipe's loss appears only at 8B.** It is within 2 points at every other size, yet it frames a full
  results paragraph.
- **Serving time is measured at one model size, one k, and one GPU type.** The abstract puts "take
  1.56-1.80x the time" next to a token range taken across all settings.
- **The fan-out repairs are tested at one k each.** Separate folders are tested only at k=8, and the guard
  and heading rule only at k=16.
- **The scope is narrow.** One model family, the hermes tool-call parser, thinking disabled, linear
  three-role pipelines, and short-context multi-hop QA.

The final sentence names some of these. The guidance ("Parallel writers should get their own folders...")
is stated as general.

- **Fix:** put a short scope line under the guidance. Add the 14B C/B reversal to the index paragraph.

### W9. Figure 4 mixes runs and has no intervals; the k=16 point changes the design. *(text/analysis only)*

Figure 4 combines different runs:

- k=1/3/5 come from the main run;
- k=8 comes from t08_k8;
- k=16 comes from t08_large, with three Researchers.

The figure has no intervals, and k=16 changes the number of Researchers as well as the payload. The caption
says "$k=16$ uses three parallel Researchers". But panel (b)'s subtitle "plain files collapse at large k"
reads as an effect of payload size, while the paper's own k=8 experiment attributes most of the collapse to
the shared folder.

- **Fix:** add interval bands or error bars. Mark k=16 as a separate design, not a point on the k axis.
  Retitle (b) so it does not attribute the collapse to k.

### W10. Small wording issues that matter for reproducibility. *(text only)*

- "Each run gets its own cache namespace". In the code, the salt includes the task ID and `time_ns()` per
  task-channel execution (`pipeline.run_task`). So no prefix is shared across tasks, not even the system
  prompt or the tool schemas. Say "each task's pipeline", and note that deployments sharing system prompts
  across tasks would see slightly lower prefill for every channel.
- The k=16 heading-rule arm has n=59 because one task errored. Say so.
- The A/A "intervals inside ±2.2" is the maximum absolute interval endpoint. Say that, so it is not read as
  a half-width.

## Questions for the authors

1. At 8B, why does the rest of the file channel cost -1.6 with tool-written notes (p10) but -5 with
   replayed broadcast notes (t09)? Is this an interaction (better notes lose more), or a difference between
   GPUs and runs?
2. What share of A1-zc's 1.2x extra generation, and of its 87-90 s straggler tasks at concurrency 32, comes
   from Researcher calls that hit the token cap?
3. In p15, how does accuracy for questions whose notes were overwritten compare with Bf's accuracy on the
   same questions? Does Bf close the gap through surviving notes, or through fewer turn-limit hits?
4. Why does the B Reviewer hit the turn limit in about 47% of tasks at k=16 even with 24 calls? Are these
   repeated reads of the same file (a loop) or a search across many files? This decides whether budget is a
   factor at all.
5. Were the instructions for each channel tuned at all (on which model, and on which tasks), or written
   once? Were the k=3 tasks used for the main results also used to develop the prompts?
6. Is the 14B reversal (C worse than B) significant within the run? What mechanism do you propose?

## Sentences that overclaim or do not match the code or numbers

1. Conclusion: *"It saved no serving time at six or 32 tasks at a time"*. At 32, the median task latency is
   28.8/27.7 s against 34.6/34.1 s, and the summed request time is 0.87x. Only the makespan of 100 tasks is
   equal (W2).
2. Sensitivity: *"B's fan-out loss at eight questions thus comes from sharing one folder."* Bf also changes
   paths and turn-limit rates (Reviewer 67% → 12%). The Bf vs one-Researcher interval allows a residual loss
   of 5.8 points (W3).
3. Introduction: *"We keep the task, the model, the roles, and their order fixed, and change only how
   results reach the next agent"*. Wording, call budget, rescue, and the position of the instruction also
   change. Wording alone moves 4B by +6.2 (W4).
4. Abstract and conclusion: *"at two of four sizes after correction"* is presented as a finding. 8B passes
   Holm by 0.00625 vs 0.00714, 32B fails by 0.0097 vs 0.00833, and the write/rest split is order-dependent
   (W1, W5).
5. Results: *"The wording does not lower accuracy."* The intervals (±3.1) do not exclude effects as large
   as the 32B write effect, and at 4B wording changes accuracy by +6.2. "We detect no loss from wording" is
   accurate.
6. Results: *"Writing through a tool call drops supporting facts from the notes at 4B, 8B, and 32B"*. There
   are no intervals, the metric has kappa 0.29 against a judge, and 5% of 8B tool-write notes are empty
   because of cap hits (W7).
7. Conclusion: *"Plain files sent more tokens, took longer, and lost accuracy in every setting"*. "Took
   longer" was measured only at k=3, with 8B, on one GPU type.
8. Readers-without-index paragraph: *"The index names the notes. C's Writer skips them in 7% of the tasks,
   and delivery rises..."*. This holds at 8B. At 14B, C trails broadcast by 16 points against B's 8 (W8).
9. Figure 4(b) subtitle: *"plain files collapse at large k"*. The k=16 point also triples the number of
   Researchers, and the paper's own k=8 test attributes the collapse mainly to the shared folder (W9).
10. Methodology: *"Each run gets its own cache namespace"*. The code salts each task-channel execution
   separately (`task_id` + `time_ns`), not each experiment run (W10).
