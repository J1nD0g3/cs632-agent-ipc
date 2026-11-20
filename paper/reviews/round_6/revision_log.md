# Round-6 revision log

Snapshot before this round: `cs632-store/main_pre_round6.tex`. Build: 6 pages including references,
no undefined references, no semicolons in the body. Every number is a macro from `paper/numbers.tex`
(regenerated, no section skipped).

## Macros added or changed in `src/agentipc/paper_numbers.py`

- `RSixGenAZc`, `RSixGenATwo`, `RSixGenB`, `RSixGenC`: completion tokens relative to broadcast, mean over
  the three served-alone runs (replaces the single-run `RFourGen*`).
- `RSixAloneN`, `RSixHiN`: tasks per served-alone run at six and at 32 tasks at a time.
- `RSixWordingNullBound`: widest end of the wording intervals at the sizes whose interval contains zero
  (8B, 14B, 32B), for "its intervals lie within +-X points".
- `ZcPooledDiff`, `ZcPooledDiffLo`, `ZcPooledDiffHi`, `ZcPooledDiffN`: zero-copy minus broadcast at k=3,
  both datasets pooled, paired by task (replaces "no difference is significant").
- `AAWorst` now prints one decimal (2.2 instead of 2), matching B's A/A interval.

## Title and abstract

- Title: "Pipes or Files? Revisiting IPC for LLM Agent Pipelines".
- Timing now from three served-alone runs (`RSixTimeAZc`, `RSixTimeC`-`RSixTimeB`), with the reason
  (decoding dominates).
- Writing/reading split from the interleaved per-size run (`RSixWriteSigWord`, `RSixReadSigWord`) replaces
  the cross-run `RFourWSigWord` claim.
- k=16: `RSixKSixteenBGap` from the guard run, attributed to parallel writers, with the guard and heading
  recoveries. Removed "neither a larger KV cache nor twice the tool budget closes the gap" and
  "readers without an index skip the notes" (review quotes 2, 3).

## 1 Introduction

- Key observation restated as "prefill disagrees with both billed tokens and serving time" (systems quote 4).
- Timing numbers replaced by RSix macros, with the decode share. Removed "files need a model that uses
  tools well" (systems quote 5).
- Second and third observations: the write/read split, and parallel writers with the guard/naming fix.
- Contributions: "four channels and a cache-friendly variant of broadcast"; sensitivity list now payload,
  parallel writers, KV cache, tool budget, model size; "derive rules" softened to "draw guidance".

## 2 Channels (was "Five Channels")

- Removed channel D (handles) entirely. Zero-copy broadcast stated as a variant of broadcast.
- The confusing "differ in where its notes go ... and §4 separates the two" sentence split into two
  (systems quote 12), with no control labels.

## 3 Methodology

- cache_salt sentence corrected: channels never hit each other's KV but share capacity (methods quote 9).
- Tokens sent: counts tokens, not price, and APIs charge more for output (methods quote 10, systems W8).
- Serving time: vLLM counters split prefill and decode.
- Delivery: stated that it measures exposure (sources included), not use.
- Removed stage attribution (old Fig. 3b) and `RightMissAOne`.
- LLM-judge validation cut to one sentence (AlignScore AUC on synthetic pairs, kappa caveat). Removed the
  judge's acceptance rate and the entity-match sentence (incl. D's entity delivery).
- Harness: states the 2,048-token output cap. Strict accuracy now for B and C only (`StrictB`, `StrictC`)
  since `StrictMax` included D. Added that the k=1/3/5 question sets overlap and that cross-run comparisons
  are named.

## 4 Results

- Copying and zero-copy: paired pooled interval (`ZcPooledDiff*`) instead of "no difference is
  significant"; per-setting bound kept as a point-estimate statement.
- Pipe heading scoped to Qwen3-8B (systems quote 11). Removed the reference to old Fig. 3b.
- Files cost more tokens: D sentence removed.
- Serving time: rewritten from three runs per channel (`RSixTime*` with min-max for zero-copy), vLLM
  prefill time (`RSixPrefillTimeAZc`) and decode share (`RSixDecodeShareAOne`), generation ratios
  (`RSixGen*`), and the 32-tasks/400k-cache load (`RSixHi*`). Heading scoped to "At six tasks at a time"
  (systems quote 6). Removed "we cannot separate generation from sequential calls" with the single-run
  numbers.
- New Fig. 3 (`fig_split.pdf`, label `fig:split`) with a caption describing arms, panels and the three
  paired effects.
- New paragraph "Writing and reading both lose accuracy" from the interleaved per-size run (RSix*), replacing
  the cross-run A1r/A1w paragraph (RFour E1 macros). Nulls given as intervals; no control labels.
- "Files lose information when written and when read" became "Readers without an index skip the notes"
  (main-run reading evidence). D sentence removed. "C comes within 6.0 points" now "C trails broadcast by"
  (systems quote 7).
- Documents-in-prompt control for B: stated as a difference with its interval.
- Replay paragraph kept.

## 5 Sensitivity

- Fig. 4 caption states the RTX 3090 servers' 34,864-token cache.
- Larger payloads: D removed.
- Cache and tool-budget paragraphs merged into one ("Neither a larger cache nor a larger tool budget closes
  the gap"): one sentence on savings returning, one on the k=16 gap and the 24-call budget (marked as a
  separate run).
- Replaced "Parallel writers race on shared files" (clash split, k=3 fan-out DiD) with two paragraphs:
  k=8 fan-out (`RSixFan*`, two runs on the same tasks and cache, difference in differences named as such,
  systems quote 14) and the k=16 write guard / heading-only run (`RSixKSixteen*`), with notes recall.
  C's smaller k=16 loss attributed largely to its naming rule, compared with C's gap from the earlier
  run on the same tasks (stated as cross-run). The 72% clash rate kept as a descriptive clause.
- Removed "A fourth agent" (Fact-checker) and "Cheaper reads make the Writer skip the notes" (read_files).
- Model size: D removed; the 32B harness miss stated plainly (`PRescueThirtyTwoBMoved` of
  `PSizeThirtyTwoN`); the normalized rerun marked cross-run; added the within-run 32B B gap from the
  writing-control run (`RSixThirtyTwoTotal`). Pipe loss phrased as "we observe it only with that model"
  (methods quote 7). The 4B zero-copy mechanism now names both the order and the instruction's move from
  system to user turn (methods quote 8).
- Run-to-run noise: bound corrected to +-2.2; states the A/A covers only the RTX 3090 servers.

## 6 Related Work

- MAST sentence now refers to the delivery measure (stage attribution removed).
- IPC paragraph: the "prefix cache plays the role of shared pages, since every token is still sent"
  sentence rewritten (systems quote 15).

## 7 Conclusion

- Timing claim at six and 32 tasks at a time; pipe loss scoped to Qwen3-8B.
- Write/read split; the "store plain replies as files" suggestion now notes it was not run as a channel and
  cites the replay control's reading loss (systems quote 17).
- Removed "Files need a model that handles tools" and the 14B index clause. Added the guard/naming
  guidance for several writers. Removed "what in file access at sixteen questions causes the collapse"
  from the untested list.

## Not changed

- Figures 1, 2, 4 and their data (already without D).
- The RTX 3090 main-run numbers, documents-in-prompt controls, Researcher replay, cache and model-size sweeps.

## Audit fixes

Snapshot before these fixes: `cs632-store/main_pre_audit6.tex`. Each item was checked against `results/`,
`results_raw/` and `src/agentipc/` before the edit. Build: 6 pages including references, no undefined
references, no semicolons in the body, `paper_numbers` with no section skipped.

New macros in `round6()`: `RSixWCut{Four,Eight,Fourteen,ThirtyTwo}` (A1w tasks with any Researcher call
`finish_reason == "length"` in `p10_write_*` raw records: 16, 7, 1, 1) and
`RSix{Four,Eight,Fourteen,ThirtyTwo}WriteUncut{,Lo,Hi,N}` (A1w minus A1r without those tasks: 4B -5.7
(-9.7 to -1.7, N=134), 8B -3.7 (-7.5 to -0.2, N=143)).

1. Title: "Pipes or Files? ..." -> "\title[Messages or Files?]{Messages or Files? Revisiting IPC for LLM Agent Pipelines}".
2. Abstract: "it still takes RSixTimeAZc x broadcast's time, because decoding dominates" -> "it saves no serving time (RSixTimeAZc x broadcast's), because decoding dominates and its agents generate RSixGenAZc x the tokens".
3. Abstract: "the loss comes from the parallel writers ... recovers RSixKSixteenGuardOverB points" -> "much of the loss comes from the parallel writers ... recovers RSixKSixteenGuardOverB of those points".
4. Intro: "Serving time follows neither count." -> "Serving time does not follow prefill. It ranks the channels as tokens sent does, though less steeply." (ranking checked: B > C > A1-zc > A1 > A2 by both).
5. Intro: "decoding takes RSixDecodeShareAOne% of broadcast's request time, so zero-copy broadcast still takes ..." -> "Served alone at six tasks at a time, zero-copy broadcast saves no serving time (RSixTimeAZc x broadcast's). Decode intervals make up RSixDecodeShareAOne% of broadcast's request time summed over requests, and zero-copy's agents generate RSixGenAZc x the tokens." (dropped the duplicate "Plain files take RSixTimeB x ..." sentence, which stays in the abstract and Section 4).
6. Intro: "the model size decides which one costs more" -> "which one costs more varies with model size".
7. Intro and Section 5 heading: "naming rule" -> "heading rule".
8. Methodology: "The writing-control, timing, fan-out, cache, and model-size runs use one RTX PRO 6000 ..." -> "The other runs, for writing control, timing, cache size, k=16 with a write guard or a larger tool budget, fan-out, model size, and zero-copy replay, use one RTX PRO 6000 ..." (parenthesis turned into a clause per the style guide).
9. Section 4 pipe: "trails broadcast by ScopeATwoDVsAOne points (Lo to Hi)" -> "trails broadcast by ScopeATwoDVsAOneAbs points (a paired difference of Lo to Hi)".
10. Section 4 timing: "vLLM's counters show it spends only RSixPrefillTimeAZc x broadcast's time in prefill. Decode takes ...% of broadcast's per-request time, so the saved prefill barely moves serving time" -> summed-over-requests wording limited to the two p11 runs with counters (p06 has no `vllm_metrics`), the overlap and co-batching caveat, and "The pipe is faster, at RSixTimeATwo x, with zero-copy's summed prefill (RSixPrefillTimeATwo x) and broadcast's output (RSixGenATwo x), so prefill and output alone do not set serving time." The audit's "same output as zero-copy" and "likely because its shorter prompts make each decode step cheaper" were not used: A2 generates 1.0x broadcast, not zero-copy's 1.2x, and per-token summed decode time does not rise with prompt length across channels (B, with the longest prompts, is 14.2 ms against A1's 16.9 ms), so the cause is not shown.
11. Section 4 timing: "zero-copy's prefill time is RSixHiPrefillTimeAZc x" -> "zero-copy's summed prefill time is RSixHiPrefillTimeAZc x".
12. Section 4: "so notes passed as a tool argument are not cut off" -> "yet a Researcher call still hits that cap in RSixWCutFour of RSixN tool-write tasks at 4B and RSixWCutEight at 8B, which cuts the notes short or leaves none" ("a Researcher call" rather than "the tool call": at 4B the capped call is the first one, which emits no tool call, and the forced write then saves short notes).
13. Section 4: "it also lowers accuracy, by RSixEightWrite points at 8B (Lo to Hi)" -> "it also changes accuracy, by RSixEightWrite points at 8B (Lo to Hi), or by RSixEightWriteUncut (Lo to Hi) without the tasks whose write was cut off".
14. Section 4: "Which step dominates depends on the size. At 8B the write step's ... make up most of B's ..." -> "In point estimates, the larger step depends on the size. At 8B the write step's ... are most of B's ..., though the read step's interval reaches RSixEightReadLo".
15. Section 4: "The main run shows how reading fails." -> "The main run shows both steps."
16. Section 5: heading "Parallel writers cause the collapse." -> "Parallel writers drive the collapse."; "in two runs" -> "a cross-run comparison"; "Parallel writers, not payload size, cause B's collapse." -> "Each of the three Researchers sees only its questions and their documents, which does not significantly move broadcast or C. Parallel writers, more than payload size, thus drive B's collapse." ("does not significantly move" instead of the audit's "leaves ... unaffected": broadcast 0.0 (-2.9 to 3.0), C 3.0 (-0.5 to 6.5)).
17. Section 5: "two repairs on RSixKSixteenBGapN tasks." -> "two repairs on RSixKSixteenBGapN tasks (RSixKSixteenHeadingOverBN for the heading rule)."
18. Section 5: "C's smaller loss ... thus comes largely from its naming rule." -> "C's smaller loss ... likely comes largely from this heading rule."
19. Conclusion: "since decoding took most of each request's time at six" -> "since decoding took most of the summed request time at six".
20. Conclusion: "guard their writes or have them name files by content, since parallel Researchers that overwrite each other caused the largest loss we saw" -> "Parallel Researchers that overwrite each other were behind the largest loss we saw, so when several agents write to shared files, guard their writes or have each head its files with its questions, which in our test also kept them from sharing file names." (checked: Researchers shared a path in 0 of 59 Bh tasks against 46 of 60 B tasks in p12).
21. Conclusion: "or why prompt order matters at 4B" -> "or why the zero-copy prompt arrangement costs the 4B model accuracy".
22. Related Work: "our delivery measure tracks one of them, ignored input" -> "our delivery measure tracks part of one of them, ignored input: notes the next agent never reads, not notes it reads and ignores".

Length cuts to stay at 6 pages (no caveat, condition, interval or sample size removed):
- Fig. 2 caption: "Counted by tokens sent (a), copying the history is the accurate choice and files are the expensive one. Counted by ..." -> "By tokens sent (a), broadcast is the most accurate and files the most expensive. By ..."; "share of prompt tokens that the engine served from its prefix cache" -> "cached share of prompt tokens".
- Fig. 3 caption: dropped the sentence restating each step as an arm difference (panel (b) already says "each step against the one before"), and "four", "instruction", "as in broadcast".
- Methodology: dropped "and vLLM's counters split each request's time into prefill and decode" (Section 4 now states what the counters measure); "cached KV ... the cache's capacity" -> "KV ... its capacity".
- Section 4 timing: dropped "A heavier load does not change the picture."
- Word trims: "the Researcher's notes" -> "the notes" (B), "are told" (C), "the Writer and the Reviewer" -> "later agents", "the tokens of broadcast" -> "broadcast's tokens/prefill", "each of the six settings" -> "all six settings", "a single," -> "one", "thirty source documents" -> "thirty documents", "Notes that are overwritten" -> "Overwritten notes", "the guarded notes"/"the headed notes" -> "the guarded"/"the headed", "the Writer's and Reviewer's prompts" -> "the later agents' prompts", "drift we have not measured" -> "unmeasured drift", "its Reviewer, which sees only the draft," -> "its draft-only Reviewer", "whose sizes depend on" -> "that vary with", "In the writing-control run, which applies the same fix and runs broadcast alongside," -> "In the writing-control run," (Section 4 states the fix for that run).
