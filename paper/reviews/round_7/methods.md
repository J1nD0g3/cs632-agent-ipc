# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (methods and statistics)

## Summary

The paper compares inter-agent channels in a Researcher-Writer-Reviewer pipeline on HotpotQA and 2Wiki with Qwen3 models on vLLM. The channels are broadcast (A1), a cache-friendly reordering of broadcast (A1-zc), a pipe (A2), shared files (B), and files with an index (C). Cost is counted three ways: tokens sent, prefill tokens computed after prefix caching, and wall time when one channel is served alone. The main claims are:

1. Zero-copy broadcast keeps broadcast's accuracy at 38-49% of its prefill, but it does not reduce serving time (1.09x).
2. Files cost more tokens and time, and they lose accuracy at two steps: the tool-call write and reading back. Which step costs more depends on model size.
3. At k=16, parallel Researchers that overwrite each other's files cause B's collapse. A write guard or a heading rule recovers about half of the loss.

The paper includes several causal controls: a matched-wording reply arm (A1r), a tool-write arm whose notes are copied forward (A1w), a Researcher replay, documents-in-prompt arms, one vs. three Researchers at k=8, a guard (Bn) and a heading-only rule (Bh) at k=16, and sweeps over cache size and model size.

I checked the numbers against `paper_numbers.py`, the run configs, and the raw records. The macros match the code. Client-side token counts match vLLM's own counters exactly on the PRO 6000 runs (for example, p11_alone_A1zc_r2: 470,580 computed tokens from both sources). The main problems are interpretive:

- The serving-time causal story conflicts with the paper's own vLLM counters.
- The "reading" step bundles much more than reading.
- The parallel-writer and overwrite attribution is stronger than the in-run data support.
- Several "N of four sizes" and "same accuracy" claims are uncorrected or lack an equivalence margin.

## Score: 3 / 5 (weak accept for a workshop)
## Confidence: 4 / 5

## Strengths

- **Paired and interleaved design.** Every channel runs on the same tasks. Job order is shuffled across channels and task sizes (`run.py`, `order_seed`). Each pipeline run has its own `cache_salt`, so no channel reuses another channel's KV. Bootstrap resampling is over tasks, which correctly treats the k questions of a task as a cluster.
- **The token accounting is verified.** On the PRO 6000 runs, the client's `prompt_tokens - cached_tokens` equals vLLM's `request_prefill_kv_computed_tokens_sum` exactly, and `num_preemptions_total` is 0 at c=6.
- **The control set is unusually thorough for a 6-page paper.** The A1r/A1w/B decomposition runs in one interleaved run per size. Replay holds the notes fixed. A2d/Bd add the documents. The guard and heading arms run in one k=16 run. A 4B zero-copy replay is included.
- **Honest disclosures.** The paper states that multiple comparisons are uncorrected, that the k sets overlap, that rescue rates are high (with a strict bound), that AlignScore agrees only moderately with a judge, and that serving-time sums overlap. An A/A rerun on the 3090 (±2.2 points) is reported.
- **Reproducibility.** Every number in the text is generated from `results/` by script.

## Weaknesses (most important first)

### 1. The serving-time causal claim conflicts with the paper's own counters (text/analysis only, plus needs new runs for the clean test)

The abstract says zero-copy "saves no serving time (1.09x broadcast's), because decoding dominates and its agents generate 1.2x the tokens". The section heading says "prefill savings buy no serving time".

The scraped counters tell a different story. Decode-interval time per generated token, `request_decode_time_seconds_sum / generation_tokens_total`:

| Concurrency | A1 | A1-zc | A2 | B |
| --- | --- | --- | --- | --- |
| c=6 (both repeats) | 16.9 ms | 14.9 ms | 13.9 ms | 14.2 ms |
| c=32 | 43.0 ms | 30.2 ms | — | 28.0 ms |

So zero-copy's prefill savings do shorten decode steps, by about 12% at c=6 and 30% at c=32. This fits the paper's own remark that prefill shares batches with decode steps. That remark also means the "96% decode share" understates prefill's cost: other requests' prefill chunks are charged to decode intervals. The share is also computed as decode/(decode+prefill), which leaves out queue time. That is harmless at c=6 but should not be called "request time".

The net 9% slowdown comes from zero-copy's Writer and Reviewer generating more tokens (324 vs. 266 generated tokens per request). That is a behavioral side effect of the prompt rearrangement, not a ceiling on what prefill savings can buy.

The pipe's 0.78x shows the same thing: with similar output, a shorter context (1.6k vs. 4.1k prompt tokens per request) makes decode cheaper per token.

All timing runs use Qwen3-8B on one RTX PRO 6000 (GPU 3). The accuracy and compute results come from RTX 3090s, where prefill is relatively more expensive than decode.

**Fixes:**
- (text/analysis) Report per-token decode time and generated tokens per request. Rephrase the claim as "zero-copy makes each generated token cheaper, but its agents generate 22% more tokens, so net time is 1.09x".
- (needs new runs) Time A1 and A1-zc with outputs held equal. Two options: run zero-copy replay (identical notes) with `min_tokens = max_tokens` set to A1's per-request lengths, or use `ignore_eos` with fixed lengths. Report per-task latency at c=1 as well, since a single pipeline's latency is what a user waits for. If possible, add one timing run on the 3090.

### 2. The "reading" step (B minus A1w) is mostly not reading (text/analysis only, plus needs new runs)

The step from A1w to B changes more than whether the Writer reads the notes from a file. In B, the Writer and Reviewer also:
- lose the documents from their prompts;
- run a tool loop with a 12-call budget;
- write `draft.md` and `final.md` through `write_file`, the same mechanism the paper says drops content;
- often depend on the forced-write rescue.

From the p10 raw records, the B rescue rates are:

| Size | Writer rescued | Reviewer rescued |
| --- | --- | --- |
| 4B | 100% | 84% |
| 8B | 55% | 25% |
| 14B | 45% | 73% |
| 32B | 35% | 10% |

B's Reviewer also exhausts its tool budget in 23% of 8B tasks. In the replay run, C's Reviewer hits the budget in 42% of tasks.

The 4B "reading" loss of -21.6 points therefore coincides with a Writer that never saved its draft unprompted. The replay control has the same confound: B and C still write their outputs through tool calls.

**Fixes:**
- (text) Call this step "downstream file handling" rather than reading.
- (analysis) Report accuracy split by rescued vs. non-rescued and by budget-hit vs. not.
- (needs new runs) Add an arm where the Writer and Reviewer get the notes file through `read_file` (or as an injected tool result) but answer in a plain reply. This isolates reading from tool-call output writing.

### 3. The "N of four sizes" counts and the size-dependent ordering are fragile under multiple testing (text/analysis only)

I computed sign-flip permutation p-values for the 12 writing-control tests (4 sizes x wording/write/read, p10 runs) and applied Holm at alpha 0.05:
- 32B write: -4.4, p = 0.0097. This fails Holm (threshold 0.0083).
- 8B write: -5.6, p = 0.0062. This passes narrowly (threshold 0.0071).
- The 8B write without truncated tasks has a CI ending at -0.2.

Under correction, "writing costs accuracy at three of four sizes" becomes "two, with a third borderline".

The ordering claim is weaker still. The intro says "which one costs more varies with model size". At 8B, the main model, write (-5.6) and read (-1.6, CI -5.3 to 2.2) are never tested against each other, and their intervals overlap. Other 8B runs put reading at 3-5 points:
- 3090 A1w run: A1w - B = 3.2 [0.3, 6.2] (`nWOverB`).
- Replay: B trails by 5 [2, 8].

There is useful evidence the paper does not use. The earlier round-4 cross-run A1w-vs-A1r estimates replicate the write effect at every size: 4B -9.2, 8B -5.3, 14B 0.0, 32B -4.3, all on 200 tasks (`nRFour*WMinusR`).

**Fixes:**
- Apply Holm or BH within each family of tests.
- Cite the round-4 replication as support for the write effect.
- Test write minus read per size.
- Remove or hedge "which one costs more varies with model size" in the intro and the conclusion.

### 4. The overwrite and parallel-writer attribution overreaches (text/analysis only, plus needs new runs)

The abstract says "much of the loss comes from the parallel writers, which overwrite each other's notes". In-run data from p12 and p07 (k=16, 100k cache):
- B tasks where no two Researchers wrote the same path still score 47.3% and 44.2% (14 tasks each), against 71-72% for broadcast. Overwriting cannot explain those tasks.
- The guard removes every clash (0% clash; writes rejected in 77% of tasks), yet B still trails by 15.3 points.
- At the k=8 fan-out, 97% of B tasks have a clash, so clash and no-clash cannot be separated there.

The DiD of -21.6 shows that three parallel Researchers hurt B. But "parallel writers" bundles three changes:
- each Researcher sees only its part of the context;
- there are more files to find;
- files get overwritten.

The one-Researcher reference (p01_cache_100k) ran on a different day and a different GPU (3 vs. 2). Broadcast's 0.0 change [-2.9, 3.0] is a useful within-pair drift check and should be described that way. The harness code for B, A1, and C did not change between those commits.

**Fixes:**
- (text) Say overwrites account for about half of the k=16 loss. Report the clash vs. no-clash split.
- (needs new runs) Add a fan-out arm where the harness gives each Researcher its own namespace (`r1/`, `r2/`, ...). This removes overwrites without the guard's error-and-retry turn. Run one vs. three Researchers in the same run.

### 5. The fact-level measures are weakly validated on real text, and "delivery" mostly counts source documents (text/analysis only, plus new annotation)

AlignScore at 0.5 agrees with a Qwen3-8B judge at kappa 0.29 and with Llama-3-8B at 0.22, and the two judges agree with each other at 0.24. The synthetic AUC of 0.996 is measured on easy, sentence-level edits.

Two internal signs that the measure is strict or noisy:
- Broadcast notes "state" only 45% of supporting facts, while the pipeline answers 72% correctly.
- In 76% of correct broadcast answers, the notes miss a supporting fact according to AlignScore (`nRightMissAOne`).

Several claims rest on this measure:
- tool-write drops facts (45% to 31% at 8B);
- overwritten notes lose facts (45/53/60/66%);
- B's notes hold 32% of facts.

Delivery in file channels counts every file the Writer read. 83% of B's Writer reads are source documents, which contain the supporting sentences verbatim. So "the files it reads state 87-94% of the facts in the notes" mainly measures document reads. It says little about whether the notes were delivered.

**Fixes:**
- (needs new annotation) Hand-label about 200 real (notes, fact) pairs to calibrate AlignScore.
- (analysis) Report the lexical and entity measures you already have (for example, entity recall 91% for A1 vs. 82% for B notes) next to AlignScore.
- (analysis) Compute delivery from notes files only, or drop the delivery claim.

### 6. "Same accuracy" for zero-copy is an equivalence claim with no margin, and 2Wiki shows a small consistent cost (text/analysis only)

Pooled k=3 is -0.8 [-2.9, 1.4]. Under exact match, zero-copy is significantly lower on 2Wiki at both k=3 and k=5:
- k=3: -3.6 [-6.4, -0.4]
- k=5: -3.2 [-5.6, -0.9]

Under the paper's own lenient accuracy, 2Wiki k=3 is -2.7 [-6.0, 0.4]. The paper says "up to 4 points lower on 2Wiki" but does not say these are significant.

**Fix:** State an equivalence margin and run TOST (90% CI inside ±3 points, for example). Report per dataset. Soften "keeps copying's accuracy" and "Zero-copy ordering costs only the 4B model" to note the 2-4 point EM cost on 2Wiki at 8B.

### 7. Cross-run and cross-GPU comparisons are not all labeled, and drift is checked only on the 3090 (text/analysis only, plus a cheap new run)

The paper says "we name the comparisons that cross runs". Some are not named:
- The scope controls (t09_scope ran only A2d and Bd) are compared with t07_main's A1, A2, and B. This underlies "Missing sources therefore do not explain the loss" and the A2d result.
- The intro's "It ranks the channels as tokens sent does" compares PRO 6000 timing runs (100 tasks) with 3090 token counts (300 tasks).
- The A/A check covers only the 3090.

**Fix:**
- (text) Label these comparisons as cross-run.
- (needs new runs, small) Run an A1/B A/A on the PRO 6000.

### 8. Prefill in interleaved runs depends on what else is running (text/analysis only)

In the main and sensitivity runs, channels share KV capacity. A1-zc's k=8 ratio (0.83x) and B/C's ratio above 1x on the 35k cache depend on the B/C/D footprints running alongside them. A deployment serving one channel would see different hit rates.

The 3090 runs did not scrape `num_preemptions_total`. Recomputation after a preemption is not counted in `prompt_tokens - cached_tokens`, and at k=16 on a 35k cache, preemptions seem likely.

**Fix:** State this caveat. Where possible, cite the served-alone counters. Check the 3090 server logs for preemptions at k=8/16.

### 9. The rescue asymmetry and its rationale (text/analysis only)

Only file channels get a second chance. The stated rationale, "since frameworks take an agent's last message as its output", argues for taking the reply as the output, not for forcing a write. The strict bound (B drops to 18%) counts a run as wrong even when the forced write produced a correct draft, so it is not informative.

**Fix:**
- Report accuracy under a "reply-as-output" policy. This is a pure re-scoring of `run.reply`, the reply each agent gave before the forced write (needs a check that the replies hold the draft).
- Report accuracy for rescued vs. unrescued runs.
- Rewrite the rationale.

### 10. Generality (needs new runs, or scope language)

The setup is narrow:
- one model family (Qwen3), with thinking off and greedy decoding;
- one prompt set and linear three-agent chains;
- multi-hop QA with short answers;
- serving measured on one GPU type with 8B only.

The pipe's loss appears only at 8B (10 points; 0-2 at 4B, 14B, and 32B, and small at k=8 and k=16 even at 8B). That suggests a prompt- or model-specific behavior rather than a channel property.

**Fix:** Run the core k=3 comparison with one non-Qwen open model (needs new runs), or scope the abstract and conclusion to Qwen3.

### Minor

- The accuracy metric is lenient: gold inside a prediction of at most gold+4 words. I checked that the k=3 pooled gaps hold under EM and F1 (A2 -10.6 EM, B -7.1, C -4.7). Saying so in one sentence would pre-empt the concern.
- "The loss is not the longer notes": the 4B gap goes from 7 to 5.8 under replay. "Not mainly" is more accurate.
- The 32B path-normalized rerun compares with the first run's broadcast; the paper labels this cross-run. Path slips occur only at 32B (0-1 slips at 4B/8B/14B), so the other sizes need no rerun. Saying this would help.
- Bootstrap over 150-300 tasks with 2,000 resamples is fine. Percentile intervals for DiD on 100 tasks are fine.

## Questions for the authors

1. Can you report, for each channel in the c=6 and c=32 timing runs, generated tokens per request and decode time per token? Would you accept the reframing in Weakness 1?
2. How many of B's Writer rescues follow a plain-text reply that already holds the full draft? What is accuracy when the reply is scored directly?
3. Were there preemptions in the 3090 k=8/k=16 runs? If so, how much recomputation is missing from "tokens computed"?
4. In A1w, how often are the tool-call notes cut at the 4,096-token cap because JSON escaping inflates their length? Do notes that are not truncated still lose facts at 8B?
5. Is the p10 task set a subset of p02's (same seeds and first-N), so that results can be paired across rounds?
6. Was the one-Researcher k=8 reference run on the same GPU model, driver, and vLLM build as p13? Was its server config (KV 100k) identical?
7. With the guard, how many Researchers retried under a new name, and how many dropped those notes?

## Sentences that overclaim or mismatch the code or numbers

- Abstract: "Served alone at six tasks at a time, it saves no serving time (1.09× broadcast's), because decoding dominates and its agents generate 1.2× the tokens." Per-token decode is 12% faster under zero-copy (14.9 vs. 16.9 ms). The slowdown is the extra output, not decode dominance as such.
- §4 heading: "At six tasks at a time, prefill savings buy no serving time." They buy cheaper decode steps. The net is zero because the prompt order changes output length.
- §4: "Summed the same way, decode makes up 96% of broadcast's request time." The code computes decode/(decode+prefill) and excludes queue time. Decode intervals also absorb other requests' prefill chunks.
- Abstract: "much of the loss comes from the parallel writers, which overwrite each other's notes." Guarded B has zero overwrites and still trails by 15.3 of 30.4 points. Unclashed B tasks still trail by about 24-28 points.
- §5: "Parallel writers, more than payload size, thus drive B's collapse." The fan-out bundles split context, more files, and overwrites, and its reference is cross-run on another GPU.
- Intro: "files lose information at two separate steps, writing and reading, and which one costs more varies with model size." At 8B the ordering is not significant, and other 8B runs show reading costing 3-5 points.
- Abstract: "writing notes through a tool call costs accuracy at three of four Qwen3 sizes". The 32B write effect (p ≈ 0.010) does not survive Holm across the 12 writing-control tests.
- §4: "Reading the notes back from files costs accuracy at three sizes, 4B, 14B, and 32B." This step includes tool-call output writing, the forced-write rescue (100% of 4B Writers), and tool-budget exhaustion.
- §4: "At 8B the write step's −5.6 points are most of B's −6.4 against broadcast". This is a point-estimate statement from one run. The 3090 runs put 8B reading at 3.2 [0.3, 6.2] and 5 [2, 8].
- Fig. 2 caption: "zero-copy keeps that accuracy at a pipe's prefill". On 2Wiki, EM is significantly lower at k=3 and k=5.
- §5: "Zero-copy ordering costs only the 4B model". Same EM caveat at 8B on 2Wiki.
- §3: "Each task runs once per channel, and we name the comparisons that cross runs." The A2d and Bd comparisons, and the timing-vs-tokens ranking, cross runs without being named.
- §4: "Missing sources therefore do not explain the loss." This is cross-run (t09_scope vs. t07_main), 8B only.
- §4: "The files it reads state 87–94% of the facts in the notes." Most of these reads (83%) are source documents, so this measures document exposure, not delivery of the notes.
- §3: "since frameworks take an agent's last message as its output". This argues for scoring the reply, not for forcing a write.
- Conclusion: "Parallel Researchers that overwrite each other were behind the largest loss we saw". Overwrites explain about half of it.
- Conclusion: "It saved no serving time at six or 32 tasks at a time, since decoding took most of the summed request time at six". Same issue as the abstract. At c=32, per-token decode under zero-copy is 30% faster.
