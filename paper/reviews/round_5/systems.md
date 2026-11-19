# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6 pages)

## Summary

The paper compares five ways that a three-agent Researcher-Writer-Reviewer pipeline can pass results: broadcast (copy the whole history), a cache-friendly reordering of broadcast ("zero-copy broadcast"), a pipe (copy only the previous output), shared files, shared files with an index, and "handles" (a short handoff plus file paths). It runs Qwen3-8B on vLLM over HotpotQA and 2WikiMultihopQA, with 150 paired tasks per dataset and k in {1,3,5}. Cost is counted three ways: tokens sent, prefill tokens computed after prefix caching, and wall-clock serving time. Main findings at k=3:
- Copying is the most accurate channel (72.3%).
- Reordering cuts prefill by 61% at the same accuracy but is 1.10x slower in a single served-alone run.
- Files send 2.8-2.9x the tokens but compute 0.79x the prefill, take up to 1.97x the time, and lose 6-14 points.

A set of controls attributes the file loss mostly to the act of writing notes through a tool call (A1w vs A1r) and partly to readers that skip the notes. Sensitivity runs cover k=8/16 (with fan-out), KV cache size, tool budget, a batched read tool, a fourth agent, and model size (4B-32B).

The paper is careful, heavily controlled, and honest about many of its limits. Its main weaknesses:
- The systems claims (serving time, cache behavior) rest on one wall-clock run and a cross-channel-interleaved server.
- The fact-level measures and stage attribution are weaker than the prose implies.
- The largest number in the abstract (the 34-point collapse at k=16) is unexplained and confounded with fan-out and harness choices.
- Several findings are idiosyncratic to one model size in one model family.
- The novelty is mainly in the measurement. The cache-friendly ordering is standard practice, and the OS framing is mostly an analogy.

## Score

**3 / 5 (weak accept, borderline).** This is a useful, carefully controlled measurement study that would start good discussion at a workshop. The systems half (time and cache) is thin, and some headline claims outrun the evidence.

**Confidence: 4 / 5.** I checked every number in the text against `numbers.tex` and the serving-time code path in `paper_numbers.py`.

## Strengths

1. **Paired, controlled design.** The same tasks run on every channel, and the paper reports bootstrap intervals over tasks for paired differences. The A/A rerun (±2 points, B-A1 gap 7.0 vs 7.8) gives a credible noise floor, which few agent papers do.
2. **Controls that separate channel from content.** Five controls do this:
   - Notes replayed into every channel.
   - A pipe that also gets the documents.
   - B with the documents in its prompts.
   - A1r/A1w, which matches the instruction wording and varies only the tool.
   - A zero-copy replay at 4B.
   The A1r/A1w control is the paper's most original result: writing notes through `write_file` drops facts (29% vs 46% at 8B) and accuracy (-5.3, CI -8.3 to -2.3) at three of four sizes, while the wording alone does not.
3. **Three cost views.** Separating billed tokens, computed prefill, and wall time is the right framing for self-hosted vs API deployments. Fig. 2b makes the prefill-vs-accuracy point clearly.
4. **Honest reporting of awkward results.** The paper reports:
   - The rescue rate and strict-accuracy bound (18-41%).
   - That the pipe's review loss exists only at 8B.
   - That the index does not help with a single named notes file.
   - That the AlignScore-judge agreement is low.
   - That the k=16 collapse has no explanation.
5. **Text and numbers agree.** All numbers come from a script-generated macro file, and I found no case where a macro value contradicts the sentence around it (see the last section for wording issues).

## Weaknesses (most important first)

### W1. The serving-time result, the paper's only systems-time evidence, rests on one run at one load level, and generation length confounds it. [needs new runs]

`RFourTime*` comes from a single `elapsed_s` per channel (`p06_alone_*`, 100 tasks, six at a time, RTX PRO 6000). There is no repetition, no interval, and no second concurrency level.

Zero-copy broadcast generates 1.3x the completion tokens (its notes grow from 1,570 to 1,992 characters). Its 1.10x time therefore mixes "prefill saved" with "more decode". At six concurrent tasks on a PRO 6000, decode dominates, so the heading "Prefill savings buy no serving time" and the abstract's "it saves no time" describe a regime, not a property of the channel.

Fix:
1. Repeat each alone run at least 3 times and report a CI.
2. Add at least one higher concurrency level (e.g., 24 or 48 tasks) and one larger k (5 or 8 with the 100k cache), where prefill weighs more.
3. Separate prefill from decode. Either replay A1's exact completions under both orderings (forced decoding or fixed outputs), or report per-call TTFT and prefill time from vLLM metrics.

Without step 3 the paper cannot say whether the cache savings buy time.

### W2. Computed-token numbers come from servers that interleave all channels. Under the 34,864-token RTX 3090 cache, a channel's hit rate depends on what other channels evict. [text/analysis only if alone-run logs have cached tokens; otherwise needs new runs]

The methodology says "Each server runs six tasks at a time, interleaved across channels" with a 34,864-token KV cache and a 32,768-token max length. That cache holds roughly one maximal prompt.

`cache_salt` prevents cross-channel hits but not cross-channel eviction or preemption. File channels make about 17 calls with growing conversations and pollute the shared LRU cache, so every number in Fig. 2b and Fig. 4a is a property of the mix, not of the channel alone. This is the paper's own "change only the channel" principle broken for the compute metric.

The paper's own data show how strong the effect is. At k=16, B computes 1.83x broadcast's prefill on the 3090 servers but 0.58x with a 100k cache. At k=8, zero-copy computes 0.85x vs 0.36x.

Fix:
- Report k=3 computed tokens from the served-alone runs (or the 100k-cache runs) next to the interleaved ones.
- Re-label Fig. 4a as "with a 35k-token KV cache", or plot it against working set divided by KV capacity.

### W3. The headline collapse at k=16 (-34 points for B, in the abstract) is unexplained and confounded. [needs new runs]

k=16 changes the topology (three parallel Researchers) as well as the payload. Fan-out alone costs broadcast 6 points at k=3 (`FanAOneDiff` = -6, CI -11 to -1).

The harness also keeps several knobs fixed across k:
- A 12-call tool budget.
- A 120-word handoff limit for D, even at 16 questions.
- A `write_file` that silently overwrites. Researchers clobber each other in 72% of B's tasks, and notes keep 34% vs 67% of facts with and without a clash.

The no-clash subgroup is only n=17. The paper says it has "not tested ... what in file access at sixteen questions causes the collapse". As a result, the most dramatic number in the abstract may come from the harness rather than the channel.

Fix (each is cheap):
- Run k=16 with a single Researcher to separate payload from fan-out.
- Run B with per-Researcher namespaced paths, or with a write that fails on an existing file.
- Log what B's Reviewer does with its calls (47-48% exhaust both 12 and 24, which suggests a loop, not a budget shortfall).

If no explanation emerges, move the 34-point number out of the abstract or qualify it.

### W4. Generality: one model family, and several findings flip between sizes. [needs new runs]

Many findings hold at only one model size:
- The pipe's review loss exists only at 8B (10 points; within 2 elsewhere).
- Zero-copy hurts only at 4B.
- The index helps at 8B but hurts at 14B (C trails by 16, B by 8).
- 32B is worse than 14B on files (B 28 raw, D 32 raw; D still -16.5 after the path fix).
- The tool-call write loss vanishes at 14B.

With one model family, a reader cannot tell channel effects from Qwen3 tool-use quirks. The conclusion's rule "Files need a model that handles tools" is never measured: there is no independent tool-use metric, and the size trend is non-monotonic.

Fix:
- Run the k=3 main matrix (or at least A1, A1-zc, A2, B, C) on one other open family with a mature tool parser (e.g., Llama-3.1-8B-Instruct or a Mistral or gpt-oss model).
- Either measure tool-use reliability (wrong-path rate, malformed calls, rescue rate) per model and correlate it with the file gap, or drop the "needs a model that uses tools well" rule.

### W5. The file channels may be a weak baseline: the harness rescues them in up to 59% of runs. [text/analysis only, plus one small run recommended]

At k=3 the forced "must write output" call fires in:
- 59% of B's Writer runs.
- 34% of B's Reviewer runs.
- 39-46% of C's Writer and Reviewer runs.

Counting rescued runs as wrong drops B, C, and D to 18-41%. At 32B the first harness missed the answer in 51 of 200 B runs and 59 of 200 D runs (paths under `workspace/`).

The paper argues frameworks take the last message as output, but a rescue rate this high means the file agents often do not finish the protocol. The B-vs-A1 gap may then measure harness and prompt fragility as much as "shared memory". There is also no "B + notes path" variant (a handoff with the path only), which would isolate discovery from the handoff's content in D.

Fix:
- Report accuracy split by rescued vs unrescued runs per channel.
- Add the path-only handoff variant.
- State in §2 that the file protocol was not tuned per model, if that is the case.

### W6. The fact-level measures and stage attribution are not reliable enough for how strongly the prose uses them. [text/analysis only; a small human annotation is recommended]

- **Validation.** AlignScore's AUC of 0.996 is on synthetic edits. On real paraphrased notes it agrees with Qwen3-8B as a judge at kappa = 0.29, and that judge itself accepts 22% of removed sentences. Agreement with a weak reference says little either way. A 150-200-item human annotation of (note, supporting sentence) pairs would settle it.
- **Fig. 3a mixes two things.** For file channels, "Reached Writer" counts facts the Writer got from any file it read, source documents included. 83% of B's Writer reads go to sources, and in 42% of tasks it never opens the notes, yet delivery is 87-94%. The metric therefore measures whether facts were available, not whether the notes were delivered. For A1, whose Writer also receives every document, the bar shows 45 instead of 100.
- **Fig. 3b's attribution is close to uninformative.** It charges the Researcher whenever its notes miss any supporting fact. In A1 the Writer has all documents, and 76% of A1's correct answers come from notes that miss a fact. So "Researcher missed", the dominant stage in every bar, is not a cause.

Fix:
- Define delivery as notes-to-Writer only, and report source reads separately.
- Attribute stages by counterfactual replay (e.g., re-run the Writer with gold-complete notes), or drop panel (b) and keep only the reviewer-broke statistic.
- Add the human check.

### W7. The paper's central framing is weaker than its best finding, and novelty is modest. [text/analysis only]

The key observation, "cost has to be counted three ways", is known to anyone who runs APIs with cached-input pricing. The paper also reports that time ranks the channels the same way tokens sent does, which weakens the observation.

"Zero-copy broadcast" is the standard "shared content first" prompt ordering. The paper admits this, and the name is a misnomer since every token is still sent. The OS analogy is mostly narrative:
- Prefix cache as "shared pages" does not fit: shared memory means not sending.
- The Lauer-Needham duality is never tested as a duality.

The paper's most interesting and novel results are about information loss:
- Writing through a tool call drops facts.
- Readers with a cheap bulk read skip the notes (80%).
- Parallel writers clobber each other.

Its own numbers support a crisp decomposition at 8B (from `numbers.tex`, model-size runs):
- A1 73.2, A1r 71.5, A1w 66.2, B 63.2.
- Wording: -1.7.
- Writing through a tool: -5.3.
- Reading from files: -3.0.

So about 70% of B's 10-point loss comes from the write side. The paper never states this.

Fix:
- Lead with the decomposition table.
- Rename A1-zc (e.g., "prefix-ordered broadcast").
- Tone down the OS framing to a motivating analogy, or test one OS-style prediction explicitly.

### W8. API cost is mis-modeled. [text/analysis only]

"Tokens sent ... is what an API bills without caching" sums prompt and completion tokens. APIs price output at about 3-5x input and cached input at about 0.1-0.5x. File channels generate 1.6-2.2x the completion tokens, so their billed cost relative to broadcast is probably larger than 2.9x.

Fix: add a dollar cost under one or two published price schedules (with and without cached-input discounts).

### W9. Missing figure for the third cost, and figure-level issues. [text/analysis only]

- **No figure shows serving time,** although it is one of the "three ways". Add a Fig. 2(c) with accuracy vs serving time (after W1).
- **Fig. 2 intervals mislead.** It shows marginal per-channel CIs that overlap (e.g., C vs A1), while the significance claims rest on paired differences. A reader looking at the plot will conclude "no difference". Add a paired-difference strip or say so in the caption.
- **Fig. 4:**
  - No intervals, and the task counts for k=8 and k=16 are not stated anywhere (the clash numbers imply 60 tasks at k=16).
  - Lines connect across the topology change at k=16.
  - Panel (a)'s title, "cache savings fade as payloads grow", is contradicted by the 100k-cache result in the next paragraph.
  - The "A1 = 1" label sits on the B/D lines.
- **Fig. 1** does not show the paper's key mechanism for files: each tool call is a model call that resends the conversation. A call count per agent (about 17 vs 3) would make Fig. 2a self-explanatory.
- **No main results table.** A k=3 table (accuracy, sent, computed, time, calls, rescue rate per channel) would replace several number-dense paragraphs.

### W10. Statistical presentation. [text/analysis only]

- "No difference is significant" for zero-copy vs broadcast is not evidence of equivalence. Report the pooled paired CI and an equivalence margin (TOST at ±3 points). The 4-point exact-match deficit on 2Wiki deserves an interval.
- Counts of "significant in five of six settings" are uncorrected. Either apply Holm or present the intervals in a small forest plot.
- Several controls compare a new arm against a reference from an earlier run, e.g., "B, C, and D then trail the first run's broadcast". With 59% output identity on identical prompts, state which comparisons are within-run and which are cross-run, and widen the cross-run ones by the A/A noise.
- The accuracy metric counts "the gold answer inside a short prediction" as correct. Define "short", and report exact match for the main table as a robustness check.

### W11. Related work gaps. [text/analysis only]

These are missing:
- KV preservation across tool calls (InferCept). This addresses exactly the "each file read resends the conversation" cost.
- Agent-program schedulers (Autellix, Ayo/Teola-style).
- Non-prefix KV reuse (CacheBlend) and cross-model KV sharing (DroidSpeak).
- OS-inspired agent memory (MemGPT/Letta, AIOS). This is the closest "files as agent memory" prior work in an OS-framed paper.

Explain why the prefix-reuse and KV-communication systems (KVCOMM, TokenDance, KVFlow) would or would not change the file-channel conclusions.

## Questions for the authors

1. At k=16, how do the message channels merge three Researchers' notes, and how are documents split among Researchers? How many tasks were run at k=8 and k=16?
2. Do the computed-token numbers in the served-alone runs match the interleaved ones at k=3 (W2)?
3. What does B's Reviewer do with 24 calls in the 47% of runs that exhaust them: re-reading the same file, listing, or rewriting?
4. Were the control arms (A1r/A1w, scope, replay, read_files, chain) run on the same server in the same batch as their reference arms, or compared against earlier runs?
5. Does accuracy differ between rescued and unrescued file-channel runs?
6. Was the file-channel prompt or protocol tuned at all (per model or per channel)? How many prompt iterations did each channel get?
7. With the same notes replayed, why does C's Writer open the notes less often than B's (63% vs 76%)? Does the index steer it toward sources?
8. Why is the D handoff fixed at 120 words for every k?

## Quoted sentences that overclaim, are unclear, or mismatch their numbers

1. Abstract: *"Zero-copy broadcast ... keeps copying's accuracy while computing 38–49% as much prefill, but with each channel served alone, six tasks at a time, it saves no time."* The run shows it is 10% slower (1.10x) while generating 1.3x the tokens, from a single run. Write "was 1.10x slower in one run, in which it also generated 1.3x the tokens", and see W1.
2. Abstract: *"and readers without an index skip the notes."* In the cleaner replay control, readers *with* an index skip the notes more (C opens them in 63% of tasks vs B's 76%). The claim holds only for the main runs at 8B and is reversed at 14B. Qualify it.
3. Abstract: *"When three parallel Researchers split sixteen questions, plain files lose 34 points, and neither a larger KV cache nor twice the tool budget closes the gap."* The numbers match (34; 33.9; +3.3). But the cause is untested and the condition changes topology and k together (W3). This is too prominent for an unexplained, possibly harness-driven result.
4. Intro: *"Our key observation is that cost has to be counted three ways"*. In the same paragraph, time "ranks the channels as tokens sent does", so for time, one of the three counts was enough. Restate the observation as "prefill disagrees with both billed tokens and time".
5. Intro and Conclusion: *"the file channels need a model that uses tools well"* / *"Files need a model that handles tools."* No tool-use metric is reported. Files trail at every size, and 32B does worse than 14B. This is unsupported.
6. §4 heading: *"Prefill savings buy no serving time."* This generalizes from one load and one GPU. Write "At six tasks at a time, prefill savings bought no serving time".
7. §4: *"In accuracy, C comes within 6.0 points of broadcast at k=3 pooled"*. 6.0 is the gap itself (72.3 vs 66.3), and "comes within" reads as reassurance. Write "C trails broadcast by 6.0 points".
8. §4: *"Writing through a tool call, not the wording, costs accuracy whenever it drops facts from the notes."* "Whenever" is a law drawn from four model sizes with no mechanism. Write "at the three sizes where it dropped facts".
9. §4: *"The wording thus costs no accuracy."* At 4B the B wording *raises* accuracy by 5.3 points, so wording matters there. At 8B the interval reaches -3.7. Write "The wording does not lower accuracy".
10. Fig. 4a title: *"cache savings fade as payloads grow"*. This is contradicted by §5's "A larger cache brings the savings back, fully at eight questions". The savings fade because of the 35k cache, not because of payload size.
11. §5: *"The pipe loses only with Qwen3-8B ..., so its loss at review is specific to that model."* This is correct and important. But then the §4 heading "A pipe is cheap but loses at review" and the conclusion's guidance generalize an 8B-only effect. Qualify both.
12. §2: *"Its instructions differ in where its notes go ... and in what each channel asks of it, and §4 separates the two for B."* Unclear. Split it into two sentences and name the control (A1r/A1w).
13. Fig. 3 caption: *"The second bar is the first times delivery"*. Unclear. Write "Reached Writer = facts in output x delivery rate".
14. §5: *"B's accuracy change from one to three Researchers, less broadcast's, is −4 points"*. Write "a difference-in-differences of −4 points (B's change minus broadcast's)".
15. §6: *"In agents, the prefix cache plays the role of shared pages, since every token is still sent"*. The "since" clause argues against the analogy, because shared memory means not sending. Rewrite or drop.
16. §5: *"close to a rescore of the 51 B and 59 D runs (of 200) whose answer the first harness missed"*. Unclear, and it buries a 25-30% harness failure rate. State it plainly and include it in W5's discussion.
17. Conclusion: *"Long results are better written as plain replies that the system stores"*. This is a recommendation for a hybrid channel. Cite the replay control, the closest test (system-stored notes read via files: -5 points vs broadcast), and note that it was not run as its own channel.
18. Contributions: *"derive rules for choosing a channel (§7)"*. §7 is a single conclusion paragraph, not rules. Either add a short rules box or soften this.

## What stands between this paper and acceptance

The information-loss half is close: controlled, novel enough for a workshop, and mostly well supported. The systems half is not yet:
- One wall-clock run.
- Compute numbers taken under cross-channel cache interference.
- No separation of prefill time from decode time.

Minimum to move to accept:
1. Repeated served-alone timing with a prefill/decode split and one higher load (W1).
2. Compute numbers from served-alone runs (W2).
3. A single-Researcher k=16 run and a namespaced-write B run, or else de-emphasizing the 34-point number (W3).
4. Rewriting the framing around the write/read decomposition, with a main table, and fixing the overclaims listed above (W7, W9, quotes).

A second model family (W4) would turn this from a Qwen3 case study into a general result.

## Round-6 recommendation

This section responds to the authors' draft plan (R1-R4). It takes into account the methods review (`round_5/methods.md`) and these constraints:

- One server of 96 GB GPUs.
- About 5,000 pipeline runs over one day.
- 12 days to the deadline.
- 6 pages.
- No second model family.
- No human labels.

### Verdict on R1-R4

**R1 (writing control): keep, with changes. This is the most important run.**
It makes the abstract's writing-loss claim within-run and removes the 2,048-token truncation confound (methods W1).

Changes:
- Use one server per size and interleave the arms in one job queue, so A1, A1r and A1w share batch composition.
- Use `max_tokens=4096` for every role in every arm, and turn on the `workspace/` path normalization for every size, not just 32B.
- Log `finish_reason`, empty notes and rescue use for each arm and role.
- Add a **B arm at 8B** (+200 runs). A1 → A1r → A1w → B then gives a within-run split of the loss into wording, writing and reading. The paper needs this split, and today it can only be pieced together across runs.
- Present R1 as its own table. Its A1 differs from the main run's A1 because of the cap change, so do not mix the two.

Cost: 4 sizes × 3 arms × 200 tasks, plus 200 B runs = **2,600 runs**.

**R2 (serving time): keep, with changes. Trim the channels, move the second load level, and add a prefill-only replay.**
Concurrency 12 is still decode-bound, so it will repeat the current result and not test whether prefill savings ever buy time.

Changes:
- Run only A1, A1-zc and B. The single runs for A2, C and D can stay as they are, labeled as single runs.
- Use 3 repeats at concurrency 6 and 2 repeats at concurrency 32 (instead of 12), in randomized order.
- Use Qwen3-8B, k=3, 100 tasks and a 100k KV cache, and run on a host with no other GPU jobs.
- Report the median and mean per-task latency with CIs, the makespan, and the cached share. At concurrency 32 the working set exceeds 100k tokens, so cache reuse may fall. If it does, that is a finding, not a failure.

Cost: 3 channels × 100 tasks × (3 + 2) repeats = **1,500 runs**.

New, zero pipeline runs, about 1 GPU-hour: replay the logged A1 and A1-zc prompts call by call, in task order, with the completions held fixed. Either force the recorded completion or set `max_tokens` to the recorded length with `ignore_eos`. Do this at concurrency 6 and 32, and record per-call TTFT and makespan. This is the only design that separates "prefill saved" from "zero-copy writes 1.3x more". Without it, the heading "prefill savings buy no time" cannot be tested.

**R3 (k=16 no-clobber): keep, with changes. Add same-run references and a heading-only arm.**
As drafted, R3 would again compare against a reference from another run.

Changes:
- Run k=16 with three Researchers, 60 tasks, on the 100k KV cache (so eviction is not a factor).
- Arms: A1, B, B-noclobber, D-noclobber, and B-heading. B-heading is B plus C's "head each file with its questions" rule, without the index; it tests methods W7, i.e. whether the heading rule rather than the index explains C's zero clashes.

Cost: 5 arms × 60 tasks = **300 runs**.

**R4 (A/A at 14B): change it to a 4B replication plus a check on how the instruction is placed.**
No sentence in the abstract rests on 14B. The abstract's 4B zero-copy loss (-7 points) and its "prompt order" mechanism do, and both are now single-run claims with a role-placement confound.

Changes:
- Rerun the `p02_size_4b` arms A1 and A1-zc on a different GPU from the original run. This is a cross-run A/A on the PRO 6000 at a size other than 8B, which methods W4 asks for, and it also replicates the 4B loss.
- In the same run, add **A1u**: broadcast with the role instruction as the first user turn instead of the system prompt. This separates order from role placement.
- 150 tasks per arm.

Cost: 3 arms × 150 tasks = **450 runs**.

### Missing experiment I rank above R4

**k=8 fan-out: A1 and B, each with 1 and 3 Researchers, in one run.**
- Setup: Qwen3-8B, 100k KV cache, 75 tasks, 4 arms.
- Claim tested: whether the k=16 file collapse comes from fan-out or from payload size (systems W3, methods Q7). Single-Researcher k=16 does not fit in the 32k context, but k=8 does. The difference-in-differences (B's change from fan-out minus A1's change) answers the question at a payload that fits.

Cost: 4 arms × 75 tasks = **300 runs**.

### Analysis only, no runs (do these regardless)

- Per-task timing medians and CIs from the existing `p06_alone_*` runs.
- vLLM preemption counts for the k=8 and k=16 runs.
- B Reviewer call traces at k=16.
- Accuracy for rescued vs unrescued runs.
- An exact-match/F1 row for each headline gap.
- Strict accuracy shown in Fig. 2.
- Holm correction within each claim family.
- The nested-task disclosure.
- The A/A bound corrected to ±2.2.

### Full plan

| Run | Runs |
| --- | --- |
| R1' (with B at 8B) | 2,600 |
| R2' | 1,500 |
| R3' | 300 |
| k=8 fan-out | 300 |
| R4' | 450 |
| **Total** | **≈5,150** |

The prefill replay adds about 1 GPU-hour on top.

### Minimal set I would accept as sufficient

1. **R1'** for at least 4B, 8B and 32B, with A1, A1r and A1w within-run and `max_tokens=4096`, plus the B arm at 8B.
2. **The prefill replay**, plus **R2'** at concurrency 6 with 3 repeats for A1, A1-zc and B.
3. **R3'** with A1, B and B-noclobber in the same run.
4. The analysis-only items above.

If R3' does not explain the collapse, the abstract should keep the 34-point number only with the qualifier "cause untested".

### Priority if only half the budget is available (about 2,500 runs)

1. Prefill replay (about 0 runs, about 1 GPU-hour).
2. R1' core: A1, A1r and A1w at 4B, 8B and 32B, 150 tasks, `max_tokens=4096` (1,350 runs). Keep the existing 14B result, labeled as cross-run.
3. R2' core: A1, A1-zc and B, 3 repeats at concurrency 6, 100 tasks (900 runs).
4. R3' core: A1, B and B-noclobber at k=16, 60 tasks (180 runs).

That totals about 2,430 runs. Next in line, in order:
- The B arm at 8B in R1'.
- Concurrency 32 in R2'.
- k=8 fan-out.
- R1' at 14B.
- R4'.
