# Round 14 revision log (text and analysis only)

Snapshot before this round: `/mnt/sda/heojin/cs632-store/main_pre_round14.tex`.
No new experiments. Every new number is a macro from `src/agentipc/paper_numbers.py` (new section `round14`).
The generator reports no skipped section, and no existing macro changed value.
Build: 6 pages including references, no undefined references, about two reference lines of slack.

## New macros (section `round14`)

| Macro | Value | Meaning |
| --- | --- | --- |
| `RFourteenRevDraft{Four,Eight,Fourteen,ThirtyTwo}` | 73, 97, 6, 100 | Reviewer reads `draft.md` (io_ops, `_norm_path`), B arm of `p16_store_*`, % of tasks |
| `RFourteenRevDraft{size}Min/Max` | 4B 71–73, 8B 94–97, 14B 1–8, 32B 98–100 | Same, over every file arm (B, Bs, Bt, Bs0, Bt0) of p16, p17 (14B, 32B), and p18 (14B) |
| `RFirstRevDraft{Tool,Told,FirstUntold,FirstTold}` | 5, 1, 2, 8 | Same, per p18 arm (computed, not printed) |
| `RFourteenRevDocsMin/Max` | 85–100 | 14B Reviewer reads any file under `docs/`, every 14B file arm of p16/p17/p18 |
| `RFourteenNotesUnderDocsMin/Max` | 79–83 | 14B B Researchers save notes under `docs/` (p16, p17, p18) |
| `RFourteenRevNotesToolMin/Max` | 79–82 | 14B B Reviewer opens the Researcher-written notes (p16, p17, p18) |
| `RFourteenRevNotesStoredMin/Max` | 1–15 | 14B Reviewer opens the stored notes in stored-reply arms (not printed) |
| `RFirstStoredFinalMin/Max`, `RFirstStoredDraftMin/Max` | 43.6–45.3, 44.7–62.0 | p18 stored-reply arms (Bt, Bs0, Bt0): final and draft accuracy |
| `RFourteenEightWriteCopyAbs` | 4.7 | abs(A1w − A1r) at 8B, crossed run |
| `RFourteenFixMin/Max` | 14–20 | Single harness changes: told path at 32B (14.2), write guard (15.1), heading rule (18.1), separate folders (19.8) |
| `RFourteenBrGapMin/Max` | 22.2–40.2 | abs(Br − A1w) across sizes, reply-output runs |
| `RFourteenGpuDrift{Min,Max,Lo,Hi,N}` | −1.3 to 1.2 (intervals −3.2 to 2.8), N = 200 | 8B size run (RTX PRO 6000, 100k cache) minus main run (RTX 3090, k = 3), same tasks and cap, per channel A1, A1-zc, A2, B, C |
| `RFourteenRescReplied/Repeated/RepliedShare` | 173 / 7 / 96% | Main run, B, k = 3: rescued Writers/Reviewers that had not used up the budget, by how they stopped |

Helper `_macro(m, name)` reads an already-generated macro back as a number, so derived ranges use the same values as the printed ones.

## Changes by review item

### 1. 14B Reviewer (methods W1, systems W5b)
- Results, crossed runs: at 14B B's drafts match copying, but B's Reviewer reads `draft.md` in 6% of tasks against 73%, 97%, 100% at 4B, 8B, 32B, and its final answers are less accurate than its drafts. Removed "the loss appears at the Reviewer".
- Stored-reply paragraph (retitled "Later agents often miss the stored reply", labeled exploratory): removed "revises the gain away". It now says that in every 14B file arm the Reviewer reads `draft.md` in 1–8% of tasks and documents under `docs/` in 85–100%, and writes its own answers. p18's stored-reply arms end at 43.6–45.3% whatever their drafts score (44.7–62.0%). With tool-written notes, 14B Researchers save notes under `docs/` (79–83%), the Reviewer opens them (79–82%), and final accuracy is 64.7%. Stated as an observation: final accuracy tracks whether what the Reviewer reads includes the notes. The 23/127 split is kept as supporting, observational evidence.
- Conclusion: removed "undid the Writer's gain" and "skips notes listed first and named". It now states the 14B Reviewer rarely reads `draft.md` (at most 8%), and lists the causal test (draft in the Reviewer's prompt, stored notes under `docs/`) as future work in one sentence.
- Intro and conclusion rule: "lead every later agent to shared state" became "naming the notes' path for later agents (which helped at 32B but not at 14B)".

### 2. Scope of recommendations (systems W1, methods W4/W11)
- Intro: rules now "for pipelines and file harnesses like ours (§7)". The unconditional rule list is gone from the intro.
- Conclusion: the copy-over-files rule rests on a 12-call budget, 2,048/4,096-token caps, and a rescue in 72% of B's main-run tasks. Single harness changes recovered 14–20 points in specific settings, so a better file harness may close the gap. Rule 1 now says "except with the smallest model".
- Abstract: "In our file harness, ...".

### 3. 8B decomposition and "tool protocol" (methods W2, systems W5d)
- Removed "Much of the files' accuracy cost comes with the tool protocol" from the abstract, intro, and conclusion. The intro's second observation is now concrete: at 4B/14B/32B later agents reading tool-written notes as files lose 8–22 points against copying them. At 8B more of the loss comes from the Researcher's tool-call write.
- Abstract: "At 8B, more of the loss comes from writing the notes through a tool call (4.7 against 2.9 points, neither Holm-significant)."
- Results: "More of B's gap there comes from the tool-call write than from the file channel (−4.7 and −2.9 points), though the post hoc contrast cannot tell the two apart (−1.8, −7.1 to 4.0)." This reports the previously unprinted Dvw contrast at 8B.
- "Mostly in rescued tasks": removed from the abstract. In Results the crossed-run split now covers all three sizes: larger on rescued tasks at 14B/32B (11.3 vs 1.0, 15.1 vs 3.1), not at 8B (1.3 vs 5.9), descriptive. The main-run split (9.4 vs 10.0) was already present.
- The heading "The file channel's tool protocol often fails" became "The file harness often fails".

### 4. Abstract (systems W2, W3, W5c)
- Zero-copy: "As decoding dominates, its runs take 1.09× broadcast's time." The 4B caveat: "with Qwen3-4B its prompt layout costs 7.0 points." "Per setting" added to the 38–49% range, and the point estimate (−0.8) added to the interval.
- Pipe: added "but with 8B at up to five questions it loses up to 14.9 points".
- "The most accurate channels are broadcast and zero-copy" became "broadcast is the most accurate channel" (zero-copy was not tested against C, and no equivalence was claimed).
- The k = 8 sentence was made shorter. It now reports the within-run folders effect (19.8 over one shared folder), and the DiD stays in §5.

### 5. Bs0, open rates, exploratory label (methods W5)
- Bs0 reported: the Writer opens `00_notes.md` in 21% of tasks untold (70% told). Bs0's draft and final are inside the reported p18 ranges.
- Open rates next to each effect: 32B told (Writer 86 vs 26, Reviewer 63 vs 6). 14B told: the Writer opens told `notes.md` in 5% vs 9% untold (the failed manipulation is now visible). First-listed: 21%/70%. Reviewer: draft reads 1–8%.
- "The told and first-listed runs below are exploratory."

### 6. Other overclaims
- Intro: "The one study that varies the channel" became "A preprint compares ..., and blackboard systems share state ..., but neither compares tool-read files with copying." The blackboard citations moved from Related Work into this sentence.
- Intro: the prefill reason now includes "while file-channel tool calls resend cached prefixes" (systems sentence 6).
- §2: the Researcher's instructions also differ in A1-zc by coming after the documents. Channels also differ, with files, in how agents give outputs (systems 8, methods 16).
- A1-zc: says what the prompt holds (team description, history, role instruction), and that reuse leaves the input unchanged, so A1-zc's accuracy differences reflect the layout (systems W3).
- Runs paragraph: the comma-spliced run-on was split into sentences, in consistent past tense (systems 10).
- Timing: "one channel per server, six concurrent tasks". "Decode accounts for 96% of broadcast's prefill-plus-decode time" by vLLM's counters. Per-run range 1.08–1.10×. Removed "cuts the prefill a deployment pays for" (systems 12–14, methods W9).
- Pipe heading: "The pipe's Reviewer turns right answers wrong", which the flip evidence supports (systems 15).
- Fact coverage: "a weak measure" added at the 32% vs 45% sentence. "By point estimate" added for the size pattern. Removed "We do not know why a tool-call write lowers fact coverage" (systems 16, methods W7).
- Removed "Of B's Writer's reads, 83% go to source documents", a per-operation share driven by file count (methods W8). The heading became "B's Writer often skips the notes".
- Write-copy significance: "significantly after correction only at 4B, though at 8B and 32B its uncorrected intervals also exclude zero (−4.7 and −4.0)" (systems W10, methods W10).
- Statistics: size-run comparisons are uncorrected. The first Holm family was chosen after earlier runs had estimated several of its effects.
- Drift: wording-run drift now carries intervals (−3.6 to 3.1). New cross-GPU check: the 8B size run on the RTX PRO 6000 repeats 200 main-run tasks at the same cap, and channels move by −1.3 to 1.2 (intervals within −3.2 to 2.8). "Drift across GPUs or caps is unmeasured" became "Cap drift is unmeasured" (systems W4, methods W6).
- Removed the cross-run "pipe with documents differs by −3.0" result, which falls inside the drift band and has no A1 of its own (methods W6, sentence 13).
- k = 16: "small next to B's 33.9-point gap in them" now names the run each gap comes from (systems 19).
- k = 8: "at least two Researchers wrote to the same path, so one could overwrite another's notes (a lost update)" (systems W11).
- Rescue provenance: "nearly all others had replied" became a macro (96%, 173 vs 7) (methods minor).
- Fig. 4 caption: the cache is "shared by six concurrent tasks of mixed channels" (systems 23, W8).
- D and Br are cut to one sentence each. Br's exclusion reason is relative to B ("its later agents reply rather than write"), and the sentence states that its Writer rarely opens the notes and reads no file at 32B (systems W9, methods minor).
- Table 1: dropped the "three runs" row, which the text reports as a spread (systems W7).

### Cuts made to keep 6 pages (no condition, interval, or sample size dropped from a kept claim)
- Removed the 4B write-cost sensitivity without cut-off tasks (−6.6), D's k = 3 accuracy, token, and prefill ratios, and the per-size Br/B lists. Removed the restating sentences that closed the timing paragraph and the conclusion's pipe summary (still in the abstract and §5).
- Shortened the captions of Fig. 1 and Fig. 3 to one line each. Fig. 3's caption no longer repeats "B's Researcher prompt in all arms" or "Copying gives later agents A1's inputs", which the text and the Table 1 caption state.

## Not done, and why
- New runs (any review item): out of scope this round. This covers a practitioner file harness (24 calls, 4,096 cap, listed and named notes, write guard), a 14B causal test (draft in the Reviewer's prompt, notes under `docs/`), a shared-system-prompt zero-copy layout, saturation throughput, channel-alone prefill on the 3090, B at the 4,096 cap on the main tasks, and a second model family.
- Human AlignScore calibration: needs annotation. The text now caveats the measure.
- Runs table (systems W4): no room on six pages. The Runs paragraph was split into one sentence per run instead.
- Cached-input pricing cost (systems W2): needs a price model (discount and output price). No room for a third cost.
- Redesigning Figure 3 and relabeling Table 1 rows (systems W7): figure work, outside a text-only round.
- One-line explanations for C < B at 14B, the incomplete k = 16 task, and whether the `workspace/` bug hit other sizes (systems W12): needs new analysis, and there was no room.
- Equivalence claim for zero-copy (90% interval inside ±3, post hoc): not stated. Instead, the claim was softened to "broadcast is the most accurate channel".
- Renaming zero-copy, and citations on instruction position: not done, to avoid renaming across figures and adding references on a full page. The A1-zc paragraph now says that accuracy differences reflect the layout.
- Dvw as a Table 1 row: reported in the text for 8B only, for space.

## Self-audit (meaning audit of the diff against the snapshot)
I checked every changed sentence for macro direction, scope, and cross-run labels.
- Abstract "lose 8.9 and 8.2 ... (Holm-corrected)": these are abs(B − A1w) at 14B/32B, which are Holm-significant. The 4B value (22.0) is also Holm-significant. Fixed the placement of "(Holm-corrected)" so that it no longer attaches to the rescue clause.
- Abstract "4.7 against 2.9 ... neither Holm-significant": A1w − A1r at 8B (p = 0.013, not Holm) and B − A1w at 8B (p = 0.12). Correct direction (costs as positive magnitudes).
- "More of B's gap ... (−4.7 and −2.9)": B − A1r = (A1w − A1r) + (B − A1w). Dvw = (A1w − B) − (A1r − A1w) = 2.9 − 4.7 = −1.8. The sign matches.
- "Its Reviewer reads draft.md in only 6% ... against 73%, 97%, 100%": all four are the B arm of p16, same definition.
- "1–8% ... 85–100%": ranges over every 14B file arm of p16/p17/p18. The text says so ("crossed, told, and first-listed runs").
- "final accuracy in the first-listed run is 64.7%": I first wrote "in that run" next to a range over three runs. I fixed it to name the run.
- "tracks whether what the Reviewer reads includes the notes (observational)": the evidence is descriptive, and no causal word was used.
- Zero-copy "−0.8 points from broadcast": the sign is A1-zc − A1. I added "from broadcast" so the baseline is stated. Earlier I had written "or −0.8 points", which hid the baseline, and I fixed it.
- "Its point estimates are within 2.7 points of broadcast per setting (3.6 by exact match)": same macros as before. "Trails by up to" became "within", which is the same bound.
- Lauer–Needham: I had briefly shortened this to "the two structures are duals", which would misattribute the paper (message-based vs monitor-based systems). I restored the original subjects.
- Intro rule: "helped only at 32B" implied a test at every size. It now says "helped at 32B but not at 14B" (the told runs were 14B and 32B only).
- Abstract k = 8 sentence: I first dropped the channel ("separate folders recover 19.8") and then fixed it to "raise files' accuracy by 19.8 points over one shared folder" (REightFoldersOverB, within one run). The 20.4 DiD stays in §5.
- Told runs: "in the file channel" was lost in compression. I restored it as "file-channel tool-written notes".
- GPU drift: the direction is the size run minus the main run. The text gives the symmetric range and names "the other GPU and cache at the same cap". The two runs differ in GPU and KV cache only (same model, cap, budget, concurrency).
- Timing "1.08–1.10×": the min and max of the same three per-run ratios whose mean (1.09) the abstract uses.
- The cross-run labels kept are the 32B told vs copied reply, folders vs one-Researcher B, the documents control, the budget doubling, the size-run 32B rerun, and the timing runs.
- No semicolons in the body. No mention of any modified vLLM.

## Meaning-audit fixes (`meaning_audit.md`, 8 items)

I checked each fix against `paper_numbers.py` and the raw records before applying it. No macro changed and `numbers.tex` was not edited.

1. **Abstract, 8B costs.** Verified: `RFourteenEightWriteCopyAbs` = |A1w − A1r| at 8B (4.7, on copied notes), `RThirteenEightFileToolAbs` = |B − A1w| at 8B in p16 (2.9), and Dvw = 2·A1w − B − A1r = −1.8 (−7.1 to 4.0). Neither cost and not the contrast is Holm-significant. Applied as proposed, plus "points" after 2.9: "At 8B, by point estimate, writing the notes through a tool call costs more (4.7 points on copied notes) than reading them as files (2.9 points), but neither cost nor their difference is Holm-significant."
2. **Intro, 8B.** Same check. Applied a reordered version so that "neither cost" follows both costs: "while at 8B the Researcher's tool-call write costs more than the file channel by point estimate, but neither cost nor their difference survives correction (§4)."
3. **§4, 8B decomposition.** Verified B − A1r = (A1w − A1r) + (B − A1w). Applied as proposed, except that "the post hoc contrast cannot tell the two apart" became "their post hoc contrast, −1.8 points (−7.1 to 4.0), is not significant", because the style guide bans anthropomorphic metric verbs ("tell").
4. **Abstract, timing.** Verified: `RSixTimeAZc` and `RSixGenAZc` come from the same three alone runs (p06, p11 r2/r3) at concurrency six (`ConcWord`). Applied as proposed, split into two sentences: "With six concurrent tasks, it generates 1.2× broadcast's output tokens and, as decoding dominates, its runs take 1.09× broadcast's time. With Qwen3-4B, its prompt layout costs 7.0 points."
5. **§4, Br.** Verified: `RFourteenBrGapMin/Max` is the range of |Br − A1w| over the four p14 (reply-output) runs (25.6, 24.0, 22.2, 40.2). `RThirteenFourteenBrOpen` = 97 and `RThirteenThirtyTwoBrNoRead` = 100, so "reads no file at 32B" holds. Applied as proposed.
6. **§4, 14B stored notes.** Verified: `RFourteenRevNotesStored` is the Reviewer's open rate of `notes.md`/`00_notes.md` over the stored-reply arms (Bs, Bt, Bs0, Bt0) of p16/p17/p18 at 14B (1–15%). Applied the audit's second option, as a parenthesis inside the tool-written sentence so the "With tool-written notes" scope still covers the 64.7% final accuracy: "the Reviewer opens them in 79–82% (against 1–15% for the stored notes), and final accuracy in the first-listed run is 64.7%." A first try as a separate sentence cost a line.
7. **§5, GPU drift.** Verified: `p02_size_8b` ran on an RTX PRO 6000 with 6,250 blocks (100k tokens, `queue_pro6000.sh`), `t07_main` on RTX 3090s (34,864 tokens), both with cap 2,048, budget 12, concurrency 6. Applied with the cache sizes in parentheses to save a line: "on an RTX PRO 6000 (100k-token cache) instead of RTX 3090s (34,864-token cache), at the same cap and tool budget".
8. **§4 opener.** Applied "datasets pooled". To save the line the opener took on its own, the sentence moved to the end of the Runs paragraph in §3 as "Unless noted, §4 uses the main run (8B, k = 3, datasets pooled)." Its scope (§4 only) is unchanged.

### Trims to keep 6 pages (no condition, scope qualifier, interval, sample size, or comparison reference dropped)
- Abstract: "LLM agents in a team pass results" became "LLM agents pass results" ("the next agent's prompt" keeps the team).
- Intro: "so the choice comes down to cost, and LLM agents change the costs" became "..., which LLM agents change". "so each copied token is prefilled again" became "so copied tokens are prefilled again". "Our contribution is a measurement" became "We contribute a measurement".
- Runs: "Servers configured the same way" became "Servers set up the same way". "a 100k-token KV cache" became "a 100k-token cache" (KV cache is defined one sentence earlier). "prefixed file paths" became "prefixed paths". Br's "whose Writer and Reviewer reply" became "whose later agents reply" (the same words §4 uses).
- §4 broadcast paragraph: dropped "more than any other channel" after 72.3%, which restated the paragraph's heading ("broadcast is the most accurate channel").
- §4 pipe paragraph: "against at most 2% in broadcast" became "(broadcast: at most 2%)".
- §4 crossed runs: "vary both at once" became "vary both" (the clause on the stepwise split states why). "changes accuracy significantly after correction only at 4B, by −8.7 points" became "the tool-call write's effect survives correction only at 4B (−8.7 points)". "than on the others" became "than on others".
- §4 stored reply: "Accuracy rises by 14.2" became "Accuracy rises 14.2", and "accuracy moves by 0.9" became "accuracy moves 0.9". "save the notes under docs/" became "save them under docs/". "tracks whether what the Reviewer reads includes the notes" became "tracks whether the Reviewer reads the notes" (same condition).
- §5 noise paragraph: "is not deterministic" became "is nondeterministic". "keeps both channels' rerun-minus-original intervals" became "keeps their ..." (broadcast and B are the only antecedent).
- Tried and reverted: "share one folder" shortened to "share one" in the intro, and "B's Reviewer" shortened to "the Reviewer" at 32B. Once the other trims fit, these were no longer needed.

### Check
- `latexmk`: 6 pages including references, no undefined references or citations, no overfull boxes. No semicolons in the body. No mention of a modified vLLM.
