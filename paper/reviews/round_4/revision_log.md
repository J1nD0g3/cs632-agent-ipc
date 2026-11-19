# Round 4 revision log

Build: 6 pages including references, no undefined references or citations. Every number in the text is a
macro from `numbers.tex` (749 macros, no skipped sections).

## New macros (added to `paper_numbers.py`)

- `NotesCharsAOne`, `NotesCharsAZc` (in `main_run`): mean Researcher note length in characters at k=3 for
  A1 and A1-zc, from the same per-run notes that `NotesShorter` uses (1,570 vs 1,992).
- `RFourWSigWord`, `RFourSizesWord` (in `round4`): the number of model sizes whose A1w minus A1r interval
  lies below zero ("three") and the number of sizes ("four"). `gap()` in `round4` now also returns the
  mean and interval, and the macros it writes are unchanged.

## Abstract

- Cost is counted three ways: tokens sent, prefill computed, serving time.
- "Copying is the most accurate channel" is now scoped to small payloads and Qwen3-8B.
- Zero-copy keeps accuracy at 38-49% of the prefill "but saves no serving time" (E3).
- Files: up to `RFourTimeB`x the time because their agents generate more (E3).
- Writing through a tool call costs facts and accuracy at three of four sizes "with the instruction held
  fixed" (E1). This replaces the 27% shorter-notes sentence.
- k=16: B loses 34 points "and neither a larger KV cache nor twice the tool budget closes the gap" (E4).
- Dropped the 4B file-channel number. Kept the 4B zero-copy loss.

## Introduction

- Key observation is now "cost has to be counted three ways". Tokens sent is "what an API bills when it
  does not discount cached input". Removed "the cost a self-hosted deployment pays" for prefill. Added the
  E3 times: B at `RFourTimeB`x with `RFourGenB`x generated tokens, and zero-copy at `RFourTimeAZc`x despite
  the 61% prefill cut.
- "Savings shrink or vanish" became "Prefill savings shrink" (the 100k k=16 run shows they do not vanish
  with a larger cache).
- Contribution 2 now names the three counts.
- Cut "We propose no new protocol or engine change..." (Related Work now says the contribution is the
  measurement).

## Five Channels

- The Researcher's instruction sentence now points to Section 4, which separates wording from tool.
- A1-zc: removed "Only the order changes". It now says the instruction moves out of the system prompt,
  every token is still sent, and the new order changes what agents write, with note lengths
  (`NotesCharsAZc` vs `NotesCharsAOne`) (systems W2, methods W8).

## Methodology

- PRO 6000 runs: "a KV size set per experiment (100k tokens unless stated)" replaces "a fixed KV size"
  (systems W9).
- Tokens sent: "what an API bills without caching and an upper bound when the API discounts cached input"
  (systems W5).
- New metric "Serving time" (one channel alone on one GPU, six tasks at a time). Removed the old
  interleaved "Latency" metric.
- One sentence saying that counts of significant settings are not corrected for multiple comparisons
  (systems W10, methods W7).
- Validating fact delivery: shortened without changing its content. The entity check sentence is
  condensed, and the dpr citation is kept.
- Tasks: cut the usable-question counts (`HotpotUsable`, `WikiUsable`).

## Results

- Fig. 2 caption: labels in (b) are now "the share of prompt tokens that the engine served from its prefix
  cache". "(b) ... at a pipe's cost" became "at a pipe's prefill".
- Copying and zero-copy: "the gain is for self-hosted serving or APIs that discount cached input" became
  "the gain is in prefill alone".
- Pipe: shortened the scope control. Dropped the Reviewer-broke percentages (`ScopeATwoBroke`,
  `ScopeATwoDBroke`) and kept the gain, the gap to broadcast with intervals, and the prefill ratio.
- Files cost more tokens: removed the interleaved wall-time sentence (`WallFileMin/Max`, `WallAOne`).
- New paragraph "Serving time follows the generated tokens" (E3). It gives each channel's time and
  completion-token ratio, says prefill savings buy no time at this load, and says time ranks the channels
  close to tokens sent (systems W1, methods W10).
- Files lose information: "when they go to files through a tool call" became "when they go to files". The
  cause is now left to the control.
- Giving files the documents: "which lies in their notes" became "which lies in how notes are written and
  read" (methods W5).
- Replaced the A1w paragraph with "Writing through a tool call loses facts" (E1, four sizes). A1r (B's
  instruction, plain reply) matches A1 in notes recall at every size. It matches A1 in accuracy at 8B,
  14B and 32B, and is 5.3 points above it at 4B. A1w matches B's notes recall. Per-size A1w minus A1r
  values with intervals are given at 4B, 8B and 32B, and 14B shows 0.0 with its interval. Conclusion:
  the cost comes from the tool call, not the instruction, whenever the call drops facts (systems W6,
  methods W1). **Cut:** the 8B RTX 3090 A1w numbers (`WN`, `WChars`, `WCharsB`, `WNotes*`, `WAcc`,
  `WGapAOne*`, `WOverB*`).
- Reading the same notes: dropped the "reads the index in `RepIndexC`%" number.

## Sensitivity

- Larger payloads: k=8 and k=16 text kept and labeled as the RTX 3090 (35k) servers.
- Replaced the n=10 cache-pressure test (`PressNTwo`, `PressBC*`, `PressAZcC*`, `PressAccMax`) and most of
  the KV sweep with "The cache explains the lost savings but not the collapse":
  - k=8 KV sweep: kept zero-copy at 35k vs 100k and the accuracy shift.
  - E4 (k=16, 100k, 60 tasks): zero-copy prefill is `RFourKSixteenCompAZc` and B's is
    `RFourKSixteenCompB` (against 1.00 and 1.83 at 35k). The B, C, D and pipe gaps are given with
    intervals (systems W4/W7, methods W3).
  - **Cut:** the 400k sentence and the B/C KV-sweep ratios.
- Tool budget: new paragraph "The tool budget does not explain it either". It reports the 52% vs 29%
  budget hits and E4's B at 24 calls (`RFourBTwentyFour`, interval, N=60). **Cut:** the k=3 24-call
  sentence (`TwFourAccMax`, which had no interval).
- Race paragraph: now opens with "The collapse therefore stays with parallel writers and readers of
  shared files". "The race is not the whole loss" became "The race we see is not the whole loss". C is
  condensed to one sentence. **Cut:** "Message channels cannot race..." and the D fan-out numbers
  (`FanBDiffAbs`, `FanAOneDiffAbs`, `FanDDiff/Lo/Hi`). The fan-out DiD and its interval are kept.
- Fourth agent: shortened, and the "others move at most 1 point" clause is cut (`ChainOtherMax`).
- Cheaper reads: dropped the token cut (`BbTokCut`).
- Model size:
  - B range is now `PSizeFourteenGapB`-`PSizeFourGapB` (8-25), which no longer uses the unnormalized 32B
    28. The C range is unchanged (the normalized 32B C gap of 8.2 is inside it).
  - 32B file numbers come from E2 (normalized paths). B, C and D gaps are given with intervals, plus one
    clause saying the first harness missed the answers of 51 B and 59 D runs and that the rescore was
    close (systems W3, methods W2).
  - **Cut:** the rescore percentages, the C Researcher slip count, and the "Shorter notes are not
    universal" sentence (superseded by E1).
  - E5 added: with A1's notes replayed into both arms, zero-copy still loses `RFourZcReplayFour` at 4B
    (interval) and `RFourZcReplayEight` at 8B (interval includes 0). So the 4B loss comes from the
    prompt order the Writer and Reviewer see, not from the longer notes.

## Related Work

- Zero-copy broadcast "applies the common practice of putting shared content first, so our contribution
  is the measurement" (systems W8).
- IPC: "the prefix cache plays the role of shared pages, since every token is still sent" replaces "plays
  the role of zero-copy". The name A1-zc is kept because the figures use it.

## Conclusion

- Zero-copy: it kept 8B accuracy and computed 61% less prefill. It saved no serving time at our load,
  where time followed the generated tokens, and it cost the 4B model accuracy.
- Pipe: "the cheapest channel by all three counts", with the review caveat kept.
- Plain replies: "lost facts and accuracy at three of four model sizes" replaces the 8B-only claim.
- Files: the index recommendation is dropped (it did not hold at 14B or in the replay). "Plain files lost
  accuracy and cost more tokens in every setting" became "lost accuracy in every setting, sent more tokens
  than copying, and took longer where we timed them, though they computed 0.7-1.2x as much prefill"
  (systems overclaim 11, methods 11).
- Open questions are updated: why a tool call drops facts, why order matters at 4B, and what in parallel
  file access causes the collapse. The "why a tool call shortens notes" and "why 4B loses with zero-copy"
  items are replaced.

## Not addressed (no space or out of scope for this round)

- Results table per channel, Fig. 1 instruction segment, Fig. 4 intervals and N, and the Fig. 3
  paired-difference intervals. Figures were kept unchanged as instructed.
- Holm-corrected counts and equivalence CIs. The text now only states that the counts are uncorrected.
- Discounted-bill column at specific price ratios. A one-sentence upper-bound statement is used instead,
  with no invented prices.
- Human calibration, AlignScore threshold sweep, per-size stage table, answered rate and length-rule
  sensitivity, second model family, and new related work (AIOS, MemGPT, CacheBlend, etc.). The
  bibliography was kept unchanged.

## Audit fixes

Snapshot before these fixes: `cs632-store/main_pre_audit4.tex`. All 12 audit items were checked against the data and applied.

1. Abstract: "but it saves no serving time ... and take up to `RFourTimeB`x the time, because their agents generate more" -> "but with each channel served alone, six tasks at a time, it saves no time ... Served alone, they take up to `RFourTimeB`x the time and generate up to `RFourGenB`x the tokens" (causal "because" dropped; p06 calls 17.2/16.0/8.3 confound generation).
2. Intro: "Serving time differs again. Plain files take ... on one GPU, because their agents generate ..." -> "Serving time, measured with each channel served alone on one GPU at six tasks at a time, ranks the channels as tokens sent does. Plain files take ..., and their agents generate ..." (p06 time and tokens-sent rankings are identical).
3. Results: heading "Serving time follows the generated tokens" -> "Prefill savings buy no serving time"; "Broadcast takes 246 s" -> "Broadcast takes 246 s for all 100 three-question tasks"; added "They also make more model calls, in the same order, so for files we cannot separate generation from sequential calls"; load "six tasks at a time" stated; last sentence -> "the channels rank by time as by tokens sent".
4. Five Channels: "separates the two" -> "separates the two for B".
5. Methodology: "notes keep fewer facts in file channels" -> "notes in file channels keep fewer of the gold entities".
6. Results: "A1r gets B's exact instruction but replies" -> "A1r gets B's instruction with only its destination sentences changed to a reply, and in A1w it gets B's instruction and writes with write_file" (checked `OUTPUT_REPLY_MATCHED` in pipeline.py). Abstract: "With the instruction held fixed" -> "With the instruction's wording matched". Paragraph close: "not the instruction" -> "not the wording".
7. Sensitivity: "A larger cache restores the savings" -> "brings the savings back, fully at eight questions and partly at sixteen" (0.36 at k=8, 0.71 at k=16); "with 35k" -> "on the same tasks with the RTX 3090 servers' `BigKv`-token cache"; heading -> "The cache does not explain the collapse".
8. Heading "The tool budget does not explain it either" -> "A larger tool budget does not close the gap"; "24 calls change B's accuracy there" -> "Yet in the separate 100k-cache runs, 24 calls change B's accuracy ... and B's Reviewer still uses all 24 in `RFourBTwentyFourRevLimit`% of runs (`RFourBTwelveRevLimit`% with 12)".
9. "The collapse therefore stays with parallel writers and readers of shared files" -> "What remains is specific to files at sixteen questions, where three Researchers write in parallel and later agents search a larger workspace"; "B's change beyond broadcast's" -> "B's accuracy change from one to three Researchers, less broadcast's"; conclusion "what in parallel file access" -> "what in file access at sixteen questions".
10. Model size: range now says "counting Qwen3-32B with the path fix below"; rerun gaps now "trail the first run's broadcast" (cross-run).
11. Conclusion: `FileCompMin`--`FileCompMax` (B and C, 0.7-1.2) -> new `FileCompBMin`--`FileCompBMax` (B only, 0.7-1.1); "took longer where we timed them" -> "took longer when served alone"; "saved no serving time at our load, where time followed the generated tokens" -> "saved no serving time with each channel served alone at six tasks at a time".
12. Conclusion: added "An index helped Qwen3-8B find the notes among many files, most at sixteen questions, but not Qwen3-14B and not when the notes were one named file."

New macros (paper_numbers.py): `FileCompBMin`, `FileCompBMax` (file_compute_range), `RFourCallsB/C/D` (round4, p06 `llm_calls`, computed but not used in the text after the length cuts), `RFourBTwentyFourRevLimit`, `RFourBTwelveRevLimit` (round4, B Reviewer `hit_turn_limit` in p07_k16_b24 and p07_k16_kv100k).

Length cuts to stay at 6 pages (no caveat removed): "Prefill is only part of what a self-hosted deployment pays" -> cut; "Its losses come at the end" -> cut; "which lies in how notes are written and read" -> cut; "a RoBERTa-large alignment model" -> cut; "so a run reuses only its own prefixes and" -> cut; ", the highest" (conclusion) -> cut; Fig. 3 caption "which §4 reports" -> cut; first contribution bullet -> "with such controls"; third bullet -> "derive rules for choosing a channel"; Related Work "They change who talks ... We change the channel and count what the engine computes" -> "They keep the channel fixed, and we change it"; "not channels with tool-mediated files" -> "not tool-mediated files"; "unless the text names another reference" -> "unless stated"; KV sentence -> "and a 100k-token KV cache unless stated"; zero-copy notes length -> "grow from X to Y characters"; smaller word trims in Larger payloads, A fourth agent ("before review", "lowers B"), readv ("itself"), replay ("than B's"), race ("ever", "of them").
