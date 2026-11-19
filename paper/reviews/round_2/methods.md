# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines" (methods and evaluation)

## Summary

The paper runs a fixed Researcher -> Writer -> Reviewer pipeline (Qwen3-8B on vLLM, HotpotQA distractor and 2WikiMultihopQA, k = 1/3/5 questions per task, 150 tasks per dataset and k) over six inter-agent channels: broadcast (A1), broadcast with the shared history ordered first so the prefix cache reuses it (A1-zc), pipe (A2), shared files (B), files with a workspace-maintained index (C), and short pushed handoffs plus files (D). It reports accuracy, tokens sent, tokens computed after prefix caching, latency, AlignScore-based fact presence/delivery, and a per-question failure attribution. Headline claims: copying is most accurate; A1-zc keeps that accuracy at 38–49% of the compute; files send 1.8–4.8x the tokens and lose information on both the writing side (notes 27% shorter when written through `write_file`) and the reading side (no index means the Writer skips notes). Causal side experiments: A1w (tool-written notes copied forward), Researcher replay (A1's notes fed to every channel), fan-out (three parallel Researchers), a 4-agent chain, batched reads, a 24-call budget, Qwen3-4B, k = 8 and k = 16, and an A/A rerun.

I checked the text against `numbers.tex`, `paper_numbers.py`, `pipeline.py`, `metrics.py`, `alignfacts.py`, `factpairs.py`, `entities.py`, `analyze.py`, `figdata.py`, the experiment configs, and the raw records of the main run. Every macro I traced is computed as the code says. The problems are in what some measures mean, in a few comparisons, and in sentences that claim more than their numbers show.

## Score: 3 / 5 (borderline; accept if the measurement-validity and wording issues below are fixed)

## Confidence: 4 / 5

## Strengths

1. **Paired, controlled design.** All channels run the same tasks. Each run gets its own cache namespace (`cache_salt` per task/channel/time). Jobs are shuffled across channels on the same servers. Accuracy gaps are paired bootstrap CIs over tasks, which is the right unit because each task bundles k questions.
2. **Unusually honest harness reporting.** The paper reports how often the forced final write rescues B/C/D, and what accuracy would be if every rescue counted as a failure (B 18.0%, C 22.9%, D 41.0%). It also reports how often the 12-call budget is used up. Few agent papers do this.
3. **An A/A control.** Rerunning A1 and B gives accuracy within 2 points and the same B–A1 gap (7.0 vs 7.8). This calibrates the cross-run comparisons that the side experiments rely on.
4. **Causal side experiments, not only correlations.** A1w (writing side) and Researcher replay (reading side) are good designs. The replay keeps an A1 reference inside the same run.
5. **Validation of the fact measure on items with known labels.** The 450 present/dropped/swapped pairs show clearly that the small LLM judges accept entity-swapped facts. Moving to AlignScore was the right call.
6. **Three cost views.** Separating tokens sent (API bill) from tokens computed (self-hosted) shows the core trade-off well (Figure 3a vs 3b). Figure 1 is a clear to-scale explanation.
7. **Reproducible numbers.** Every number in the text is a generated macro.

## Weaknesses (most important first)

### W1. The fact-presence measure is validated only on easy, verbatim cases. On the real pairs it disagrees with every other measure, and the paper does not say so.
The synthetic "present" item puts the supporting sentence **verbatim** into a context made of its own paragraph's sentences (`factpairs.synthetic`). Agent notes paraphrase, compress and merge facts, and the synthetic set has no such case. On the 864 real (notes or Writer input, fact) pairs, `alignscore_validation.json` shows AlignScore agreeing with the Qwen3-8B judge 62% of the time (kappa 0.29), with Llama-3-8B 59% (kappa 0.22), and with lexical anchors 77% (kappa 0.54). AlignScore says "yes" to 39% of the real pairs. The absolute levels also differ widely. For A1's notes at k = 3: AlignScore 45%, Qwen judge 73% (`\nJNotesAOne`), exact entity match 91% (`\nEntAOneNotes`). One example row from the main run: A1 notes with AlignScore recall 0.125, yet 2 of 3 answers correct. So the paper's statement that A1's notes "state 45% of the supporting facts" is a statement about AlignScore on paraphrase, and the paper has not shown that AlignScore is reliable there.
**Fix:** Hand-label about 200–300 real pairs, stratified by channel and stage, and report each measure's precision and recall against those labels. Add paraphrased "present" items to the synthetic set (for example, an LLM-paraphrased F checked by hand). Report the real-pair agreement numbers in the paper. Present fact levels as "AlignScore-detected" and rely mainly on the between-channel differences.

### W2. Delivery and failure attribution are defined differently for message and file channels, and the attribution is driven mostly by how strict the measure is.
- For message channels, `writer_input` is only the Researcher's notes (`pipeline.run_task`), so delivery is 100% "by construction". But the A1 and A1-zc Writers also receive **every source document**. For file channels, `writer_input` includes the source documents the Writer read. Figure 2a's "Reached Writer" bar is therefore 45% for A1, even though the A1 Writer had all supporting facts in its prompt. For B, by contrast, facts that arrived through `docs/` reads are counted.
- In the attribution, a wrong answer is "Researcher missed" whenever **any** supporting fact is missing from the notes by AlignScore (`alignfacts.py`, `all(...)`). With per-fact recall around 45%, most questions, right or wrong, will have a missing fact. That is why "Researcher missed" dominates every bar in Figure 2b (20% of A1's questions), including channels where the Writer had the documents and so could not have been held back by the notes. The paper gives no base rate: how often do *correctly* answered questions also have a "missing" fact?
**Fix:** Define delivery on the Writer's whole input in every channel (A1 and A1-zc then deliver 100% of supporting facts, and A2 delivers the notes). Report the base rate of "notes miss a fact" among correct answers. For channels whose Writer sees the documents, either drop "Researcher missed" or relabel it ("notes incomplete, Writer had documents"). Better still, attribute with an intervention, for example by giving the Writer the gold supporting sentences on a subset.

### W3. "Changing only the channel" is not true of the prompts or the harness, and the A1w decomposition inherits the confound.
Per `pipeline.py`:
- The C Researcher is also told to "Start each notes file with a heading that says which questions it covers" and that other agents read the index first.
- The D Researcher must also write a 120-word handoff.
- The A1-zc Researcher gets its instruction after the documents. Its notes differ as a result (AlignScore 50% vs 45%).
- The B Researcher is told "The other agents cannot see your reply… choose the file names and how to split them."
- File channels also get tool schemas, a "[N tool turns left]" countdown, a "reply without calling a tool" nudge after each write, a stop on repeated calls, and the forced write.

According to `results/_failed/*/notes.txt`, most of these were added after smoke runs in which the file channels failed. A1w's Researcher uses B's prompt *and* the `write_file` tool. The heading "The tool call, not the file, shortens the notes" therefore attributes to the tool-call format an effect that could equally come from the workspace framing ("others cannot see your reply", "split into files").
**Fix:** Put every prompt and harness rule in an appendix and state that the harness was tuned on file-channel smoke runs. Add two cheap A1w variants: (a) the message-channel instruction text with output only through a `submit_notes` tool; (b) the file-framing text with a plain reply. Reword the heading to "Writing for the workspace shortens the notes" unless (a) and (b) separate the two causes.

### W4. The writing-versus-reading split is presented more precisely than the data allow.
"More than half of B's loss therefore comes from…": on these 200 tasks, B's loss is 72.0 − 64.2 = 7.8 points and A1w's is 4.7 (CI 2–8). The share is therefore anywhere from about 25% to about 100%. The two halves also do not add up: writing (A1w, 5) plus reading (replay, 5, CI 2–8) is about 10, more than the 7.8 total. That points to an interaction or to noise. The replay also tests reading under easier conditions than B's real runs (one clearly named `notes.md`, with A1's longer notes).
**Fix:** Bootstrap the ratio (writing loss / total loss) and report its CI. State that the two effects overlap rather than add. Say "both sides contribute losses of similar size". Optionally, replay B's own notes, with B's own file names, into A1 and B.

### W5. The cache-capacity conclusions rest on one small cache, and k = 16 is confounded with fan-out.
- The KV cache holds 34,864 tokens (RTX 3090, 32k context, concurrency 6). Whether prompts "fit" is a property of this testbed, not a general one.
- The cache-pressure runs (`t08_pressure_c1`, `t08_pressure_c2`) exist, but the paper leaves them as a TODO comment in the source. So the mechanism "the prefixes they resend no longer stay cached" is assumed, not measured.
- At k = 16 the three parallel Researchers each see only their own documents (`rtask_block`, `split_task`). The Researcher-to-Writer prefix reuse that gives A1-zc its saving at k ≤ 5 is therefore impossible by construction. "Zero-copy saves nothing (1.00x)" mixes this structural effect with eviction.
- k = 16 has only 60 tasks.
- The abstract attributes B's 34-point loss to "large payloads". The body shows that much of it comes from write clashes and the tool budget (B's Writer hits the budget in 32% of runs, its Reviewer in 52%).
**Fix:** Report the pressure runs. Report per-call cache-hit rates (`cached_tokens / prompt_tokens`) by channel and k, so the eviction mechanism is measured. Run k = 16 with one Researcher, or k = 8 at concurrency 1. Reword the abstract to "at k = 16 with three parallel Researchers…".

### W6. The fan-out paragraph leaves out the reference channel that would isolate the race.
`\nFanAOneDiff` = −6 (−11 to −1): broadcast also loses 6 points under the same three-Researcher fan-out, where no write race can happen. B's −10 therefore includes a general fan-out cost. The race-specific part is roughly −4, and its CI is not reported. "The race comes from the parallel writers, not from the payload" is fair. Using B's −10 as evidence of the clash's effect on accuracy is not.
**Fix:** Report A1 (and A1-zc, A2) fan-out deltas, and a paired difference-in-differences (B fan-out effect minus A1 fan-out effect) with a CI.

### W7. Zero-copy's "same accuracy" is a non-significance claim, and the paper reports neither the exact-match result nor latency.
- `\nGapAZcSig` counts only cells where A1-zc is significantly *worse*, and it uses no equivalence margin.
- Recomputing paired bootstraps from `rows.jsonl.gz`, A1-zc's exact match on 2Wiki is significantly lower at k = 3 (−3.6, CI −6.7 to −0.4) and k = 5 (−3.2, CI −5.6 to −0.9). Lenient accuracy on 2Wiki at k = 3 is −2.7 (CI −5.8 to +0.4). The paper says only "up to 4 points lower".
- A1-zc also changes the Researcher's output (notes 50% vs 45%), so equivalence is not guaranteed by construction.
- A1-zc's wall time is 1.1x broadcast's (`\nWallAZc`, unused in the text). At k = 3 it averages 34.0 s vs 31.2 s and produces more completion tokens (965 vs 835). That weakens the implicit "cheaper" message for latency-sensitive users.
**Fix:** Run a TOST equivalence test with a stated margin (for example ±3 points). Report exact match for every channel. Report and discuss latency.

### W8. Statistics: many uncorrected tests, overlapping settings, and missing CIs in figures and sensitivity results.
- There are 5 channels × 6 cells in the main grid, plus the sensitivity runs, and no correction for multiple comparisons.
- The k = 1/3/5 tasks are drawn with the same seed through `random.sample(pool, n*k)`. The k = 1 questions are a prefix of the k = 3 and k = 5 draws, so "significant in 5 of 6 settings" is not six independent replications.
- Figure 3 shows *unpaired* CIs, which overlap visually even where the paired differences are clearly significant. Figure 4 has no intervals at all, although `fig4_scaling.json` contains them.
- "Change accuracy by at most 3 points on 100 paired tasks" (24-call budget) is a max of point estimates with no CI. At n = 100 the CI is about ±6.
- C vs B, the comparison behind "an index helps", is never tested directly. My recomputation supports it (C − B: +6.0, +2.0, +5.1, +14.7, +5.1, +5.7 points; CI excludes 0 in 4 of 6 cells). This should be in the paper.
**Fix:** Apply Holm correction, or fit a mixed-effects logistic model (question random effect; channel × dataset × k fixed effects). Plot paired CIs. Add CIs to Figure 4 and to every sensitivity delta. Report C − B.

### W9. "Tokens computed" is defined one way in the text and computed another way in the code, and decoding is left out.
The text says computed = tokens sent minus cached prompt tokens, which would include completion tokens. The code computes `prefill_tokens = Σ(prompt − cached)`, which excludes them. File channels generate about twice the completion tokens (k = 3: B 1,608, C 1,447, D 1,245 vs A1 835). Decode tokens are the expensive ones per token, so "files compute 0.79x" understates their cost. "Tokens sent" also treats input and output tokens as costing the same, which no API does.
**Fix:** Call the quantity "prefill tokens computed", report decode tokens separately, and add GPU-seconds or a price-weighted cost (input, cached input, output).

### W10. The file-channel results depend on the harness, and some failures specific to file channels go unreported.
Without rescues, B and C would score 18% and 23%. 28–34% of B/C runs hit the 12-call budget even at k = 3. In the main run, B's Researcher hits `max_tokens = 2048` in 7.3% of k = 3 runs and C's in 3.3%, against 0.3% for A1. A truncated tool call loses its JSON arguments. 5% of B runs and 3.3% of C runs end with empty notes. The "27% shorter" figure includes these empty notes. Excluding them it is about 24% (mean 1,185 vs 1,559 characters), so the claim survives, but the failure mode should be reported.
**Fix:** Report truncation and empty-note rates by channel. Raise `max_tokens` for tool-call turns, or show that results are stable when truncated runs are excluded. Report the note-length median alongside the mean.

### W11. Generality.
The study uses one model family (Qwen3, thinking off, one tool-call parser) and one task type in which the documents already fit in the Researcher's prompt. The case that motivates files (artifacts larger than the context) is absent, as the conclusion admits. The B and C Writers are told to read documents only "to check a doubtful fact". The A1 Writer, meanwhile, gets all documents for free, which makes A1 an unusually strong reference. Against the pipe, the fair comparison when the Writer has no documents, files do as well or better (C 66.3 vs A2 62.1; replay: B and C lose 5 points against the pipe's 8).
**Fix:** Run a 100-task subset on one non-Qwen model. Say explicitly that A1's advantage includes giving the Writer every document. Frame the file channels against A2 as well as against A1.

### W12. The accuracy metric is lenient, and format compliance may differ by channel.
`correct()` accepts the gold answer contained in a prediction of up to gold length + 4 words. File channels take answers from `final.md`, or from the reply when the file is missing (`final_from_reply`). Parse failures count as wrong.
**Fix:** Report exact match and F1 for every channel, and the per-channel rate of unparsed or missing answers.

## Questions

1. What is the share of *correctly* answered questions whose notes "miss" at least one supporting fact by AlignScore? (It tells how much "Researcher missed" in Figure 2b explains.)
2. Can you hand-label even 100 real (notes, fact) pairs? On those, which measure is closest to the truth, and does the B > C > D ordering of notes recall survive?
3. In A1w, does the Researcher see B's full instruction ("other agents cannot see your reply… choose the file names and how to split them")? Have you tried a message-channel instruction with tool-only output?
4. At k = 16, how much of A1-zc's lost saving comes from the parallel Researchers seeing only their own documents, and how much from eviction? What do the concurrency-1 and concurrency-2 pressure runs show?
5. What is B's fan-out effect minus A1's, with a CI?
6. Why is A1-zc slower in wall time than A1 (1.1x)? Is the difference in completion length (965 vs 835 tokens) significant?
7. How many B/C Researcher tool calls were truncated at 2048 tokens? Did the forced write recover those notes?
8. In the replay, C's Writer reads `index.md` in only 53% of tasks and opens the notes less often than B's (63% vs 76%), with lower delivery (75% vs 90%). Is the index making things worse when there is one obvious file?
9. Were the k = 8 and k = 16 runs interleaved on the same servers as their A1 references (needed for the compute ratios), and were any runs lost to context overflow?

## Sentences that overclaim or do not match the code or numbers

- **"Our key observation is that *cost has to be counted three ways*"** (Introduction). The paragraph names two (sent, computed), and so does the abstract ("both as tokens sent… and as tokens the engine computes"). Either name the third (latency?) or say "two ways".
- **"its instructions differ only in where its notes go (a reply, or files written with a `write_file` tool)"** (§2). The code also differs: C adds a heading rule and an index notice, D adds a handoff, A1-zc moves the instruction after the documents, and B's text adds "others cannot see your reply… choose the file names and how to split them" (W3).
- **"*tokens computed* subtracts the prompt tokens the engine served from its cache"** (Metrics). Read against "tokens sent", this includes completion tokens. The code (`prefill_tokens`) excludes them (W9).
- **"Qwen3-8B used as a judge accepts nearly everything (100, 78, 41%)"**. The judge correctly rejects 78% of dropped facts; its failure is on entity swaps (accepts 59%). Say "accepts most entity-swapped facts".
- **"[exact entity match] ranks the channels the same way"**. Only the split between message and file channels holds. Notes: AlignScore B 32 > C 30 > D 25; entities C 85 > D 83 > B 82. Delivery: AlignScore D 51 vs entities D 94. The real-pair agreement (kappa 0.22–0.54) is not reported.
- **"no difference significant, though under exact match it is up to \nZcEmGapMax points lower on 2Wiki"**. Under exact match the 2Wiki gap is significant at k = 3 and k = 5 (W7). The significance count is one-sided and is not an equivalence test.
- **"With handles the Writer trusts the handoff and opens even less (\nDelivDMin–\nDelivDMax% delivered)"**. Entity-match delivery for D is 94% (`\nEntDDeliv`). The 46–54% reflects AlignScore on a 120-word handoff, not facts withheld from the Writer.
- **"The tool call, not the file, shortens the notes."** A1w changes the tool *and* the instruction text (W3).
- **"More than half of B's loss therefore comes from asking the model to write its result as a tool-call argument; the rest comes from reading."** The point estimate is 60%, with a numerator CI of 2–8 points. Writing plus reading (5 + 5) is more than B's total loss (7.8) (W4).
- **"B by \nSmallBGapMin–\nSmallBGapMax points and C by \nSmallCGapMinThreeFive–\nSmallCGapMaxThreeFive at three and five questions"**. B's macros (21–31) span all k. The k = 3,5 values are 22–29 (`\nSmallBGapMinThreeFive`, `\nSmallBGapMaxThreeFive`). Likewise "Handles lose \nSmallDGapMin–\nSmallDGapMax" (5–15) spans all k, while the k = 3,5 range is 5–12, inside a sentence whose scope is "three and five questions".
- **Abstract: "at large payloads plain files lose \nGapBKSixteen points while an index loses \nGapCKSixteen"**. This is k = 16 with three parallel Researchers (60 tasks), where write clashes and the budget (Writer 32%, Reviewer 52% budget hits) drive part of the loss. "Large payloads" alone is not the cause (W5, W6).
- **Abstract: "Once prompts outgrow the KV cache, zero-copy saves nothing"**. At k = 16 the parallel Researchers make Researcher-to-Writer reuse impossible regardless of cache size (W5). At k = 8 it still saves 17%.
- **"Part of the collapse happens before anyone reads… B answers \nFanBDiff points… relative to one Researcher"**. Broadcast loses \nFanAOneDiff (−6) under the same fan-out with no race. Omitting it overstates the race's effect on accuracy (W6).
- **"The tool budget does not drive the results… change accuracy by at most \nTwFourAccMax points on \nTwFourN paired tasks"**. This is a maximum of point estimates with no CI, at n = 100.
- **Conclusion: "When it does not fit, the pipe is the cheap choice and loses little, and a checking stage helps it more than any other channel."** The 4-agent chain was run only at k = 3, where the history fits. The checking-stage evidence does not cover the "does not fit" regime.
- **"so the gain is for self-hosted serving or APIs that discount cached input"** (zero-copy). Wall time is 1.1x broadcast's (`\nWallAZc`, unreported). The gain is in prefill compute, not latency.
- **Figure 2 caption: "share that reached the Writer"**. For A1 and A1-zc the Writer received every document, so every supporting fact reached it. The bar shows only the notes (W2).
- **"C's accuracy comes within \nGapCMax points of broadcast"**. C is significantly below broadcast in 2 of 6 cells (2Wiki k = 3: −8.4, CI −12.4 to −4.4). "Within 8 points" reads as "close". Report C − B directly, which does support the index claim.
- **Source hygiene:** `% TODO(numbers pending): cache pressure (1/2/6 concurrent runs), fan-out at k=3.` remains in `main.tex`. Fan-out at k = 3 is now reported; the cache-pressure part is still missing.
