# Round 11 revision log

Snapshot before edits: `/mnt/sda/heojin/cs632-store/main_pre_round11.tex` (and `refs_pre_round11.bib`).
Build: 6 pages including references, no undefined references. `paper_numbers` regenerated with no
skipped sections. The 99 new macros are additions only; no existing macro changed value.

## Macros added (`src/agentipc/paper_numbers.py`)

In `round10()`, from the p16 raw records and rows:
- `RTen{Size}RescueReplyFile`, `RTen{Size}RescueToolFile`: share of Bs and B tasks in which the Writer or
  the Reviewer needed the forced write (4B 100/100, 8B 44/66, 14B 100/77, 32B 43/43).
- `RTen{Size}WriteCopyEm` (+`Lo`, `Hi`): the copied-notes write effect (A1w minus A1r) under exact match.
- `RTen{Size}WriteCopyHotpot`, `RTen{Size}WriteCopyTwoWiki` (+`Lo`, `Hi`, `N`): the same effect per dataset.
- `RTen{Size}WriteCopyClean` (+`Lo`, `Hi`, `N`), `RTen{Size}WriteCopyCut`: the effect without A1w tasks
  whose Researcher call hit the token cap or needed the forced write (4B: 18 tasks, -8.7 to -6.6).
- `RTenDriftMax`, `RTenDriftLo`, `RTenDriftHi`: PRO 6000 repeat check. p16 reruns A1r, A1w and B of p10 on
  the same tasks and settings. The largest per-arm paired difference is 0.9 points, and all intervals lie
  within -3.6 to 3.1.

In `round10_text()`:
- `RTenCell{Effect}{Size}`: Table 1 cells, bold with a dagger when Holm-significant.
- `RTenHolm{Effect}AbsMin`, `RTenHolm{Effect}AbsMax`: range of the Holm-significant effects in absolute
  points (copy-to-files reply 20-34, tool 8-22).

Existing macros now cited: `RSixPrefillTimeAZc` (0.49), `REightDecodeMsAZc`/`AOne` (14.9/16.9 ms),
`RTenHiMedAZc` (0.82), `RSixHiTimeAZc` (1.00), `CompRatioBAZc` (2.0).

## Items applied

1. **Metric fix and the 2x2 interpretation.** The text uses the regenerated open rates. A new paragraph
   ("At 14B and 32B, the Writer seldom opens a reply stored as a file") reports the following:
   - Through files, the stored reply scores 21.3 and 8.2 points below tool-written files at 14B and 32B
     (both Holm-significant), and the 4B and 8B intervals include zero.
   - At those sizes, the Writer opens the Researcher's files in 99% and 95% of tasks but `notes.md` in only
     9% and 24%.
   - This is stated as an observation about findability, not a tested cause, because Bs also changes the
     file's name, number and location.
   - The 8B exception (78% vs 59%) and the 4B low rates (5%, 13%) are given.
   - The "unexplained" sentence is removed. "Does no better" / "does not help" is removed from the
     abstract, introduction, Fig. 3 caption and conclusion.
2. **Strongest effect first.**
   - Abstract, introduction, Table 1 and Results now lead with delivery: the reply moved from copying into
     files costs 20-34 points, and tool-written notes 8-22, Holm-significant at 4B, 14B and 32B.
   - The claim that delivery costs more than the tool-call write is scoped to three of four sizes ("except
     at 8B"), because at 8B the tool delivery effect (-2.9) is smaller than the write effect (-4.7).
   - The tool-call write paragraph follows, with the Holm caveat (4B only; three of four uncorrected) and
     the methods.md caveats:
     - 8B is a 2Wiki effect (-9.3; HotpotQA 0.0);
     - under exact match, the 8B interval includes zero;
     - without the 18 cut or forced 4B writes, the 4B effect is -6.6 (-10.1 to -3.3).
   - The conclusion keeps the Holm caveat.
3. **Overgeneral headings.**
   - "Files are less accurate in every setting" became "B trails broadcast in every setting, and C trails
     it by less". C's deficit range (-1.3 to 8.4, significant in two of six) is now stated.
   - "The tool-call write costs accuracy on copied notes, not through files" became "... on copied notes at
     some sizes".
   - The guard heading now says "in one run".
   - The serving heading is scoped to Qwen3-8B.
   - "Plain files" in the abstract became "files without an index".
4. **Serving time.**
   - Scoped to Qwen3-8B, three-question tasks and one RTX PRO 6000.
   - Reports prefill time 0.49x, decode 14.9 vs 16.9 ms per generated token, and 1.2x output tokens.
   - At 32 tasks at a time, the median task takes 0.82x while the batch takes 1.00x.
   - "Saves no serving time" was removed from the abstract and introduction. The conclusion keeps "does not
     finish a batch sooner", which matches the data.
5. **Rescue rates.** Table 1 has a new row "Rescued (%)" (stored reply / tool files) per size. The text
   states that at 4B every file task was rescued, so the 4B file arms' accuracy rests on the rescue. The
   Harness paragraph points to the row.
6. **PRO 6000 drift.** "May include unmeasured drift" was replaced by the measured bound (at most 0.9
   points, intervals within -3.6 to 3.1). Methods now says that drift is bounded in Section 5.
7. **Other items.**
   - **Lauer-Needham.** Reframed: messages vs shared data under monitors map onto each other, so the
     primitives' costs decide, and LLM agents change these costs.
   - **Related work.** Added MemGPT and AIOS, both verified in `related_work.md` (bib entries added).
   - **Table 1 readability.** Delivery rows come first, Holm-significant cells are bold, the caption states
     the claim, and the sign convention is simplified.
   - **Wording run.** "Wording run" is defined in the Runs paragraph before its first use.
   - **Broadcast layout.** A1's instruction placement (ahead of the history, so almost no shared prefix) is
     described in Section 2. The introduction states that files compute 2.0x zero-copy's prefill.
   - **Zero-copy.** Section 2 now says that zero-copy still sends the tokens (only recomputation is saved)
     and moves the instruction to the end. Section 5 adds that the moved instruction is untested as the
     cause of the 4B loss.
   - **Zero-copy accuracy.** "Within 2.7 points" now says these are point estimates.
   - **Pipe.** "Up to 16% of questions in a setting."
   - **Statistics.** Decoding noise is part of the intervals.
   - **Replay.** The cross-run "as large as the stored reply's" sentence was deleted.
   - **32B rerun.** The sentence was condensed but keeps its cross-run label.
   - **Recommendations.** Scoped to "Qwen3 models and tool-call file access as tested" and "with Qwen3-8B
     ... each repair tested at one size".
   - **Space.** To keep 6 pages, venue names in `refs.bib` are abbreviated (e.g. "NeurIPS") and two DOIs
     on 1970s/1990s papers were dropped. The Fig. 1 caption and the Runs paragraph were shortened (the
     sweep list is already in Section 5). The Section 5 lead sentence was removed.

## Not done, and why

- **Figure edits.** These are Fig. 2's "no significant loss" arrow label, Fig. 4's subtitle and broken
  line, and de-emphasising the 14B bar in Fig. 3.
  - The figures are rendered by `archfig`, which is not on PATH in this session, so I did not touch the
    figure scripts.
  - The text gives the paired interval next to each zero-copy claim.
  - A caption note for Fig. 2 pushed the paper to 7 pages, so it was reverted.
- **Bib entries.**
  - Tam et al. ("Let Me Speak Freely?"): not in `related_work.md`, so it could not be verified.
  - Lost in the Middle: it is verified, but the sentence and entry cost two lines over the page limit. It
    was dropped in favour of a plain "untested" statement.
- **No mentions, per scope.**
  - The D (handles) channel, the Br and Bb controls, and the 4-agent chain (methods #6) are not mentioned,
    for space. "We measure five channels" became "We compare five channels".
  - The local vLLM modification (methods #5) is not mentioned, per the author's decision. "vLLM v0.33.0" is
    kept.
- **Runs table (systems W11).** There is no space for it. The Runs paragraph was shortened instead.
- **Pooled tests.** A pooled test or Holm correction for the uncorrected "N of six settings" counts and a
  test of the interaction (W10, methods #10) would need new analysis. The interaction is labelled "not
  tested" and is no longer interpreted in the text.
- **Abstract details.** The 4B zero-copy loss (W8) and the 99% collision rate (#13) are not in the
  abstract, for space. Both remain in the body.
- **Needs new runs.** Not attempted: the auto-read/discovery arm, a 24-call budget at k=3, a second model
  family, the stock-vLLM rerun, repairs at a common k, fixed-output timing, and human labels for
  AlignScore.

## Audit fixes

Snapshot before these edits: `cs632-store/main_pre_fix11.tex`. All seven items in `meaning_audit.md` were
checked against the data first and applied as suggested.

1. **Findability rates (§4).** Recomputed from `results_raw/p16_store_*`: the 9%/24% rates are the stored-reply
   arm's (Bs, 14/150 and 36/150) and the 99%/95% rates are B's. The sentence now says "the Writer opens the
   Researcher's tool-written files ... but the stored `notes.md` in only ...".
2. **Rescue at 14B (§4).** The Writer's or Reviewer's write is forced in 150/150 Bs tasks at 14B (and in 150/150 of
   both file arms at 4B). The sentence now covers both: "... and at 14B in every stored-reply task, so the accuracy of
   these arms rests on the rescue."
3. **§5 heading.** 15.1 of 30.4 is 49.7%, so the heading says "about half or more" again.
4. **§4 heading.** C's deficit starts at -1.3 (2Wiki, k=1), so the heading says "C trails it by less or not at all".
5. **Abstract scope.** Folders were tested only with Qwen3-8B at k=8 (`p15_k8_*` configs), so the recommendation
   reads "with Qwen3-8B, parallel writers should get their own folders".
6. **Abstract reference.** `REightFanB` is three-Researcher B minus one-Researcher B (`paper_numbers.py`), so the
   abstract says "... points against one Researcher".
7. **Drift scope (§3).** The A/A rerun (`t09_repeat`) and the crossed runs (`p16_store_*`) both use k=3, so the
   sentence now says §5 "measures [drift] on three-question tasks" instead of "bound".

**Figures** (all three keep their size: 506 x 134.03, 120.03 and 127.84 pt; lint clean).
- **Fig. 2.** "no significant loss" is replaced by the paired interval: "-61% prefill / accuracy -0.8 / paired 95% CI
  -2.9 to +1.4", read from the k=3 A1-zc row of `fig4_scaling.json` (same main run and pairing as
  `\nZcPooledDiff*`). The caption is unchanged, since the label states that it is paired.
- **Fig. 3.** Panel (a) now has 95% intervals (bootstrap over tasks). `figdata.py` adds `notes_*_lo/hi` to
  `fig3_split.json`, and every other data file was regenerated byte-identical. The 14B stored-reply bar was
  not de-emphasised. The text now explains it (the Writer opens `notes.md` in 9% of tasks, and every task is rescued),
  so no figure change was clearly right.
- **Fig. 4.** No line joins k=8 to the fan-out point at k=16 in either panel. Panel (b) has paired 95%
  intervals (series dodged slightly, "Paired 95% CI" in the legend). Its subtitle no longer asserts a cause:
  "B drops at k=16, where both payload and writers change". Panel (a) has no intervals because the data file has
  none for prefill.

**Space.** The fixes pushed the paper to 7 pages, so line-saving trims were made without changing any claim:
§2 broadcast ("comes first, in the system prompt"), §4 ("neither the facts nor accuracy drop", "tool-written
files", "This findability gap"), §5 replay ("documents in the index", dropped "of tasks"), §5 tool budget
("Going from ... moves", "B's ...-point gap"), Related Work (dropped "an agent's" and "such as scheduling"),
Conclusion ("skips", "zero-copy costs"), and the abstract (dropped "accuracy" before "points" and "models").
Captions were tried with added whisker notes, but those cost two full-width lines, so the notes went into the figures.
Result: 6 pages including references, no undefined references.
