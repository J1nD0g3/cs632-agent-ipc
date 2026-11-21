# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6 pages)

## Summary

The paper compares five ways of passing results between the agents of a fixed Researcher-Writer-Reviewer pipeline: copying the whole conversation (A1, broadcast), broadcast with the shared history placed first so the prefix cache reuses it (A1-zc, "zero-copy"), passing only the previous output (A2, pipe), shared files accessed through tool calls (B), and files plus an auto-maintained index and a heading rule (C). Qwen3 models (4B-32B) run on vLLM v0.33.0 over bundled HotpotQA/2Wiki questions (k = 1-16 per task). The paper reports these main findings:

1. The channels rank differently by prefill than by tokens sent. At k = 3, B sends 2.9x broadcast's tokens but computes 0.79x its prefill. Zero-copy cuts broadcast's prefill by 61%, and its accuracy difference has a 95% CI of -2.9 to 1.4 points.
2. A 2x2 "crossed" design (how the Researcher writes notes x how later agents get them) shows that, on tool-written notes, file access costs 8-22 points at 4B, 14B and 32B (Holm-corrected). It is not significant at 8B.
3. At k = 8, three Researchers sharing one folder lose 21.2 points against one Researcher, and per-Researcher folders recover 19.8 of them.

Sensitivity sections vary the KV-cache size, payload, tool budget and model size. The paper concludes that, under this harness, Qwen3 agents whose state fits in the context should copy the conversation forward.

This is a careful and unusually honest measurement paper. It uses paired designs, reports intervals everywhere, Holm-corrects its tests, and names its post hoc choices. All the numbers I checked against `numbers.tex` match the text. My concerns are about what the headline accuracy effect actually measures, and whether the main model's story holds together. Prefill is used as the cost metric, yet decode dominates time. The recommendation also overreaches what the data show.

## Score and confidence

- **Score: 3 / 5** (borderline, leaning weak accept). The method is solid for a workshop and the honesty is commendable. However, the headline accuracy claim is entangled with harness behaviour (the rescue, the tool budget, output-file obligations), and the arm that would separate these was run but is not reported.
- **Confidence: 4 / 5**

## Strengths

- **S1. Controlled, paired design.** The same tasks run on every channel, each pipeline gets its own `cache_salt`, channels are interleaved on each server, and there are explicit controls: a documents control, a replay control, a rerun, and the crossed 2x2. This design is much better than the usual "framework X vs framework Y" comparison.
- **S2. The crossed 2x2 is the right tool.** It avoids order-dependent stepwise attribution. Reporting the interaction (which equals row 4 minus row 3, and also row 2 minus row 1; I checked) is good practice.
- **S3. The "told runs" are a clean causal probe.** Naming `notes.md` raises the 32B Writer's open rate from 26% to 86% and accuracy by 14.2 points (10.2 to 18.4). The paper also honestly reports that the same pointer does nothing at 14B. The finding that a 14B Writer ignores an explicitly named file is interesting and actionable for agent-runtime designers ("discoverability" of shared state).
- **S4. Honest scoping.** Post hoc tests are labelled, cross-run comparisons are marked, the equivalence margin is admitted to be post hoc, and the conclusion lists the open questions. The abstract reports the 95% CI rather than leaning on the post hoc equivalence test.
- **S5. Cache-capacity sensitivity.** The paper reports zero-copy at 0.36x with 100k- and 400k-token caches against 0.85x with a 35k cache, and shows the file channels flipping from 0.60x to 1.22-1.29x. This is a useful systems point: a channel's prefill depends on who else competes for the cache.
- **S6. Figure 2 is good.** It is one glance, with the -61% arrow and the paired CI on it, and the caption correctly warns that the whiskers are unpaired.

## Weaknesses (most important first)

### W1. The "files cost accuracy" headline is largely a harness and rescue effect, and the arm that would show this is unreported

Fix type: **text/analysis only** for the reporting. **Needs new runs** for a clean test.

The paper's evidence:

- **4B:** 100% of file-channel tasks needed the rescue (Table 1, "Rescued" row 100/100), so the -22.0 at 4B measures "4B cannot follow the write-file protocol plus forced-write fallback", not file access.
- **14B and 32B:** "most of the cost sits in rescued tasks, where files trail copying by 11.3 and 15.1 points, compared with 1.0 and 3.1 on the others." On the tasks where agents follow the protocol, the file channel costs about 1-3 points.
- **Main run:** 215 of 300 B tasks (72%) and 198 of 300 C tasks (66%) have some rescued agent (`nRTwelveMainRescNB`/`NC`). The text reports only the per-role range "34-59%". In addition, 34% of B tasks exhaust the 12-call budget, and 22 of 300 B Researcher calls hit the token cap, against 1 for broadcast.

So B and C as measured are mostly "rescued" channels. In addition, the crossed design does not separate *reading inputs through tools* from *being obliged to write outputs through tools*. The copy arms reply, whereas the file arms must write `draft`/`final.md`, and the rescue fires on the output side.

§2 says the authors ran "a variant of B whose Writer and Reviewer reply instead of writing files" but do not report it. That is exactly the control that isolates input access from output protocol.

Finally, the main-run sentence "rescued tasks are about as accurate as the others (62.5% against 63.5%)" is an unpaired comparison. It conflicts in spirit with the crossed-run analysis, which finds that rescued tasks carry the cost.

**Fixes:**

1. Report the reply-variant of B, even as a single sentence with its paired gap.
2. Report the any-agent rescue rate and a *paired* rescued/non-rescued decomposition against broadcast for the main run, as is already done for the crossed runs.
3. Rephrase the headline as what it is: "file-based protocols induce tool-protocol failures (missed writes, exhausted budgets) whose fallback costs accuracy."
4. Ideally, rerun one crossed size with (a) a larger budget and cap at k = 3 and (b) the reply-output variant, to show how much remains.

### W2. The main model (Qwen3-8B) story does not hold together

Fix type: **text/analysis only**, plus **needs new runs** for the cap check.

The abstract and intro lead with 8B, but the crossed runs, which are offered as the explanation of why files lose, show no significant file-access cost at 8B:

- copy→files, tool-written notes: -2.9 (-6.2 to 0.4)
- copy→files, reply: -5.1, not Holm-significant

The 8B loss in the wording/crossed data comes mostly from the *Researcher's tool-call write* (-4.7 / -5.6, with fact coverage falling from 43% to 32%), not from file access.

Meanwhile, B's 8B gap to broadcast varies across runs:

| Run | GPU | Cap | B gap to broadcast (points) |
| --- | --- | --- | --- |
| Main run | RTX 3090 | 2,048 | 7.8 |
| Size runs | RTX PRO 6000 | presumably 2,048 | 10.0 |
| Wording run | RTX PRO 6000 | 4,096 | 6.4 |
| Crossed tool-file vs reply-copy | RTX PRO 6000 | 4,096 | 7.5 |

The cap, the GPU and the Researcher wording all vary across these, and "We did not measure drift across GPUs or token caps." A reader cannot tell what explains the 8B main-run gap.

**Fixes:**

1. Add one explicit sentence: "At 8B, B's loss comes mostly from the tool-call write, not from reading files."
2. Make the abstract's "three of four sizes" sentence not read as if it explains the 8B result in the previous sentence.
3. Run A1 and B at 8B with caps of 2,048 and 4,096 on the same GPU to bound the cap effect.

### W3. Prefill is the cost metric, but it barely matters for time here, and its measurement may undercount under memory pressure

Fix type: mostly **text/analysis only**. The preemption check may need server logs.

**Decode dominates time.** Decode is 96% of broadcast's summed prefill+decode time. A 61% prefill cut therefore saves about 2-3% of time, and zero-copy's 1.2x longer outputs more than eat that (run 1.09x, median task 0.99x). At 32 tasks at a time, its median task takes 0.82x but its batch 1.00x. These come from two runs, with no interval reported, and the paper does not say why only two of the three alone-runs have per-request counters.

**The cost argument needs real prices.** The paper's cost case therefore rests on API pricing. However, "tokens sent" sums prompt and completion tokens equally, and ignores both cached-input discounts and the higher output-token price.

**Possible undercount.** On the RTX 3090 servers the KV cache holds 34,864 tokens with a 32,768-token context and six concurrent tasks. This is a memory-starved regime where vLLM v1 preemption (recompute) is likely. `cached_tokens` per response does not count recomputation after preemption, so "tokens computed" may undercount, especially for B and C at k = 8 and 16.

**The ranking depends on the cache.** The first observation (B computes 0.79x broadcast's prefill) depends on this regime. At k = 8, B is 1.22x on the 35k cache and 0.60x on 100k.

**Fixes:**

1. Report vLLM's preemption counts for the 3090 runs.
2. Report measured prefill *time* alongside tokens. `numbers.tex` already has `RSixPrefillTimeAZc` = 0.49.
3. Add a priced cost table under one or two representative price sheets (input, cached input, output).
4. Give run-to-run spread for the 32-concurrency timing.
5. Move the "decode dominates" fact into the abstract or intro, so readers calibrate what "-61% prefill" buys.

### W4. The recommendation and several framing claims overreach the numbers

Fix type: **text/analysis only**.

**"Copy the conversation forward" ignores the pipe.**
- In the size runs, the pipe ties broadcast at 14B (0.0) and 32B (1.2).
- At k = 16 on the 3090s, the pipe stays within 0.5 points while computing 0.37x the prefill.
- The pipe sends about 0.4x the tokens.

For larger models, then, the data suggest "copy only what the next agent needs" may be as good and much cheaper. In addition, zero-copy loses 7.0 points at 4B, so "copy forward" with the zero-copy layout is not universally safe.

**C is close to broadcast at 8B.** C is *not* significantly below broadcast in four of six 8B settings (gap -1.3 to 8.4), so "files cost accuracy" is mainly a B result at 8B.

**"We vary only this choice, the channel" (abstract) is too strong.** All of the following change with the channel:
- the Researcher's instructions differ across channels (wording alone moved 4B accuracy by 6.2 points);
- zero-copy moves the role instruction to the end of the prompt (outputs change by 1.2x, and accuracy drops 7 points at 4B);
- file channels add an output-writing obligation and the rescue.

**Fix:** scope the conclusion by model size, give the pipe its due, and soften the "vary only" sentence.

### W5. Novelty and systems contribution are thin, and the IPC lens is mostly decorative

Fix type: **text/analysis only**, or **needs new runs** for a system contribution.

**Zero-copy is not new.** It is the shared-prefix layout that Prompt Cache, Parrot and KVFlow already assume, as the paper says. The new piece is its measured accuracy cost (none at 8B and above, -7 at 4B, unexplained).

**The fan-out result is a write-collision bug.** The k = 8 fan-out loss comes from Researchers overwriting each other's files: 99% of tasks had colliding paths, and 58% kept only one Researcher's notes. Any namespacing fixes this, and the paper's own fix (per-Researcher folders) confirms it. Making it a headline finding in the abstract and intro oversells a harness property.

**The IPC lens adds labels, not leverage.** Mapping the index to a directory, folders to namespaces, and the write guard to `O_EXCL` adds labels but no leverage. There is no design that follows from the analogy, and Lauer-Needham duality is invoked but never used.

**"Zero-copy" is a misnomer.** The tokens are copied and sent, and only recomputation is avoided; the paper itself says so.

**Fixes:**

1. State the contribution as a measurement plus a short list of concrete runtime rules: put shared history first; namespace concurrent writers; make shared state discoverable (the told-run result); budget tool calls with the rescue in mind.
2. Demote the fan-out collision from the abstract.
3. Consider renaming zero-copy (e.g., "prefix-shared broadcast").
4. A small system contribution would lift the paper substantially. One example is a file channel whose `read_file` results are placed into a shared, cacheable prefix, combining files' selectivity with zero-copy's reuse.

### W6. The fact-coverage measure is too weak for the claims made with it

Fix type: **needs new annotation** (no GPU runs).

AlignScore separates synthetic kept/removed sentences well (AUC 0.996), but on real notes it agrees with a Qwen3-8B judge only at kappa = 0.29. Neither of these is a gold standard. Yet coverage carries substantive claims:

- "B's notes state 32% of the supporting facts, compared with broadcast's 45%"
- "Fact coverage falls at the same sizes, from 43% to 32% at 8B"
- Figure 3a and its caption claim

Figure 3a has only per-bar intervals, no paired test.

The paper should also say whether coverage for tool-written notes counts every file the Researcher wrote. At 14B, 79% of tool-written notes are saved under `docs/`.

**Fixes:**

1. Human-label about 150-200 (sentence, notes) pairs and report AlignScore's precision and recall against the human labels, with the threshold chosen on them.
2. Add paired tests for the coverage claims.
3. Otherwise, present coverage strictly as a weak secondary signal.

### W7. Too many runs, configurations and cross-run comparisons for a reader to track, and one undisclosed bug

Fix type: **text/analysis only**, plus a small **new run** for GPU drift.

The paper uses about twelve distinct runs:
- main run, documents control, replay control, rerun;
- size runs and the 32B rerun;
- wording run, crossed runs, told runs;
- alone-timing runs and 32-concurrency runs;
- k = 8 fan runs, k = 16 repair runs, budget runs, KV runs.

These span two GPU types, two token caps and three KV sizes, all introduced in one dense "Runs" paragraph.

"At 32B, B and C come from a rerun that fixes a harness bug": the bug is not described, and the reader cannot tell whether it touched other runs (e.g., the rescue path or the crossed runs). The size-run B and C values at 32B (rerun) are never shown, only folded into a range.

**Fixes:**

1. Add a compact run table (run, GPU, KV, cap, k, sizes, channels, tasks, section where used). Space can come from W9 and W10 trims.
2. Describe the 32B bug in one sentence and state its scope.
3. Measure one A1/B pair on both GPU types to bound cross-GPU drift. This is needed because results-section explanations rely on PRO 6000 runs to interpret the 3090 main run.

### W8. Selective reporting of two channels that were run

Fix type: **text/analysis only**.

The handoff channel (D) is mentioned as "run but not reported", yet its numbers exist and are interesting as a middle ground:
- 65.1% accuracy;
- 1.3x broadcast's tokens and 0.59x its prefill;
- gap to broadcast of 2.0-11.9 points, significant in four of six settings.

The B reply-variant is in the same position (see W1). Omitting completed arms without a reason invites a selection reading.

**Fix:** give one sentence each with the headline numbers, or explain why they are out of scope.

### W9. Statistical presentation issues

Fix type: **text/analysis only**.

**The second Holm family's "DvW" contrast is hard to interpret.** The text describes it as "this cost exceeds the tool-call write's cost on copied notes by 13.3 points". It equals (FT - CT) - (CT - CR) = FT - 2CT + CR, a comparison of two simple effects from different baselines. It is post hoc, does not appear in Table 1, and its meaning is unclear. Either define it plainly and say why it matters, or drop it; the interaction already makes the point.

**Other issues:**
- The bootstrap resampling unit (task vs question) is not stated.
- Per-setting significance counts are uncorrected and the settings share questions; this is disclosed, but the counts still headline paragraphs.
- The equivalence margin (+/-3 points, chosen after the run) adds little and can be cut.
- The timing ratios have no intervals.

### W10. Figures and Table 1 do not all make their claim at a glance

Fix type: **text/analysis only**.

- **Figure 3:** the key comparison (tool-written, copied vs tool-written, file channel) sits in non-adjacent bars (2 vs 4). Reorder so that each writing mode's copied/file bars are adjacent, or annotate the deltas on the bars. Panel (a) relies on the weak coverage measure (W6).
- **Figure 4a:** the subtitle "savings fade as payloads grow" is false for the pipe, which stays at 0.37-0.41x throughout. It also renders on page 6, after §5 has discussed it on page 5.
- **Figure 4b:** the pipe's gap shrinks from -10 points at k = 3 to -3 at k = 8 and -0.5 at k = 16. This is never discussed, but it supports W4.
- **Table 1:**
  - The interaction row is derivable (row 4 minus row 3), and the second-family DvW tests are not shown although the bold† legend refers to that family.
  - The "Rescued (%)" row is the most decision-relevant line (W1) but is visually the least prominent.
  - The caption cites "(§3)" for the further tests while §3 cites "(§4)".
- **Figure 1:** B's and C's Reviewer is drawn reading only `draft`, and B's Writer only `d01..d30`. In fact any agent can read any file. The figure should show the reads that matter, including the Writer reading notes.

### W11. Clarity and writing

Fix type: **text/analysis only**.

**Density.** The prose is grammatical and mostly careful, but very dense: many sentences carry 3-6 numbers with intervals, and the run vocabulary piles up ("wording run", "told runs", "stored reply", "rescue", "crossed arms").

**Setup before use.**
- "Wording run" is introduced in §3 before the reader knows what wording effect it isolates; name it by purpose (e.g., "Researcher-prompt control").
- The "Run-to-run noise" paragraph underpins every comparison and belongs in Methodology, not at the end of Sensitivity.

**Structure.** The crossed runs across four sizes are in Results, while the size runs are in Sensitivity. Consider one "Model size" subsection.

**Specific sentences.**
- The §3 Harness sentence about `final.md` ("which happens in the main and crossed runs for at most one task per channel at k = 3 and at most seven of 300 at any k") is hard to parse. The crossed runs have 150 tasks, so which run does "seven of 300" refer to?
- "B's and C's runs take 1.80x and 1.56x as long, as their agents generate…" uses an ambiguous "as" (causal vs temporal); write "because".
- "Fact coverage falls at the same sizes" leaves "same" ambiguous (the significant size, or all three with point losses?).

## Questions for the authors

1. What does the unreported "B with replying Writer/Reviewer" variant show against broadcast and against B, at 8B and at one larger size?
2. In the main run, what is the paired gap to broadcast on rescued vs non-rescued B tasks, rather than the unpaired 62.5% vs 63.5%?
3. What explains B's 7.8-point gap at 8B in the main run, given that file access costs only -2.9 (n.s.) at 8B in the crossed runs? How much is the 2,048-token cap?
4. How many preemptions did vLLM record on the 34,864-token 3090 servers at k = 3, 8 and 16? Does "tokens computed" include recomputation after preemption?
5. What was the 32B harness bug? Did it affect any other run, in particular the rescue or the crossed runs?
6. Why do only two of the three alone-timing runs have per-request counters? What is the spread of the 0.82x median at 32 tasks at a time?
7. In the 14B stored-reply arm, every file-channel task needed the rescue (100%). What do the Writer and Reviewer do instead of writing? Is the 30-point loss there a protocol failure rather than a missing pointer?
8. Does fact coverage for tool-written notes include every file the Researcher wrote, including those under `docs/`?
9. Why does zero-copy generate 1.2x broadcast's output tokens? Is a variant that keeps a role-neutral system prompt first (and only a short role tag last) closer to broadcast's behaviour, especially at 4B?
10. Why does the pipe's gap to broadcast shrink from about 10 points at k = 3 to 0.5 at k = 16 (Figure 4b)?
11. What is the bootstrap resampling unit?

## Quoted sentences that overclaim, are unclear, or mismatch their numbers

1. **Abstract: "We vary only this choice, the channel."** This overclaims. The Researcher's wording, the instruction position (zero-copy), the output-writing obligation and the rescue also vary; §2 itself admits the wording difference.
2. **Abstract: "Shared files send 1.8–4.8× broadcast's tokens, but the prefix cache absorbs most of the resending."** This holds at k ≤ 5 on these servers. At k = 8 on the 3090s, B and C compute 1.22x and 1.29x broadcast's prefill, so the cache does not absorb it. Scope the sentence.
3. **Abstract: "moving later agents from copying to tool-call file access costs 8–22 accuracy points at three of four Qwen3 sizes."** At 4B, 100% of these tasks are rescued. At 14B and 32B, non-rescued tasks lose only 1.0 and 3.1 points. The sentence attributes to "file access" what is mostly protocol failure plus fallback (W1).
4. **Abstract: "At eight questions, files without an index lose 21.2 points when three Researchers share one folder instead of one."** This is cross-run, and the mechanism is Researchers overwriting each other's files (99% collisions). Say so, or drop the sentence from the abstract.
5. **Abstract and Conclusion: "Qwen3 agents whose state fits in the context should copy the conversation forward."** The pipe ties broadcast at 14B (0.0) and 32B (1.2) at about 0.4x the tokens, and zero-copy loses 7.0 at 4B. The recommendation should depend on model size.
6. **Intro: "Our second observation is that files cost accuracy even when the notes are written the same way."** This is not significant at 8B, the model the rest of the intro is about.
7. **§4 heading: "Zero-copy shortens the median task at 32 tasks at a time but not at six."** It rests on two runs and has no interval. It is also awkward: mix of numeral and word, and "at … at".
8. **§4: "Zero-copy thus pays off when uncached prompt tokens cost more than cached ones or when per-task latency under heavy load matters."** The first clause is tautological. The second rests on a single 0.82x figure without spread.
9. **§4: "the significant interaction makes this loss specific to the stored reply."** Tool-written notes also lose 8.9 and 8.2 points in the file channel at 14B and 32B. The interaction shows that the loss is *larger* for the stored reply, not *specific* to it.
10. **§4 heading: "At 32B, the stored reply loses because later agents are not told where it is."** Naming the file recovers 14.2 of the 20.4-point copy→files loss, and the comparison is cross-run against the crossed run. Write "largely because".
11. **§4: "rescued tasks are about as accurate as the others (62.5% against 63.5% for B…)."** This is an unpaired comparison. It sits uneasily with the crossed-run finding that rescued tasks carry most of the file-channel cost.
12. **§4: "Fact coverage falls at the same sizes, from 43% to 32% at 8B."** "Same sizes" is ambiguous, and the measure has kappa = 0.29 against an LLM judge.
13. **§5 heading: "Run-to-run noise is small next to the file-based channels' gaps."** This is true for B. C's 8B gaps (-1.3 to 8.4) are of the same order as the ±2.2-point rerun band.
14. **Figure 4a subtitle: "Prefill: savings fade as payloads grow."** This does not hold for the pipe, which stays flat at 0.37-0.41x.
15. **§3: "which happens in the main and crossed runs for at most one task per channel at k = 3 and at most seven of 300 at any k (datasets pooled)."** This is unclear, because the crossed runs have 150 tasks and only k = 3.
16. **Table 1 caption: "among the 8 further tests (§3)"** points to §3, while §3 says the tests are in §4. The 8 tests include four "DvW" contrasts that do not appear in the table.

## What stands between this paper and acceptance

The minimum, all text/analysis only:

- Report the reply-output B variant and the handoff channel (one line each).
- Reframe the file-channel accuracy loss as protocol failure plus rescue, with a paired rescued/non-rescued decomposition in the main run.
- Explain the 8B gap explicitly.
- Scope the recommendation by model size and acknowledge the pipe at 14B and 32B.
- Put the decode-dominates-time fact and a priced cost comparison up front.
- Add a compact run table and describe the 32B bug.
- Fix the Figure 3 bar order and the Figure 4a subtitle.

With these, the paper is a solid workshop measurement contribution.

To be clearly above the bar, the paper would need:

- one crossed size rerun with a larger tool budget and cap, plus the reply-output variant;
- an 8B cap comparison on the same GPU;
- a small human validation of fact coverage.
