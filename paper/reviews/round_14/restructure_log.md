# Round 14 restructure of §4 Results and §5 Sensitivity (text only)

Snapshot before editing: `/mnt/sda/heojin/cs632-store/main_pre_restructure.tex`.
No new experiments, no new macros, and `numbers.tex` was not edited. The set of macros used in §4–§5 is the
same as before, except `nRTenHolmTests` and `nRTwelveHolmTests`, which left the Table 1 caption and are
still defined in the Statistics paragraph of §3 (the two Holm families).
Build: `latexmk` succeeds, with no undefined references or citations. The body (through the Conclusion) ends
on page 6. References start on page 6 and end on page 7. There is one `Overfull \vbox (1.9pt too high)` while
page 7 (references only) ships out. Nothing in the body is affected.
There are no semicolons in the body, no mention of a modified vLLM, and no venue is named.

Following the author's added constraint, the freed space was **not** filled. I added only these:
- a two-sentence opener for §4 and a one-sentence opener for §5
- an answer-first lead sentence for each subsection
- one closing line for §4.3
- the Table 1 row explanations that moved out of the caption

No earlier-cut qualifier was restored. I checked the round 13 and round 14 cut lists, and none of those
cuts makes a claim in the current text inaccurate.

## New outline

- **§4 Results** opener: §4.1 asks whether copying is expensive, §4.2 how much the file channels lose, and §4.3 why.
  - **§4.1 Is copying expensive?** (`sec:cost`)
    - Answer: copying the whole conversation sends more tokens than the pipe but fewer than files. Broadcast
      computes the most prefill, but zero-copy cuts it below files' without shortening runs.
    - Evidence (no head): the token and prefill ranking (Fig. 2), now including the pipe's token cost.
    - Paragraph "Zero-copy shortened the median task only with many concurrent tasks." (timing, unchanged)
  - **§4.2 How much do file channels lose?** (`sec:accuracy`)
    - Answer: at three questions, broadcast is the most accurate channel, and the file channels trail it.
    - Evidence (no head): broadcast vs. zero-copy accuracy, then B's and C's gaps and C vs. B.
    - "The pipe's Reviewer turns right answers wrong."
    - "Files lose accuracy even with the documents or with broadcast's notes." (documents and replay controls)
    - "Two excluded variants also trail copying." (D and Br, one sentence each)
  - **§4.3 Why do files lose?** (`sec:cause`)
    - Answer: on tool-written notes, later agents that read the notes as files lose accuracy at 4B, 14B, and
      32B. At 8B, neither the cost of reading nor that of writing survives correction. The two further threads
      are then named.
    - (a) "Reading tool-written notes as files costs accuracy at three sizes." This covers:
      - the crossed 2×2 (Table 1, Fig. 3) and the Table 1 row semantics
      - the wording-run caveat and the three-run replication
      - the write effect on copied notes and the 8B point-estimate split
      - fact coverage, now covering both the main run and the crossed runs
    - (a, continued) "The loss appears at different stages at 14B and 32B." This covers the draft/final rows
      and the 14B Reviewer's `draft.md` reads.
    - (b) "The file harness often fails." This holds:
      - the main-run budget, cap, and rescue statistics, and the main-run rescued/kept split
      - the Rescued row of Table 1, the claim that every 4B file task was rescued, and the crossed-run
        rescued/kept split
    - (c) "B's Writer often skips the notes, and later agents often miss the stored reply." This holds:
      - B's and C's main-run Writer skip rates
      - the stored reply vs. tool-written notes comparison
      - the exploratory label and the 32B told run
    - (c, continued) "At 14B, listing told notes first helps the drafts but not the final answers." This
      holds the 14B told and first-listed runs, the 14B Reviewer observation, and the 23/127 split.
    - Closing line: "All three threads thus point to the later agents, in how they read tool-written notes,
      how often the harness rescues them, and whether they open the notes."
- **§5 Sensitivity**
  - New opener: "This section asks when the answers of §4 change, first with cache capacity and questions per
    task, then with parallel writers and model size, and last between runs and GPUs."
  - Paragraphs unchanged and in their original order: cache and k, k=8 folders, k=16 guard/heading/budget,
    model size, then noise.

Float placement: Fig. 3 sits at the top of page 4. Table 1 is on page 4, the page where §4.3 starts and
first cites it. Fig. 4 is on page 5, the page where §5 starts.

## Moved paragraphs and sentences

| Content | Before | After |
| --- | --- | --- |
| "The pipe sends the fewest tokens (\nSentATwo per task)" | pipe paragraph (accuracy) | §4.1 ranking paragraph |
| Broadcast/zero-copy accuracy | own paragraph, head "At three questions, broadcast is the most accurate channel." | §4.2 lead paragraph, head turned into the answer sentence |
| B/C gaps and C vs. B | paragraph "Files trail broadcast, and B's Writer often skips the notes." | §4.2 lead paragraph |
| Main-run fact coverage (32% vs. 45%) | same paragraph | §4.3(a), next to crossed-run coverage |
| B's/C's Writer skip rates (42%, 8%) | same paragraph | §4.3(c), first sentences |
| Harness paragraph (budget, cap, rescues, main-run split) | before Table 1, between controls and crossed runs | §4.3(b) |
| "At 4B, every file-channel task needed the rescue ..." and the crossed rescued/kept split | end of the crossed paragraph | §4.3(b), after the main-run split |
| 14B/32B stage-of-loss sentences | middle of the crossed paragraph | own paragraph in §4.3(a) |
| D/Br paragraph | after the crossed paragraph | end of §4.2 |
| 32B told run | stored-reply paragraph | stays in §4.3(c), first paragraph |
| 14B told, first-listed, and Reviewer observation | same paragraph | second paragraph of §4.3(c) |
| Table 1 and Fig. 4 source | between harness and crossed paragraphs | just before §4.3 |

## Wording changes beyond transitions and moves

1. **Headings.**
   - "The channels rank differently by prefill than by tokens sent." became the §4.1 answer sentence. The
     intro keeps this observation.
   - "On tool-written notes, files cost accuracy at three sizes, at different stages." was split into two
     heads, "Reading tool-written notes as files costs accuracy at three sizes." and "The loss appears at
     different stages at 14B and 32B." Both claims are unchanged.
   - "Later agents often miss the stored reply." was merged with "B's Writer often skips the notes" into the
     §4.3(c) head.
   - New head for the 14B paragraph: "At 14B, listing told notes first helps the drafts but not the final
     answers." It rests on the told `00_notes.md` vs. told `notes.md` draft gain (+17.3, 12.4 to 22.4) and
     final gain (+1.1, -2.4 to 4.9). The paragraph sits after "The told and first-listed runs below are
     exploratory."
2. **Pipe.** "The pipe sends the fewest tokens (...) but trails" became "The pipe, the cheapest channel by
   tokens sent, trails". The number moved to §4.1.
3. **Br.** Its two sentences were joined into one ("..., and its Writer opens the notes in ..."), with the
   same content.
4. **Fact coverage.** "B's notes state" became "B's notes in the main run state". The two coverage sentences
   were joined ("..., and in the crossed runs coverage is lower for tool-written notes at 4B, 8B, and 32B by
   point estimate").
5. **Harness and skip rates.** I added "In the main run," at the start of each, because they now sit inside
   §4.3, next to crossed-run results.
6. **Table 1 caption.**
   - Before, it was a claim plus row definitions. It is now: "Paired effects on accuracy in the crossed
     runs (points, 95% intervals), arm after the arrow minus arm before. Bold†: Holm-significant in its
     family (§3). §4.3 explains the rows."
   - Moved to the text:
     - "Copy: A1's inputs" became "Copying gives later agents A1's inputs."
     - The interaction definition (row 4 minus row 3).
     - "Each row changes one factor at a fixed level of the other." This states the simple-effect design.
     - The Rescued row: "share of file tasks with a rescued Writer or Reviewer, on reply and on tool-written
       notes".
     - The Draft/final rows: "accuracy of drafts and final answers on tool-written notes".
   - Holm families: the caption now points to §3, which defines the 16-effect family and the 8-test post hoc
     family that holds the interaction.
   - The caption's claim, "files cost accuracy ... and more on the stored reply, which also differs in name
     and place", moved into §4.3(c). It reads "files cost more on the stored reply than on tool-written notes
     (Table 1, rows 1 and 2), and the stored reply also differs in name and place."
7. **Stored reply.** "The stored reply scores 21.3 and 8.2 points below tool-written notes ... (Table 1, both
   Holm-significant)" became "In the file channel, it scores ... (both Holm-significant)". The Table 1
   reference moved to the sentence before.
8. **14B told.** "At 14B, the Writer opens the told notes.md" became "In the told run, the Writer opens ...".
   This avoids repeating "At 14B" right after the head.
9. **Intro.** The 8B cross-reference now points to §4.3 (`sec:cause`) instead of §4. Section numbers did not
   change.

## Self-audit (sentence by sentence, against the snapshot)

- **§4.1 answer.** The claim "Copying the whole conversation sends more tokens than the pipe but fewer than
  files" holds on three counts:
  - The pipe sends the fewest tokens (5.6k).
  - B and C send 2.9× and 2.8× broadcast's tokens.
  - Zero-copy sends A1's messages (Fig. 2a puts it next to A1).
  
  "Broadcast computes the most prefill" is Fig. 2's caption claim (12.4k against 9.8k for B, 4.8k for
  zero-copy, and 4.7k for the pipe). "Zero-copy cuts it below files' without shortening runs" matches the
  intro ("cuts broadcast's prefill by 61%, to below that of files, but not its run time") and the timing
  paragraph (1.08–1.10×).
  
  The brief's "in tokens sent, yes" was written as "more than the pipe but fewer than files". Files send
  more tokens than broadcast, so a plain "yes" would misstate the ranking.
- **§4.2 answer.** "At three questions, broadcast is the most accurate channel, and the file channels trail
  it." This joins the two old heads ("At three questions, broadcast is the most accurate channel." and "Files
  trail broadcast"). The ranges that follow are the same, including C's minimum of -1.3, so a reader still
  sees that C is not below broadcast in every setting.
- **"The pipe, the cheapest channel by tokens sent"** restates "the pipe sends the fewest tokens" (§4.1),
  with the same scope (main run, k=3) and no excluded arm compared.
- **§4.3 answer.**
  - "Lose accuracy at 4B, 14B, and 32B" is row 2 of Table 1, all Holm-significant. The next paragraph says
    so.
  - At 8B, "neither the cost of reading nor that of writing survives correction". This holds for all four
    8B simple effects (-5.1, -2.9, -4.7, and -2.4, none bold), and it matches the abstract and intro.
  - I made no claim on whether reading costs more than writing at 4B, 14B, or 32B. That comparison depends
    on the order of the decomposition, which the paper avoids, and only the 8B contrast is reported.
- **"Each row of Table 1 changes one factor at a fixed level of the other"** holds by construction. Rows 1
  and 2 change the channel at reply or tool-written notes. Rows 3 and 4 change how notes are written, under
  copy or files.
- **"Files cost more on the stored reply than on tool-written notes (rows 1 and 2)".** The point estimates
  hold at every size (-34.2 vs. -22.0, -5.1 vs. -2.9, -30.0 vs. -8.9, and -20.4 vs. -8.2). The old caption
  stated the same claim without a significance qualifier, and I added none. The qualifier "also differs in
  name and place" is kept.
- **"In the file channel, it scores 21.3 and 8.2 points below tool-written notes"** is row 4 (Reply→tool,
  files), tool-written minus stored reply. The direction is right, and both values are bold.
- **"The loss appears at different stages at 14B and 32B."** The content is identical to before. The 4B
  sentence moved to (b), and its wording is unchanged ("these arms' accuracy rests on it").
- **Harness paragraph.** Only "In the main run," was added, which is correct (these are `RTwelve*` and
  `RThirteenMain*` macros from `t07_main`). The crossed-run rescue sentences keep "In a descriptive split".
- **Exploratory label.** "The told and first-listed runs below are exploratory." still comes before every
  told and first-listed result, including the new 14B paragraph that follows. The Statistics paragraph still
  says that these comparisons are uncorrected and that the first-listed ones are post hoc. "(observational)"
  is kept.
- **14B head.** "listing told notes first" names the actual manipulation: the told `00_notes.md` against the
  told `notes.md` in the same run. "Helps the drafts" means +17.3 (12.4 to 22.4). "Not the final answers"
  means +1.1 (-2.4 to 4.9).
- **Closing line of §4.3.**
  - "Point to the later agents" summarizes the three threads, each on its own evidence:
    - the read cost on tool-written notes
    - the rescues of Writers and Reviewers (the Rescued row, and the main-run breakdown of rescued
      Writers/Reviewers)
    - Writer and Reviewer open rates
  - It adds no number and no causal word ("point to" rather than "explain").
  - It does not say that rescues are only of later agents. The Researcher cap sentence is still in (b).
- **§5 opener.** It frames the section only. The five paragraph heads and bodies are unchanged.
- **Cross-run labels, intervals, and sample sizes.** All are kept, in the same places:
  - **Cross-run labels:** the timing runs, the documents control, the three-run spread, the 32B told run
    against copied reply notes, the cache sizes, folders against one-Researcher B, the budget doubling, and
    the size-run 32B rerun.
  - **Sample sizes:** RTenN, RSixAloneN, REightFanBN, and the other N macros.
  - **Intervals:** every interval stays next to its number.
- **Post hoc labels.** The 8B Dvw contrast is still "post hoc". The interaction's post hoc family is now
  reached through §3 instead of the caption.

## Not done

- No qualifier was restored. None of the earlier cuts (rounds 13 and 14) leaves a current claim inaccurate,
  and the author asked to prefer shorter text.
- I did not change any wording outside §4–§5 except the intro's cross-reference. §3 still says "Unless
  noted, §4 uses the main run", which is still correct.
- The overfull vbox (1.9pt) is on the references-only page 7. It comes from how the bibliography columns
  split, not from the body. I left it.

# §5 restructure and audit items (snapshot: cs632-store/main_pre_s5.tex)

## Part 1: audit items applied (17 of 17, F10 skipped as superseded)

Each item was checked against the text and `numbers.tex` before it was applied.

- **M1.** Caption rewritten as given. The rows below the rule are percentages, which the Rescued and Draft/final rows confirm.
- **M2.** "at 4B, 14B, and 32B (Table 1, the interaction, post hoc)". The interaction cells are bold at 4B, 14B, and 32B, and 8B (2.2) is not bold.
- **M3.** The 4B rescue qualifier moved into (a), after "all Holm-significant", and was deleted from (b). The Rescued row is 100/100 at 4B. Changed: "these arms'" became "the 4B file arms'" so the antecedent is clear.
- **M4.** The closing "All three threads..." line was deleted. The data agree with the audit: main-run B is 9.4 rescued vs 10.0 kept, and crossed 8B is 1.3 vs 5.9.
- **M5 + F4.** Retitled to "Which channels lose accuracy?" and given the new lead. The B/C range and the pipe sentences were shortened as the audit says. "all six" uses `\nGapBSigWord` so that the number stays a macro.
- **M6.** New head applied. Changed: "This link is observational" became "The link between reading the notes and final accuracy is observational", because the preceding sentence gives no single link for "This" to refer to.
- **M7.** Added "(§4.1)".
- **F1.** Deleted the §4 roadmap.
- **F2.** Applied. Changed: "though not its run time" became "though zero-copy's runs are no shorter". "its" was ambiguous between broadcast and zero-copy. Zero-copy's run time is 1.08–1.10x broadcast's at six tasks and 1.00x at 32, so the claim holds in both runs.
- **F3.** The result now comes before the reason. The reason is a separate sentence: "The runs are not shorter because decode accounts for ... and zero-copy generates ...". This is the same causal claim as the abstract's "as decoding dominates".
- **F5.** The Br open rates moved to §4.3(c), after the C sentence. Changed: added "In the reply-output runs," so that the run condition stays attached.
- **F6, F7, F8.** Applied as given.
- **F9.** Head applied. "At least as much" holds for main-run B (10.0 ≥ 9.4), main-run C (6.0 = 6.0), and crossed 8B (5.9 ≥ 1.3).

## Part 2: §5 restructure

- **Opener (answers, no roadmap).** "Prefix-cache savings hold only while the shared history of concurrent tasks fits in the KV cache. B loses more when parallel Researchers share one folder, and model size changes which channels lose and where."
- **§5.1 "Larger tasks keep prefix-cache savings only while the shared history fits"** (sec:larger). The old paragraph, now opened by "The savings of §4.1 shrink at eight questions". "Prefix-cache" was added because the pipe keeps its saving at k=16 without the cache. Without the qualifier, the head would contradict the paragraph's last sentence.
- **§5.2 "Parallel Researchers in one folder cost B accuracy"** (sec:writers). The k=8 folders paragraph and the k=16 guard/heading paragraph are merged into one argument:
  - The losses in §4.2–4.3 come from runs with one Researcher.
  - A likely new cause: same-path writes, so one Researcher can overwrite another's notes (a lost update).
  - The k=8 DiD and the 99% clash rate.
  - The folders, with their residual loss and confound kept.
  - At k=16, the guard and the heading rule.
  - One OS-mapping sentence.
  - The budget result, kept where it was, at the end.

  The head says "B", not "files", because only B was run with a shared folder (at k=16, C's gap is 5.1 against B's 33.9). The modal stays "can/likely", as in the old "could overwrite".
- **§5.3 "Model size changes which channels lose and where"** (sec:size). The old paragraph, led by "In the size runs, which repeat the comparison of §4.2 at four sizes". One closing sentence restates the §4.3 stage result (final answers at 14B, drafts at 32B) as a back-reference, with no new number.
- **Noise.** The noise paragraph is now `\paragraph{Noise.}` in §3 after Statistics. "Each task runs once per channel, so decoding noise is part of the intervals" was merged into its first sentence, which removes the duplicate. Statistics now ends "may include drift, which we measure next." The head claim "small next to B's gaps" was dropped, because B's gaps are not yet shown in §3. The numbers themselves still support it.
- **Cross-references.** The intro's folder claim now points to §5.2. "larger-payload runs of §5" is kept.

## Self-audit (sentence by sentence)

- **Macros.** The set used is identical to the snapshot. No number is hard-coded.
- **Labels.** Each count is the same or higher than in the snapshot:
  - "cross-run": 9 → 9
  - "post hoc": 3 → 4 (M2)
  - exploratory/observational: 2 → 3 (M6)

  Every interval and N is next to its number.
- **Style.** The body has no semicolons. No modified vLLM is mentioned, and no venue is named.
- **Floats.** Figures 2–4 and Table 1 sit on the page of their first mention.
- **Build.** The build has no undefined references and no "??".
- **Pages.** The body (through the Conclusion) ends on page 6. References start on page 6 and end on page 7.
