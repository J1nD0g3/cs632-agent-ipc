# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (round 14, systems reviewer)

## Summary

The paper compares five ways of passing state between three LLM agents (Researcher, Writer, Reviewer): copying the whole conversation (A1, broadcast), the same content reordered so that the shared history forms a cacheable prefix (A1-zc, "zero-copy"), passing only the previous output (A2, pipe), a shared workspace read and written through tool calls (B), and B with an auto-maintained index and a heading rule (C). The setup is Qwen3 4B–32B on vLLM v0.33.0 with prefix caching, on HotpotQA/2Wiki tasks that bundle k = 1–16 questions. The main findings are:

1. The channels rank differently by tokens sent than by prefill. Files send 2.9× broadcast's tokens but compute 0.79× its prefill. Zero-copy computes 0.39× at k = 3, at an accuracy difference of −0.8 (−2.9 to 1.4).
2. Files lose accuracy, and a crossed design (how the notes are written × how later agents get inputs) attributes the loss mostly to the later agents' file channel. At 14B and 32B the loss is concentrated in tasks the harness had to rescue.
3. At k = 8, three Researchers sharing a folder lose about 20 points, and separate folders recover them.
4. Prefill savings disappear once the shared history no longer fits the KV cache, and they barely change wall-clock time, because decoding takes 96% of the time.

The paper is honest about its limits: it labels results as cross-run, post hoc, or descriptive, and it generates every number from a script. It is also very dense, and several of its headline claims and "runtime rules" go further than the evidence.

## Score

**3 / 5 (weak accept, borderline).** The measurement is careful and the controls are better than usual for this genre. But the systems payoff is thin: prefill savings do not reach wall-clock time, and tokens sent ignores cached-input pricing. The file-channel conclusions are tied to a harness that fails in most tasks. The evaluation reads as a sequence of runs rather than an argument.

**Confidence: 4 / 5.** I know KV/prefix caching and agent serving well and checked the numbers against `numbers.tex`. I did not rerun anything.

## Strengths

- **S1. A clean, novel framing.** In the OS analogy, shared memory is supposed to save copies. Here it *increases* tokens sent (2.9×), because the reader is stateless and every read is a tool call that resends the conversation, while the prefix cache absorbs most of that resending (73% cached). That inversion, with Figure 2's two panels side by side, is the most interesting systems observation in the paper.
- **S2. Paired design with sensible controls.** The paper uses paired bootstrap over tasks. The documents control and the replay control rule out the two obvious alternative explanations for the file channel's loss (missing documents, worse notes), and the rerun bounds run-to-run noise (±2.2).
- **S3. The crossed 2×2 instead of a stepwise ablation.** It is explicitly motivated ("a stepwise split would make each change's share depend on the order"), it is run at four model sizes, and it is repeated across three runs (spread ≤ 3.3 points).
- **S4. Capacity sensitivity done right.** The PRO 6000 run at k = 8 with 35k, 100k, and 400k caches gives 0.85×, 0.36×, and 0.36× zero-copy prefill with accuracy fixed (≤ 1.6 points). This cleanly supports "prefill savings need the shared history to fit in the cache."
- **S5. Honest reporting of negative systems results.** Zero-copy's run takes 1.09× broadcast's time at six concurrent tasks and 1.00× at 32. Few papers would print that.
- **S6. Reproducibility hygiene.** All numbers are macros from one script. The statistics paragraph states which families are Holm-corrected, which are post hoc, and which comparisons are cross-run.

## Weaknesses (most important first)

**W1. The file-channel conclusions are conclusions about a harness that mostly fails, yet they are promoted to a general rule ("copy rather than share files").** In the main run the harness rescues an agent in 72% of B's tasks and 67% of C's. At least one agent exhausts its tool budget in 34% of tasks, a Researcher hits the 2,048-token cap in 22/300 B tasks (broadcast: 1), and at 4B *every* file-channel task needs the rescue. The Writer skips the notes in 42% of B's tasks. The stored `notes.md` is opened in 9% of tasks at 14B, because `list_files` sorts it after 30 documents. These are properties of a 12-call budget, an overwriting `write_file`, a lexicographic listing, and a 2,048-token cap. The paper itself shows that changing them moves accuracy by 14–20 points (told at 32B: +14.2; write guard: +15.1; heading rule: +18.1; separate folders: +19.8). With effects this large from single harness changes, "copy rather than share files" cannot be separated from "our file harness was weak." Doubling the budget was tested only at k = 16, where the loss has a different cause (shared-folder clobbering).
*Fix (needs new runs):* At k = 3, run one "reasonable practitioner" file harness that combines the fixes you already found: notes path named and listed first, a larger budget (24), the token cap at 4,096, `write_file` refusing overwrites, and the documents attached. Report its gap to broadcast on the 8B main tasks and at 14B/32B. If the gap stays near 8–10 points, the rule stands. If it closes, the paper's message becomes "files need X, Y, Z," which is also publishable.
*Minimum fix (text only):* Restate the rule as conditional on this harness and drop it from the intro's list of rules.

**W2. The systems payoff of the headline metric is not shown, and the abstract hides that.** The abstract and intro lead with prefill (−61%, "38–49% of broadcast's prefill"). Results then say decoding takes 96% of broadcast's time, zero-copy generates 1.2× the output tokens, and its run takes 1.09× broadcast's time (batch 1.00× at 32 concurrent tasks). For a systems venue, a reader who stops at the abstract will believe zero-copy makes pipelines cheaper or faster. Separately, "tokens sent ... as an API bills without cached-input discounts" models a pricing regime that the major APIs no longer use; they discount cached input, often by 50–90%. Under such pricing, the claim that the "channels rank differently" depends on the discount and should be shown, not assumed.
*Fix (text/analysis only):*
- Add one abstract sentence: "...but, because decoding dominates, it barely shortens runs (1.09× and 1.00× of broadcast's time)."
- Add a third cost to Figure 2 or a sentence: API cost with cached input billed at, say, 10% and 50%. This can be computed from your existing `cached_tokens` logs.
- State what prefill savings buy in your setting: GPU-seconds, energy, or headroom at saturation.

*Optional (needs new runs):* Measure throughput at saturation (tasks/s with an open-loop arrival rate), which is the regime in which prefill savings should appear.

**W3. "Zero-copy" conflates a cache-layout change with a prompt change, and the paper attributes the accuracy effect to the former by implication.** Prefix caching is exact, so any accuracy or behaviour difference between A1 and A1-zc comes from moving the role instruction out of the system prompt and to the end of the prompt. The 7.0-point loss at 4B (5.8 even with replayed notes) and the 1.2× output tokens are prompt-order effects. Nothing in the text says so. The conclusion lists "why zero-copy lowers accuracy at 4B" as unknown, and the first runtime rule ("put the shared history first") is stated without the model-size caveat. The name is also misleading for a systems audience: tokens are still sent, tokenized, and scheduled; only recomputation is avoided.
*Fix:*
- (Text only) Say explicitly that cache reuse is semantics-preserving and that A1-zc's accuracy deltas measure instruction placement. Cite instruction-position and "lost in the middle" work. Qualify rule 1 with the 4B result. Consider renaming to "prefix-shared broadcast."
- (Needs new runs, small) Add a layout that keeps a single shared system prompt containing all three role instructions, followed by the shared history and a short role tag. This gets the same prefix reuse without moving instructions to the end and would show whether the 4B loss is avoidable.

**W4. The evaluation is a run log, not an argument, and the reader cannot track the comparisons that cross runs and GPUs.** Methodology introduces in one paragraph:
- the main run
- the documents control, replay control, and rerun
- the size runs and the 32B rerun
- the crossed runs
- the wording run
- the reply-output runs
- the told runs
- the first-listed run

These span two GPU types, KV caches of 34,864 / 35k / 100k / 400k, and token caps of 2,048 / 4,096. Results then cite a further set of "two other runs," "three runs," and "one RTX PRO 6000 run." In the k = 16 paragraph two different B gaps for the same setting appear (30.4 in the PRO 6000 run, 33.9 in "its" gap from another run). "Drift across GPUs or caps is unmeasured," yet several headline numbers are cross-GPU: the 32B B/C gaps, the told-vs-copied comparison, and the folders-vs-one-Researcher comparison.
*Fix (text/analysis only):*
- Add a compact runs table (run, model(s), GPU, KV cache, cap, k, tasks, arms, section where used) and refer to runs by its row labels.
- Measure cross-GPU drift instead of declaring it unmeasured: the 8B size run on the PRO 6000 (A1 73.2, B gap 10.0, A2 gap 10.2) repeats the main run's 8B k = 3 conditions on the 3090 (B 9.6, A2 10.2 pooled). Compute the paired difference on overlapping tasks.
- Order the Results as claim → evidence → caveat, and move D and Br (W9) to one sentence or an appendix.

**W5. Several sentences in the abstract, intro, and conclusion are stronger than the numbers support.**
- (a) *Rescue story.* The abstract says the 14B/32B file costs come "mostly in tasks where the harness rescued an agent." For the main model, the paper's own main-run split says the opposite: B trails "about as much" with a rescue (9.4) as without (10.0), and C by 6.0 and 6.0. In the crossed run at 8B, the split also goes the other way (`nRTwelveEightFileToolResc` = 1.3 vs `Kept` = 5.9; not in the text). Rescue is also post-treatment and selects harder tasks.
- (b) *Rule 3.* "Lead every later agent to shared state" is supported at 32B only. At 14B, naming the path changed accuracy by 0.9 (−2.0 to 4.0), and listing it first changed final accuracy by 1.1 (−2.4 to 4.9). The conclusion even concedes this in the next sentence. The intro and conclusion also word the rule differently ("to shared state" vs "that edits the answer to the stored notes").
- (c) *Pipe sentence.* The abstract's pipe sentence picks the favourable conditions (14B, 32B, 8B at k = 16) and omits that the pipe loses 3.3–14.9 points at 8B for k ≤ 5, which the conclusion does state.
- (d) *"Much of the files' accuracy cost comes with the tool protocol."* This is close to definitional, because the file channel *is* the tool protocol. The informative content is which part of it costs accuracy. At 8B, the main model, neither Copy→files effect survives correction (−5.1, −2.9).

*Fix (text only):*
- Report the rescue split at all sizes, including 8B and the main run, or drop it from the abstract.
- Demote rule 3 to "at 32B."
- Add the 8B k ≤ 5 pipe loss to the abstract sentence.
- Replace "comes with the tool protocol" with the specific finding, e.g. "later agents that must find state through tool calls lose 8–22 points at 4B/14B/32B even with the same notes."

**W6. The AlignScore fact measure is too weak for the weight it carries.** It is validated on synthetic kept/removed/altered sentences (AUC 0.996, an easy task) but agrees with a Qwen3-8B judge only at κ = 0.29, and the judge itself is unvalidated. Yet it fills half of Figure 3 and supports the uncaveated Results sentence "B's notes state 32% of the supporting facts, against broadcast's 45%." The conclusion's open question "why a tool-call write lowers fact coverage" also treats the effect as established. Tool-written notes may differ in format (markdown inside JSON strings, escaping, truncation at the cap), which can bias an NLI-style scorer by itself.
*Fix (text/analysis, plus a small human annotation):*
- Annotate ~100 (notes, supporting sentence) pairs by hand, stratified by arm, and report AlignScore's agreement with humans by arm.
- Until then, drop Figure 3a, or move it to one sentence with the caveat, and caveat the 32% vs 45% sentence.

**W7. Figure 3 and Table 1 do not make their claims at a glance.** Figure 3b's claim ("on tool-written notes, files lower accuracy at 4B, 14B, 32B") requires comparing the 2nd and 4th bars of each group. Two pairs of pale colours (lavender and pale teal) are hard to tell apart, and panel (a), the weak measure, comes first. Table 1 has seven effect rows with cryptic labels ("Reply→tool, files") plus three descriptive rows in "x/y" format. The reader must decode the arrow convention, two Holm families, and a post hoc pooled row.
*Fix (text/analysis only):*
- Replace Figure 3 with one panel of paired *effects*: Copy→files on tool-written notes and on the reply, and Reply→tool on copy, with paired CIs per size and a zero line. Let Table 1 hold the rest.
- In Table 1, give rows plain-English labels ("Files instead of copying (tool-written notes)"), drop the three-runs row to text, and split Draft/final into two rows.

Figure 2 works well. Figure 4 is fine, but the k = 8 folder result, which is an abstract claim, has no figure.

**W8. Interleaving channels on a shared KV cache confounds per-channel prefill.** Six tasks from *different* channels share one 34,864-token cache. `cache_salt` prevents cross-channel *reuse* but not cross-channel *eviction*: B's long tool loops can evict A1-zc's shared prefix and vice versa. So a channel's "cached %" depends on its co-runners and on the mix, not only on its own layout. This matters most for the main-run prefill numbers at k ≥ 5 and for the "savings fade" curve in Figure 4a.
*Fix:* (Text/analysis only) State the mix explicitly and report prefill from the channel-alone timing runs (PRO 6000, 100k cache) alongside the main-run numbers. (Needs new runs, cheap) For one k, run each channel alone on the 3090 cache to show the curve is not a co-runner artifact.

**W9. Two "excluded variants" take a full paragraph without supporting a claim.** D is described, measured in six settings, and then excluded. Br is excluded "because it changes how agents give outputs," yet it is used to argue something. At 32B, Br's Writer "reads no file in 100% of tasks," so the 32B Br arm is degenerate.
*Fix (text only):* Cut to one sentence each or move to an appendix, and use the space for W4's runs table.

**W10. Statistics: correct but sometimes presented to understate consistent effects or overstate stability.**
- "On copied notes, only at 4B does the tool-call write change accuracy significantly." This is true under Holm, but the 8B and 32B intervals (−8.0 to −1.1; −7.1 to −0.9) also exclude zero, and the wording run's write effects were significant at three sizes. A consistent −4 to −5 point cost of the tool-call write at 8B and 32B is being described as nothing.
- "The wording-run arms ... move by at most 0.9 points" reports point estimates whose intervals span −3.6 to 3.1.
- The first Holm family "was chosen after earlier runs on the same tasks," and the told and first-listed analyses are uncorrected and post hoc. The told/first-listed paragraph is a chain of exploratory follow-ups at n = 150.

*Fix (text only):*
- Say "significant after Holm only at 4B; at 8B and 32B the uncorrected intervals exclude zero (−4.7, −4.0)."
- Give the drift interval, not only the maximum point estimate.
- Label the told/first-listed paragraph as exploratory in its first sentence.

**W11. Novelty and positioning.**
- "The one study that varies the channel" cites a non-peer-reviewed Zenodo preprint [20]. The blackboard papers the related work itself cites [7, 19] do compare a shared-state design against message-passing baselines.
- "Put the shared history first" is standard prompt-caching guidance from the API providers, and Parrot, KVFlow, and Prompt Cache already exploit it, as the related work acknowledges.
- The k = 8 folder result is a classic lost-update race: `write_file` silently overwrites, and 99% of tasks clash. Its fix is unsurprising to an OS audience.
- The Lauer–Needham duality is invoked but never used to predict anything.

*Fix (text only):*
- Soften "the one study."
- Position the contribution as *quantifying* the costs and the accuracy side effects of these well-known layouts in agent pipelines.
- Call the folder result what it is (lost updates; the fix is O_EXCL-style or per-writer namespaces), and report the fraction of Researcher notes actually lost.
- Either use the duality (e.g., "the dual of a file read is a copied message; the costs differ because...") or cut it to a clause.

**W12. Unexplained anomalies the reader will notice.**
- At 14B in the size runs, C (index + heading rule) trails broadcast by 16.0, *twice* B's 7.5. Yet the paper says C beats B in four of six 8B settings.
- One of the 60 k = 16 heading-rule tasks "did not complete," with no explanation of why or how missing tasks are handled.
- The 32B `workspace/` path-prefix bug changed B's gap from 28.5 to ≤ 24.8. Were other sizes affected at lower rates?

*Fix (text only):* One sentence each.

## Questions for the authors

1. If the Writer at k = 3 had a 24-call budget, the 4,096 cap, and `notes.md` listed first and named, how much of B's 8B gap would remain? (See W1.)
2. What does A1-zc's prompt look like exactly? Is there no system prompt, or an empty one? Did you try one shared system prompt with all role instructions?
3. Under cached-input pricing (e.g., cached input at 10% of the price), do B and C still send more than broadcast in dollars?
4. How much of the main run's per-channel cached fraction changes when a channel runs alone versus interleaved?
5. In the k = 8 three-Researcher B arm, what fraction of Researcher notes were overwritten before the Writer read them?
6. Why does the 8B crossed run show the opposite rescue split (1.3 on rescued vs 5.9 on non-rescued tasks) from 14B and 32B?
7. Why is C worse than B at 14B?
8. Were the main-run task samples and the 200-task control samples nested (the same tasks)? If so, can you report a direct cross-GPU paired check for 8B?
9. Why is the PRO 6000 KV cache capped at 100k tokens? Is the cap kept the same across model sizes, so that the 32B and 4B runs face the same cache pressure?

## Sentences that overclaim, are unclear, or mismatch their numbers

1. Abstract: *"Much of the files' accuracy cost comes with the tool protocol."* This is close to tautological, since the file channel is the tool protocol. Say what part of it costs accuracy (W5d).
2. Abstract: *"files cost 8.9 and 8.2 points against copying at 14B and 32B (Holm-corrected), mostly in tasks where the harness rescued an agent"*. True at 14B/32B, but false for the main model: main-run 8B gives 9.4 vs 10.0, and crossed 8B gives 1.3 vs 5.9. The split is descriptive and post-treatment.
3. Abstract: *"Zero-copy computes 38–49% of broadcast's prefill at up to five questions, at an accuracy difference of −2.9 to 1.4 points (95% interval) at three."*
   - The range is per (dataset, k) setting, while every other prefill number in the paper is pooled (0.47/0.39/0.38). Say "per setting."
   - The sentence reports an interval without its point estimate (−0.8).
   - "at three" dangles.
   - It omits that this saves no wall-clock time (W2).
4. Abstract: *"With Qwen3-14B or 32B at three questions, or Qwen3-8B at sixteen, passing only the previous output stays within 1.2 points ..."*. This selects the favourable cells and omits the 3.3–14.9-point loss at 8B for k ≤ 5.
5. Intro: *"The one study that varies the channel compares references, summaries, and KV caches [20]"*. This overclaims exclusivity; the cited blackboard work also compares shared state with messaging.
6. Intro: *"shared files send more tokens than ... broadcast but compute 0.79× its prefill, because consecutive broadcast prompts share almost no prefix."* This is half the reason. The other half is that B's later agents never receive the documents in their prompts and their tool loops reuse each other's prefixes (73% cached).
7. Intro: *"From it we draw four runtime rules ... lead every later agent to shared state, and copy rather than share files."*
   - Rule 3 holds only at 32B.
   - Rule 4 is harness-conditional (W1).
   - Rule 1 should carry the 4B caveat (W3).
8. §2: *"The channels otherwise differ only in what the Writer and the Reviewer receive."* This is inaccurate. In B and C the Writer and Reviewer also *produce* output through tools, under a budget and a rescue, so how they give outputs differs too. Br exists precisely because of this.
9. §2, A1-zc: *"each prompt ... ends with the role's instruction, which A1 puts in the system prompt."* This is unclear: does A1-zc have a system prompt at all?
10. §3 Runs: *"On the same tasks and cap, an earlier wording run ran broadcast and every crossed arm but the stored reply, the reply-output runs interleave B, ..., and the told runs (14B and 32B) interleave, ..."*. This is a comma-spliced run-on with a tense shift (ran / interleave). Split it, or replace it with a table.
11. §3 Tasks: *"draw 150 tasks for each dataset and each k ∈ {1,3,5}, each pair a setting."* This is too terse; write "each (dataset, k) pair is a setting."
12. §4 timing: *"We timed each channel alone on one RTX PRO 6000, ... six at a time."* "Alone" (one channel per server) and "six at a time" (six tasks) read as contradictory. Say "one channel per server, six concurrent tasks."
13. §4 timing: *"By vLLM's per-request counters in two of these runs, decoding takes 96% of broadcast's prefill and decode time."* This is awkward. Write "decode accounts for 96% of broadcast's GPU time (prefill + decode), by vLLM's per-request counters."
14. §4: *"Zero-copy thus cuts the prefill a deployment pays for"*. Who pays for prefill if time is unchanged? Name the resource (GPU-seconds or cached-input billing).
15. §4: *"The pipe loses accuracy at its Reviewer."* The evidence is right→wrong flips (16% vs 2%). No draft-level accuracy is reported for the pipe, so the stage attribution is not shown.
16. §4: *"B's notes state 32% of the supporting facts, against broadcast's 45%."* This is stated without the "weak measure" caveat that the crossed-run paragraph attaches to the same metric.
17. §4: *"On copied notes, only at 4B does the tool-call write change accuracy significantly"*. True after Holm, but the 8B and 32B intervals exclude zero (W10).
18. §4: *"Br stays out because it changes how agents give outputs."* B also changes how agents give outputs, relative to copying. Clarify that the exclusion is relative to B.
19. §5: *"In two other runs, doubling the budget to 24 calls moves B's accuracy by 3.3 points ..., small next to its 33.9-point gap."* The same paragraph opened with a 30.4-point gap. Say which run each gap comes from.
20. §5: *"On the RTX PRO 6000, the wording-run arms that the crossed runs repeat move by at most 0.9 points."* These are point estimates; the intervals span −3.6 to 3.1.
21. §5: *"Drift across GPUs or caps is unmeasured."* It is measurable from data you already have (W4), and several headline comparisons depend on it.
22. Conclusion: *"Our runs support four runtime rules"*. Immediately afterwards the conclusion says rule 3 failed at 14B. Either weaken "support" or scope each rule.
23. Figure 4 caption: *"with a shared 34,864-token KV cache"*. "Shared" by six concurrent tasks across channels; say so, since it is the mechanism behind panel (a).

## What stands between this paper and acceptance

Three things, in order:

1. Make the abstract and the runtime rules match the evidence. Add the timing result, scope the rescue claim, and qualify the rules by size and harness. This is text only.
2. Add a runs table and cut D, Br, and the less informative sub-analyses, so the evaluation reads as claim → evidence. This is text only.
3. Show that the file-channel loss survives a reasonable harness at k = 3: the budget, the cap, listing and naming the notes, and refusing overwrites (needs new runs; one 8B run at k = 3 on 150–200 tasks would suffice).

With (1) and (2), this is a solid workshop paper. With (3), its central claim about files becomes credible beyond this harness.
