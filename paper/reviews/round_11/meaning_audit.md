# Round 11 meaning audit

Checked: 105 sentences on changed lines (headings and captions included) and all 24 Table 1 cells (16 effects, 4 interactions, 4 rescue pairs). Every macro was resolved in `numbers.tex` and traced to `paper_numbers.py`. The rescue, open-rate, drift and write-caveat values were recomputed from `results_raw/p16_store_*` and `p10_write_*`. Only items that need a fix are listed.

Verified and correct, so not listed:
- The Holm ranges: 20-34 and 8-22.
- "Except at 8B".
- The interaction defined as row 4 minus row 3.
- The 8B 2Wiki, HotpotQA and exact-match caveats.
- The 18 cut or forced 4B tasks (clean N = 132).
- The open rates: 99/9, 95/24, 59/78, 13/5.
- The rescue row, which counts only Writer or Reviewer forced writes, as the caption says.
- The drift bound: A1r, A1w and B, p16 vs p10, 12 paired comparisons with the same config apart from the GPU, and code changes between the two commits that are additive only.
- The serving numbers: 0.49, 14.9/16.9 ms and 0.96 from the same two counter runs; 0.82 and 1.00 from the same two 32-task runs.
- Lauer-Needham.
- MemGPT and AIOS against `related_work.md`.
- The abbreviated bib entries.
- No semicolons in the body.
- No mention of a modified vLLM.
- PDF matches `numbers.tex`.

| # | new text | issue | suggested fix (exact text; macros) |
| --- | --- | --- | --- |
| 1 | §4 findability paragraph: "At 14B and 32B, B's Writer opens the Researcher's files in \nRTenFourteenOpenToolFile{}\% and \nRTenThirtyTwoOpenToolFile{}\% of tasks but \texttt{notes.md} in only \nRTenFourteenOpenReplyFile{}\% and \nRTenThirtyTwoOpenReplyFile{}\%." | The 9% and 24% rates come from the stored-reply arm (Bs), not from B. B's Researcher writes its own files and B has no `notes.md`. "B's Writer" attributes both rates to one arm. | "At 14B and 32B, the Writer opens the Researcher's tool-written files in \nRTenFourteenOpenToolFile{}\% and \nRTenThirtyTwoOpenToolFile{}\% of tasks but the stored \texttt{notes.md} in only \nRTenFourteenOpenReplyFile{}\% and \nRTenThirtyTwoOpenReplyFile{}\%." |
| 2 | §4 delivery paragraph: "At 4B, the harness forced the Writer's or Reviewer's write in every file task, so the 4B file arms' accuracy rests on the rescue." | This is incomplete in a way that matters for the next paragraph. At 14B the stored-reply arm is also rescued in every task (Table 1: \nRTenFourteenRescueReplyFile; raw data: the Reviewer is forced in 150/150 Bs tasks, against 105/150 for B). The 14B stored-reply deficits (-30.0 delivery, 21.3 below tool files) therefore also rest on the rescue. The text implies that only 4B does. | "At 4B, the harness forced the Writer's or Reviewer's write in every file task, and at 14B in every stored-reply task, so the accuracy of these arms rests on the rescue." |
| 3 | §5 heading: "At sixteen questions, a write guard or the heading rule recovers half or more of B's loss in one run." | The guard recovers \nRSixKSixteenGuardOverB of \nRSixKSixteenBGap points (15.1/30.4 = 49.7%), which is less than half. The old heading's "about half" was correct. | "At sixteen questions, a write guard or the heading rule recovers about half or more of B's loss in one run." |
| 4 | §4 heading: "B trails broadcast in every setting, and C trails it by less." | C does not trail broadcast in every setting. On 2Wiki at $k=1$, C is 1.3 points above broadcast (the body's deficit range starts at \nGapCMin). Read with the first clause, the heading says that C trails it everywhere. | "B trails broadcast in every setting, and C trails it by less or not at all." |
| 5 | Abstract: "With Qwen3 models and tool-call file access as tested, agents should copy results forward as replies, and parallel writers should get their own folders." | The scope is too wide for the second recommendation. Separate folders were tested only with Qwen3-8B at $k=8$, and the conclusion says "With Qwen3-8B ... each repair tested at one size". As written, the abstract scopes the folders recommendation to all Qwen3 sizes. | "With Qwen3 models and tool-call file access as tested, agents should copy results forward as replies, and, with Qwen3-8B, parallel writers should get their own folders." |
| 6 | Abstract: "At eight questions, three parallel Researchers sharing one folder cost files without an index \nREightFanBAbs accuracy points, and separate folders recover \nREightFoldersOverB." | The edit dropped the reference ("against one Researcher"). Without it, readers will take 21.2 as the gap to broadcast. That gap is a different number (\nGapBKSixteen at $k=16$). \nREightFanB is three-Researcher B minus one-Researcher B. | "At eight questions, three parallel Researchers sharing one folder cost files without an index \nREightFanBAbs accuracy points against one Researcher, and separate folders recover \nREightFoldersOverB." |
| 7 | §3 Harness: "We mark comparisons between separate runs as cross-run, since they may include run-to-run drift, which we bound in \S\ref{sec:sensitivity}." | Overstated. §5 measures drift only on three-question tasks: A/A on the RTX 3090 (±\nAAWorst), and p16 vs p10 on the PRO 6000 (≤\nRTenDriftMax, three arms). The cross-run $k=16$ comparisons (tool budget, against the earlier PRO 6000 run) are not covered, and B's $k=16$ gap varies by about 3.5 points across runs (33.9 vs 30.4). "Bound" implies a general bound. | "We mark comparisons between separate runs as cross-run, since they may include run-to-run drift, which \S\ref{sec:sensitivity} measures on three-question tasks." |

Number of fixes: 7.
