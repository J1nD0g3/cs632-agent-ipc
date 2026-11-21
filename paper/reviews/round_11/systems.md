# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (systems reviewer, round 11)

## Summary

The paper compares five ways of passing results between the agents of a fixed Researcher -> Writer -> Reviewer pipeline (Qwen3 on vLLM, multi-hop QA from HotpotQA and 2Wiki, k questions bundled per task):

- broadcast (A1), which copies the whole conversation;
- zero-copy broadcast (A1-zc), the same messages reordered so the shared history comes first and the prefix cache can reuse it;
- pipe (A2), which passes only the previous agent's output;
- shared files (B), accessed through tool calls;
- files plus an index (C).

It measures tokens sent, prefill tokens computed, serving time and accuracy. It adds controls: replayed notes, documents given to later agents, a 2x2 "crossed" design (how notes are written x how they are delivered) at four model sizes, sweeps of cache size and payload, and a fan-out experiment with one or three Researchers.

The main claims are:

1. Prefill ranks the channels differently from tokens sent. Zero-copy cuts prefill by 61% at k=3 without a significant accuracy loss at 8B, but does not save serving time.
2. Writing notes through a tool call costs accuracy when the notes are copied forward. Through files, a stored reply does no better than tool-written notes.
3. When three parallel Researchers share one folder, plain files lose 21.2 points at k=8, and per-writer folders recover 19.8 of them.

The paper is careful and unusually honest about its caveats: cross-run labels, Holm correction in Table 1, an A/A rerun, and a note that the AlignScore labels are weak. The engineering of the controls is good. My concerns are about what the file-channel numbers actually measure, an abstract whose emphasis does not match Table 1, a prefill comparison anchored on a cache-hostile baseline, and a serving-time claim that the paper's own numbers partly contradict.

## Score and confidence

- **Score: 3 / 5** (weak accept for a workshop: a useful, well-controlled measurement study, but the framing overstates generality and several headline sentences need repair).
- **Confidence: 4 / 5.**

## Strengths

1. **Clean manipulation of the channel with real controls.** The paper keeps task, model, roles and order fixed and uses paired comparisons on the same tasks. It also adds replayed notes, documents-for-later-agents, a wording control and the crossed 2x2. Few agent-communication papers separate "what the producer writes" from "how the consumer receives it". The crossed design (Table 1, Fig. 3) is the right way to do that, and the paper correctly notes that a stepwise split would be order-dependent.
2. **Prefill is treated as a first-class cost.** Separating tokens sent (billing), prefill computed (self-hosted compute) and serving time is the right systems lens. Fig. 2's "73% cached" labels make the point that tool loops resend the conversation but mostly hit the cache.
3. **Statistical hygiene above the norm for workshop papers.** The paper uses paired bootstrap intervals over tasks and an A/A rerun (+/-2.2 points). It applies Holm correction to the 16 simple effects in Table 1. It labels cross-run comparisons, reports how often the rescue turn fires and how accuracy changes if every rescued task is scored wrong, and states that the k=1/3/5 question sets overlap.
4. **The cache-size sweep shows a mechanism.** At k=8, zero-copy goes from 0.85x to 0.36x of broadcast's prefill when the cache grows from 35k to 100k tokens, with accuracy moving less than 1.6 points. This is a clean demonstration that the savings need the shared history to stay resident.
5. **The fan-out experiment is well designed.** It runs one versus three Researchers on the same 100 tasks on one server and adds a per-writer-folder arm. It reports the collision rate (99%) and the "only one Researcher's notes left" rate (58%), so the mechanism is visible, not inferred.
6. **Reproducible numbers pipeline.** Every number in the text comes from a script-generated macro, and I found no macro that disagrees with its sentence (with the exceptions of wording noted below).

## Weaknesses (most important first)

### W1. The file-channel accuracy mostly measures tool-protocol compliance under this harness, not the channel. (needs new runs + text/analysis)

The paper's own numbers show that file channels lose accuracy mainly because the consuming agent does not do what it is told:

- **Main run (B).** B's Writer never opens the notes in 42% of tasks, and 83% of its reads go to source documents. This happens even though its instruction says "Find the notes with list_files and read them; read a source document only to check a doubtful fact."
- **Crossed runs.** The Writer opens the clearly named `notes.md` in only 5% (4B), 9% (14B) and 24% (32B) of tasks. Through files, the stored reply then scores 33.6%, 44.2% and 56.4%, against 67.8%, 74.2% and 76.9% when copied.
- **Rescue turn.** The forced-write rescue fires in 34–59% of tasks for B's Writer and for B's and C's Reviewers. Scoring rescued tasks as wrong drops B to 18.0% and C to 22.9%. Per `numbers.tex`, about 53% of B's Writers reply instead of writing their file.
- **Tool budget.** B's and C's Reviewers exhaust the 12-call budget in 29% and 34% of k=3 tasks (`nKThreeBReviewerLimit`, `nKThreeCReviewerLimit`). This is not reported in the paper.
- **32B harness bug.** The 32B harness missed the final answer file in 51 of 200 B tasks because of a `workspace/` path prefix, which required a rerun.

So "files are less accurate" is, to a large extent, "Qwen3 under vLLM's function-calling parser often does not open the file it was told to read, or runs out of tool calls". That is a real and useful deployment finding. But it is a property of the model's agentic competence, the 12-call budget, the file naming and the rescue policy, not of shared memory as an IPC mechanism. The IPC framing ("message passing vs shared memory") invites readers to generalize to the channel.

Fixes:
- **(a) text/analysis.** Add a short failure decomposition per channel and size: notes never opened, budget exhausted, rescued, truncated tool write. Report accuracy conditional on the Writer opening the notes. If B conditional on reading the notes is close to A1, the paper's message changes.
- **(b) needs new runs.** Add one arm that separates delivery from discovery, for example a harness that returns the notes file's content as the Writer's first tool result (an "auto-read" or mmap-like delivery). Also add a k=3 run with a 24-call budget, since the budget binds at k=3, not only at k=16.
- **(c) text.** Reframe the conclusions as "with current open models and tool interfaces" rather than as a property of the channel.

### W2. The abstract and introduction foreground the weakest effect in Table 1 and understate the strongest. (text/analysis only)

- **The tool-write effect.** The abstract leads observation 2 with "Writing the Researcher's notes through a tool call costs accuracy at three of four model sizes ... (at one after Holm correction)". That effect is -4.0 to -8.7 points and survives correction only at 4B.
- **The delivery effect.** The largest and most robust effects in Table 1 are the delivery effects. Copy->files for replies is -34.2, -5.1, -30.0 and -20.4 points, Holm-significant at three sizes. Copy->files for tool-written notes is also significant at three sizes. The abstract never states this.
- **The stored reply is understated.** "A plain reply stored as a file does no better than tool-written files" understates a significant reversal: tool-written files beat the stored reply by +21.3 at 14B and +8.2 at 32B, both marked with a dagger. The conclusion repeats it as "storing the reply as a file does not help", and also drops the Holm caveat ("at three of four sizes").

Fix: reorder observation 2. Lead with "delivery through files costs 20–34 points at three of four sizes, largely because the Writer does not open the notes". Then give the tool-write effect with its Holm caveat. State plainly that through files a stored reply is significantly worse than tool-written notes at 14B and 32B, and keep the Holm caveat in the conclusion.

### W3. The prefill story is anchored on a cache-hostile baseline, and "zero-copy" is standard practice under a misleading name. (text/analysis only)

Broadcast puts each role's instruction in the system prompt, ahead of the shared history, so it gets 1% cached tokens. The first observation ("files send 2.9x the tokens yet compute only 0.79x as much prefill") exists only because of this layout. Against zero-copy, B and C compute 2.0x the prefill. Measured against the sensible message baseline, files rank worst on every cost.

"Put the static/shared content first" is the standard advice for any prefix cache, including provider prompt-caching guides, Parrot and KVFlow. The paper admits as much ("we contribute the measurement"). "Zero-copy" is also a misnomer, since the tokens are still sent (13.6k per task); only recomputation is avoided. The related-work paragraph says exactly this.

Fixes:
- Make A1-zc the reference for the prefill observation.
- State that A1 reproduces AutoGen's layout and is cache-hostile by construction.
- Rename A1-zc to something like "prefix-ordered broadcast". Alternatively, keep the name but say in §2 that only recomputation is avoided.
- Fig. 1 should draw the role-instruction block: first in A1, last in A1-zc. That placement is the only difference between the two, and it is invisible in the figure.

### W4. The serving-time claim is contradicted in part by the paper's own numbers, and the experiment was set up so prefill could not matter. (text/analysis; a decisive version needs new runs)

- **Concurrent median.** The abstract says zero-copy "saves no serving time". §4 reports that at 32 concurrent tasks with a 400k cache, zero-copy's median task takes 0.82x broadcast's time. Only the batch makespan is unchanged (1.00x). Median task latency is serving time.
- **Prefill is too small to matter.** Decoding is 96% of broadcast's summed prefill+decode time. Removing all prefill could save at most about 4%, so the "no serving-time savings" result follows from the workload's decode-heaviness and says little about the channel.
- **Output length confound.** Zero-copy's agents generate 1.2x the output tokens (longer notes: 1,992 vs 1,570 characters). The 1.09x time at six concurrent tasks therefore mixes a prompt-layout effect on output length with the cache effect.
- **Attribution under batching.** The per-request prefill/decode split under continuous batching with chunked prefill is itself an approximation. The paper should say how it was computed.

Fixes:
- **Text.** Change the abstract and introduction to "does not shorten batch completion time" and report the 0.82x median.
- **Analysis.** Normalize time per output token, or report time-to-first-token per agent.
- **New runs (optional).** Use a prefill-heavier regime (k=8 with a 100k cache, or higher concurrency) where the 61% cut could plausibly matter.

### W5. Cache-sensitive numbers come from heterogeneous co-scheduling, and many claims rest on cross-run, cross-GPU comparisons with unmeasured drift. (needs new runs)

**Shared cache.** The main run interleaves six tasks across channels on one server, "so channels share its KV-cache capacity". A channel's prefill at k>=8 therefore depends on its neighbors. B and C resend long conversations and plausibly evict zero-copy's prefixes. The k=8/16 prefill points in Fig. 4a ("zero-copy saves no prefill at sixteen questions") are partly a property of the mix, not of the channel. The PRO 6000 cache sweep also runs all channels, so it shares the issue.

**Cross-run comparisons.** These carry several claims:

- the pipe-with-documents result (+6.8);
- the 24-call budget;
- the 32B rerun, which replaced C's gap as well even though no C task was affected;
- the "as large as the stored reply's" comparison;
- the replay comparison.

The A/A rerun covers only the RTX 3090 servers. The three estimates of B's k=16 gap (33.9 on the 3090s, 33.9 in the earlier PRO 6000 run, 30.4 in the repair run) suggest drift of about 3–4 points, which is comparable to several of the effects discussed.

Fixes:
- Measure prefill under contention per channel alone at k=8/16, or report per-channel eviction counts.
- Repeat the A/A rerun on the PRO 6000 (one channel pair, 100–200 tasks).
- Keep cross-run numbers out of the abstract and conclusion.

### W6. The fan-out result is a lost-update artifact of an overwrite-by-default `write_file`, its OS-natural baselines are missing, and the headline has no figure. (needs new runs + text)

In 99% of three-Researcher B tasks, two Researchers wrote the same path. Broadcast cannot lose updates because the harness concatenates the replies. A systems audience will read this as the classic lost-update problem.

- **Missing baselines.** The obvious OS answers are an append-only shared log, O_EXCL (the write guard), and per-process namespaces (folders). They are tested piecemeal: folders only at k=8, the guard and the heading rule only at k=16 ("We did not test separate folders at this size").
- **Confound.** The folders arm also changes the paths the Writer sees, which the paper acknowledges.
- **No figure.** The abstract's 21.2/19.8 numbers appear in no figure. Fig. 4b instead shows the k=16 point, where fan-out and payload are confounded, and its subtitle attributes the drop to folder sharing.

Fixes:
- **Text.** Add a small bar chart (1R B, 3R B, 3R folders, 3R A1, with CIs) or fold these numbers into Fig. 4b.
- **New runs.** Test all three repairs (guard, folders, append-only log) at one payload size.

### W7. The fact-coverage measure is too weak to carry the mechanistic claims built on it. (text/analysis; validation needs annotation, not GPU)

AlignScore at a 0.5 threshold separates synthetic pairs well (AUC 0.996). On real notes, it agrees with a Qwen3-8B judge at kappa = 0.29, and that judge is itself unvalidated and from the same family as the agents. Yet §4 explains the tool-write loss as "its notes state fewer supporting facts (32% against 43% at 8B)", and Fig. 3a has no intervals.

The 4B gap (22% vs 48%) is probably robust; the 8B and 32B gaps are less certain. The truncation rate of tool writes in the crossed runs is also not reported. The earlier run cut off 16% of tool writes at 4B and 7% at 8B, and the uncut-only effect shrank from -8.7 to -5.7 at 4B. Part of the "tool write drops facts" story may be truncation.

Fixes:
- Human-label a stratified sample of 100 notes and report agreement.
- Add CIs to Fig. 3a.
- Report crossed-run truncation rates and the uncut-subset effect.

### W8. Scope and generality. (needs new runs to fix; text to scope)

The study uses one model family, one engine, one tool-call parser, and one task type. The task bundles k independent HotpotQA questions with all distractor paragraphs given to the Researcher. The size results already show that the conclusions flip with the model: the pipe loses only at 8B, and zero-copy costs 7.0 points at 4B. This means a second family is necessary before "agents should copy results forward" can be stated as advice.

Fixes:
- **New runs.** Add one non-Qwen model at about 8B (main-run channels at k=3) as a minimum.
- **Text.** Put the 4B zero-copy loss in the abstract, next to the 8B interval.

### W9. Related work misses the closest explanations and the OS-for-agents line. (text only)

- **Format restrictions.** The tool-write effect is very likely a case of format restrictions degrading generation: content written inside a JSON string argument. "Let Me Speak Freely?" (Tam et al., 2024) and the follow-ups on structured-output degradation are the obvious citations, and they would also answer the paper's closing "we have not studied why".
- **Instruction position.** Zero-copy moves the role instruction to the end of a long context. Position effects such as lost-in-the-middle and instruction recency are a plausible cause of the 4B loss.
- **OS-for-agents.** MemGPT (OS-style virtual context) and AIOS (an LLM agent OS) are the obvious reference points for an "IPC for agents" paper at an OS-for-AI venue.
- **Lauer–Needham.** The paper invokes the duality as motivation, but the duality is between message-oriented and procedure-oriented systems, not message passing versus shared memory. Either say how it maps or drop it.

### W10. Statistics are not uniform across claims. (text/analysis only)

- **Uncorrected counts.** Counts such as "significantly in five of six settings" and "C is significantly above B in four of six settings" are uncorrected across overlapping settings. The paper discloses this, but the counts still read as evidence; report a pooled paired test instead, or apply Holm there too.
- **Untested interaction.** The interaction row is labeled "untested", yet the text interprets its intervals ("lies above zero at all sizes but 8B"). Either test it or do not interpret it.
- **Nondeterminism.** Identical prompts give identical notes in only 59% of tasks. Each task runs once per channel, so per-task decoding noise is folded into the bootstrap. That is acceptable, but say so.

### W11. Presentation and flow. (text only)

- **Order of introduction.** The Methods section mentions "the earlier wording run" before it is described (it first appears in §4's crossed-run paragraph).
- **Run accounting.** The serving paragraph's accounting is hard to follow: "three times ... in two runs with vLLM's per-request counters ... in two runs with 32 tasks at a time". Give a compact table of runs (GPU, cache, n, channels, purpose); it would replace about 10 lines of prose in Methods.
- **Jargon.** "Plain files" (abstract) is undefined; say "B (files without an index)".
- **Table 1.** The caption states no takeaway, and the sign convention ("arm right of the arrow minus the one left") makes readers work. Put the delivery rows first, bold the daggered cells, and state the claim in the caption.
- **Fig. 3.** The eye goes to the 14B stored-reply collapse (44%), which the text leaves "unexplained". The caption's claim ("copied replies are the most accurate arm") is not what the figure emphasizes. Either explain the collapse or de-emphasize it.
- **Fig. 4.** There are no intervals. Sample sizes are mixed (300/200/60). The line from k=8 to k=16 connects across a regime change (fan-out). Panel (b)'s subtitle asserts a cause the figure cannot show. Break the line at the dashed divider and add CIs.
- **Fig. 2.** Good. The "no significant loss" annotation correctly relies on the paired interval, and the caption warns that the whiskers are not paired.
- **Narrative.** The evaluation reads as a sequence of well-controlled findings rather than an argument. The three observations are only loosely connected by the IPC framing, and the IPC paragraph in Related Work (index = directory, folders = namespaces, guard = O_EXCL) is the paper's most systems-flavored insight. Consider building §5 around it: "the file channel needs the same three OS mechanisms (naming, isolation, exclusion) that files needed".

## Questions for the authors

1. What is B's (and the stored reply's) accuracy conditional on the Writer opening the notes? What do 4B and 14B Writers do in the stored-reply arm when they never open `notes.md`: read the documents, answer closed-book, or get rescued?
2. B's k=16 gap is exactly 33.9 both in the main 3090 run (`nGapBKSixteen`) and in the earlier PRO 6000 run (`nRFourKSixteenGapB`, from `p07_k16_kv100k`). Please confirm these are independent measurements and not the same data.
3. What fraction of tool-call writes were truncated at the 4,096-token cap in the crossed runs, and what is the tool-write effect on uncut tasks only?
4. Why 12 tool calls? At k=3, B's and C's Reviewers exhaust it in 29–34% of tasks. How does B at k=3 change with 24?
5. For 32B, C's gap is taken from the rerun (8.2) even though none of C's tasks were affected by the path bug (the first run gives 9.3). Why replace it?
6. How were per-request prefill and decode times attributed under continuous batching with chunked prefill?
7. Does AutoGen's group chat really put the role instruction ahead of the shared history in every call? Cite the code path, since the prefill comparison depends on it.
8. At 4B, zero-copy loses 7.0 points even with replayed notes. Is the cause the instruction moved to the end, or the missing system prompt? A variant with the instruction in a short system prompt plus a repeated suffix would tell.

## Sentences that overclaim, are unclear, or mismatch their numbers

1. Abstract and introduction: "Zero-copy broadcast ... computes 38–49% of broadcast's prefill at up to five questions per task but saves no serving time." Serving time was measured only at k=3, and at 32 concurrent tasks the median task takes 0.82x broadcast's time. "Does not shorten batch completion time (k=3)" is what the data show.
2. Abstract: "With Qwen3-8B, copying the whole conversation (broadcast) is the most accurate channel." Zero-copy is statistically indistinguishable (-2.9 to 1.4) and beats broadcast in at least one setting (gap minimum -1.3). Say "broadcast and zero-copy are the most accurate".
3. Abstract: "but a plain reply stored as a file does no better than tool-written files." It does significantly worse at 14B (-21.3) and 32B (-8.2), both Holm-significant. The same applies to the introduction's "does no better than tool-written notes" and the conclusion's "storing the reply as a file does not help".
4. Conclusion: "A tool-call write lowers accuracy when its notes are copied, at three of four sizes". This drops the abstract's "(at one after Holm correction)".
5. §4 heading: "Files are less accurate in every setting." C's gap ranges from -1.3 to 8.4 and is significant in only two of six settings, so C is not less accurate in every setting. Restrict the heading to B.
6. Introduction: "At three questions per task, shared files send 2.9x the tokens of copying the whole conversation (broadcast), yet the engine computes only 0.79x as much prefill." This is true, but only because broadcast's layout defeats the prefix cache (1% cached). Against zero-copy the ratio is 2.0x. As written, it reads as a property of files.
7. §4: "Less prefill does not mean less serving time, because decoding dominates." Decoding dominates in this workload (96%). The general phrasing overreaches. Also, zero-copy generates 1.2x more output, so the comparison is not prefill-only.
8. §4: "Zero-copy thus pays off mainly where prefill is billed." It also pays off in per-task latency under load (0.82x median), by the paper's own number.
9. §4: "The interaction, whose interval lies above zero at all sizes but 8B, makes a stepwise split order-dependent." The interaction is labeled untested in Table 1. The sentence is also hard to parse; say "because the two effects interact (Table 1, last row), a stepwise split would assign different shares depending on order".
10. Fig. 4b subtitle: "B drops at k=16, where three Researchers share a folder." The figure cannot separate fan-out from payload at k=16. The causal evidence is the separate k=8 experiment.
11. §5: "At sixteen questions, a write guard or the heading rule recovers about half of B's loss or more." The figures are 15.1 and 18.1 of 30.4, measured on 60 and 59 tasks in a run whose B gap (30.4) differs from Fig. 4's 33.9. Say which baseline is meant. Also, 30.4 - 18.1 = 12.3, not the stated 12.6; the n differs, so state it.
12. §4: "Across runs, this loss of the file channels is as large as the stored reply's at 8B." This is a cross-run equality of two point estimates (5.2 vs 5.1) with overlapping intervals of about +/-3; it supports "similar", not "as large".
13. Abstract: "three parallel Researchers sharing one folder cost plain files 21.2 accuracy points." "Plain files" is undefined. The sentence also omits that 99% of these tasks had overwrite collisions, which is the mechanism and the reason the folder fix works.
14. Abstract and conclusion: "Agents should copy results forward as plain replies." Given W1 and W8, scope it: "with Qwen3 models and tool-call file access as tested".
15. §4: "Its Reviewer sees only the draft and turns right answers wrong in up to 16% of questions". This is a per-setting maximum. Give the k=3 pooled value next to it so it does not read as typical.

## What stands between this paper and acceptance

For a workshop, the measurement is publishable once the claims are aligned with the numbers. That means rewriting the abstract and introduction per W2, W3 and W4 and fixing the overclaims listed above, which is all text. The two changes that would most raise my score are:

- a failure decomposition for the file channels, with accuracy conditional on reading the notes (W1a), which is analysis only;
- one small run that separates delivery from discovery: auto-read notes, or a 24-call budget at k=3 (W1b).

Together they would show whether "files lose" is about the channel or about current models' tool use. A second model family (W8) and a fan-out figure with all three OS-style repairs (W6) would make it a strong workshop paper.
