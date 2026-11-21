# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (round 12, systems reviewer)

## Summary

The paper compares five inter-agent channels in a fixed Researcher -> Writer -> Reviewer pipeline of Qwen3 models on vLLM v0.33.0, using bundles of k multi-hop QA questions (HotpotQA, 2Wiki). The channels are full-conversation broadcast (A1), a prefix-ordered "zero-copy" broadcast (A1-zc), a pipe (A2), shared files reached through tool calls (B), and files plus an auto-maintained index and a heading rule (C). The main run uses Qwen3-8B on RTX 3090s. Separate RTX PRO 6000 runs cross note writing (reply or tool call) with note delivery (copied or file) at four model sizes, time each channel served alone, vary the KV-cache size, and split the k=8/k=16 fan-out effect.

Headline claims:
1. At k=3, files send 2.9x broadcast's tokens but compute 0.79x its prefill. Zero-copy cuts broadcast's prefill by 61% with an accuracy difference of -0.8 (CI -2.9 to 1.4).
2. Delivering the Researcher's reply through files costs 20-34 points at three of four sizes after Holm correction. That is more than the cost of writing notes through a tool call.
3. Three parallel Researchers sharing one folder cost B 21.2 points at k=8, and separate folders recover 19.8.

The paper is careful, hedges a lot, and has more controls than most workshop papers. My main concern is about what the controls show: most of the accuracy story is about how Qwen3 behaves under this tool harness (it fails to write, fails to open the notes, or clobbers files), not about files as a channel. The cost story is told in a metric (prefill) that the paper's own timing shows is not the dominant cost.

## Score

**3 / 5 (weak accept / borderline).** It is a solid, honest measurement paper with useful negative results. The headline framing claims more generality than the evidence supports, and the most practical cost result (serving time) cuts against the paper's emphasis.

**Confidence: 4 / 5.** I read the source, every number macro the text uses, the four figures, and parts of the harness (`pipeline.py`, `paper_numbers.py`) to check definitions.

## Strengths

- **Clean core manipulation.** The task, roles, order, model, and decoding are fixed, and comparisons are paired on identical tasks. Per-task `cache_salt` prevents cross-task or cross-channel reuse.
- **Unusually rich controls:**
  - wording control for B's Researcher instructions;
  - replayed broadcast notes in every channel;
  - documents added to the pipe and to B;
  - A/A reruns;
  - an in-run drift check on the PRO 6000;
  - KV-cache size sweep;
  - a tool-budget check.
- **The 2x2 crossed design (write mode x delivery mode) is the right idea.** It avoids order-dependent stepwise attribution and is run at four model sizes with Holm-corrected permutation tests.
- **Honest reporting of awkward facts:**
  - rescue rates and the strict-scoring bound;
  - "accuracy of these arms rests on the rescue";
  - the separate-folder confound (paths change);
  - zero-copy's longer outputs;
  - zero-copy not finishing a batch sooner.
- **Every number is generated from results by a script** (`numbers.tex`), and I found no transcription errors between macros and prose.
- **Figures 1, 2, and 4 are clean and readable.** Figure 2b's annotation of the zero-copy arrow with the paired CI is effective.

## Weaknesses (most important first)

### W1. The file-channel accuracy losses mostly measure harness and agent-behavior failures, and the headline number comes from the most degenerate arm. [needs new runs; partly analysis of existing logs]

The evidence that "files" lose accuracy is dominated by failures that are properties of this harness and prompt with Qwen3 tool calling:

- **Rescue.** In the main run, the forced write ("rescue") fires in 34-59% of tasks for B's Writer and for B's and C's Reviewers. Scoring rescued tasks as wrong drops B from 62.8% to 18.0% and C from 66.3% to 22.9%. In the crossed runs, the rescue fires in 100% of file tasks at 4B and in 100% of stored-reply tasks at 14B (Table 1, last row).
- **Unopened notes.** The Writer opens the stored `notes.md` in only 5% (4B), 9% (14B), and 24% (32B) of tasks. In B it never opens the notes in 42% of main-run tasks.
- **Clobbering.** At k=8 fan-out, 99% of B tasks have two Researchers writing the same path, and in 58% only one Researcher's notes survive.

The abstract's 20-34-point range comes from the "Copy -> files, reply" row. That arm stores a system-named `notes.md` that the Writer rarely opens, and at 4B and 14B every task in it was rescued. So it mainly measures whether a given Qwen3 size goes looking for one particular file. It is not a general cost of delivering notes through files. The paper says so itself ("rests on the rescue"; "an observation, not a tested cause"), yet it puts this number in the abstract, the introduction, and the conclusion. The arm closest to real file-based systems (tool-written files, row 2) costs 8-22 points.

The introduction motivates file channels with systems that "store subagent results and pass references." No evaluated channel passes a reference. `numbers.tex` contains results for a handoff variant (D; e.g., gaps of 6.7/8.8/9.0/32.0 points by size) and a read-then-reply variant (Br) that are not reported.

**Fix:**
- *Analysis:* classify every file-channel task by failure mode: no tool call at all, notes never opened, notes opened but answer wrong, output lost or misnamed. Report the breakdown per channel and size.
- *Analysis:* lead with the tool-written-files effect (8-22) and present the stored-reply arm as a findability probe.
- *New runs:* add one realistic reference-passing channel, where the Writer is told the notes' path(s) in its message. Report D if that is what it is.
- *New runs:* repeat at least the k=3 main comparison with a second model family that has mature tool calling. Without that, the recommendation "agents should copy results forward" is a statement about Qwen3 tool use.

### W2. Prefill is the wrong headline cost; by the paper's own serving-time data, files are the most expensive channel and the pipe beats zero-copy. [text/analysis only for k=3; needs new runs for other k]

The first observation is that "channels rank differently by prefill than by tokens sent," and Figure 2b labels prefill "Tokens computed per task (self-hosted)." But the timing section reports:

- decoding is 96% of broadcast's prefill-plus-decode time;
- B and C take 1.80x and 1.56x broadcast's wall time (not 0.79x);
- zero-copy takes 1.09x (it generates 1.2x more output tokens);
- the pipe takes 0.78x.

For a self-hosted deployment, then, serving time ranks the channels much as tokens sent does, and the "rank reversal" between prefill and tokens sent is not the cost that matters there. For API deployments, cached input is discounted, not free, so neither "tokens sent" nor "prefill" is a bill.

The pipe also matters here. It computes about zero-copy's prefill (4.7k vs 4.8k), sends 0.42x the tokens, runs in 0.78x the time, and ties broadcast's accuracy at 4B, 14B, and 32B (gaps 1.5, 0.0, 1.2; CIs include 0). It loses only with 8B. So at three of four sizes, the pipe matches or beats zero-copy on every measured cost at equal accuracy. Yet zero-copy gets the abstract, the figure annotation, and the conclusion.

There are also two smaller problems:
- The "96% decode" share comes from vLLM's per-request phase timers summed over concurrently batched requests. That is per-request wall time including batching interference, not GPU-time share. Say so, or measure GPU busy time.
- Timing ratios are given without spread. The macros have min/max across the three runs (e.g., B 1.68-1.96); report them.

**Fix:**
- Add serving time (or GPU-seconds per task) as a third cost axis in Figure 2, next to tokens sent and prefill.
- Add an API-bill estimate under a stated cached-input discount (e.g., 10% or 50% of the input price).
- Reframe observation 1 around what each deployment pays.
- Give the pipe's cost/accuracy position at 14B/32B the prominence it earns.

### W3. The crossed-run decomposition is interpreted through untested comparisons, while the significant interaction goes untested. [text/analysis only]

Table 1's claim "delivery through files costs more accuracy than the tool-call write" compares the magnitudes of different simple effects without testing their difference. Meanwhile, the interaction row (row 4 minus row 3) has CIs that exclude zero at 4B, 14B, and 32B (12.2, 21.1, 12.2), yet the table marks it "not tested." With interactions this large, "the cost of delivery" and "the cost of the write" are not single quantities. At 14B, the tool-call write *raises* accuracy by 21.3 points when notes go through files and changes it by 0.2 when they are copied. The honest summary is that the cost of files depends on whether the Researcher or the system names and writes the file. That is a finding about findability, which the paper half-says in its 14B/32B paragraph.

**Fix:**
- Include the interaction, and if you keep the claim, the difference between the delivery and write effects, in the permutation/Holm family.
- Rewrite the Table 1 caption and the second observation around the interaction.
- Report row 2 (tool-written files) as the delivery effect most relevant to deployed systems.

### W4. The main-run narrative is Qwen3-8B-specific, and 8B is an outlier on several axes. [text only]

All of Figure 2, Figure 4, the timing, the mechanism paragraphs, and the fan-out experiments use 8B. But numbers.tex shows that 8B behaves unusually:

- The pipe loses accuracy only at 8B (10.2 points; 4B/14B/32B: 1.5, 0.0, 1.2).
- The delivery effects in Table 1 are smallest at 8B, and at 8B the Writer opens `notes.md` more often than tool-written notes, the reverse of 14B/32B.
- The index (C) does not help at every size. At 14B, C trails broadcast by 16.0 points and B by only 7.5 (`nPSizeFourteenGapC` vs `nPSizeFourteenGapB`). The paragraph title "B trails broadcast in every setting, and C trails it by less or not at all" holds only for the 8B main run, and the "Model size changes which channels lose" paragraph does not mention the reversal.

**Fix:**
- Add a compact per-size table (A1 accuracy, and gap per channel with CI, for A1-zc, A2, B, C).
- Qualify every 8B-only statement in its sentence, including the C-vs-B claim and the pipe claim.
- Say explicitly that the channel ranking among the non-file channels changes with size.

### W5. Shared-cache interleaving and cross-run, cross-GPU, cross-configuration comparisons weaken several quantitative claims. [text/analysis; some new runs]

**Shared cache in the main run.** Six concurrent tasks, interleaved across five channels, share one 34,864-token cache. Each channel's prefill therefore depends on what the other channels are doing; B and C's long tool loops compete with zero-copy's shared prefix. Figure 4a's "savings fade as payloads grow" is partly an artifact of this mix. At k=8 with 100k or 400k caches, zero-copy computes 0.36x again. The text says "the KV of six concurrent tasks no longer fits," which is the mix, not the channel.

**Fix:** state that per-channel prefill in Figure 4a depends on co-scheduled channels. Report each channel's prefill served alone at k=8 (or use the existing 100k run as the reference), and say which dataset and GPU the "100 such tasks" use.

**Configuration differences across runs.** Comparisons span:
- RTX 3090 vs RTX PRO 6000;
- 2,048- vs 4,096-token generation caps;
- 35k, 100k, and 400k caches;
- separately launched runs. The 32B file-channel rerun is compared against the first run's broadcast. The tool-budget effect is compared against "an earlier RTX PRO 6000 run." The scope runs are compared against the main run.

Drift is measured only within the 3090 main run and within the PRO 6000 crossed runs, not across GPUs or caps. The setup of the size study (GPU, cache, cap) is never stated; Qwen3-32B in bf16 cannot run on a 24 GB 3090, so the study is at least partly on the PRO 6000.

**Fix:** add a one-table run inventory (run, model, GPU, KV tokens, gen cap, tasks, channels, used in which claim). Where a claim is cross-run, prefer an in-run comparison, or rerun the reference arm in the same run.

### W6. The fact-coverage measure is too weakly validated to carry Figure 3a and the mechanism claims. [text/analysis; small annotation effort]

AlignScore agrees with a Qwen3-8B judge at Cohen's kappa = 0.29. The judge is also from the model family under test and is itself unvalidated. The synthetic AUC of 0.996 checks deletions and alterations of verbatim sentences, not the paraphrased, compressed notes being scored. Several claims nonetheless rest on this measure:
- "B's notes state 32% of the supporting facts, against broadcast's 45%";
- "Where the effect appears, the notes state fewer supporting facts ... 32% against 43%";
- the whole of Figure 3a.

**Fix:** have humans label a stratified sample (about 100 notes x facts across channels and sizes), report agreement of AlignScore and of the judge against it, and either recalibrate the threshold or present fact coverage qualitatively. Alternatively, replace it with a cheaper, more checkable proxy: does the notes text contain the gold answer string or the bridge entity?

### W7. The scope is narrower than the title and recommendations. [text only, or new runs for a second workload]

The workload favors messages by construction:
- All state fits in context.
- The Researcher receives every document in its prompt.
- In B and C, the Writer receives only the questions and must rediscover what the Researcher already summarized.

None of the reasons people use files is exercised: state larger than the context, selective reading of large corpora, persistence across sessions, or many consumers. The conclusion admits this in one sentence. The title ("Messages or Files?") and the abstract's recommendation ("agents should copy results forward as replies") do not.

**Fix:** narrow the title or subtitle and the recommendation to "when shared state fits in context," or add one workload where it does not (e.g., a long-document or repository task in which broadcast must truncate).

### W8. The novelty claims need sharpening. [text only]

- **Prefix ordering is standard practice.** Putting the shared, static content first so the prefix cache reuses it is what serving systems (SGLang/RadixAttention, Parrot, KVFlow, Preble-style prefix-aware scheduling) and every provider's prompt-caching guide already recommend. The paper concedes this ("just puts shared content first, so we contribute the measurement").
- **The fan-out fixes are textbook.** Per-writer namespaces and an O_EXCL-style write guard are textbook fixes for a write-write naming conflict. The 21.2-point "fan-out loss" is the consequence of losing two-thirds of the notes to overwrites, and the paper reports 99% same-path collisions.
- **The IPC framing is not used analytically.** The Lauer-Needham duality is cited but never tested; nothing in the evaluation asks whether the two designs are duals here.

**Fix:**
- State the measurement contributions crisply, e.g., "the accuracy cost of files is a findability cost: X points when the reader must discover the notes, Y when it is told where they are," which requires W1's reference channel.
- Present the fan-out result as a data-loss result, quantifying accuracy as a function of the share of notes lost.
- Either use the IPC lens to predict something that is then checked, or cut it to a sentence.
- Related work should cover prompt-ordering and prefix-aware scheduling work beyond Parrot/KVFlow, and agent harnesses that pass file references.

### W9. The evaluation does not yet read as one argument. Too many runs are introduced piecemeal, and the third headline has no figure. [text only]

I count at least 13 distinct experiment families:
- main;
- three 3090 controls;
- scope-pipe;
- wording;
- crossed;
- serving-alone x3;
- high-load x2;
- KV sweep;
- size study;
- 32B rerun;
- k=8 fan-out;
- k=16 guard/heading;
- tool budget.

Many are introduced in the sentence that first uses them ("in a separate run on 200 tasks", "an earlier RTX PRO 6000 run", "on 100 such tasks"). §4 jumps from the 8B main run (cost, accuracy) to the four-size crossed runs (Table 1, Figure 3) and back to 8B mechanism paragraphs ("Without an index, B's Writer mostly reads documents"). The k=8 fan-out experiment behind the third observation has no figure; Figure 4b shows only the confounded k=16 point.

Figure 3 asks the reader to subtract bar heights to get the effects the text discusses. Its "Reply, copied" (light navy) and "Reply, stored as file" (light teal) fills are hard to tell apart in print.

**Fix:**
- Add the run inventory (W5).
- Order §4 as cost (8B), then accuracy (8B), then why files lose (unopened notes, write failures, rescue), then the same comparisons across sizes.
- Replace Figure 3b with a dot plot of the Table 1 paired effects, or fold Table 1 into it so the claim is visible at a glance.
- Add a small panel for the k=8 one-folder / three-folder / one-Researcher comparison.

### W10. The statistical reporting is inconsistent across claims. [text/analysis only]

- Counts like "significantly in five of six settings" and "C is significantly above B in four of six" are uncorrected, over settings whose question sets overlap.
- Each task runs once per channel, although identical prompts yield identical notes in only 59% of tasks. Decoding noise is therefore large per task even though it averages out in aggregates.
- The zero-copy claim reads like non-inferiority without a stated margin: a 2.9-point loss is not excluded.
- Timing and median-latency ratios (0.82x, 1.00x) come from two runs with no spread.

**Fix:**
- Holm-correct or drop the "k of six" counts.
- State the equivalence margin you consider negligible and whether the zero-copy CI clears it.
- Give min-max across runs for every timing ratio.

## Questions for the authors

1. What does the 14B Writer actually do in stored-reply tasks (100% rescued, `notes.md` opened in 9%)? Does it issue any tool call before replying? Could vLLM's function-call parser be dropping tool calls for this arm or size? A per-turn trace summary would settle whether this is model behavior or parser behavior.
2. Where does `notes.md` sit relative to `docs/` and to tool-written notes, and what names did Researchers choose for tool-written notes? The text says the stored reply changes "name, number, and location." Which of these could you equalize cheaply (e.g., by storing the reply under the name a tool-writing Researcher used)?
3. `numbers.tex` includes a handoff channel (D) and a read-then-reply variant (Br; at 32B, its Writer opens the notes in 0% of tasks and scores 31.1 points below B). Why are they omitted? D seems to be exactly the reference-passing design the introduction cites.
4. In the k=8 fan-out, which paths collided? Was it a default like `notes.md`? What is the collision rate in C, whose k=16 loss is only 5.1 points?
5. What GPU, KV cache, and generation cap did the four-size study use? Which runs, if any, mix GPUs within one comparison?
6. The k=16 B gap is 33.9 both in the main 3090 run (Figure 4) and in "an earlier RTX PRO 6000 run" (`nRFourKSixteenGapB`), with different CIs. Is the identical point estimate a coincidence? Please confirm the tool-budget comparison uses the right reference.
7. With per-task `cache_salt`, role instructions and tool schemas are never reused across tasks, as they would be in production. How much would cross-task reuse change the prefill ranking, especially for B and C, whose system prompt plus tool schemas is a fixed prefix?
8. Why is zero-copy's decode time per generated token lower (14.9 vs 16.9 ms; 30.2 vs 43.0 ms at 32 concurrent tasks)? Is this a batching artifact of the per-request counters?
9. How sensitive are the accuracy gaps to the lenient matcher ("gold inside a prediction at most four words longer")? Do the file-channel gaps hold under exact match, as you show for zero-copy and the 8B write effect?

## Sentences that overclaim, are unclear, or mismatch their numbers

1. Abstract: "With Qwen3-8B, copying the whole conversation (broadcast) is the most accurate channel."
   - Broadcast is statistically tied with zero-copy (-0.8, CI -2.9 to 1.4).
   - Zero-copy's point estimate is higher at k=16 (+0.6) and at 14B (+1.0).
   - Write "broadcast and zero-copy are the most accurate channels."
2. Abstract: "delivering the Researcher's reply through files instead of copying it costs 20-34 accuracy points at three sizes after Holm correction."
   - This arm was rescued in 100% of tasks at 4B and 14B, and its file was opened in 5-24% of tasks at 4B/14B/32B (see W1).
   - It is a findability probe, not "files."
3. Abstract: "three parallel Researchers sharing one folder cost files without an index 21.2 points against one Researcher."
   - Ungrammatical ("cost files ... points").
   - It also hides that 99% of these tasks had same-path overwrites.
4. Abstract and Conclusion: "agents should copy results forward as replies."
   - It is ambiguous whether this means broadcast or the pipe. The pipe loses 10.2 points at 8B and ties at the other sizes.
   - It is not scoped to "state that fits in context."
5. Intro: "Most systems copy." Unsupported; cite or soften.
6. Intro: "Our first observation is that the channels rank differently by prefill than by tokens sent." True, but by serving time (1.80x / 1.56x for B/C, 1.09x for zero-copy) the files-cheaper-than-broadcast ranking disappears. See W2.
7. §4: "Zero-copy thus pays off where prefill is billed and in per-task latency under load."
   - APIs do not bill prefill; they discount cached input.
   - "Under load" rests on two runs (0.82x median), with no spread reported.
8. §4: "By vLLM's per-request counters in two runs, decoding takes 96% of broadcast's summed prefill and decode time." These are per-request wall-time phases under batching, not GPU-time shares. Say so.
9. §4 heading: "B trails broadcast in every setting, and C trails it by less or not at all." This holds for the 8B main run only. At 14B, C trails by 16.0 against B's 7.5.
10. §4 heading: "With Qwen3-8B, the pipe's Reviewer loses accuracy."
    - The pipe loses accuracy (through its Reviewer).
    - The heading should say this is 8B-specific (4B/14B/32B gaps are 1.5/0.0/1.2).
11. §4: "B's file list does not say which file holds the notes, so 83% of the reads by B's Writer go to source documents, and in 42% of tasks the Writer never opens them."
    - "so" asserts an untested cause.
    - "them" is ambiguous: the notes or the documents?
12. §4: "At 4B, the harness forced the Writer's or Reviewer's write in every file task, and at 14B in every stored-reply task, so the accuracy of these arms rests on the rescue." If so, the bold daggered 4B and 14B entries in Table 1 rows 1-2, and the "34" at the top of the abstract range, should not be presented as channel effects.
13. Table 1 caption: "Except at 8B, delivery through files costs more accuracy than the tool-call write." This difference of effects is not tested, while the interaction, which is large and has CIs excluding 0 at three sizes, is labeled "not tested."
14. §5 heading: "Prefill savings need the shared history to fit in the cache." The 35k cache is shared by six interleaved tasks across five channels, so this is also a statement about the co-scheduled mix.
15. §5: "On 100 such tasks, zero-copy computes 0.36x and 0.36x ..." It is unclear which tasks ("such"), dataset, and GPU. Write "the same ratio, 0.36x, with both 100k and 400k caches."
16. §5 heading: "When work fans out, parallel writers sharing one folder cause most of B's loss."
    - The evidence comes from a constructed k=8 fan-out.
    - The separate-folder arm was not run at k=16.
    - The mechanism is overwrite data loss (58% of tasks keep one Researcher's notes).
17. §5 heading: "Run-to-run noise is small next to the file channels' gaps." True for aggregate accuracy within a GPU. It does not cover cross-GPU or cross-cap comparisons, and per-task outputs differ in 41% of identical-prompt cases.
18. §5: "For Qwen3-32B, these ranges use a rerun that fixes a harness path bug ... against the first run's broadcast (cross-run)." The size ranges in the same sentence mix in-run and cross-run gaps without marking which is which.
19. Related work: "Zero-copy broadcast just puts shared content first, so we contribute the measurement." Awkward, and it undersells: say what the measurement shows that was not known.
20. Related work: "We study IPC between agents." Filler; cut it, or state the distinction from MemGPT/AIOS precisely.
21. Methods: "Scoring every rescued task as wrong cuts B's accuracy from 62.8% to 18.0%." This alarming bound is given without saying what the rescue does: the agent replied in plain text, and the harness asked it to save. Without that, readers will conclude that the file channel barely functions.

## What stands between this paper and acceptance

1. Re-anchor the accuracy headline on the tool-written-file effect, and add a failure-mode breakdown (W1, W3). Ideally also add a reference-passing channel and one non-Qwen model.
2. Add serving time and an API-bill model as cost axes, and give the pipe's cost/accuracy position at 14B/32B its due (W2).
3. Add a per-size table, and qualify the 8B-only claims, including C vs B at 14B (W4).
4. Add a run inventory, and remove or mark cross-GPU and cross-configuration comparisons (W5, W9).
5. Scope the title and recommendations to "state that fits in context" (W7).

With 1-4 done as text and analysis plus a modest number of new runs, I would move to a 4.
