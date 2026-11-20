# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6 pages)

## Summary

The paper compares ways for agents in a fixed Researcher -> Writer -> Reviewer pipeline to pass results.
The channels are: copying the whole history (A1, broadcast), the same history reordered so consecutive
agents share a cached prefix (A1-zc, "zero-copy broadcast"), passing only the previous output (A2, pipe),
a shared workspace accessed through tool calls (B), and the workspace plus an auto-maintained index and a
heading rule (C). It uses Qwen3 4B-32B on vLLM v0.33.0 with prefix caching, on HotpotQA and 2Wiki tasks
that bundle k questions. It reports accuracy, tokens sent, tokens computed (uncached prefill), and serving
wall time.

Main claims:
1. Prefill disagrees with both billed tokens and serving time. At k=3, files send 2.9x broadcast's
   tokens but compute 0.79x its prefill. Zero-copy computes 61% less prefill at no detectable accuracy
   cost (-0.8, CI -2.9 to 1.4), yet takes 1.09x broadcast's wall time because its agents generate 1.2x
   the tokens.
2. Files lose accuracy at two steps: the tool-call write of the notes (significant at 4B and 8B after
   Holm) and everything after it (significant at 4B, 14B and 32B).
3. Parallel writers in one folder cause most of B's fan-out loss. At k=8, three Researchers cost B 21.2
   points, and a folder per Researcher recovers 19.8 of them. At k=16, a write guard recovers about half.

The paper is unusually careful about controls (wording vs. tool, replaying the same notes, giving files
the documents, an A/A rerun, a Holm-corrected split) and candid about scope. My concerns are that the
systems contribution is thin and partly rests on a cache-hostile baseline. The serving-time analysis is
inconclusive and confounded by output length. The k>=8 cost results come from channels sharing a very
small KV cache. The two accuracy decompositions disagree at 8B. And the prose is so dense with numbers
from a dozen differently configured runs that the reader cannot easily tell which number comes from which
setup.

## Score and confidence

- **Score: 3 / 5** (borderline / weak accept). This is a careful measurement study with honest caveats
  and some useful practitioner guidance, but it has a thin systems insight and several confounded cost
  claims.
- **Confidence: 4 / 5.**

## Strengths

1. **A clean, relevant question.** Copying vs. tool-mediated files is a real design choice in current
   agent frameworks, and as the paper says, the agent-communication literature mostly holds the channel
   fixed. Figure 1 shows the five channels clearly.
2. **Unusually thorough controls for a workshop paper.** The paper separates wording from the tool
   (Fig. 3), replays identical notes into every channel, gives files the documents, compares one vs.
   three Researchers with a difference-in-differences, adds a per-writer-folder arm, and reruns A1 and B
   to measure run-to-run noise. Most obvious alternative explanations have at least one test.
3. **Paired design and honest statistics.** The study uses paired bootstrap intervals, applies Holm
   correction where the decomposition claims are made, names cross-run comparisons explicitly, reports a
   strict-accuracy bound for the rescue (B 18.0%, C 22.9%), and states that broadcast-vs-zero-copy
   non-inferiority holds only to within 2.9 points.
4. **Reports negative and inconvenient results.** Zero-copy does not save wall time. The index does not
   help when notes are replayed. The pipe loses only with 8B. Zero-copy costs the 4B model 7 points.
   The paper does not hide any of these.
5. **Reproducible numbers.** Every number is a macro generated from results by a script, and I found no
   case where a number in the text disagrees with `numbers.tex` (details below).
6. **Actionable fan-out finding.** The finding that 99% of three-Researcher B tasks have a path clash and
   58% end with only one Researcher's notes is a concrete, easily fixed failure mode that practitioners
   will recognize.

## Weaknesses (most important first)

### W1. The cost story rests on a cache-hostile broadcast and on prefill counts that do not reach wall time. *(needs new runs + text)*

- **The 0.79x comparison uses a weak baseline.** The headline "first observation" contrasts files'
  2.9x tokens with 0.79x computed prefill against A1. A1 is cached only 1% (Fig. 2b) because each role's
  system prompt comes first. Against the cache-friendly A1-zc, which the paper itself recommends, B and C
  compute 9.8k / 4.8k = 2.0x the prefill. "Files compute less than copying" is therefore true only for a
  cache-hostile way of copying. The paper should lead with the A1-zc comparison, or at least state it.
- **Serving time is confounded by output length.** A1-zc changes the prompt order, which changes what
  the agents write (notes grow from 1,570 to 1,992 characters, and agents generate 1.2x the tokens). The
  1.09x wall time thus mixes the cache effect with a behavioural effect.
- **The "decodes faster" claim rests on unreliable counters.** It comes from per-request counters summed
  over overlapping requests. The paper itself says these sums "do not split wall time" and, at 32
  concurrent tasks, "do not explain its wall time". Yet the claim appears in the abstract.
- **Fix: trace replay with fixed outputs.** Record each channel's per-call prompts and outputs, then
  replay them against the engine with the output lengths forced (e.g., `min_tokens = max_tokens =`
  recorded length, or a fixed continuation). The cache's effect on time is then isolated from what the
  agents choose to write.
- **Fix: better time metrics.** Report per-task pipeline latency (p50/p95) and GPU busy time rather than
  run makespan. Six-wide batches over 100 tasks are likely dominated by stragglers.
- **Fix: do the arithmetic the counters allow.** At six tasks, 1.2 x 14.9/16.9 = 1.06, which nearly
  accounts for the 1.09x. At 32 tasks, 1.25 x 30.2/43.0 = 0.88 matches the summed request time (0.87),
  so the remaining gap to 1.00x wall time is a makespan or straggler effect. `numbers.tex` also contains
  a 96% decode share for A1 (`\nRSixDecodeShareAOne`) that the text never uses. If decode dominates, say
  so: it is the single most important fact for interpreting every prefill number in the paper.

### W2. The k>=8 cost results (Fig. 4a, "savings fade") depend on a tiny, shared KV cache and may miss recomputation. *(needs new runs)*

- **The cache is barely larger than one request.** The main servers have a 34,864-token KV cache and a
  32,768-token context, so the cache barely holds one maximal request.
- **Channels evict each other.** Six tasks run at once, interleaved across channels, so channels evict
  each other. The paper concedes that "the ratios also depend on their neighbors".
- **The fade is a capacity effect, not a property of k.** The 100k-cache sensitivity check (0.36x vs.
  0.85x at k=8) shows that the fade depends on capacity. Figure 4a, however, presents it as a function
  of k.
- **Preemption may be missing from the cost metric.** "Tokens computed" seems to come from API usage
  (prompt minus cached tokens). If so, it does not count prefill redone after preemption, which is likely
  at k>=8 on this cache.
- **Fix, runs:** run each channel alone and sweep cache capacity and concurrency. Plot computed prefill
  against the ratio of working set to KV capacity. That plot is the systems result the paper is reaching
  for.
- **Fix, metric:** read prefill and preemption counts from the engine's metrics (e.g., the Prometheus
  prompt-token and preemption counters) and confirm that "tokens computed" includes recomputation.

### W3. The two accuracy decompositions disagree at 8B, and the sequential attribution is order-dependent. *(needs new runs; text at minimum)*

- **The two estimates conflict.** Figure 3 attributes only -1.6 points (CI -5.3 to 2.2, n.s.) to "the
  rest of the file channel" at 8B. The replay control, which stores broadcast's notes as `notes.md`, finds
  the same rest of the channel costs 5 points (2 to 8) at 8B, and the conclusion leans on it ("Even
  broadcast's notes stored as one file lost 5 points").
- **Likely cause: an interaction.** The decomposition charges "rest of channel" against a tool-write arm
  whose notes have already lost facts (31% vs. 45% at 8B). Losing access to poor notes costs less than
  losing access to good ones. A sequential (wording -> write -> rest) attribution assumes additivity.
  Change the order and the per-step numbers change.
- **Fix:** run the full 2x2 design, writer (reply vs. tool write) x delivery (copied vs. files), in one
  interleaved run per size, and report the main effects and the interaction. The replay arm is already
  most of the missing cell, but it is cross-run.
- **Minimum text fix:** state that the attribution is order-dependent and reconcile the 8B numbers
  explicitly.

### W4. The fact-level mechanism rests on a weakly validated measure. *(needs new annotation; no GPU runs)*

- **The claims that depend on it.** "Writing through a tool call drops supporting facts" (Fig. 3a), the
  27%-shorter / 32%-vs-45% notes comparison, and the delivery numbers all depend on AlignScore at 0.5.
- **The validation is weak.** On the paper's own evidence, AlignScore separates synthetic perturbations
  well (AUC 0.996), but these are easy cases. On real notes it agrees with a Qwen3-8B judge at only
  kappa = 0.29. That judge shares a model with the systems under test, and is itself not a gold standard.
- **"Delivery" does not measure delivery.** It counts any file the Writer read, and 83% of reads are
  source documents. So "delivery 87-94%" while the Writer never opens the notes in 42% of tasks measures
  exposure to the facts, not receipt of the notes. The paper says so, but then still reports delivery
  numbers as if they were informative.
- **Fix:** have humans label supporting-fact presence on ~150 notes (stratified by arm and size) and
  report AlignScore's precision and recall against those labels.
- **Fix:** drop "delivery" in favour of the directly observed "Writer opened the notes" rate, which the
  paper already has.
- **Fix:** confirm that tool-call arguments are JSON-unescaped before scoring, and state how notes from
  writes that hit the 4,096-token cap are scored.

### W5. The fan-out conclusions mix payload with parallel writers, and the guidance outruns its evidence. *(needs new runs + text)*

- **k=16 changes two things at once.** It changes both payload and the number of Researchers.
- **Figure 4 attributes the collapse to k.** Its subcaption says "plain files collapse at large k", but
  the paper's own k=8 experiment attributes the loss to a shared folder.
- **The recommended fixes have unequal evidence.**
  - Per-writer folders, the strongest fix, were tested only at k=8.
  - The write guard and the heading rule were tested only at k=16, where they leave 15.3 and 12.6 points
    of loss.
  - The abstract nevertheless recommends all three as alternatives ("own folders, or a write guard or a
    rule to head each file").
- **The k=8 claim is stated as certain.** "B's fan-out loss at eight questions thus comes from sharing
  one folder" rests on a folders-vs-one-Researcher difference of -1.5 with a CI reaching -5.8. The paper
  also notes that folders change the paths the Writer sees.
- **Fix, runs:** run per-writer folders at k=16 (60 tasks suffice), and the write guard at k=8, so all
  three fixes are compared on the same footing.
- **Fix, figure:** relabel the k=16 point in Fig. 4 as "16, 3 writers, shared folder", or split it into
  its own panel.
- **Fix, text:** soften "comes from" to "mostly comes from".

### W6. Generality: one model family, an outlier main model, and heavy harness dependence. *(needs new runs; text at minimum)*

- **The main model is the outlier for the pipe.** The pipe's loss appears "only with Qwen3-8B", which is
  the main model. Figure 3 shows the decomposition also changes shape by size.
- **The rescue does much of the work.** It fires in 34-59% of B/C Writer and Reviewer runs. Without it,
  B falls to 18.0% and C to 22.9%.
- **What is being measured is ambiguous.** A large part of "files lose accuracy" may be Qwen3's
  function-calling reliability under vLLM's parser, rather than the file abstraction itself.
- **Fix:** add one other open model family at k=3 (A1, A1-zc, A2, B, C on 150 tasks), report rescue and
  cap-hit rates per channel and size in a table, and frame the accuracy findings as specific to this
  harness and model family.

### W7. Statistics: many uncorrected significance counts, single runs per task, and cross-GPU drift. *(text; one A/A run on the RTX PRO 6000)*

- **Most significance counts are uncorrected.** "Significantly in five of six settings", "four of six",
  and similar counts are not corrected and come from overlapping question sets. Only the Fig. 3 runs get
  Holm correction.
- **The intervals miss nondeterminism.** Each task runs once per channel, yet identical prompts give
  identical outputs in only 59% of tasks. The bootstrap intervals cover task sampling, not this
  nondeterminism.
- **Drift was measured on only one GPU type.** It was measured on the 3090s, but many cross-run
  comparisons sit on the RTX PRO 6000.
- **Some conclusions are marginal against drift.** The pipe-with-documents run trails broadcast by 3.0
  (CI -5.3 to -0.7), cross-run, against a measured drift of ±2.2.
- **Fix:** name the primary comparisons up front and apply Holm or BH across every significance count
  in the paper. Run one A/A rerun on the RTX PRO 6000. Flag cross-run comparisons in the run table (W9).

### W8. Novelty and systems insight are limited, and some related work is missing. *(text/analysis only)*

- **Little here is new as a technique.** The paper concedes that zero-copy ordering is "the common
  practice of putting shared content first". The file channel's token blow-up follows directly from
  stateless tool loops. The accuracy results are model behaviour.
- **The IPC analogy stays at the level of naming.** The index is called a directory and folders are
  called namespaces, but no OS principle is used to predict anything.
- **Missing related work.**
  - Engines that keep KV across tool calls: InferCept (ICML'24).
  - Agent-program schedulers: Autellix.
  - Non-prefix KV reuse: CacheBlend (EuroSys'25), DroidSpeak.
  - OS-style agent context and storage managers: AIOS, MemGPT.
  - MetaGPT's publish-subscribe message pool, which is a third IPC model besides copy and shared files.
- **Fix:** add a simple cost model that predicts the copy-vs-files crossover and test it against Figs. 2
  and 4. The model needs prefill as a function of calls per agent, shared-prefix length and cache
  capacity, plus decode as a function of generated tokens. That turns a set of measurements into a
  systems result.

### W9. Clarity: the paper reads like a lab notebook. *(text only)*

- **Too many differently configured runs without a guide.** There are at least ten runs:
  - main, scope, replay and rerun on the 3090s with a 35k cache and a 2,048-token cap;
  - the Fig. 3 split with a 4,096-token cap on the PRO 6000;
  - the earlier 2,048-token-cap split;
  - the size runs;
  - the 32B path-fix rerun;
  - one-vs-three Researchers;
  - the k=16 repairs;
  - the 24-call budget;
  - serving at 6 and at 32 concurrent tasks.

  They differ in GPU, cache, token cap and task count (60-300), and several paragraphs pack 6-10
  intervals each. A reader cannot hold this.
- **Fix:** add one table of runs (purpose, GPU, KV cache, cap, tasks, k, arms, paired or cross-run) and
  refer to runs by ID.
- **Fix:** move secondary intervals into a table and shorten the abstract, which currently has about
  14 numbers.
- **Typography:** use math minus signs. In the PDF, "-36.4 to -26.0" breaks across a line as
  "(-36.4 to -" / "26.0)".
- **Naming:** "Zero-copy" is a misnomer, since the paper itself says "Every token is still sent" and the
  cache "removes the recomputation of a copy but not the copy itself". A systems audience will object.
  Consider "prefix-ordered broadcast", or justify the name explicitly.

### W10. The figures mostly work, with a few at-a-glance problems. *(text/figure only)*

- **Fig. 1:** clear; no issues.
- **Fig. 2:**
  - Panel (b) makes its claim at a glance. However, the arrow label "-61% computed, no sig. loss"
    overstates non-inferiority, since a 2.9-point loss is not excluded. Use "within -2.9/+1.4 pts".
  - The legend's "Message channels" marker is dark blue, but A2 is drawn grey.
  - The "1% cached" annotation on A1 is the most important caveat in the figure. Mention it in the
    caption.
- **Fig. 3:**
  - The claim reads well.
  - "Tool-call write" has different shades in (a) and (b), and (a)'s colours encode arms while (b)'s
    encode steps. Unify them, or use distinct names.
  - Mark which bars survive Holm.
- **Fig. 4:**
  - (a) is on the 35k shared cache. Say "interleaved channels" in the subcaption.
  - The "A1 = 1" label collides with C's k=1 point.
  - The 1.8x B/C values at k=16 are not discussed in the text.
  - (b): see W5.

## Questions for the authors

1. How exactly is "tokens computed" obtained? Does it include prefill redone after preemption, or
   recomputation of evicted prefixes within a tool loop? How many preemptions occurred at k=8 and k=16 on
   the 35k-cache servers?
2. Why is A1 cached only 1%? Does each role's system prompt precede the documents? Would a group chat
   with a shared system prompt and per-role suffix (what A1-zc does) be the more realistic "broadcast"
   baseline?
3. Which roles produce A1-zc's extra 20% of generated tokens? Is it all the Researcher's longer notes?
4. In B, are Researchers told a file name? Does `write_file` overwrite or append? What did the per-writer
   folder arm's index or listing look like to the Writer?
5. What are the rescue and cap-hit rates per channel, size and role? What is accuracy when tasks needing
   the rescue are excluded from every channel, not just counted as wrong?
6. Before AlignScore scoring, are tool-call notes JSON-unescaped? How are truncated (cap-hit) writes
   handled?
7. `numbers.tex` gives 5,400 main runs (= 6 channels x 900 task instances) and contains values for a
   channel "D" that the paper never mentions. Was a sixth channel run and dropped? If so, why, and does
   dropping it affect any "significant in X of six settings" counts or the run-to-run argument?
8. Why does A1-zc decode per token faster (14.9 vs. 16.9 ms)? Is it less chunked-prefill interference
   in the batch? Does the 96% decode share in `numbers.tex` hold for all channels?
9. The Holm family is "the 12 tests of these runs". Why not correct across all claims in Section 4?
10. The "broadcast changes by -0.9 ... which also checks drift" control is itself a treatment (three
    Researchers). How do you separate drift from the treatment effect there?

## Number check (numbers.tex vs. text)

I checked every number in the abstract, intro and conclusion, and most numbers in Sections 4-5, against
`numbers.tex`. All match, including these:

- the ZC ratio of 38-49;
- 61% prefill cut;
- -2.9 to 1.4 accuracy interval;
- 1.2x generated tokens and 1.09x time;
- files sending 1.8-4.8x the tokens and taking 1.56-1.80x the time;
- write effects significant at two sizes after Holm, rest-of-channel at three;
- 21.2-point fan-out loss and 19.8-point folder recovery;
- the write guard recovering 15.1 of 30.4 points ("about half", 50%);
- the heading rule recovering 18.1;
- B 8-25 and C 8-22 points behind across sizes;
- pipe 10 points behind at 8B only;
- ZC 7 points behind at 4B;
- replay losses of 5 and 8;
- 0.7-1.1x prefill for files at k<=5.

The problems I found are of scope or wording, not arithmetic. They are listed below.

## Quoted sentences that overclaim, are unclear, or mismatch their numbers

1. **Abstract:** "It computes 38–49% as much prefill, within -2.9 to 1.4 points of copying's accuracy at
   three questions per task."
   - 38-49% holds only for k<=5. At k=8 it is 83% (35k cache) and at k=16 100%.
   - Add "at up to five questions per task, when the shared history fits the cache".
2. **Abstract:** "Served alone at six tasks at a time, it decodes each token faster but generates 1.2×
   the tokens."
   - "Decodes each token faster" comes from summed per-request counters, which the paper says do not
     explain wall time.
   - Either drop it from the abstract or present it as the arithmetic in W1.
3. **Abstract:** "...changing only the channel..."
   - The Researcher's wording differs across channels, and A1-zc changes prompt order and hence outputs.
   - The body handles both, but the abstract claim is stronger than the design.
4. **Intro:** "Our first observation is that prefill disagrees with both billed tokens and serving time.
   At three questions per task, shared files send 2.9× the tokens that copying does, yet the engine
   computes only 0.79× as much prefill."
   - This is true only against a 1%-cached broadcast.
   - Against zero-copy copying, files compute about 2.0x the prefill (9.8k vs. 4.8k).
5. **Fig. 2b label:** "−61% computed, no sig. loss". **Caption:** "zero-copy's accuracy is not
   significantly lower than broadcast's".
   - Non-significance is not equivalence, since the CI admits a 2.9-point loss.
   - Use the interval.
6. **Results:** "At those three sizes it also lowers accuracy, by -5.6 points at 8B."
   - "Lowers by -5.6" is a double negative. Use "by 5.6 points".
7. **Results:** "The wording does not lower accuracy."
   - Better: "No detectable loss (intervals within ±3.1); at 4B it raises accuracy by 6.2."
8. **Results:** "This step costs accuracy at three sizes, 4B, 14B, and 32B, and three survive the
   correction."
   - Correct by the numbers, but it conflicts with the replay result at 8B (5 points, CI 2 to 8) without
     comment (W3).
9. **Results, heading:** "Readers without an index skip the notes."
   - In the replay, "the index does not help" and C's Writer opens the notes *less* often than B's (63%
     vs. 76%). At k=16 the heading rule alone recovers 18.1 points.
   - C's main-run advantage may come from the heading rule rather than the index. The heading attributes
     it to the index.
10. **Sensitivity:** "B's fan-out loss at eight questions thus comes from sharing one folder."
    - The folders-vs-one-Researcher CI reaches -5.8, and folders also change the paths the Writer sees.
    - Use "mostly comes from".
11. **Sensitivity:** "broadcast changes by -0.9 points ..., which also checks drift between runs."
    - This is a treatment arm (three Researchers), not an A/A check.
12. **Sensitivity:** "Rerunning A1 and B on 200 main tasks gives each difference's interval inside ±2.2
    points."
    - Unclear: which difference? (Rerun minus original, per channel?)
13. **Fig. 4b subcaption:** "plain files collapse at large k; the pipe recovers".
    - Section 5 attributes the collapse to parallel writers in one folder, not to k.
14. **Conclusion:** "It saved no serving time at six or 32 tasks at a time."
    - At six it *cost* 9% more time (1.09x, 1.08-1.10 over three runs). Say so.
15. **Conclusion:** "so a system may do better to store an agent's plain reply as a file, which we did
    not test as a channel. Even broadcast's notes stored as one file lost 5 points in the rest of the file
    channel."
    - The replay is close to exactly that test, and it lost 5 points.
    - The two sentences pull in opposite directions. Reconcile them.
16. **Abstract / Conclusion:** "Parallel writers should get their own folders, or a write guard or a rule
    to head each file with its questions."
    - These three remedies were tested in different settings: folders at k=8, the guard and the heading
      rule at k=16.
    - At k=16 the guard and the heading rule leave 15.3 and 12.6 points of loss.
    - They are not interchangeable on the evidence shown.

## What stands between this paper and acceptance

The minimum for a confident accept:

- **Text-only changes:**
  - Reframe the cost observation against cache-friendly copying (W1).
  - Fix the scope of the 38-49% claim, Fig. 4b's attribution, and the fan-out guidance (W5).
  - Reconcile the 8B decomposition with the replay (W3).
  - Add a run table and trim the number density (W9).
  - Add the missing related work (W8).
- **Three modest new experiments:**
  - (a) A fixed-output trace replay for serving time (W1).
  - (b) Each channel alone across cache capacities, with recomputation counted (W2).
  - (c) Per-writer folders at k=16 (W5).
- **Strongly recommended:**
  - A 2x2 write x delivery run (W3).
  - Human validation of the fact measure (W4).
  - One non-Qwen model at k=3 (W6).
