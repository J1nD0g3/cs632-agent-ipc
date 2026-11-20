# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines"

Reviewer role: systems (ML systems / OS-for-AI workshop, 6-page track)

## Summary

The paper compares ways a three-agent Researcher -> Writer -> Reviewer pipeline can pass intermediate results. The channels are broadcast (copy the whole history), pipe (copy only the previous output), shared files reached through `list/read/write_file` tool calls (B), and files plus an auto-maintained `index.md` (C). It also tests a cache-friendly variant of broadcast that puts the shared history first ("zero-copy broadcast", A1-zc). Experiments use Qwen3-8B (and 4B/14B/32B for sensitivity) on vLLM v0.33.0 with prefix caching, on bundles of k HotpotQA/2Wiki questions, with 150 paired tasks per dataset and k. Cost is reported as tokens sent, prefill tokens computed after caching, and wall time when a channel is served alone. The main findings are:

- (i) Zero-copy broadcast keeps broadcast's accuracy at 38-49% of its prefill, but serving time does not improve, because decode accounts for 96% of summed request time and the agents generate 1.2x the tokens.
- (ii) Files send 1.8-4.8x the tokens and take 1.56-1.80x the time.
- (iii) Files lose accuracy at a write step (tool-call notes hold fewer facts) and a read step, and which step costs more depends on model size.
- (iv) At k=16 with three parallel Researchers, B collapses (about -30 points) because writers overwrite each other's files. A write guard recovers 15 points and a heading rule 18.

The paper adds several controls: replayed notes, a wording-only arm, tool-write-then-copy, documents added to file agents, a fan-out difference-in-differences, A/A reruns, and an AlignScore sanity check.

## Score and confidence

- **Score: 3 / 5** (borderline; weak accept for a workshop if the framing is narrowed and the serving and harness issues are addressed in text)
- **Confidence: 4 / 5**

## Strengths

1. **The controls are careful for a workshop paper.** The four-arm split (wording / tool write / read) and the replay of the same notes into every channel separate effects that naive channel comparisons mix together. The k=8 one-vs-three-Researcher difference-in-differences (-21.6, CI -26.8 to -16.6) is the strongest causal result in the paper.
2. **Negative results are reported honestly.** "Zero-copy saves no serving time" at both 6 and 32 concurrent tasks contradicts the paper's own prefill story, and the paper states it in the abstract instead of hiding it. The strict-accuracy numbers for rescued runs, the 32B path bug, the uncorrected multiple comparisons, and the unmeasured drift on the second GPU type are all disclosed.
3. **The cost metrics are useful.** The paper separates tokens sent, tokens computed, and wall time, and shows that they rank channels differently. Files send 2.9x the tokens but compute 0.79x the prefill. That point is useful to practitioners who reason only in billed tokens.
4. **The overwrite finding is concrete and actionable.** Parallel writers collide on file names in 72% of B's k=16 tasks, and a one-line guard or naming rule recovers about half the loss. Framework authors can act on this directly.
5. **The paired, bootstrapped statistics are appropriate.** Intervals are computed over tasks, so they respect the clustering of questions within a task. The paper also measures nondeterminism (59% identical outputs from identical prompts) and checks rerun stability (A/A within ±2.2 points).

## Weaknesses (most important first)

### W1. The workload structurally favors copying, so the title's question is answered only in the regime where files cannot win. (needs new runs)
Every Researcher gets all documents in its prompt, and the full history fits in a 32k context up to k=8. The file channel's natural advantage is selective access to state larger than the context, plus persistence and reuse across tasks, and none of the experiments exercise it. The conclusion admits this in its last two sentences, but the title, abstract and introduction ("which is the cheaper way to pass the same result") read as a general verdict. Multi-hop QA with 10-paragraph distractor sets is also the setting where the copying literature (Optima, PACT) already did well.

*Fix:* Do at least one of the following:
- (a) Add a workload whose shared state exceeds the context window or the KV cache, such as a larger retrieval corpus per task (open-domain HotpotQA with 100+ paragraphs) or a small code-repo task. Show where the crossover lies.
- (b) Retitle and scope the claims to "when the shared history fits in context", stating that in the abstract.

Option (b) is text-only and is the minimum.

### W2. The serving-time result is confounded and thinly analyzed, and the systems mechanism is not named. (needs new runs, plus text/analysis)
The serving runs have four problems:
- **Output length differs by channel.** Zero-copy generates 1.2x the tokens and B 2.1x, so the wall-time ratios mix prefill savings with output-length changes that the channel induced.
- **They run on a different GPU.** The serving runs use the RTX PRO 6000 with a 100k cache, while the token and accuracy results use the RTX 3090.
- **The decode share predicts the null result.** With decode at 96% of summed request time, at most about 4% can be saved, so the result is close to arithmetic rather than a finding.
- **The pipe result points to an unstated mechanism.** The pipe has zc's prefill and broadcast's output yet is faster (0.78x). That matches decode attention cost scaling with context length: prefix caching removes recompute but not the per-step KV reads over a long context. The paper stops at "prefill and output alone do not set serving time" and does not name or measure this mechanism, which is the one a systems audience would care about.

*Fix:*
- Re-time with outputs fixed per task, for example by replaying recorded completions with `ignore_eos` and `max_tokens` set to the recorded length, or by forcing identical outputs across channels. This isolates the channel's own effect on time.
- Report TPOT or decode time per output token per channel from existing vLLM metrics. This is text/analysis only if the logs exist.
- Add one prefill-bound configuration (short outputs, long documents, or open-loop arrivals at saturation) where prefill savings could appear, and report throughput rather than only alone-wall-time.
- State the GPU for the serving runs in that paragraph.

### W3. The file-channel harness is fragile enough that it may be measuring the agent loop rather than the channel. (needs new runs)
At k=3 the "must write your output" rescue fires in 34-59% of B's Writer runs and of B's and C's Reviewer runs. Without it, B scores 18.0% and C 22.9% (vs. 62.8/66.3). The 32B result swung by about 17 points after a path-normalization fix. At k=16, raising the tool budget from 12 to 24 calls barely helps (+3.3, CI -0.5 to 7.4). When over half of the agents fail to finish their own protocol, "files lose accuracy" may mean "this tool loop with this model at 12 calls and 2,048 tokens per call loses accuracy". The paper also never shows what the calls are spent on (repeated reads, listing, re-reading documents).

*Fix:*
- Report per-channel tool-call breakdowns (list / read-notes / read-doc / write / repeated reads) and the tool-limit hit rate at k=3.
- Audit answer-extraction failures at 8B the way the 32B path bug was found.
- Run one k=3 setting with a stronger tool harness or a second model family that is better at tool use (e.g., Llama-3.1-8B-Instruct or a 70B model). This shows whether the file-channel gap survives.
- Test the paper's own recommendation ("store an agent's plain reply as a file") as a channel. It is the most actionable claim and is currently untested.

### W4. Tokens-computed results for the main runs are confounded by interleaving channels on a shared, small KV cache. (needs new runs, or analysis only via simulation)
Each RTX 3090 server runs six tasks at a time, "interleaved across channels", with a 34,864-token KV cache that channels share in capacity. A channel's eviction pressure is therefore set partly by its neighbors. B/C's 30k+ token resends can evict zc's prefixes, which is exactly the effect the k=8 result (zc 0.83x) and Figure 4a attribute to payload size. The served-alone timing runs avoid this, but Figures 2b and 4a do not.

*Fix:* Either re-measure tokens computed with each channel served alone at the same concurrency, or replay each channel's logged prompt-token sequences through a vLLM-faithful block-LRU simulator at 35k/100k/400k capacity, one channel at a time. Either way, report whether the k=8 "savings fade" survives without neighbors.

### W5. The fact-level measure (AlignScore) is weakly validated but carries mechanistic claims. (needs new annotation, small)
- **Weak agreement.** Agreement with the Qwen3-8B judge on real notes is κ = 0.29, which is "fair", not "moderate" as the text says. Neither measure is checked against human labels.
- **Load-bearing claims.** Figure 3a ("the tool-call write drops facts"), the 45% vs 32% notes comparison, and the guard/heading notes percentages all rest on this measure.
- **Weak link to accuracy.** Broadcast's notes state only about 45% of the supporting facts yet the pipeline answers 72%, so coverage and accuracy look only loosely connected.
- **Delivery is uninformative for files.** In the file channels it counts source documents, so B's delivery is 87-94% even though the Writer never opens the notes in 42% of tasks.

*Fix:*
- Label about 200 (note, fact) pairs by hand and report AlignScore's and the judge's agreement with humans.
- Add per-task correlations between fact coverage and accuracy.
- Redefine delivery for file channels as facts received from the notes file(s) only, or drop it and use the open rate, which already supports the "readers skip the notes" claim.

### W6. The "reading" step is a catch-all, not reading. (text/analysis only)
In Figure 3 the "reading files" effect is B minus "tool-call write copied forward". That difference includes every downstream change:
- Writer and Reviewer receive only the questions.
- The Writer writes its draft to a file and the Reviewer must find it.
- The rescue path.
- The 12-call budget.

Calling all of it "reading" overclaims a mechanism (e.g., "reading them back from files costs accuracy at three sizes"). The replay experiment has the same scope.

*Fix:* Rename the step "downstream file access" or "finding and reading", and list what it contains. Alternatively, add an arm where the Writer gets the notes by file but the Reviewer still gets the draft by message, which splits the step (that arm needs new runs).

### W7. Novelty is modest, and the IPC framing is not used analytically. (text/analysis only)
- **Prior practice.** Zero-copy ordering is standard prompt-caching practice, and the paper says so ("our contribution is the measurement").
- **The OS analogy is decorative.** Tool-mediated files are closer to a file system behind system calls (or RPC) than to shared memory, and the cost model of Lauer–Needham duality is never instantiated. The analogy's real payoffs go unclaimed: the write guard is O_EXCL / per-writer namespaces, the heading rule is self-describing records, and the index is a directory.
- **Missing related work:**
  - position-independent or non-prefix KV reuse (CacheBlend, EPIC), which would get zc's savings without reordering and so might avoid the 4B accuracy loss;
  - KV retention across tool calls (InferCept, Continuum), which is directly relevant to B's per-call resends and to eviction at k=8;
  - agent-serving systems (Autellix, Ayo);
  - OS-for-agents work (AIOS) and file-based agent memory (MemGPT/Letta);
  - DroidSpeak, for cross-agent KV.

*Fix:*
- Add a small analytic cost model: prefill = uncached prefix tokens; file cost = calls × context − cached. Fit it to the existing logs and use it to predict the k / cache-size crossover in Figure 4a. That turns the measurement into a systems result.
- Add the related work above.
- Rename "zero-copy" (W9).

### W8. Some headline claims lean on cross-run comparisons with unmeasured drift. (text/analysis only, or new runs)
Several claims compare runs:
- the fan-out DiD (one vs. three Researchers in different runs);
- "C's smaller loss at k=16 likely comes largely from this heading rule" (heading 12.6 [7.2, 18.2] vs. C 7.2 [2.4, 12.0] from an earlier run; the intervals overlap);
- the 32B path-fixed gaps.

All of these are on the RTX PRO 6000, where the paper says A/A drift is unmeasured. Nondeterminism is large: 41% of identical-prompt Researcher outputs differ.

*Fix:* Run one A/A rerun on the PRO 6000 (needs new runs, small). Otherwise hedge the heading-rule attribution to "may explain part of" and keep the DiD as the only cross-run causal claim.

### W9. Writing: the number density hides the argument, and some terms mislead. (text/analysis only)
- **Number density.** The body carries about 220 numeric macros in five pages, most with intervals, and many paragraphs are runs of short sentences each stating a number. The reader has to reconstruct the argument. The abstract ends on an isolated fact ("A 4B model loses 7 points with zero-copy ordering.") rather than a takeaway.
- **"Zero-copy" is a misnomer.** The paper itself says "Every token is still sent" and "the prefix cache removes the recomputation of a copy but not the copy itself". A name like "prefix-ordered" or "cache-ordered" broadcast would be accurate.
- **Harness detail appears early.** "A leading `workspace/` in a path is treated as the root" appears in the split paragraph before it is explained in Model size.
- **Mixed paragraph.** The heading "Neither a larger cache nor a larger tool budget closes the gap" sits over a paragraph that opens with a larger cache *restoring* zc's savings.

*Fix:*
- Move most secondary numbers into one compact table (channel × {sent, computed, time, acc, Δ, CI}). Keep 2-3 numbers per paragraph in the text.
- End the abstract with the guidance sentence.
- Rename the zc variant.
- Split the cache/budget paragraph.

### W10. Figures: two make their claim at a glance; two need work. (text/analysis only)
- **Fig. 1 (mechanism)** is clear. It omits the file channels' main cost, though: each tool call resends the growing conversation. It also does not show zc's instruction moving to the end, which is the confound behind the 4B loss. Add a resend loop arrow on B/C and an "instr." segment at the end of zc's bars.
- **Fig. 2 (trade-off)** reads in three seconds. The arrow label "-61% computed, same accuracy" overstates a non-significant -0.8 (CI -2.9 to 1.4). Use "no significant accuracy change". The paper's own counterpoint, that this saves no serving time, has no visual. A third small panel (serving time vs. accuracy) would stop readers from taking away the wrong headline.
- **Fig. 3 (split)**:
  - Panel (a) has no intervals, and its title "The tool-call write drops facts" is false at 14B. Change it to "...drops facts at 4B, 8B, 32B".
  - The "Reading files" bar inherits W6's naming problem.
- **Fig. 4 (scaling)**:
  - Panel (b) has no confidence intervals, and the k=16 point (n is not stated in the text or caption) carries the "collapse" claim.
  - Plotting relative to A1 hides whether "the pipe recovers" because the pipe improves or because broadcast degrades at large k. Add CIs, give n per k, and show A1's absolute accuracy, at least in the caption.
  - Connecting k=8 to k=16 with a line across a change of regime (fan-out) invites a trend reading. Break the line.

### W11. Billing claims ignore cached-input pricing. (text/analysis only)
"Tokens sent ... counts what an API bills without caching." Major APIs now discount cached input tokens heavily, so the cost ranking under realistic billing could differ, especially for B/C, which are 73% cached.

*Fix:* Add a row computing billed cost under a typical cached-input discount and output premium from the existing logs.

## Questions for the authors

1. At k=3, what fraction of B's and C's Writer and Reviewer runs hit the 12-call limit, and what are the calls spent on? At k=16, the Reviewer still exhausts the budget at 24 calls in about half of runs. Is the agent looping on the same files?
2. With six channels interleaved on a 34,864-token cache, how much of zc's k=8 prefill (0.83x) comes from eviction by B/C neighbors rather than by zc's own working set?
3. What is decode time per output token for A1, A1-zc and A2 in the serving runs? Does it scale with context length as the pipe result suggests?
4. Under exact match, zc is up to 4 points lower on 2Wiki. Is that difference significant, and does the lenient matcher (F1 ≥ 0.8 or containment) favor longer outputs, which zc produces?
5. Did you consider passing the notes by message and only the documents by file (a hybrid), or a pointer-plus-summary channel? This is the obvious design point between A2 and B, and it is close to what the cited production system does.
6. How were the 150 tasks sampled, and how much do the k=1/3/5 question sets overlap? The paper says they overlap, which matters for the "N of six settings" counts.
7. Is the Qwen3-8B fact judge the same checkpoint as the agents? If so, does agreement with AlignScore differ between channels (e.g., lower on tool-written notes)?
8. In the replay experiment, B's Writer never opens a single clearly named `notes.md` in 24% of tasks. What does it do instead? Does it answer from the documents?

## Quoted sentences that overclaim, are unclear, or mismatch their numbers

1. **§3 Metrics:** "on real, paraphrased notes it agrees only moderately with a Qwen3-8B judge (κ = 0.29)".
   - κ = 0.29 is fair or weak agreement by the usual scales, not moderate. Say "agrees weakly".
2. **Abstract and §1:** "This is the message-passing versus shared-memory question of operating systems."
   - Tool-mediated files are accessed through mediated calls, closer to a file system or RPC than to shared memory. Soften to "an analogue of".
3. **§1:** "It keeps the channel fixed, so it cannot tell whether copying or sharing is the cheaper way to pass the same result."
   - TOAP (cited later) compares passing a reference vs. a summary vs. KV, which partly varies the channel. Qualify.
4. **Fig. 2 annotation:** "-61% computed, same accuracy".
   - The paired difference is -0.8 (CI -2.9 to 1.4), so say "no significant change". The EM gap of up to 4 points on 2Wiki is also unmentioned here.
5. **Abstract:** "much of the loss comes from the parallel writers, which overwrite each other's notes. A guard against such writes recovers 15.1 of those points".
   - The guard recovers about half (15.1 of 30.4), and B with the guard still trails by 15.3. "About half" is the accurate phrase, and the remaining gap is unexplained.
6. **§4:** "reading them back from files costs accuracy at three sizes, 4B, 14B, and 32B".
   - The step includes everything downstream of the Researcher (see W6), not reading alone.
7. **Fig. 3a title:** "The tool-call write drops facts".
   - Not at 14B (47-48% vs. 44-45%), so qualify by size.
8. **§4, Giving files the documents:** "Missing sources therefore do not explain the loss."
   - The CI (-2.8 to +3.8) cannot exclude an effect of about 4 points against a B loss of about 7-8. Say "do not explain most of the loss".
9. **§5 heading:** "Neither a larger cache nor a larger tool budget closes the gap."
   - The paragraph opens by showing a larger cache restores zc's savings. The budget was tested only at k=16 on 60 tasks, with a CI up to +7.4. Split the paragraph and hedge the budget claim.
10. **§5:** "C's smaller loss at sixteen questions likely comes largely from this heading rule."
    - This is a cross-run comparison with overlapping intervals (12.6 [7.2, 18.2] vs. 7.2 [2.4, 12.0]). Say "may come partly".
11. **§5:** "Parallel writers, more than payload size, thus drive B's collapse."
    - This is supported at k=8 by the DiD, but the k=16 guard leaves half the loss, so "a large part of" is safer.
12. **§7:** "The pipe is the cheapest channel by all three counts".
    - On tokens computed it ties zc (4.7k vs. 4.8k at k=3; 0.38 vs. 0.38 at k=5). Say "cheapest or tied".
13. **§3 Metrics:** "It counts what an API bills without caching in tokens".
    - This is correct as written, but the paper then uses tokens sent as the billing story (Fig. 2a axis "API billing") although cached-input discounts are now standard. Label the axis "tokens sent (uncached billing)".
14. **§2:** "Zero-copy broadcast ... Every token is still sent."
    - The name contradicts the description; see W9.
15. **§4:** "A leading `workspace/` in a path is treated as the root."
    - It is unclear in context; it is a harness fix explained only in §5.
16. **Fig. 2 caption:** "Bars are 95% intervals of each channel's mean".
    - These are whiskers, not bars, and paired intervals (the ones that matter) are not shown.
17. **§3 Methodology:** "Each server runs six tasks at a time, interleaved across channels ... channels never hit each other's KV, though they share its capacity."
    - This is the W4 confound, stated but not followed through to the k=8 cache claims.

## What stands between this paper and acceptance

The core comparison is careful and honestly reported. The three items that most limit it are:

1. **Claims scoped beyond the workload.** Narrow the claims to "shared history fits in context", or add one workload where it does not (W1).
2. **Serving result unexplained.** Explain it mechanistically, with context-length-dependent decode, and control output length (W2).
3. **Fragile harness.** Show that the file-channel losses are not mostly an artifact of a fragile tool loop with one model family, given 34-59% rescue rates and 50% budget exhaustion (W3).

Fixing the interleaving confound in tokens computed (W4), validating the fact measure against humans (W5), and cutting the number density in favor of a summary table and a small cost model (W7, W9) would turn this from a careful measurement report into a workshop paper with a clear, transferable systems lesson.
