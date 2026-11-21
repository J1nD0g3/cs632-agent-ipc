# Round 13 revision log

Snapshot before edits: `cs632-store/main_pre_round13.tex`. Build: 6 pages including references, no
undefined references, no semicolons in the body. All new numbers come from the new `round13` section of
`src/agentipc/paper_numbers.py` (regenerated, nothing skipped).

## New macros (section `round13`)

- `BootN` (bootstrap resamples, read from `analyze.paired`).
- Main run, k=3: `RThirteenMainResc{B,C}` (% of tasks with any agent rescued),
  `RThirteenMain{Resc,Kept}Gap{B,C}` (+Lo/Hi/N; paired broadcast lead on rescued and other tasks),
  `RThirteenMainBudgetShareB`, `RThirteenMainRevBudgetShareB`, `RThirteenMainWriterBudgetShareB` (share of
  B's rescued Writers/Reviewers whose rescue followed an exhausted tool budget).
- Crossed runs (p16), per size: `RThirteen{size}Draft{ReplyCopy,ToolCopy,ReplyFile,ToolFile}` (draft accuracy,
  scored like the final answers), `RThirteen{size}FileToolAbs`.
- Reply-output runs (p14), per size: `RThirteen{size}BrVsToolCopy` (+Lo/Hi/N), `RThirteen{size}ReadPFourteen`
  (+Lo/Hi/N), `RThirteen{size}BrOpen`, `RThirteen{size}BrNoRead`.
- B - A1w replications over p10/p14/p16, per size: `RThirteen{size}ReadRep{Min,Max}`,
  `RThirteen{size}ReadPooled` (+Lo/Hi/N; per-task mean over the three runs), `RThirteenReadRepSpreadMax`.
- Pipe: `RThirteenPipeSent{Fourteen,ThirtyTwo,KSixteen}`, `RThirteenPipeSent{Min,Max}`,
  `RThirteenPipeGapMax`, `RThirteenPipeKSixteen{Lo,Hi}`.
- `RThirteenToldThirtyTwoVsReplyCopy` (+Lo/Hi/N; told stored reply p17 minus copied reply p16, cross-run).
- `RThirteenHiMedAZc{Min,Max}` (per-run median-task ratios at 32 tasks at a time).
- `REightFanDiDAbs` (size of the k=8 difference in differences).

## Items applied

1. **File-channel cost as a tool-protocol cost.** Abstract, intro, and conclusion now say much of the cost
   comes with the tool protocol, and give 14B/32B (8.9, 8.2, Holm) separately from 4B (22.0, every task
   rescued). New Results paragraph "The file channel's tool protocol often fails": any-agent rescue share
   (72% B, 67% C), the two triggers (35% of B's Writer/Reviewer rescues after an exhausted budget, 78% of
   Reviewer rescues), and paired gaps on rescued vs other tasks (B 9.4 vs 10.0, C 6.0 vs 6.0), marked
   descriptive. Harness paragraph names both rescue triggers. Stage of the loss: two Table 1 rows
   (draft/final for copy and files on tool-written notes) and text: 14B at the Reviewer, 32B in the Writer's
   drafts (Reviewer recovers part), 4B all rescued. Unpaired 62.5 vs 63.5 sentence removed.
2. **Omitted arms.** D: accuracy 65.1, 1.3x tokens, 0.59x prefill, 2.0-11.9 gap, significant in four of six,
   and why it is excluded (message plus files). Br: in-run Br - A1w per size (-25.6, -24.0, -22.2, -40.2),
   larger than B's loss at 8B/14B/32B, Writer opens notes in 12/30/97% at 4B/8B/14B and reads no file at 32B,
   and why it is excluded (changes the output side). Three-run replication of B - A1w: text gives the
   maximum spread (3.3 points), Table 1 adds a "three runs" row with per-task pooled estimates (post hoc).
3. **Fan-out.** Abstract and intro use the difference in differences (20.4, interval in Sec. 5) instead of the
   cross-run 21.2; heading scoped to eight questions; one-folder vs three-folder B changes no longer quoted.
4. **Recommendation.** Abstract, intro, conclusion: at 14B, 32B, and k=16 the pipe stays within 1.2 points
   of broadcast at 0.41-0.42x its tokens, but loses up to 14.9 at 8B; Model-size paragraph gives the 14B/32B
   pipe intervals and token ratios. Zero-copy defined as still sending every token (only the prefix's KV is
   reused). Contribution stated as a measurement plus four runtime rules. "We vary only this choice" removed.
5. **Statistics.** Bootstrap unit stated (tasks, 2,000 resamples). Second Holm family described as post hoc;
   Table 1 caption calls its tests post hoc and points to Sec. 3; the Dvw contrast's numbers dropped from the
   text. Post hoc equivalence margin sentence removed. Cross-run marks added (timing runs, KV-cache accuracy
   shift, wording/reply-output replications, told vs copied reply). Figure 4a subtitle now "savings fade as
   payloads grow, except the pipe's" (re-rendered, lint clean). Figure 4 moved in the source so it renders on
   page 5 with Sec. 5. 32B path-prefix fix described once in Runs, with its scope.
6. **Quoted overclaims fixed.** "most accurate" scoped to three questions; zero-copy "point estimates within";
   "pays off" replaced with per-run 0.81/0.83 median ratios and the cache change noted; "specific to the
   stored reply" replaced with "costs more ... which also differs in name and place"; 32B told heading scoped
   to tool-written notes, plus the cross-run gap to copied reply notes (-6.7); "the cost depends on how notes
   are written" removed from Table 1 caption and conclusion; "same sizes" coverage sentence rephrased and
   coverage called weak; "larger tool budget" -> "doubling the tool budget"; noise heading scoped to B;
   final-from-reply sentence clarified (main run for the 300-task count); Table 1 Sec. reference fixed.
   `% TODO p18` placed after the 14B placement sentence; 14B told interpretation unchanged.

## Cuts made to stay at 6 pages

Intro roadmap sentence; Lauer-Needham sentence shortened; Sec. 2 fan-out sentence moved to Tasks; ChatDev
pipe aside; B's and C's/pipe's alone-run times except zero-copy's; documents-control pipe sentence merged;
C-at-14B size-run sentence; 4B zero-copy notes-length detail; identical-notes example in the noise paragraph;
Br/D definitions moved from Sec. 2 to Runs/Results; IPC related-work paragraph folded into Agent
communication; the "index acts as a directory" analogy sentence; "B's file list does not say which file
holds the notes"; figure captions shortened (Figure 3 no longer restates the coverage claim).

## Not done

- New runs requested by reviewers (larger budget/cap crossed rerun, 8B cap comparison, cross-GPU drift,
  human labels for coverage, preemption counts): need runs or annotation.
- Run table (systems W7), priced cost table and decode share in the abstract (systems W3), per-arm AlignScore
  kappa (methods W5), Figure 3 bar reorder and Figure 1 read arrows (systems W10): no page room or need new
  analysis/figure work; not in this round's list.
- 8B "B's loss comes mostly from the tool-call write" (systems W2): not added, since the crossed design
  avoids order-dependent attribution and neither 8B file effect is Holm-significant.
- p18 (00_notes.md) result: run in progress; `% TODO p18` marks the spot.

## Meaning-audit fixes (meaning_audit.md)

Each fix was checked against the data or code before it was applied. No new macros were needed, and
`numbers.tex` regenerates unchanged with no skipped sections.

1. **Intro fourth rule.** Applied: "copy rather than share files", matching the conclusion. The size claim does
   not fit the data (4B pipe gap 1.5, -1.3 to 4.5).
2. **Abstract pipe scope.** Applied: "With Qwen3-14B or 32B at three questions, or Qwen3-8B at sixteen ... within
   1.2 points of broadcast's accuracy (point estimates)". `RThirteenPipeGapMax` is the largest of the point gaps
   from p02_size_14b, p02_size_32b, and the k=16 row of Figure 4 (t08_large, 8B on the RTX 3090s).
3. **Conclusion pipe scope.** Applied, with the same scope and "(point estimates)".
4. **Model-size direction.** Applied: "trails broadcast by". `PSize*GapATwo` is broadcast minus pipe
   (`-mean` of pipe minus A1 in `pro6000`).
5. **Three-run spread.** Applied: "at each size the three runs' estimates differ by at most 3.3 points".
   Recomputed B - A1w per run (p10, p14, p16): 4B -21.6/-23.1/-22.0, 8B -1.6/-4.9/-2.9, 14B -8.9/-10.0/-8.9,
   32B -8.4/-9.1/-8.2, so the largest spread is 3.3 (8B).
6. **Br versus B.** Applied, with B's in-run values (`RThirteen*ReadPFourteen`, p14 B - A1w). Recomputed Br - B in
   p14: 4B -2.4 (-7.6 to 2.9), 8B -19.1, 14B -12.2, 32B -31.1, so "about as much at 4B" holds.
7. **D scope.** Applied: k=3 now scopes only accuracy, tokens, and prefill, and the gap range and "significantly in
   four" cover the six settings.
8. **Rescue triggers.** Applied in Harness and Results. `pipeline.run_agent` also stops on a verbatim repeat of
   the last tool call (`repeat_stop`). Recounted B's rescued Writers and Reviewers in t07_main at k=3: 98 budget,
   173 reply, 7 repeat, so "nearly all the rest had replied".
9. **Conclusion causal claim.** Applied: "Much of the files' accuracy cost comes with the tool protocol." The 8B
   split is 9.4 (rescued) versus 10.0 (others).
10. **"Sufficed" at 32B.** Applied: "helped". The told 32B stored reply still trails copied reply notes by 6.7
    points (-10.4 to -3.1, cross-run).
11. **Lauer and Needham.** Applied: "Lauer and Needham showed that message-based and monitor-based systems map
    onto each other". This matches the cited paper's title (duality of operating system structures).

### Cuts to stay at 6 pages

The fixes added about three lines. To make room: "all the documents" became "the documents"; "files written
with write_file" became "write_file calls"; "prompt tokens reported as uncached" became "uncached prompt
tokens"; "is ... points less accurate than broadcast" became "trails broadcast by ... points" (pipe paragraph);
"rescues some agent" became "rescues an agent"; "their tool budget" became "their budget"; "replied instead of
writing" became "replied without writing"; "the rescue is an outcome of the channel" became "the rescue depends
on the channel". We also dropped the closing sentence "Dropping the output file thus does not remove the file
channel's cost.", because the new Br-versus-B sentence already says this. The paper is 6 pages with references,
with no undefined references and no overfull boxes. `% TODO p18` is unchanged.

## p18: first-listed stored reply at 14B (`% TODO p18` filled)

Snapshot before editing: `/mnt/sda/heojin/cs632-store/main_pre_p18.tex`. Data: `results/p18_first_14b/20261121-191515-8d096a4`
(Qwen3-14B, the 150 tasks and settings of p17_told_14b, arms Bt, Bs0, Bt0, B interleaved in one run).

New section `round13_first` in `paper_numbers.py` (macro prefix `RFirst`). Drafts are scored like final answers
(as in `round13`), opens use `writer_opened_notes(rec, agent=...)`, and paired intervals use `paired` (2,000
resamples, task ids sorted as in every other section).

- Final accuracy: B 64.7, Bt 43.6, Bs0 45.3, Bt0 44.7 (`RFirstAcc{Tool,Told,FirstUntold,FirstTold}`).
- Writer opens notes: 99 / 5 / 21 / 70%. Reviewer: 79 / 1 / 3 / 15% (`RFirstOpen*`, `RFirstReviewerOpen*`).
- Draft Bt0 - Bt +17.3 (12.4 to 22.4), `RFirstDraftFirstToldOverTold`. Draft Bt0 - B -8.4 (-13.1 to -3.8),
  `RFirstDraftFirstToldOverTool` (computed, not in the text).
- Final - draft: B -5.8 (-8.7 to -3.1), Bt -1.1 (-4.7 to 2.7), Bs0 -6.4, Bt0 -17.3 (-22.7 to -12.0)
  (`RFirstRevise*`). Final Bt0 - Bt +1.1 (-2.4 to 4.9), `RFirstAccFirstToldOverTold`.
- Bt0 split by Reviewer opening the notes (observational): 23 tasks -4.3, 127 tasks -19.7
  (`RFirstReviseFirstTold{Opened,Skipped}` and `...N`).
- Point estimates match the brief. Some interval ends differ from the brief by up to 0.3 points; the bootstrap
  draws depend on task order, and this section sorts task ids like the rest of the file. The final Bt0 - Bt
  interval matches exactly.

Text changes:
1. Results: the 32B paragraph and the 14B sentences are one paragraph, retitled "The stored reply trails
   tool-written notes partly because later agents do not find it." The 14B part now says: naming the path
   alone moves accuracy by 0.9 points (p17), list_files lists notes.md after the documents, so the first-listed
   run names it 00_notes.md. The told Writer then opens it in 70% of tasks instead of 5% and its draft gains
   17.3 points. The Reviewer opens it in 15% and revises the gain away (-17.3 draft to final against -1.1 for
   told notes.md), so final accuracy rises only 1.1. The 23/127 Reviewer split is marked observational. The
   docs/ placement observation (79% of tool-writing Researchers save under docs/) is dropped; the new run
   replaces it as the 14B finding.
2. Methods, Runs: one sentence defines the 14B first-listed run. Statistics: its comparisons are uncorrected
   and post hoc.
3. Conclusion: the rule is now "lead every later agent that edits the answer to the stored notes", followed by
   "Naming the path helped at 32B. At 14B, the file also had to be listed first, and then only the Writer used
   it." Open question changed to why a 14B Reviewer skips notes listed first and named. Intro rule list
   changed to "lead every later agent to shared state" to match.

Cuts to stay at 6 pages (meaning kept): "chosen post hoc after we saw the crossed runs" -> "chosen post hoc";
"(... of the Reviewers), and nearly all the rest" -> "(... of Reviewers), and nearly all others"; "This split"
-> "The split"; "in two of these runs" -> "in two runs"; "summed prefill and decode time" -> "prefill and decode
time"; "but, in our runs, little of the time" -> "but little of the time"; "compared with broadcast's" ->
"against broadcast's"; "Of the reads by B's Writer ... the Writer never opens" -> "Of B's Writer's reads ...
it never opens"; "whose index names the notes files" -> "whose index names the notes"; "(Table 1, bottom rows)"
-> "(Table 1)"; "and neither survives the correction" -> "and neither survives correction"; "again a
descriptive split" -> "a descriptive split"; "in two back-to-back runs on one server" -> "in two back-to-back
runs"; "removes drift common to both channels" -> "removes common drift"; "which confounds this arm" -> "a
confound"; "We did not test separate folders at this size" -> "... here"; "raising the budget from 12 to 24
calls" -> "doubling the budget to 24 calls"; the 33.9-point gap's interval dropped; "against 7.8 originally"
-> "(7.8 originally)"; "With batching, greedy decoding" -> "Batched greedy decoding"; "the three wording-run
arms" -> "the wording-run arms"; "We did not measure drift across GPUs or token caps" -> "Drift across GPUs or
caps is unmeasured." The paper is 6 pages with references, with no undefined references and no overfull boxes.

## p18 meaning-audit fixes (p18_audit.md)

Each fix was checked against the text and data before applying it:
- Fix 1 (Methods, Runs): `results/p18_first_14b/20261121-191515-8d096a4/config.yaml` runs B, Bt, Bs0, and Bt0
  with seed 2, `use_tasks` 75 per dataset (150 tasks), and `max_tokens` 4096, the same as `p17_told_14b`, and every
  `RFirst*` macro compares arms within this run. Now: "A 14B first-listed run, on the same tasks and cap,
  interleaves tool-written notes, the told notes.md, and the stored reply named 00_notes.md, told and untold."
- Fix 2 (Statistics): "The told and first-listed runs' comparisons are uncorrected, and the first-listed run's are
  post hoc."
- Fix 3 (Conclusion): at 32B the told Writer opens notes.md in 86% (26% untold) and the Reviewer in 63% (6%), so
  both agents follow the path. At 14B the Writer opens told notes.md in 5% and 00_notes.md in 70%, the Reviewer opens
  00_notes.md in 15% (`RFirstReviewerOpenFirstTold`), and the draft gain of 17.3 is revised away (-17.3). Now:
  "Naming the path led both agents to the notes at 32B. At 14B, the Writer followed it only when the file was also
  listed first, and the Reviewer, which opened it in only \nRFirstReviewerOpenFirstTold{}\% of tasks, undid the
  Writer's gain."
- Fix 4 (zero-copy timing): "in our runs" restored ("... but, in our runs, little of the time").
- Fix 5 (fan-out): `p15_k8_one` and `p15_k8_three` both ran on GPU 4 (port 8204), the second starting when the
  first ended (16:46:12). "on one server" restored.
- Fix 6 (fan-out): "removes drift common to both channels" restored (the DiD subtracts the A1 change from the B
  change on the same tasks).
- Fix 7 (timing): `RSixDecodeShareAOne` uses vLLM metrics from `p11_alone_*_r2` and `_r3`, two of the three alone
  runs. Now "in two of these runs".

The fixes pushed the paper to 7 pages (references [31] and [32] spilled). Trims kept to recover 6 pages, each
needed (reverting any one of them gives 7 pages again):
1. Channels, A2: "and the Reviewer gets the draft" -> "and the Reviewer the draft".
2. Results, timing: "Zero-copy's agents generate 1.2x broadcast's output tokens" -> "Zero-copy generates ...".
3. Table 1 caption: "Copy: broadcast's inputs." -> "Copy: A1's inputs." (A1 is broadcast).
4. Table 1 caption: "among the 16 effects of rows 1-4, or, for the interaction (row 4 minus row 3), among the
   8 post hoc tests (Section 3)" -> "among the 16 effects of rows 1-4 or, for the interaction (row 4 minus row 3), the
   8 post hoc tests" (second "among", one comma, and the section pointer dropped; the families are defined in
   Statistics).
Other trims tried and reverted because they were not needed: "with replacement", "(A1)", "its last call", "one
forced write call", "its tool budget", "supplies", "runtime rules", "on ... on the model", "copying only the
previous output" -> "the pipe", and several fan-out rewordings. No condition, scope qualifier, interval, sample
size, or comparison reference was dropped, and numbers.tex was not edited. The paper is 6 pages with references,
with no undefined references and no overfull boxes. No semicolons were added, and no modified vLLM is mentioned.
