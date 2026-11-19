# Review: "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines" (round 2, systems reviewer)

## Summary

The paper treats how agents in a pipeline pass results as an IPC choice. A Researcher, a Writer and a Reviewer run on HotpotQA and 2WikiMultihopQA with Qwen3-8B on vLLM, under six channels: copy the whole history (A1), the same with a prefix-cache-friendly order (A1-zc), a pipe that forwards only the previous output (A2), shared files read with tools (B), files with an auto-maintained index (C), and short pushed handoffs plus files (D). Cost is counted as tokens sent (API billing) and tokens computed after prefix-cache hits (self-hosted). The main findings:

- Copying is the most accurate channel at k <= 5. A1-zc keeps that accuracy at 0.39x the computed tokens.
- Files send 1.8-4.8x the tokens but compute 0.7-1.2x.
- Files lose information on the write side (notes written through `write_file` are 27% shorter) and on the read side (Writers skip the notes).
- At large payloads (k = 16, with three parallel Researchers) the savings from the cache disappear, the pipe catches up, and plain files collapse (-34 points).

Sensitivity runs vary pipeline length, tool budget, batched reads, model size (Qwen3-4B), and include an A/A noise control. There are also two decomposition experiments: A1w separates the write side, and a replay separates the read side.

This is a careful, honest measurement paper. Several of its findings are new and useful to practitioners. Its main problems:

- It describes the experiment as varying "only the channel", but the channels also change what context downstream agents can see.
- The large-payload headline mixes three effects: payload size, a change of topology, and the tool budget.
- The fact-delivery metric is weaker than presented. The paper's own cross-checks, computed but not reported, disagree with AlignScore.
- Several sentences state ranges or framings that the macros do not support.

## Score

**3 / 5 (borderline; weak accept if the framing and metric issues are fixed).** Confidence: **4 / 5.**

## Strengths

1. **Two cost accountings.** Counting cost as both tokens sent and tokens computed is the right lens. Figure 2's two panels show at a glance that the ranking depends on who pays. This is the paper's clearest contribution.
2. **The decomposition experiments are good science.** A1w (tool-call writing with copied delivery) and the replay of fixed notes into every channel separate the write side from the read side. Few agent-communication papers do this.
3. **Practical, surprising findings.** Three stand out:
   - Writing through a tool call shortens notes (1,093-1,145 vs 1,554-1,559 characters).
   - Cheap bulk reads make the Writer skip the notes: 80% of tasks never open them, at a cost of 8-16 points.
   - Parallel Researchers clash on file names in 72-91% of tasks.

   Each is concrete and actionable.
4. **Honest reporting of the harness.** The rescue rate and the strict accuracy (B at 18.0% if rescued runs count as wrong), the tool-budget saturation, the A/A control, and the 59% identical-output rate for identical prompts are all disclosed.
5. **Paired design and a reproducible pipeline.** Every channel runs the same tasks, the paper reports bootstrap intervals over tasks, and every number is generated into macros.

## Weaknesses (most important first)

### W1. The design varies more than "only the channel"

The abstract and the introduction say the paper changes "only how the Researcher's and Writer's results reach the next agent". By §2, the channels also change whether downstream agents see the **source documents**:

- In A1 and A1-zc, the Writer and the Reviewer get all documents in the prompt.
- In A2 they get none.
- In B, C and D the documents become files that must be fetched with tool calls.

So A1 vs A2, and A1 vs B, mix the transport (copy vs file) with the scope of context (notes + documents vs notes only). The paper's own explanation of the pipe's loss says as much: the Reviewer "sees only the draft", against "notes and documents". That is a statement about scope, not about IPC.

Figure 3a has the same problem. It shows A1's "Reached Writer" at 45%, but A1's Writer also holds every supporting sentence verbatim in its prompt.

**Fix.** Either restate the claim ("the channel determines both the transport and what context each agent can see"), or add the missing cells of a 2x2 design:

- B with the documents still in the prompt, so only inter-agent results go through files.
- A2 with the documents.

A1w and the replay already cover half of this design. Two more channels at k = 3, with 200 tasks each, would make the IPC framing honest.

### W2. The large-payload result mixes three effects, and its cache claim depends on the harness

The abstract says that "once prompts outgrow the KV cache, zero-copy saves nothing and a pipe matches copying… at large payloads plain files lose 34 points while an index loses 5". All of this comes from k = 16, which differs from k <= 8 in three ways at once:

- **Topology.** Three parallel Researchers instead of one.
- **Budget.** The tool budget binds (52% of B's Reviewers exhaust it). The paper itself concludes that "the large-payload collapse is that of B under this budget".
- **Sample size.** n = 60 tasks, a number not stated anywhere in the paper.

The race analysis also shows that the clash barely moves accuracy: B answers 38% with a clash vs 41% without one.

At k = 8, the one point where payload changes alone, the picture is milder:

- A1-zc still saves 17% (0.83x).
- The pipe loses a significant 3 points (interval 1.3-4.6).
- B loses 8 points, as it does at k <= 5.

"Outgrowing the cache" is also a property of the harness: six tasks run concurrently on one 34,864-token cache, interleaved across channels. A single pipeline at k = 8 likely fits. The source still has `% TODO(numbers pending): cache pressure (1/2/6 concurrent runs)`.

**Fix.**
- Run the concurrency sweep (1, 2 and 6 concurrent tasks) at k = 8 and report the computed ratio for each.
- State n = 200 for k = 8 and n = 60 for k = 16.
- Rewrite the abstract so the -34 points are attributed to "three parallel writers under a 12-call budget", not to payload size.
- In Figure 4, break the lines at the k = 16 separator.

### W3. The fact-delivery metric (AlignScore) is validated only on easy, verbatim pairs, and the cross-checks the paper ran disagree with it

**What the validation covers.** The 450 synthetic pairs keep, drop, or entity-swap a sentence copied from the documents, so they test only verbatim matching. Real notes are abstractive.

**Real-output cross-checks.** The artifacts include `alignscore_validation.json`, which compares AlignScore on 864 real facts against two other measures:

| AlignScore compared with | Agreement | Cohen's kappa |
| --- | --- | --- |
| Qwen judge | 62% | 0.29 |
| Lexical match | 77% | 0.54 |

AlignScore says "yes" for 39% of the facts. None of these numbers appear in the paper.

**Absolute levels differ widely.** For A1's notes at k = 3:

| Measure | A1 notes recall |
| --- | --- |
| AlignScore | 45% |
| Entity match | 91% |
| LLM judge (`JNotes`) | 73% |

**Entity match does not rank the channels the same way.** The paper says it does, but this holds only for message channels vs file channels:

| Measure | Notes recall, file channels | Delivery |
| --- | --- | --- |
| AlignScore | B 32 > C 30 > D 25 | D 46-54% |
| Entity match | C 85 > D 83 > B 82 | D 94% |

The D-delivery gap matters most. The narrative that D's Writer "trusts the handoff and opens even less" rests entirely on AlignScore. Compressed 120-word handoffs are exactly the kind of text where entity mentions survive but sentence-level entailment fails.

**Fix.**
- Hand-label about 150-200 real (fact, text) pairs drawn from the notes and the handoffs, and report AlignScore's precision and recall on them.
- Report all three measures side by side, in a small table or an appendix row.
- Delete "it ranks the channels the same way", or restrict it to "message vs file channels".

### W4. The stage attribution is dominated by the order of the checks and disagrees with the text

A wrong answer is blamed on the Researcher whenever its notes miss any supporting fact, and that check runs first. But the notes miss 50-75% of the facts under AlignScore, so almost every error lands in "Researcher missed". Figure 3b shows this: "Not delivered" is about 1% for every file channel, D included, even though D delivers only about 52%.

This also contradicts the read-side story the text tells ("files lose information on both sides"). By Figure 3b, reading costs almost nothing. By the replay experiment it costs 5 points. Both cannot be right under the same metric.

**Fix.**
- Report the base rate: how many *correct* answers would also be labeled "Researcher missed"?
- Use the replay experiment as the counterfactual attribution, since it holds the notes fixed.
- At minimum, state in the caption that the attribution is ordered and conservative toward the Researcher.

### W5. The novelty of the headline technique is limited, and the IPC analogy is looser than claimed

A1-zc puts the shared history first and the instruction last. That is the standard advice for prefix caching (provider prompt-caching documentation, the rationale behind Parrot and KVFlow), and the paper calls it "the simplest member of this family". Yet the abstract and Figure 2 present it as the main positive result.

The IPC analogy also breaks at an important point. Agents have no real shared memory, because every file read is a copy into the context. The real analogue of shared memory is KV sharing (KVCOMM, TokenDance, CacheBlend-style non-prefix reuse), which the paper does not evaluate.

The new parts are the measurement findings:
- the write-side effect of tool calls,
- read-side skipping, and how an index or batched reads change it,
- file-name races between parallel writers,
- the inversion between the two cost metrics.

**Fix.**
- Recast the contributions around these findings, and treat A1-zc as the strong baseline that every comparison should beat.
- Say explicitly where the OS analogy fails.
- Add related work on OS-style agent systems (MemGPT/Letta, AIOS) and on position-independent KV reuse (CacheBlend, EPIC). The latter would make even plain A1 cheap regardless of order.

### W6. The file channel may be a weak (strawman) implementation, and the paper's own recommendation goes unmeasured

The harness rescue does a lot of work in B:

- B's Writer is rescued in 59% of runs, 53% because it "answered in its reply instead of the file".
- B's Reviewer is rescued in 34% of runs.
- Without rescue, B scores 18.0%.

The model is often not following the file protocol at all. The conclusion recommends "let agents write long results as plain replies and have the system store them", which describes a system-mediated file channel. That design is never run.

**Fix.** Add a channel E in which:
- the harness stores each reply as a file, and
- the harness dereferences pushed handles itself, so no model-driven reads are needed.

This channel also separates two things the paper currently conflates: shared storage as a design, and access to files driven by the model.

### W7. Concurrency confounds both computed tokens and latency

Six tasks run concurrently, interleaved across channels, and share KV capacity. `cache_salt` prevents sharing between channels, but not eviction across them. A channel's hit rate therefore depends on its neighbors: A1's 5k-token prompts can evict B's per-call prefixes.

Latency is measured "under the shared load", and A1-zc's wall time is **1.1x** broadcast (`\nWallAZc`). The paper reports wall times for every channel except A1-zc. That omission matters, because A1-zc is the channel the paper recommends for its lower compute.

**Fix.**
- Report A1-zc's latency and explain it.
- Measure computed tokens and latency for each channel in isolation, at concurrency 1, on a subset.

### W8. The conclusion's rules overgeneralize beyond the evidence

- "Zero-copy broadcast matched the most accurate channel." It cost Qwen3-4B 3-11 points, significant in 3 of 4 settings. The rule should depend on the model, and the abstract should say so.
- "When it does not fit, the pipe is the cheap choice… and a checking stage helps it more than any other channel." The checking-stage experiment ran at k = 3, where the history *does* fit.
- The evidence covers one model family, one task family, and single runs per (task, channel).

**Fix.**
- Add one non-Qwen model, for example Llama-3.1-8B at k = 3 with the six channels.
- Scope each rule to the regime in which it was measured.

### W9. Statistical reporting is uneven

- Figure 2 shows unpaired 95% intervals, which overlap even where the paired differences are significant. Figure 4 has no intervals at all, although the data file contains them.
- The B vs C difference is never tested, yet "an index helps" depends on it: pooled at k = 3 it is 62.8 vs 66.3.
- Many sub-experiments run on 100-200 tasks, with no correction for multiple comparisons.
- The A/A control bounds mean shifts at about 2 points. Several reported effects are at or below that:
  - tool budget: <= 3 points;
  - other channels in the chain experiment: <= 1 point;
  - A1-zc vs A1 notes recall: 50 vs 45, from a Researcher whose prompt differs only in order.

**Fix.**
- Plot paired differences, or add them to Figure 2.
- Add the intervals to Figure 4.
- Report B vs C with an interval.
- Soften "the effects we report are larger than this noise".

### W10. Cost accounting is incomplete

The introduction says that "cost has to be counted three ways" but names only two.

Real APIs bill cached input at a discount (roughly 10-50% of the full price). That gives a concrete third, dollar-cost axis, which would place A1-zc and the file channels between the two panels of Figure 2.

Prefill FLOPs are not linear in tokens, and decode time is not counted.

**Fix.**
- Name the three ways explicitly.
- Add a dollar-cost column under one or two published pricing schemes.

### W11. Figure issues

- **Fig. 1.**
  - It omits A1-zc, the channel the paper promotes most, which would show the shared history as pale (reused) blocks.
  - "Own turns" and "Sent" are both white legend swatches.
  - The caption does not point out that B's Writer never opens the notes in this example, which is the paper's read-side point.
  - "(forced)" is not explained.
- **Fig. 2.**
  - The claim reads in three seconds.
  - The intervals are unpaired (see W9).
  - A1-zc and A2 overlap at about 4.7k in panel (b). Consider offsetting their labels.
- **Fig. 3a.**
  - The y-axis runs to 100% while every bar stays under 50%.
  - "Reached Writer" for A1 and A1-zc ignores the documents in their prompts (W1).
  - A1-zc's 50 vs A1's 45 is unexplained in the text.
- **Fig. 3b.**
  - "Not delivered" is invisible.
  - The panel undercuts the read-side narrative (W4).
- **Fig. 4.**
  - Lines connect k = 8 to k = 16 across a change of topology.
  - There are no intervals.
  - The relative axis hides that A1 itself stays flat: 74, 72, 70, 70 and 72% at k = 1, 3, 5, 8 and 16. The flat A1 is what makes "the pipe recovers" true, so state it.

## Questions for the authors

1. How many tasks are at k = 8 and k = 16, and why does k = 16 need three Researchers? Does 160 paragraphs exceed the 32k context?
2. Is A1-zc's 1.1x wall time an effect of the interleaving, or of longer outputs when the instruction comes last?
3. What does AlignScore score on hand-labeled real notes and handoffs? Why is the cross-check on 864 real facts (kappa 0.29 against the judge, 0.54 against lexical match) not reported?
4. Of the *correct* answers, what fraction would the attribution rule label "Researcher missed"?
5. How are the six concurrent tasks assigned to channels, and how many servers ran the main experiment? What is each channel's cache hit rate at concurrency 1?
6. Is the B-C accuracy gap at k = 3 significant? What is its paired interval?
7. With Qwen3-4B, is C significantly *worse* than B anywhere? Its worst gap (35) is larger than B's (29).
8. In the fan-out experiment, broadcast itself loses 6 points (-11 to -1) with three Researchers. Net of that, what is B's race-specific loss?
9. How long must a prediction be to count as "short" in the accuracy rule, and how much does that rule contribute compared with exact match or F1 alone?

## Quoted sentences that overclaim, are unclear, or mismatch their numbers

1. **Abstract:** "Once prompts outgrow the KV cache, zero-copy saves nothing and a pipe matches copying at 0.37× its compute; at large payloads plain files lose 34 points…"
   - All of this is k = 16, which has three parallel Researchers, n = 60, and a binding budget (W2).
   - At k = 8, where the cache is also exceeded, zero-copy still saves 17% and the pipe loses a significant 3 points.
2. **Methods:** "Qwen3-8B used as a judge accepts nearly everything (100, 78, 41%)".
   - In `judge_synthetic.json` these numbers are accuracies, not acceptance rates. The judge rejects 78% of the dropped facts, so it accepts 22% of them and 59% of the swapped ones. "Nearly everything" is wrong for the dropped facts.
   - Say instead: "accepts 22% of removed facts and 59% of swapped ones".
3. **Methods:** "…by exact string… it ranks the channels the same way."
   - Entity match ranks the file channels C > D > B for notes (AlignScore: B > C > D).
   - It puts D's delivery at 94%, against 46-54% under AlignScore (W3).
4. **Introduction:** "Our key observation is that *cost has to be counted three ways*". Only two ways are defined.
5. **Results:** "C's accuracy comes within 8 points of broadcast (66.3% vs 72.3%), while B loses 6–14 points."
   - "8" is C's worst gap in a single setting (`\nGapCMax`), but it is placed beside the pooled values, whose gap is 6.0.
   - Use one convention. Better, report C vs B directly.
6. **Results:** "More than half of B's loss therefore comes from asking the model to write its result as a tool-call argument".
   - The point estimate is 4.7 of 7.8 points (60%).
   - But the A1w-B interval is 0 to 6, so "more than half" is not established at 95%.
7. **Section heading:** "The tool call, not the file, shortens the notes." A1w still writes a file through `write_file`, so the experiment cannot separate the tool call from the file. It separates writing from reading.
8. **Results:** "a task takes 1.8× (B), 1.7× (C), and 1.4× (D) broadcast's 31 s…, and the pipe 0.9×." This omits A1-zc's 1.1×, the channel the paper recommends (W7).
9. **Sensitivity:** "The race comes from the parallel writers, not from the payload: … B answers -10 points (-15 to -5) relative to one Researcher".
   - Broadcast also loses 6 points (-11 to -1, `\nFanAOneDiff`) when it moves to three Researchers. The race-specific loss is therefore about 4 points.
   - "Answers -10 points" is also awkward wording.
10. **Sensitivity:** "Part of the collapse happens before anyone reads." With a clash B answers 38%, and without one 41%. The clash barely moves accuracy, as the next sentence half-admits.
11. **Sensitivity, Qwen3-4B:** "the file channels fall far behind broadcast: B by 21–31 points and C by 19–35 at three and five questions."
    - B's 21-31 is the range over **all k** (`\nSmallBGapMin/Max`).
    - At k = 3 and 5 the range is 22-29 (`\nSmallBGapMinThreeFive/MaxThreeFive`), while C's 19-35 does use the k = 3, 5 macros. The same sentence uses two conventions.
12. **Sensitivity, Qwen3-4B:** "Handles lose 5–15 points, and the pipe at most 4 at three and five questions."
    - Handles' 5-15 is the all-k range; at k = 3 and 5 it is 5-12.
    - The pipe's "at most 4" is restricted to k = 3, 5. At k = 1 the pipe loses up to 13 (`\nSmallATwoGapMax`), which goes unmentioned.
13. **Sensitivity, Qwen3-4B:** "The index helps less".
    - C's worst gap (35) exceeds B's (29), and C exhausts its tool budget more often (19-35% vs 13-19%).
    - The index may hurt here. Say so, or test C vs B.
14. **Sensitivity:** "the effects we report are larger than this noise." Not true of several reported effects of 3 points or less (W9).
15. **Results:** "Its tokens sent stay those of broadcast (13.6k)."
    - A1 sends 13.3k; A1-zc sends 3% more (the extra instruction message) and 15% more at k = 1 (`sent_rel` 1.15).
    - Say "about those of broadcast".
16. **Conclusion:** "When it does not fit, the pipe is the cheap choice and loses little, and a checking stage helps it more than any other channel." The checking-stage result was measured at k = 3, where the history fits.
17. **Conclusion:** "zero-copy broadcast matched the most accurate channel". This holds for Qwen3-8B only. It cost Qwen3-4B 3-11 points, a fact the abstract also omits.
18. **Introduction, contributions:** "with 150 paired tasks per condition". This holds for k = 1, 3, 5 per dataset only. The sub-experiments use 60-200 tasks, so state the n per experiment.
19. **Section 2:** "Every Researcher receives the same user message". True of the user message, but A1-zc's Researcher gets a different system/instruction order, and its notes differ: 50% vs 45% facts recall in Figure 3a. Say so, because it means A1-zc is not "only an order change" for the Researcher.
20. **Typography:** the paragraph header renders as "IPC.." with a double period (`\paragraph{IPC.}`).
21. **Harness:** "(mostly, 53%, a Writer that answered in its reply instead of the file)". It is unclear whether this is 53% of all runs or of rescued runs. The code computes it over all runs.

## What would move this to a clear accept

1. Run the two missing channels from W1 (B with documents in the prompt, A2 with documents), or reword the "only the channel" claim.
2. Rewrite the large-payload claim (W2) and run the concurrency sweep.
3. Hand-validate AlignScore on real outputs and report the three measures honestly (W3).
4. Add the system-mediated file channel E (W6).
5. Fix the macro-to-sentence mismatches listed above.
