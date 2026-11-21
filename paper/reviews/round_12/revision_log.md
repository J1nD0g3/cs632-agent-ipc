# Round 12 revision log

Snapshot before editing: `/mnt/sda/heojin/cs632-store/main_pre_round12.tex`.
Build: 6 pages including references, no undefined references or citations. `paper_numbers` regenerates with no
skipped section. Figure 3 re-rendered with `archfig run fig_split.py` (lint clean).

## New analysis (`round12()` in `src/agentipc/paper_numbers.py`)

All from existing raw records. Nothing was rerun.

| Quantity | Value | Macros |
| --- | --- | --- |
| 2x2 interaction, paired sign-flip permutation, per size | 4B 12.2 (p<0.001), 8B 2.2 (p=0.39), 14B 21.1 (p<0.001), 32B 12.2 (p<0.001) | `RTwelve{Size}Inter{,Lo,Hi,P}`, `RTwelveCellInter{Size}` |
| File channel's cost on tool-written notes minus the tool-call write's cost on copied notes, (A1w-B)-(A1r-A1w) | 4B 13.3 (6.2 to 20.2), 8B -1.8 (-7.1 to 4.0), 14B 9.1 (4.4 to 14.2), 32B 4.2 (-1.1 to 9.6); p = 0.001, 0.59, <0.001, 0.14 | `RTwelve{Size}Dvw{,Lo,Hi,P}` |
| Second Holm family (8 tests: interaction and the difference above at 4 sizes) | Interaction survives at 4B, 14B, 32B. Difference survives at 4B, 14B | `RTwelveHolmTests`, `RTwelveHolm{Inter,Dvw}{SigWord,Sizes,PMax}`, `RTwelveMark*` |
| Rescued vs non-rescued accuracy, main run k=3 | B 62.5% (n=215) vs 63.5% (n=85). C 65.8% (198) vs 67.3% (102) | `RTwelveMain{Resc,Kept}{Acc,N}{B,C}` |
| Rescued vs non-rescued, crossed runs, B (tool-written) | 4B 37.1 (150) vs none. 8B 66.3 (99) vs 64.1 (51). 14B 62.9 (115) vs 74.3 (35). 32B 55.7 (64) vs 71.3 (86) | `RTwelve{Size}{Resc,Kept}{Acc,N}B` |
| Same, Bs (stored reply) | 4B 33.6 (150) vs none. 8B 66.7 (66) vs 69.0 (84). 14B 44.2 (150) vs none. 32B 51.3 (65) vs 60.4 (85) | `RTwelve{Size}{Resc,Kept}{Acc,N}Bs` (not cited in text) |
| Final answers taken from the Reviewer's reply (final.md missing) | at most 1 task per channel at k=3 (main and crossed runs, B/C/Bs). Worst cell: 7 of 300 (B, k=1, main run). D, not reported, has 20/300 at k=1 | `RTwelveFinalReplyKThreeMax`, `RTwelveFinalReplyMax`, `RTwelveFinalReplyMaxN` |
| Any agent hit the 12-call budget, main run k=3 | B 34% (103/300), C 34% (103/300) | `RTwelveBudget{B,C}` |
| A Researcher call reached the 2,048-token cap, main run k=3 | B 22/300 (verified), A1 1/300 | `RTwelveCap{B,AOne}{,N}` |
| Zero-copy median task / broadcast's, six at a time | 0.99 (three runs: 0.996, and two runs averaging 0.99, range 0.99 to 1.00) | `RTwelveSixMedAZc{,Min,Max}` |
| Zero-copy minus broadcast, 90% bootstrap interval (TOST at +/-3) | -2.4 to 1.0, inside the margin | `RTwelveZcNinety{Lo,Hi}`, `RTwelveZcMargin`, `RTwelveZcEquiv` |
| Share of B's k=16 gap recovered (same run, bootstrap) | guard 50% (34 to 65), heading rule 59% (44 to 74) | `RTwelveShare{Guard,Heading}{,Lo,Hi,N}` |

Also: `RTwelveHolm{Inter,Dvw}Sizes` produces a serial-comma list ("4B, 14B, and 32B").

## Items from the request

1. **Factor renamed.** The 2x2 now crosses how the Researcher writes its notes with how later agents get their
   inputs: *copying* (broadcast: documents, notes and draft in the prompt, answers by reply) or the *file
   channel* (B: inputs through tool calls within the 12-call budget, outputs written as files, with the rescue).
   Defined in Methodology/Runs after the Harness paragraph, which now defines the tool budget and the rescue first.
   Used in the abstract, intro, Table 1 caption ("Copy: broadcast. Files: the file channel."), Figure 3 caption
   and legend ("Reply, file channel", "Tool write, file channel"), Results, and Conclusion. The phrase "how notes
   reach the Writer" no longer appears.
2. **Lead with the tool-written effect.** Abstract, intro (second observation), and conclusion now give
   8-22 points on tool-written notes at three of four sizes (`RTenHolmFileTool*`). The 20-34 stored-reply range
   is gone from abstract, intro, and conclusion and appears only in Table 1.
3. **Interaction and "costs more than the write" tested.** A second Holm family of 8 tests (stated in
   Statistics as separate, and as fixed after earlier runs on the same tasks). The interaction row of Table 1 now
   carries bold/dagger marks from this family. The text reports the difference test: the file channel's cost
   exceeds the tool-call write's cost at 4B and 14B only, not at 32B (4.2, -1.1 to 9.6) or 8B. The old Table 1
   claim "Except at 8B, delivery through files costs more than the tool-call write" was removed.
4. **Rescue.** The strict "score rescued tasks as wrong" bound and its macros were removed from the text.
   Replaced by rescued vs non-rescued accuracy: about equal at 8B in the main run (B, C) and in the 8B crossed
   run, lower for rescued tasks at 14B and 32B, and no comparison at 4B (all rescued). The final-from-reply
   fallback is documented in the Harness paragraph with its counts. The 12-call budget binding (34% of B and C
   tasks at k=3) and the token cap (22/300 B vs 1/300 broadcast Researcher calls) are reported in the
   Results paragraph on why B loses.
5. **Unreported arms disclosed** in one sentence at the end of Section 2 (handoff channel and the reply-output
   variant of B, "left to the appendix"), with no numbers.
6. **14B C vs B.** The model-size paragraph now says C does not beat B at every size: at 14B C trails broadcast
   by 16.0 (12.0 to 19.8) against B's 7.5 (4.0 to 10.8). The 8B heading on B and C is qualified "With Qwen3-8B".
7. **Serving time.** The six-at-a-time median task ratio (0.99, three runs) now sits next to the 32-at-a-time
   0.82. The paragraph heading says zero-copy shortens the median task only at high concurrency. The decode
   share is described as per-request time under batching, and "where prefill is billed" became "where uncached
   prompt tokens cost more than cached ones".
8. **The two 33.9s.** Verified from raw records. `nGapBKSixteen` comes from the main RTX 3090 run
   (`results/t08_large/20261118-233802-61c575b`: A1 72.4%, B 38.5%, 60 tasks). `nRFourKSixteenGapB` comes from
   the PRO 6000 12-call reference run (`results/p07_k16_kv100k/20261120-004705-732346b`: A1 71.9%, B 38.0%,
   interval 28.7 to 39.2). Both differences are 0.33854. This is a coincidence, not a mislabel. The text now
   names the main-servers run for the first one, gives the second one's interval, and says it is the 12-call run
   of the PRO 6000 pair and equals the main run's gap by coincidence. The paper never printed an interval for the
   first value, so no interval was mislabeled.
9. **One vs three Researchers** are now "two runs back to back on one server (cross-run)". Bf vs one-Researcher B
   is marked cross-run.
10. **Structure and style.** The Results section opens with a one-sentence route (cost and accuracy, why files
    lose, then across sizes). Each paragraph opens with its question or its claim, then gives evidence. The
    "B and C trail" and "why B's Writer reads documents" paragraphs were merged so the answer and its evidence
    sit together. Ledger sentences were cut: the 2Wiki/HotpotQA split of the 8B write effect, the 27%
    shorter-notes clause, the "1.8-4.8x across settings" repeat, the 32B harness-bug count, and the conclusion's
    repair numbers. The "Clarity and grammar" checklist was applied to every sentence: no semicolons or question
    marks in the body, commas after introductory phrases (also in headings), no untested "so" causes (B's file
    list, zero-copy's output tokens), clear antecedents ("the notes" not "them", "these ranges" not "they"),
    units on numbers ("accuracy points", "18.1 points"), serial commas, hyphenated compound modifiers. "Most
    systems copy" became "Many systems copy". The prior-work sentence now says "mostly with the channel fixed".

## Other text-only reviewer items applied

- The abstract and the Figure 2 discussion say broadcast and zero-copy are the most accurate channels (they are
  tied). The Figure 2 caption no longer claims broadcast is most accurate.
- Zero-copy equivalence: the 90% interval lies inside a +/-3-point margin. The margin is the one the methods
  reviewer suggested and was not stated in advance.
- The recommendation is scoped to state that fits in the context, Qwen3, tool-call file access, and this
  harness's tool budget and rescue, and it says "copy the conversation forward" (broadcast/zero-copy, not the
  pipe).
- Per-server dispatch noted ("Jobs rotate across servers, so a task's channels may run on different servers").
- The KV-sensitivity paragraph says each channel's prefill also depends on the channels that share its cache.
- The noise paragraph says drift across GPU types and caps was not measured.
- k=16 repairs: recovered shares with bootstrap intervals. The heading now says "about half", not "about half
  or more", because the guard's interval starts at 34%.
- The stored-reply paragraph is scoped as an observation. It names the asymmetry the methods reviewer found
  (the Reviewer is told `draft.md`, the Writer is not told the stored file's name) and uses the significant
  interaction to say the stored reply's loss is not the channel's cost. `% TODO p17` marks where the p17 result
  will go. The interpretation was not otherwise changed.
- Related work: the "just puts shared content first" and "We study IPC between agents" sentences were rewritten.

## Not done, and why

- **Needs new runs:** a notes-only file arm or Bd inside the crossed run; a closed-book floor; budget 24 and
  cap 4,096 at k=3; a fresh task draw; a non-Qwen model; replayed completions and a concurrency sweep for timing;
  a reference-passing channel that tells the Writer the path (p17 covers the stored-reply variant).
- **No space in 6 pages:** a run-inventory table, a per-size channel table, a k=8 fan-out panel, a
  failure-mode breakdown, timing min-max spreads (macros `RSixTime*Min/Max` exist), EM versions of all main
  gaps, the reply-scored rescue variant and the rescue-cause breakdown, and a serving-time axis or API-bill
  model in Figure 2. The appendix that the new disclosure sentence points to does not exist yet in `main.tex`.
- **Needs annotation:** human labels to calibrate AlignScore and the judge. Fact coverage is still described as
  approximate, and the text no longer says that a tool-call write "drops facts" as an established cause.
- **Removed for space, recoverable from macros:** the strict-rescue bound (`Strict*`, replaced as asked), the
  absolute intervals of the two k=16 repairs (`RSixKSixteen{Guard,Heading}OverB{Lo,Hi}`; the share intervals
  replace them), the 32B harness-bug count (`PRescueThirtyTwoBMoved`), the 2Wiki/HotpotQA split
  (`RTenEightWriteCopy{TwoWiki,Hotpot}`), and the notes-length ratio (`NotesShorter`).

## p17: stored reply with the notes path told (`round12_told()`)

Runs `p17_told_14b` and `p17_told_32b` (one interleaved run per size, crossed-run tasks and cap) compare the
stored reply with the Writer not told the notes path (Bs), the same arm with the Writer and Reviewer told
"The Researcher's notes are in notes.md." (Bt), and tool-written files (B). Snapshot before editing:
`cs632-store/main_pre_told.tex`.

- Stored-reply paragraph (Results) rewritten. New heading: "At 32B, the stored reply loses because the Writer
  does not find it." At 32B, telling the path raises the Writer's opening of `notes.md` (`RToldThirtyTwoOpen*`)
  and accuracy (`RToldThirtyTwoToldOverUntold*`), ending above tool-written notes
  (`RToldThirtyTwoToldOverTool*`). At 14B the pointer does not help (`RToldFourteenOpenTold`,
  `RToldFourteenToldOverUntold*`). The docs/ placement of 14B's tool-written notes
  (`RToldFourteenToolNotesUnderDocs`) is stated as an observation, with "We did not test this placement as a
  cause." The `% TODO p17` comment is gone. The old untested-naming-gap caveat is replaced by the test.
- Methodology: one sentence adds the told runs to "Runs", and Statistics says their comparisons are uncorrected
  (they are in neither Holm family).
- Conclusion: adds "Readers must be led to stored files: naming the path sufficed at 32B but not at 14B." The open
  question now reads "why a told 14B Writer skips notes.md". Abstract and intro do not mention the stored reply
  and are unchanged.
- Trims to stay at 6 pages: the stored-reply paragraph cites Table 1 for Holm significance instead of restating
  it, the 4B "seldom opens either" clause is dropped, the conclusion is tightened (same claims and scope), the
  Table 1 caption drops "All arms use B's Researcher instructions" (stated in the text), and a few words elsewhere
  ("only", "the"). The copied-notes paragraph now says the 8B and 32B losses "do not survive Holm correction".
- Build: 6 pages including references, no undefined references. `numbers.tex` was not edited.

## Told-run meaning audit fixes (`told_audit.md`)

Checked first against `results_raw/p17_told_{14b,32b}/*/records.jsonl.gz`. At 32B, the Reviewer reads `notes.md` in
63% of Bt tasks against 6% of Bs, and the Writer in 86% against 26%, as the audit says. The 14B and 32B copy-to-files
effects on the stored reply are both Holm-significant in the current `numbers.tex`.

1. Heading now reads "At 32B, the stored reply loses because later agents are not told where it is." The optional
   Reviewer clause is in: `round12_told` adds `RTold{Fourteen,ThirtyTwo}ReviewerOpen{Untold,Told,Tool}` (share of
   tasks whose Reviewer read a Researcher-written file or `notes.md`, via `writer_opened_notes(rec, "reviewer")`, which
   now takes the agent as an optional argument with the Writer as default). The text adds "and the Reviewer in 63%
   instead of 6%", and accuracy moves to its own sentence. Regenerating `numbers.tex` only added the six new macros.
   With both agents now named in the heading, "Unlike the Reviewer, who is told the draft's name, the Writer is not
   told this file's name" became "Neither later agent is told this file's name" (also true of the Bs instructions).
2. "(Table 1, both Holm-significant)" restored in the stored-reply paragraph.
3. The 8B parenthesis now names both arms: "78% for notes.md against 59% for tool-written notes".
4. Methods: "interleave, in the file channel, tool-written notes and the stored reply with and without its path ...".
5. Conclusion: "Later agents may need to be told where a stored reply is: naming its path sufficed at 32B but not at 14B."

Trims to stay at 6 pages: the copied-notes paragraph's "The write also lowers accuracy at 8B and 32B, but these losses
do not survive Holm correction." became "The 8B and 32B losses do not survive Holm correction." (both effects are
negative in Table 1), and the conclusion drops "(95% interval)" after the zero-copy accuracy interval (Statistics
defines the intervals). Build: 6 pages including references, no undefined references, no semicolons in the body.
`numbers.tex` was not edited by hand.
