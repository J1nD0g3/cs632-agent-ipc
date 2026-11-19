# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6 pages)

## Summary

The paper compares five ways for agents in a Researcher-Writer-Reviewer pipeline to pass results: broadcast
(A1), broadcast reordered so the shared history is a common prefix ("zero-copy", A1-zc), a pipe (A2), shared
files (B), files with an index (C), and files plus a short handoff (D). It uses Qwen3-8B on vLLM v0.33.0
with prefix caching, HotpotQA and 2Wiki, and 150 paired tasks per dataset and k. It reports two costs:
tokens sent (an API bill) and prefill tokens not served from the cache (presented as the self-hosted cost).
Main claims: (1) the two costs rank channels differently (files send 2.9x but compute 0.79x at k=3);
(2) A1-zc keeps broadcast's accuracy and computes 61% less; (3) files lose facts both when written (a tool
call shortens notes; the A1w control) and when read (the replay control); (4) the savings shrink when
concurrent prompts outgrow the KV cache, and B collapses at k=16; (5) the conclusions depend on model size
(4B to 32B).

The paper is unusually careful about controls for a workshop submission: replaying the same notes, A1w,
documents-in-prompt (Bd, A2d), fan-out at k=3, repeat runs, a KV-size sweep, and validation of the fact
measure. All numbers come from a generator script. The main problem for a systems venue is the cost
accounting. "Tokens computed" counts prefill only, and the paper never checks it against time. The logs
already in the artifact suggest that time ranks the channels close to the token-sent order, not the
prefill order. That weakens the paper's "key observation". A second problem is that A1-zc is not a pure
reordering, because it changes what the Researcher writes.

## Score and confidence

- Score: **3 / 5** (borderline; leaning accept if weakness 1 is fixed with a real time or throughput
  measurement and weaknesses 2-4 are addressed in text or with the cheap runs below)
- Confidence: **4 / 5** (I checked the claims against `numbers.tex`, the generator, the figure scripts,
  and the main-run rows)

## Strengths

1. **Clean question, good framing.** The message-passing vs shared-memory framing is natural and
   memorable, and it is new to make the channel the independent variable (prior work prunes or compresses
   over a fixed channel).
2. **Controls that separate content from channel.** The replay experiment (same notes into every channel),
   A1w (tool-call write, copied read), Bd/A2d (documents added), and the k=3 fan-out control are the right
   experiments. The write-cost (A1w) and read-cost (replay) results add up to roughly B's total loss, which
   is a nice decomposition (see Analysis 7).
3. **Paired design, intervals, noise check.** Every channel runs the same tasks; paired bootstrap
   intervals; a repeat run shows the B-A1 gap reproduces (7.0 vs 7.8 points); the paper reports the
   nondeterminism of greedy decoding under batching (59% identical outputs for identical prompts).
4. **Honest scoping.** The rescue rate, strict accuracy (18-41%), the budget dependence at k=16, and the
   limits in the conclusion are stated rather than hidden.
5. **Validated fact measure.** AlignScore is checked on 450 synthetic pairs (AUC 0.996) and cross-checked
   with an entity match that needs no model. The authors say plainly that fact-level numbers are
   approximate.
6. **Reproducibility.** Macros come from a script, and configs and per-call logs are kept.

## Weaknesses (most important first)

### W1. The "self-hosted cost" is prefill tokens, and the paper's own wall-time data contradict it.

The key observation ("cost has to be counted two ways") rests on prefill tokens standing in for what a
self-hosted deployment pays. Decode tokens are excluded entirely, and per-call overhead is ignored. The
main run already records `wall_s` and `completion_tokens`, and at k=3 they say (pooled, 300 tasks):

| Channel | Prefill computed | Decode tokens | Wall time / task |
|---|---|---|---|
| A1 | 12.4k | 835 | 31.2 s |
| A1-zc | 4.8k (0.39x) | 965 | 34.0 s (**1.09x**) |
| A2 | 4.7k | 791 | 27.6 s |
| B | 9.8k (0.79x) | 1,608 | 57.7 s (**1.85x**) |
| C | 9.8k | 1,447 | 52.0 s |
| D | 7.2k | 1,245 | 44.0 s |

At k=1, A1-zc takes 21.1 s against A1's 13.7 s (1.54x), because its Researcher decodes 456 tokens against
210. By wall time, the ranking is A2 < A1 < A1-zc < D < C < B, which is close to the tokens-sent ranking.
The 61% prefill cut buys no speed. The text reports only the file channels' wall-time ratio
(1.4-1.8x) and leaves out `\nWallAZc` = 1.1, which is in `numbers.tex` but never cited. Wall time is also
confounded here, since six tasks of mixed channels share each server. So the paper currently has no clean
time measurement at all.

**Fix.** Measure serving cost directly (Experiment 1). Report decode tokens next to prefill. Rename "tokens
computed" to "prefill computed", or define a compute measure that includes decode. Reword the abstract,
intro and conclusion so prefill savings are not presented as the self-hosted cost. If time ranks the
channels like tokens sent, say so. That would still be a finding, but a different one.

### W2. Zero-copy broadcast is not "the same content as A1"; the reordering changes what the Researcher writes.

The paper says "Only the order changes." But the Researcher is reordered too (documents first, instruction
last), and it writes longer notes: 1,992 vs 1,570 characters at k=3 and 1,663 vs 757 at k=1. Its notes
state 50% of the supporting facts against A1's 45% (Fig. 3a shows this without comment). A1-zc's accuracy
parity therefore combines two things: the ordering's effect on the Writer and Reviewer, and different, longer
notes. The same sensitivity costs the 4B model 7 points (3 to 11). Prompt order clearly changes behavior,
so "zero-copy" is not semantics-preserving, as the name implies.

**Fix.** Run A1-zc on replayed A1 notes, or use a variant that reorders only the Writer and Reviewer
(Experiment 3). Report note length per channel in the text. Drop "only the order changes", or limit it to
the prompt and say the output changes.

### W3. The Qwen3-32B file-channel numbers are a harness artifact, and a post-hoc rescore cannot fix them.

In B and D, 51 and 59 of 200 runs at 32B write the final answer to `workspace/final.md`, and the harness
looks only at `final.md`. The paper then states "Files trail broadcast at every size, B by 8-28 points", and
the 28 is mostly that artifact: the rescore gives B 64.5% and D 61.3% against 75.8%, gaps of about 11 and 15.
The rescore is also only partly valid. When an upstream agent (Writer) writes to a prefixed path, the
downstream agent (Reviewer) may fail to find the draft, and rescoring the final file does not undo that. In C,
126 Researcher runs also used prefixed paths. Path resolution is an environment property, like a working
directory, not a "model that handles tools" property. Any real agent filesystem would normalize
`workspace/x` to `x`.

**Fix.** Rerun B, C and D at 32B with path normalization in the tool layer (Experiment 2). Use those numbers
in the range, and keep the prefixing behavior as a one-line observation. Check the 4B and 14B logs for the
same slip.

### W4. The k=16 collapse of plain files is mostly attributed to mechanisms the paper does not isolate.

The abstract headlines B's 34-point loss at k=16 (60 tasks; my bootstrap over the rows gives -38.5 to -29.2).
At that setting three things change together: three parallel Researchers (write clash), a 12-call budget
that B's Reviewer hits in 52% of runs, and cache pressure. The paper rules out cache pressure with 10 tasks
(`\nPressNTwo` = 10), which is too few to support "explains the lost savings but not the accuracy collapse".
The clash analysis is correlational, and it shows that the clash barely moves accuracy (38% with a clash vs
41% without), even though note recall halves. The k=3 fan-out control finds B's own fan-out cost
insignificant (-4, -10 to +2). The 24-call budget was tested only at k=3. As written, the "Parallel writers
race" paragraph suggests the race causes the collapse, but the data point more toward the budget.

**Fix.** Run Experiment 4 (budget 24/48 at k=16, and B with per-Researcher namespaces). Give N and intervals
for every k=8 and k=16 number in the text and in Fig. 4. Qualify the abstract sentence with "under a 12-call
budget".

### W5. "Tokens sent = what an API bills" ignores cached-input pricing, which makes the two-cost gap look larger than it is.

The major APIs discount cached input, often by 50-90%, and price output at several times input. The paper
mentions this once ("or APIs that discount cached input"), but the abstract and intro present tokens sent
as the bill. From the logged means at k=3, with cached input at 0.1x and output at 5x input, my rough
estimate is: A1 1.00, A1-zc 0.63, A2 0.52, B 1.24, C 1.19, D 0.87. Under that pricing, B costs about 1.2x
broadcast, not 2.9x, and A1-zc saves on the API bill too. That moves the paper's central "two ways"
contrast.

**Fix.** Add a third cost column, the discounted bill at one or two published price ratios (Analysis 2). Say
which deployments the raw tokens-sent figure describes (APIs without caching, or with caching disabled).

### W6. Instruction wording is confounded with the tool call in the "notes shortened by the tool call" claim.

The Researchers' "instructions differ in where its notes go and in what each channel asks of it". A1w
inherits B's instructions and writes through `write_file`, so A1w vs A1 changes both the wording and the
medium. The heading "The tool call, not the file, shortens the notes" therefore claims more than the
control shows. The effect also does not hold at 14B (B's notes state 48% against A1's 44%), yet the
conclusion recommends plain replies in general.

**Fix.** Add a control with B's exact Researcher instruction but a reply-based output (Experiment 5). Put
the A1 and B Researcher prompts in an appendix or the artifact. Limit the conclusion's recommendation to
the models where A1w shows the effect (the planned A1w size sweep answers this).

### W7. The fact-delivery measure and the stage attribution are weakly tied to accuracy.

76% of broadcast's correct answers come from notes that miss a supporting fact. AlignScore agrees with the
Qwen judge at kappa 0.29 on real notes. On D's handoffs, the entity check gives 94% delivery and AlignScore
about 50%. Fig. 3b charges the Researcher whenever its output misses any supporting fact, even in A1 and
A1-zc, where the Writer has all the documents. So the 20% "Researcher missed" bar for A1 mostly reflects the
attribution rule. Fig. 3a's "Reached Writer" bar for message channels equals the first bar by construction,
although A1's Writer in fact received every supporting fact through the documents.

**Fix.** Show that note recall predicts correctness (Analysis 5), add a small human calibration
(Analysis 6), and for channels whose Writer has the documents, count facts available to the Writer
(documents included). Otherwise drop panel 3b or relabel it as a lower bound.

### W8. Novelty is modest, and the OS analogy is loose.

Putting static shared content first so a prefix cache can reuse it is standard prompt-caching practice, and
it is the premise of SGLang's RadixAttention, Parrot, Prompt Cache and KVFlow, which the paper cites. The new
part is the measured comparison across channels, not A1-zc. The paper should say this plainly.
"Zero-copy" is also a misnomer. Every token is still sent and tokenized, and the engine shares KV blocks,
which is closer to page sharing / deduplication (or COW `fork`) than to zero-copy IPC. Related work also
misses OS-for-agents work (AIOS, MemGPT/Letta, LLM-based semantic file systems), KV and latent communication
between models (DroidSpeak, Cache-to-Cache, LatentMAS-style latent messaging), non-prefix KV reuse
(CacheBlend, which is relevant to a pipe that re-adds the documents), and agent-workflow serving (Autellix,
Teola/Ayo).

**Fix.** Rename A1-zc (for example "prefix-shared broadcast") or justify the term. Position the contribution
as measurement, and add the missing related work in about four lines.

### W9. Clarity: too many numbers in prose, and the key figures mislabel or omit the mechanism.

- The paper carries more than 150 numbers in running text and has no results table. Readers cannot compare
  accuracy, sent, prefill, decode, calls, time, notes and delivery per channel at k=3 without
  reconstructing it. Add one table, which also frees prose.
- **Fig. 2b labels are wrong.** "x% cached" is computed as `1 - prefill / (prompt + completion)`, so
  completion tokens count as cached. A1's "7% cached" is really 0.5% of prompt tokens, and A2's "15%" is
  about 1.3%. Use `cached / prompt`.
- **Fig. 1** does not draw the role instruction, which is the one thing that differs between A1 and A1-zc.
  Without it, the figure does not show why A1 gets no reuse. Add an "Instruction" segment at the start (A1)
  and at the end (A1-zc).
- **Fig. 4** joins k=8 and k=16 (fan-out) with a line across a design change, gives no N or intervals, and
  does not show the cache-size dimension that the text treats as the cause. Break the line at the divider,
  add intervals, and consider a small third panel or inset with the 35k/100k/400k sweep.
- "The cache and model-size runs ... use one RTX PRO 6000 per server with a fixed KV size" contradicts the
  KV sweep in the same section. Say "a KV size set per experiment".
- State N per experiment in one place, for example a column in the table. Right now N varies between 10,
  60, 100, 200 and 300 and is scattered across the text.

### W10. Statistics: unadjusted multiple comparisons and some underpowered claims.

Counts like "significantly in five of six settings" come from unadjusted 95% intervals. The k=16 pressure
test (10 tasks), the fan-out control (100 tasks, not significant) and the 24-call check (100 tasks) support
negative claims ("changes by at most", "not the whole loss") that need power or equivalence bounds. Report
the interval, not only "at most X points", and use Holm or a similar correction for the significance
counts.

## Requested experiments (prioritized)

Run counts are task-runs (one pipeline execution).

1. **Serving cost in time, channel by channel (required).** Run each channel alone, not interleaved, with
   Qwen3-8B at k=3 and k=8 on 100 tasks, at fixed concurrency 6 and at one saturating level (for example
   24). Record makespan / tasks per hour, GPU-busy seconds, per-request prefill and decode time from
   vLLM's request metrics, and TTFT. Also run concurrency 1 on 50 tasks at k=3 for unloaded latency.
   *Tests:* "the engine computes 0.79x ... the cost a self-hosted deployment pays", "zero-copy cuts the
   tokens computed by 61%" as a cost saving, and the conclusion's deployment advice. *Size:* 6 channels x 2 k
   x 100 x 2 concurrency ~ 2,400, plus 300 at concurrency 1. Most runs are short at k=3, and a 96 GB GPU fits
   this easily.

2. **Qwen3-32B with path normalization (required).** Rerun B, C and D at 32B, k=3, on the same 200 tasks,
   with the tool layer resolving `workspace/x` to `x`. Keep everything else fixed. *Tests:* "Files trail
   broadcast at every size, B by 8-28 points" and "the file channels need a model that uses tools well".
   *Size:* 3 x 200 = 600. This replaces the post-hoc rescore.

3. **Zero-copy with content held fixed (required).** (a) Add A1-zc to the replay experiment (A1's
   Researcher notes, reordered Writer and Reviewer prompts) on the 200 replay tasks at 8B. (b) Run the same
   at 4B to see whether the 7-point loss comes from the Researcher's output or from instruction-last
   prompts for the Writer and Reviewer. *Tests:* "the same content as A1 ... only the order changes" and
   "keeps copying's accuracy". *Size:* 200 + 200 (+200 A1 replay at 4B if not already available).

4. **Decomposing the k=16 collapse (strongly want).** At k=16 with 8B on 60-100 tasks: B, C and D with 24-
   and 48-call budgets, and B with per-Researcher namespaces enforced by the harness (`r1/`, `r2/`, `r3/`)
   at budget 12. *Tests:* "plain files collapse", "parallel writers race on shared files", and how much of
   the collapse is the budget. *Size:* (3 x 2 + 1) x 100 ~ 700, plus 100 A1 if run on different hardware.

5. **Instruction wording vs tool call (strongly want).** An A1 variant whose Researcher gets B's exact
   instruction text but answers in a reply that is copied as in A1. Pair it with A1w on the same 200 tasks.
   *Tests:* "The tool call, not the file, shortens the notes." *Size:* 200 (and 200 per model size if run
   with the A1w sweep).

6. **A second model family (strongly want, if one can be served).** Any non-Qwen instruct model with
   function calling and at least 32k context (for example Llama-3.1-8B-Instruct, Mistral-Small-24B or
   Gemma-3-12B). Six channels, k=3, 200 tasks. *Tests:* the generality of every main claim; tool-call
   shortening, index use and path handling are all model behaviors. *Size:* 1,200. If no such model is
   available, say so in the limitations and keep the claims scoped to Qwen3.

7. **Powered cache-pressure test at k=16 (want).** Replace the 10-task concurrency-2 run with 60 tasks at
   concurrency 2 vs 6, or 60 tasks at 400k vs 35k KV at concurrency 6, for A1, A1-zc, B and C. *Tests:*
   "Cache sharing ... explains the lost savings but not the accuracy collapse." *Size:* 4 x 60 x 2 ~ 480.

8. **Rescue ablation (want, only if Analysis 9 cannot be done from logs).** B, C and D at k=3 with the last
   message taken as the output and no forced write. *Tests:* how much of the file channels' accuracy depends
   on the rescue. *Size:* 3 x 200 = 600.

### On the two planned experiments

- **(a) Qwen3-32B with a 100k KV cache at k=8:** not necessary for any claim in the current text. The
  32B/35k "corner" cell (`p03_corner_32b_35k`) is computed in `numbers.tex` but never cited, and the
  cache-size effect is already shown cleanly at 8B (35k/100k/400k, accuracy within 1.6 points). It is
  worth running only if the paper adds the corner cell, for example to claim that the cache effect holds at
  32B (B computes 2.37x at 35k, which is notably more than 8B's 1.29x). If so, run it after Experiment 2
  with path normalization on, or the B/D accuracies in the 2x2 will carry the same artifact. Cost:
  ~600 runs.
- **(b) A1w at 4B/8B/14B/32B:** useful, keep it, and prioritize **14B** (where B's notes are not shorter,
  48% vs 44%) and **32B**. These decide whether the conclusion's "write long results as plain replies"
  holds beyond 8B. 4B is the least informative, because its file channels fail for many reasons. 8B at
  100k is needed only for matched hardware. Pair it with Experiment 5 (same tasks) so wording and medium
  are separated at each size.

## Analyses that need no new runs

1. **Decode and time.** Report completion tokens and wall time per channel and k (already in the rows).
   Explain why A1-zc is slower (longer Researcher output) and say that prefill savings did not shorten
   tasks under this load.
2. **Discounted API bill.** Compute a per-channel cost with cached input at 0.1x and 0.5x and output at
   4-5x input from the logged prompt, cached and completion tokens.
3. **Cost model from per-call logs.** Regress per-call `latency_ms` on uncached prompt tokens, cached
   tokens, completion tokens and the concurrent load, to estimate GPU-seconds per channel and how much
   prefill vs decode contributes. This partly covers W1 until Experiment 1 runs.
4. **Fix Fig. 2b** (cached share = cached / prompt) and Fig. 1 (draw the instruction segment).
5. **Does note recall predict correctness?** A per-question logistic regression of correctness on the
   AlignScore and entity recall of the notes, with channel as a covariate. If the channel effect stays
   after conditioning on recall, files lose accuracy beyond the facts they drop.
6. **Human calibration.** Two annotators label about 100 (note, supporting fact) pairs, stratified by
   channel and including D handoffs. Report each measure's agreement and say which one the paper trusts
   where AlignScore and the entity check disagree (D: about 50 vs 94).
7. **Explicit write/read decomposition.** On the overlap of the A1w, replay and main subsets, tabulate
   A1-A1w (write cost), A1-B on replayed notes (read cost), and A1-B (total) with paired intervals.
8. **N and intervals for every number in Fig. 4 and §5**, including the 60-task k=16 cells (I get B -33.9,
   -38.5 to -29.2; C -5.1, -8.6 to -2.0; A2 -0.5, -3.2 to +1.9).
9. **Rescue sensitivity from logs.** Score the agent's last message, where logged, instead of the rescued
   file, and report the rescue rate at the 24-call budget.
10. **Note length by channel**, including A1-zc vs A1 at each k.
11. **Holm-corrected significance counts** and equivalence bounds for the "changes by at most" claims.
12. **Offline cache replay (if the token sequences of the calls can be rebuilt).** Replay each channel's
    call sequence alone through an LRU block cache at several capacities, to get prefill vs KV capacity per
    channel without co-tenancy effects. This would also back the k=8/16 cache explanation in a cleaner
    form than the shared-server runs.

## Questions for the authors

1. What exactly are the Researcher prompts of A1, A2, B, C, D and A1w? Which lines differ besides where the
   notes go?
2. In A1, is the role instruction a system message at the start, as in AutoGen? Is the near-zero reuse in
   A1 (0.5% of prompt tokens) representative of real frameworks, or would a framework that keeps a common
   system prompt already get most of A1-zc's saving?
3. Why does A1-zc's Researcher write 1.3x (k=3) to 2.2x (k=1) longer notes than A1's?
4. What does the rescue call see? Do downstream agents use the rescued output? Does the rescue rate change
   at 24 calls?
5. Were the PRO 6000 runs also six concurrent tasks, interleaved across channels?
6. What is A1 at k=16: three Researcher replies concatenated in a fixed order? How are the A1-zc prefixes
   arranged with three parallel Researchers?
7. Did 4B or 14B also write to prefixed paths?
8. Does enabling Qwen3 thinking change tool use (index reads, note opening, path errors)? Agents are often
   run with it on.
9. What counts as a "short prediction" in the containment rule, and how much do accuracies change under
   exact match alone across all channels (not only A1-zc)?

## Sentences that overclaim or do not match their numbers

1. Intro: *"Yet the engine computes only 0.79x as much prefill, the cost a self-hosted deployment pays."*
   B decodes 1.9x as many tokens and takes 1.85x the wall time (57.7 s vs 31.2 s). Prefill is one part of the
   self-hosted cost, and not the part that sets latency here.
2. Abstract: *"Zero-copy broadcast ... keeps copying's accuracy while computing 38-49% as many tokens."*
   This counts prefill only. A1-zc decodes more and is 1.09x slower at k=3 (1.54x at k=1). It also loses
   7 points at 4B.
3. §2: *"The same content as A1 ... Only the order changes."* The Researcher's output changes (1,992 vs
   1,570 characters; 50% vs 45% of facts).
4. Fig. 2 caption: *"Labels in (b) give the share of the tokens sent that the engine served from its prefix
   cache."* The labels count completion tokens as cached. A1's 7% is 0.5% of prompt tokens.
5. §5: *"Files trail broadcast at every size, B by 8-28 points."* The 28 includes 51 of 200 runs lost to the
   harness not resolving `workspace/`. The rescored gap is about 11.
6. Abstract: *"When three parallel Researchers split sixteen questions, plain files lose 34 points."* This
   holds at a 12-call budget that B's Reviewer exhausts in 52% of runs, on 60 tasks. The budget qualifier
   belongs in the abstract.
7. §5: *"Cache sharing among concurrent runs explains the lost savings but not the accuracy collapse."* The
   accuracy half rests on 10 tasks.
8. §5 heading: *"Parallel writers race on shared files. Part of B's collapse at sixteen questions happens
   before anyone reads."* Accuracy is 38% with a clash and 41% without. The race halves note recall but
   barely moves accuracy, and the k=3 fan-out control is not significant.
9. §4 heading: *"The tool call, not the file, shortens the notes."* Instruction wording is confounded, and
   at 14B B's notes are not shorter (48% vs 44%).
10. Abstract: *"With small payloads, copying is the most accurate channel."* This holds only for 8B and is
    tied with A1-zc. At 14B, A1-zc (74.7%) is above A1 (73.7%), and the pipe is within 1-2 points at 14B
    and 32B.
11. Conclusion: *"Plain files lost accuracy and cost more tokens in every setting."* At k <= 5 they
    computed fewer tokens than broadcast (0.67-0.79x). Say "sent more tokens".
12. Intro: *"Our key observation is that cost has to be counted two ways"* together with *"tokens sent ...
    the cost an API bills"*. Under cached-input discounts (Analysis 2), B costs about 1.2x broadcast, not
    2.9x, so the two counts disagree much less than the paper says.
13. Related work: *"In agents, the prefix cache plays the role of zero-copy."* Every token is still sent. KV
    block sharing is closer to page sharing or deduplication.
14. Conclusion: *"When the shared history fits the cache, copy it and order prompts so the cache reuses
    it."* This is supported by prefill counts and 8B accuracy, not by time or by 4B. Qualify it until
    Experiment 1 is done.
