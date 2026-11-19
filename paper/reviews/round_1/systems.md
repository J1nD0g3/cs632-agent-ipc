# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6 pages)

## Summary

The paper fixes a three-stage Researcher-Writer-Reviewer pipeline (Qwen3-8B, vLLM v0.33.0, prefix caching on) and changes only the inter-agent channel. There are six variants: copy the history (A1), the same with a cache-friendly order (A1-zc), pipe (A2), shared files (B), files plus an auto-maintained index (C), and pushed handles (D). It reports accuracy, tokens sent, tokens computed after prefix caching, and an LLM-judged trace of where supporting facts are lost, on HotpotQA and 2Wiki with 150 paired tasks per dataset and k. The main claims are: (1) sent and computed cost rank the channels in opposite orders, and cache-friendly ordering gives copying a pipe's compute at no accuracy cost; (2) files lose information on the writing side (shorter notes) and on the reading side (readers skip the notes), and an index fixes the reading side; (3) these effects depend on KV capacity, pipeline length, read granularity and model size.

**Score: 3 / 5** (weak accept for a workshop, if the sensitivity confounds are fixed or the claims are scoped down)
**Confidence: 4 / 5**

## Strengths

1. **A clean, well-motivated control.** The task, roles and order are fixed and only the channel changes. Comparisons are paired across channels on the same tasks, and runs get separate `cache_salt` namespaces. That is the right design for a measurement paper, and most agent-communication work does not do it.
2. **Counting cost two ways is the paper's best idea.** Figure 2(a) vs 2(b) makes it at a glance: files are the most expensive channel by tokens sent (2.9x) and mid-pack by tokens computed (0.79x). Systems readers will remember this result.
3. **Stage-level attribution.** The supporting-fact trace (Figure 3) goes beyond end accuracy and explains *why* a channel loses: the pipe's Reviewer overturns right answers, and B's Writer never opens the notes in 42% of tasks. The notes-length effect (27% shorter notes when they go to a file) is surprising, and I have not seen it reported before.
4. **Useful negative and sensitivity results.** Batched reads (`readv`) hurt accuracy, the tool budget is checked at 12 vs 24 calls, run-to-run nondeterminism is quantified honestly (59% identical outputs), and the 4B model shows that zero-copy ordering is not free for every model.
5. **Figure 1 is excellent.** It is to scale and call by call. It explains the "stateless model resends the conversation" mechanism better than the text does.
6. All numbers are generated macros (`numbers.tex`), which suggests a reproducible pipeline.

## Weaknesses (most important first)

1. **The headline sensitivity result confounds payload size with concurrency and topology.** The abstract says "once prompts outgrow the KV cache, zero-copy saves nothing." But two other things change along with k:
   - (a) **Concurrency.** At k=8 the loss of reuse comes from *six concurrent runs* sharing a 34,864-token KV cache, not from any single prompt outgrowing the cache. A single k=8 prompt fits easily under the 32,768-token context. This is a harness choice that the Methodology never mentions; it appears only in §5.
   - (b) **Topology.** At k=16 the pipeline also switches to three parallel Researchers. With fan-out, the Writer's shared history is no longer a prefix that any one Researcher prefilled, so A1-zc can lose its reuse for reasons that have nothing to do with cache capacity. B now has to find three notes files instead of one, which could explain its 34-point collapse without any cache effect.

   **Fix:** these are exactly the two pending experiments; see "What the pending experiments must show" below. In addition, plot Figure 4(a) against *working set / KV capacity* (concurrent runs x per-run live prefix tokens / 34,864) instead of k, and report vLLM's measured prefix-cache hit rate and eviction counts directly instead of inferring them. If fan-out explains k=16, separate the k=16 point from the k-axis or drop it from the "payload" story.

2. **Tokens computed is presented as "what a self-hosted deployment pays," but latency and GPU time are never reported.** The contributions promise accounting for "latency, file I/O," and `numbers.tex` contains wall-clock ratios (`\nWallB` = 1.8, `\nWallC` = 1.7, `\nWallD` = 1.4, A1-zc 1.1, A2 0.9). None of them appear in the paper. With 17 sequential calls, B can compute 0.79x the prefill and still take about 1.8x the wall time, which reverses the self-hosted conclusion for latency-sensitive users. Computed prefill also leaves out decode tokens and the attention cost over cached context.
   **Fix:** add end-to-end latency and GPU-seconds per task (one more column or a third panel in Figure 2), and say that tokens computed is a prefill proxy. Otherwise remove "latency" and "file I/O" from the contribution bullet.

3. **"Writing to a file changes the writer" is not isolated from prompt and format differences.** The paper says "the same Researcher, given the same input, writes 27% shorter notes." In the file channels, though, the Researcher's prompt contains tool schemas, and its notes are produced as a JSON-escaped function-call argument parsed by vLLM's tool parser. The input is therefore not the same, and the shorter notes may come from emitting text inside a tool call rather than from the file destination. D's Researcher is even worse (50% of facts vs 73%), and the text never explains it.
   **Fix:** a 2x2 ablation with output mode {plain reply, `write_file` call} x destination {message, file}. For example, the harness saves a plain reply to a file, and a message channel delivers through a `send_message` tool. Also report output-token limits per call, and how often the forced-write call fired per channel.

4. **The stage attribution does not support "an index fixes the reading side" as written.** In Figure 3(b), "Not delivered" is barely visible for every channel (about 1% of questions). The differences between B, C and D are almost entirely "Researcher missed," which is a writing-side category. C's Researcher also states more facts than B's (63 vs 59), even though the index cannot affect the Researcher. That suggests Researcher-side noise, and the 59% identical-output rate supports this. Finally, the attribution treats channels unequally: in B, C and D the Writer can read the source documents itself, so a fact the Researcher "missed" is recoverable there but not in A2. So Figure 3(a) (delivery drops from 59 to 49) and Figure 3(b) (delivery explains almost no errors) tell different stories, and the paper does not reconcile them.
   **Fix:**
   - Define "reached the Writer" precisely for file channels. Does it count facts the Writer read from source documents?
   - Reconcile 3(a) with 3(b).
   - Most importantly, use *common random numbers*: generate the Researcher's output once and replay the same notes into every channel's downstream stages. That cleanly separates reading-side effects from writing-side effects and removes the Researcher's batching noise from all downstream comparisons.

5. **The LLM-judge measurement is not validated.** Qwen3-8B judges fact presence in text that Qwen3-8B wrote. Self-preference bias is documented (Panickssery et al., NeurIPS 2024), and the paper gives no human agreement, no stronger-judge agreement, and no judge-repeatability number. All of §4's "lose information" claims rest on it.
   **Fix:** hand-label 100-200 (sentence, text) pairs stratified by channel and report precision and recall, or Cohen's kappa. Alternatively, re-judge a subset with a stronger model from another family. Report whether judge error differs by channel; file-channel notes are shorter and may be more paraphrased.

6. **Novelty and related work are thin on the systems side.** Cache-friendly prompt ordering for multi-agent workflows is the subject of KVFlow (NeurIPS 2025), Parrot (OSDI 2024), Prompt Cache (MLSys 2024), TokenCake, Continuum and Autellix. Engine vendors' prompt-caching guides also recommend "static prefix first." TOAP (2026 preprint) directly measures reference vs summary vs KV-cache sharing between agents, which is the closest prior work, and it is not cited. "Agentic File System" (arXiv 2512.05470) and AIOS are not cited either, although both use the file/OS framing. Your own `related_work.md` lists most of these. As written, A1-zc reads like a known technique given a new name.
   **Fix:** cite these works and position the contribution as *measurement*: the sent-vs-computed inversion, the writing-side effect, and the index result. Do not present zero-copy ordering as a mechanism contribution. Name the specific gap: none of these works compares channels with the engine's computed cost held as a first-class metric.

7. **The IPC framing is decorative, and "zero-copy" is a misnomer.** A1-zc still *sends* every token (13.6k vs 13.3k); only prefill is deduplicated. That is closer to page-cache sharing or memoization than to zero-copy, which in OS terms means the data is not moved. Lauer and Needham's point was *duality* (equivalent performance under equivalent implementations), not "neither wins everywhere." The OS literature is not used to predict anything: no fbufs/LRPC-style argument, and no capability semantics for handles.
   **Fix:** either rename (e.g. "prefix-shared broadcast") or define precisely what is zero-copy (the KV, not the tokens). Use the IPC lens to state one falsifiable prediction that the data tests, e.g. that a duality-style equivalence holds when the cache is large enough. Characterize Lauer and Needham correctly.

8. **Accuracy claims rest on single runs despite large nondeterminism.** 41% of identical Researcher prompts produce different output, so run-level variance is large, and the paired bootstrap over tasks does not capture it. "Within the noise of it in every dataset and k" is an absence-of-evidence claim, made with 6+ settings and no multiple-comparison correction.
   **Fix:** run each main condition 3 times, or use vLLM's batch-invariant mode if available. Report between-run spread. Use an equivalence test (TOST with a stated margin, e.g. ±3 points) for "same accuracy" claims, and state the number of tests behind "significantly in 5 of six settings."

9. **Harness choices may disadvantage specific channels, and that needs to be shown.**
   - Is D's handoff cap fixed at 120 words for all k? At k=16 that is about 7 words per question, which would explain D's -11.
   - What is the notes file called in B? If the name does not say "notes," B's "Writer never opens the notes" is partly a naming artifact, and B vs C measures naming rather than indexing.
   - The pipe's Reviewer is asked to check a draft with no evidence. A pass-through Reviewer, or a pipe that forwards the draft's evidence field, is a fairer pipe.
   - In the 12-call setting, 28-34% of B and C runs hit the budget. The 24-call check is good, but 14-16% still hit it.
   - Report invalid-read rates (Figure 1 shows "read (no such file)" for D) and answer-parse failures per channel.

10. **Missing reference points.** There is no single-agent baseline (one call with all documents and questions) and no Writer-draft accuracy. A reader cannot tell whether the pipeline helps at all, or how much of each channel's loss happens at the Reviewer.
    **Fix:** add a single-agent row to Figure 2 and per-stage (draft vs final) accuracy.

11. **Generality of the "rules."** One model family, one GPU class with a very small KV cache (34,864 tokens, barely above max-model-len), and one task type where every document fits in context. That regime structurally favors copying. "Share files only with an index, and only with a model that handles tools" is drawn without any model that handles tools well: even the 8B loses with files.
    **Fix:** add one stronger tool-using model for accuracy only, e.g. Qwen3-32B on a larger GPU, or an API model. Without it, rephrase the rules as conditional on this regime. Give the k thresholds in hardware-independent units (working set / KV capacity).

12. **API cost model.** "Tokens sent ... the quantity an API bills" ignores the fact that major APIs now discount cached input automatically (often by 50-90%) and price output at several times the input rate. The 2.9x billed ratio is therefore an upper bound.
    **Fix:** add a priced column under one or two public price sheets with cached-input discounts.

## What the pending experiments (§5 TODO) must show

- **Cache pressure (1 / 2 / 6 concurrent runs, at k=8 and preferably also k=3):**
  - If A1-zc at k=8 with 1 concurrent run returns to about 0.4x computed, and B and C fall back below 1x, then the effect is *cache pressure from co-running pipelines*, not payload size. The abstract, §5's first paragraph and the conclusion's "when it does not fit" must then be reworded in terms of the concurrent working set vs KV capacity.
  - If the savings stay low even with 1 run, the paper must explain the mechanism (intra-run eviction as B's conversation grows? chunked prefill? scheduler preemption?) with hit-rate or eviction counters.
  - Either way, report accuracy across concurrency levels. It should be flat; if it moves, batching nondeterminism is larger than the channel effects.
  - Also run k=3 at 6 vs more concurrent runs. Production servers run far more than six pipelines, so it matters whether the headline 61% saving survives realistic load.
- **Fan-out at k=3 (three parallel Researchers):**
  - If A1-zc loses its savings with fan-out at k=3, then "zero-copy saves nothing" at k=16 is a *topology* effect. In that case either fix the zero-copy layout (e.g. a shared document prefix before the per-Researcher notes) or attribute the effect correctly.
  - If B drops sharply at k=3 with fan-out, then B's 34-point collapse at k=16 comes from having to find several notes files, which supports the index story but not a payload story.
  - Also report absolute A1 accuracy at k=3 with and without fan-out. "The pipe matches broadcast at k=16" may mean that broadcast degrades with fan-out or long context, not that the pipe improves; Figure 4(b) shows only differences.
  - Ideally add k=16 with a single Researcher if it fits in 32k, or k=8 with fan-out, to separate the two factors at the large-k end.

## Figures

- **Figure 1:** very good. Minor: "Own turns" (white) and "Sent" (white outline) look nearly identical, and the 8-item legend is dense. Say whether the task is typical (median-call task) or hand-picked; B's "write draft (forced)" and D's "read (no such file)" make it look like a showcase of failures.
- **Figure 2:** makes its claim at a glance. Change "same accuracy" in the annotation to "within 95% CI." Consider adding a latency panel (Weakness 2) or encoding wall time as marker size.
- **Figure 3:** (a) and (b) tell different stories (Weakness 4). In (b), "Not delivered" is an invisible yellow sliver; if it is really that small, the text should say so. Otherwise the reading-side story needs another explanation. Add CIs to (a).
- **Figure 4:**
  - B (light square) and D (light triangle) share almost the same pale blue-grey, and they are hard to tell apart in print and in grayscale. Use distinct hues or line styles.
  - There are no CIs, although the k=8/16 sample sizes are not stated anywhere.
  - There is no absolute A1 accuracy per k, so relative points cannot be interpreted.
  - k=16 is plotted on the same categorical axis as a different experiment (fan-out). The dashed divider helps, but the line segments from 8 to 16 still imply a trend.
  - Caption (b), "the pipe recovers," is an interpretation that the plot cannot distinguish from "broadcast declines."

## Questions for the authors

1. What exactly is a "run," and what does "six concurrent runs" mean? Are runs from different channels co-scheduled on the same server? If so, a channel's cached-token count depends on its co-runners. How are tasks assigned to servers and in what order?
2. How many tasks are used at k=8 and k=16, and with which datasets?
3. What is the notes file named in B, and what do the B, C and D prompts say about where the notes are?
4. Is the D handoff cap 120 words for every k?
5. In A1-zc, is the Researcher's prompt also reordered (shared documents first)? Which exact prefix does the Writer reuse, and how many tokens of it?
6. For file channels, does "reached the Writer" count facts the Writer read from source documents, or only facts read from the notes?
7. Why does C's Researcher state more facts than B's (63 vs 59) when the index cannot affect the Researcher? Is that within run-to-run noise?
8. What judge prompt was used, and is it shared across stages and channels? Was it validated against any human labels?
9. How often does the forced-write call fire, per channel and per agent?
10. Why does D's Researcher state only 50% of facts? Does writing the handoff crowd out the notes?
11. Does Qwen3-8B with thinking enabled change the file-channel results? Thinking often matters for tool use.
12. Why does C compute *more* than B at k=1 and k=8 (1.22x vs 1.07x; 1.29x vs 1.22x)? Is the index read itself the cost?

## Sentences that overclaim or are unclear

- Abstract: "This is the message-passing versus shared-memory question of operating systems." Assertive for an analogy; files accessed through model calls are neither shared memory nor cheap to access.
- Abstract: "With small payloads, copying is the most accurate channel." C is not significantly worse in 4 of 6 settings (`\nGapCSig` = 2), and the C gap ranges from -1 to 8.
- Abstract: "Once prompts outgrow the KV cache, zero-copy saves nothing." Confounded with concurrency (k=8) and fan-out (k=16); no single prompt outgrows the cache.
- Abstract: "at large payloads plain files lose 34 points while an index loses 5." This holds only at k=16 with three parallel Researchers; payload is not the only thing that changed.
- Intro: "Our key observation is that cost has to be counted three ways." The abstract and metrics define two ways (sent, computed); the third is never named or reported.
- Intro: "the classic finding is that neither wins everywhere [10, 11]." This mischaracterizes Lauer and Needham (duality) and L4 (fast IPC by design).
- Contributions: "accounts for tokens sent, tokens computed, latency, file I/O." Latency and file I/O are not reported.
- Contributions: "zero-copy ordering makes it as cheap to compute as a pipe." True for Qwen3-8B at k≤5 under the tested concurrency; for 4B it costs 3-11 points.
- §2: "Only the order changes; the engine is unmodified." The order changes the instruction position, which the 4B result shows is not semantically neutral.
- §4: "Zero-copy broadcast is within the noise of it in every dataset and k." Absence of a significant difference is not equivalence; state a margin.
- §4: "Writing to a file changes the writer: the same Researcher, given the same input..." The input is not the same (tool schemas, function-call output).
- §4: "Files lose information on both sides; an index fixes the reading side." Figure 3(b) attributes almost no wrong answers to delivery.
- §4: "C's accuracy comes within 8 points of broadcast." "Within 8" is the worst case; the pooled gap is 6 points, and C is not significantly different in 4 of 6 settings. Say that directly.
- §5: "six concurrent runs no longer fit the server's KV cache together." This is the first mention of concurrency; it belongs in §3, together with how concurrency was chosen.
- §5: "the pipe matches broadcast's accuracy (within 1 point)." Without absolute numbers this may reflect broadcast degrading, not the pipe improving.
- §5: "The 12-call limit, if anything, understates their cost." Fair, but 14-16% of runs still hit the cap at 24, so the true unconstrained cost is unknown.
- §6: "The agent analogues are the same: the prefix cache plays zero-copy, and the index plays the directory." The prefix cache deduplicates compute, not copies; the tokens are still sent.
- Conclusion: "zero-copy broadcast was the most accurate channel." A1 (72.3) is nominally higher than A1-zc (71.6); the two are tied.
- Conclusion: "When it does not fit, the pipe is the cheap choice and loses little, and a checking stage helps it more than any other channel." "Does not fit" is confounded (see Weakness 1). The checking-stage claim rests on one experiment at one k.
- Conclusion: "Share files only with an index, and only with a model that handles tools." No model that handles tools well was tested, so the second half is a conjecture.

## Verdict

This is a careful, well-presented measurement study with one memorable systems insight (sent vs computed cost inversion) and one interesting behavioral finding (writing to files shortens notes). It is a reasonable workshop paper if:
- the pending experiments disentangle cache pressure and fan-out from payload size, and the abstract is reworded to match;
- latency is reported;
- the LLM judge gets even a small validation;
- the closest prior work (KVFlow, Parrot, TOAP) is cited and the contribution is positioned as measurement rather than mechanism.

Replaying a fixed Researcher output into all channels would strengthen the information-loss section considerably at low cost.
