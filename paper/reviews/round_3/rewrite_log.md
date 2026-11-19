# Round 3 style rewrite: change log

Source before the rewrite: /mnt/sda/heojin/cs632-store/main_pre_style.tex. Numbers before: /mnt/sda/heojin/cs632-store/numbers_pre_style.tex.
Body semicolons (abstract to conclusion, captions excluded): 35 before, 0 after. Captions are unchanged (5 semicolons).
PDF: 6 pages, no undefined references. All existing macros keep their names and values. New macros are listed at the end.

## Abstract
- Split the long cost sentence: the channel and the two cost measures are now two sentences.
- The zero-copy appositive now reads "Zero-copy broadcast, which orders the prompt so ..., keeps copying's accuracy while computing 38-49% as many tokens". The "its ... its" ambiguity is gone, and the macros are unchanged.
- Turned the final semicolon chain into short sentences. Dropped "the cheap pipe loses little" and "while an index loses \nGapCKSixteen". Both still appear in Sec. 5 (Larger payloads).

## Introduction
- Paragraph 1: the dismissal of prior work now has a because-clause ("so it cannot tell whether copying or sharing is the cheaper way ...").
- Paragraph 2: removed the paired "is not free" reversals and the colons. Each cost is now a plain sentence.
- Paragraph 3: now opens "This paper presents a controlled comparison ...". The key observation says "two ways" (tokens sent, tokens computed), which matches the two that follow, and the next sentence starts "Specifically". The second observation lost its "not from the channel alone" reversal and now reads "depend on the cache and the model as well as on the channel".
- Added a challenge sentence and a sentence on what the work is not (no new protocol or engine change).
- Contributions are now verbs with section pointers. Removed bullet 1's five-item metric list, which Methodology defines. Removed bullet 2's four findings, which the abstract and Results carry.

## Five Channels
- Split the 53-word intro sentence. C, D and A1-zc are no longer named before they are defined. "Head each file with its questions" moved into the C paragraph, where Sensitivity relies on it. The handoff and last-instruction items were dropped from the intro because the D and A1-zc paragraphs already state them.
- Added one sentence explaining the count: zero-copy broadcast is a variant of broadcast, not a sixth channel. The section title is unchanged.
- The role descriptions and the D paragraph now use periods instead of semicolons.
- Not applied: switching the B/C/D letters to words in running text. The figures and captions use the letters, so the text keeps them.

## Methodology
- Tasks and Model: semicolons became periods.
- Metrics: split into "Metrics" and a new run-in paragraph, "Validating fact delivery". Stage attribution is now three short sentences, with the rule unchanged: Reviewer if the draft was right, otherwise Researcher, delivery, or Writer. The detector's "first stage that lost something" was not used, because it would charge a different stage when the draft was right but the notes missed a fact. "The split is coarse" and \nRightMissAOne stay. The latency definition now carries the load scope ("under the shared load of six tasks per server"), so Results no longer repeats "under our shared load".
- Validation: dropped the AlignScore per-class rates (\nSynAPresent, \nSynADropped, \nSynASwapped), the judge's acceptance of altered sentences (\nSynQAcceptSwapped), the Llama parenthetical, the lexical kappa (\nAsLexKappa), and the entity recalls (\nEntBNotes, \nEntCNotes, \nEntAOneNotes). Kept the AUC (\nSynAAuc), the judge's acceptance of removed sentences (\nSynQAcceptDropped), kappa (\nAsQKappa), the "treat as approximate" caveat, the entity check's direction, and the D-handoff caveat (\nEntDDeliv).
- Harness: the rescue sentence is now the range \nForcedMin--\nForcedMax% over the same three roles as before (B's Writer, B's and C's Reviewers). Dropped "mostly \nForcedBWriterReply%" and the budget-exhaustion pair (\nForcedBReviewerBudget, \nForcedCReviewerBudget). The strict accuracies are now the range \nStrictMin--\nStrictMax%. "(task, channel)" became "each task runs once per channel".

## Results
- Headings: the first is now "Copying and zero-copy". "Files lose information on both sides; an index helps ..." became "Files lose information when written and when read." "Missing documents ..." now ends "... the file channels' loss". The A1w paragraph keeps its contrast heading. The paragraph is split at the replay, which gets a new run-in heading, "Reading the same notes".
- Zero-copy: accuracy and compute are now separate sentences. The exact-match caveat (\nZcEmGapMax on 2Wiki) stays in the body as its own short sentence rather than moving to the caption, so the figure environment is untouched. The reason and the scope (self-hosted or cached-input discounts) are kept.
- Pipe: "5 of six" now renders "five of six" (\nGapATwoSigWord). The A2d sentence uses unsigned macros: "answers 6.8 points more than the pipe, which leaves it 3.0 points below broadcast". It keeps the broke rates (4% vs 10%) and the 0.96x compute. Dropped the A2d interval and n.
- Files cost more: split the ratio and reason sentences. The latency sentence is now the range \nWallFileMin--\nWallFileMax x of broadcast's 31 s. Dropped zero-copy's and the pipe's latency ratios (\nWallAZc, \nWallATwo) and the per-channel file ratios. Dropped the repeated "under our shared load"; Metrics now states it.
- Files lose information: dropped the character pair (\nNotesCharsFile vs \nNotesCharsMsg). The k=3 scope of the 27% now sits in the sentence. "Facts in its notes" became "facts in the Researcher's notes". The C sentence is split. Dropped "(\nAccC% vs \nAccAOne%)". The count of settings where C is significantly above B stays as its own sentence ("four of six", \nCoverBSigWord).
- Missing documents: dropped the Bd interval and kept the point change. The "notes, not access" contrast stays because it is the finding.
- A1w: dropped \nWCharsAOne. The self-contradictory "the rest comes from reading" is gone. The text now says the tool-call cost is a large part of B's loss and the interval against B does not exclude that it is all of it, as the intervals support. Added "We have not tested why the tool call shortens the notes."
- Replay: dropped "(\nRepBAcc% vs \nRepAccAOne%)" and kept the gap, its interval, and n. Dropped the closing "An index pays off when there are many files ..."; Sensitivity (Parallel writers) makes that point with data.

## Sensitivity
- Reordered: "Larger payloads" now comes first. The cache ablation follows it as the cause, in an unheaded second paragraph, and the "It is the shared cache, not the payload" heading is gone.
- Larger payloads: the sixteen-question sentence is split into zero-copy, pipe, and files. "The index holds C to ... and handles hold D to ..." became "C loses \nGapCKSixteen and D \nGapDKSixteen".
- Cache ablation: kept B and zero-copy. C is summarized as "C behaves like B", and \nPressCCTwo and \nPressCCSix are dropped. Added a sentence saying these ratios divide a channel's computed tokens by its own tokens sent. The accuracy comparison (B and C, two vs six runs) is now "changes by at most \nPressAccMax points" (new macro, 3.8). Dropped the mention of the one-run-per-server reruns, whose numbers were never reported.
- Parallel writers: dropped \nClashD at k=16. The fan-out list is now separate sentences, and B's and broadcast's changes use unsigned macros (\nFanBDiffAbs, \nFanAOneDiffAbs). Kept the DiD with its interval and "not significant at this size". Dropped C's fan-out change (\nFanCDiff and its interval) and D's clash rate and change (\nFanClashD, \nFanDDiff and its interval). D's result is now stated as "clash about as often ... D does not lose accuracy in this control". The ambiguous "as" in the budget clause was not turned into "because", since that cause is untested. The two accuracies now read "with a clash" and "without one", and the budget is stated alongside them.
- Fourth agent: heading "A fourth agent". n moved into the first sentence. Not applied: the detector's guess that the Fact-checker sees the notes. In the pipe it receives only the draft (pipeline.py, and the pipe definition in Sec. 2). The text says so and states that the cause is untested.
- Cheaper reads: the interval is no longer presented as the cost. The paragraph now gives \nBbAccB -> \nBbAcc and "a drop of \nBbAccLo--\nBbAccHi points at 95%", with no new number typed.
- Smaller model: the KV parenthesis now states its point: these runs do not face more cache pressure than Qwen3-8B's. Concurrency is 6 in both configs and the 4B cache is larger. Dropped "(but up to \nSmallATwoGapMax at one question)"; the three-and-five-question scope covers the pipe's "at most". The significance count now renders as a word (\nSmallAZcSigThreeFiveWord). The untested cause is one "We suspect, but have not tested" sentence.
- Tool budget: heading "Tool budget". "The large-payload collapse is that of B under this budget" became "B's collapse at k=16 is a result for this budget". The detector's causal "part of B's collapse" was not used.
- Run-to-run noise: split the list. Not applied: the floating-point-order reason, because neither the paper nor the results support it. "On a batching server" stays as the stated condition.

## Related Work
- Citation chains now use periods instead of semicolons. "The agent analogues are the same" became "The agent versions map directly".

## Conclusion
- Varied the imperatives: two of them are now declarative ("Long results are better written ...", "Files need a naming discipline ..."). Results are reported in past tense and "In our runs" is added. The cost rule keeps only the compute range (\nFileCompMin--\nFileCompMax) and drops \nFileSentMin--\nFileSentMax, which the abstract and Results carry. The last semicolon became a period, and the limitations sentence is otherwise unchanged.

## Not applied from the detector
- A cited number in intro paragraph 1. related_work.md says the "~15x" figure is unconfirmed, and numbers may not be typed by hand.
- Letter-to-word channel names (see Five Channels).
- Moving the exact-match caveat and the C-vs-B settings count into captions (kept in the body; captions untouched).
- The causal rewrites in Parallel writers ("because"), the Fact-checker reason, and the run-to-run reason (all untested).
- "At least half of B's loss" and "reading costs the rest" for A1w (the intervals do not support them).

## New macros (paper_numbers.py)
WallFileMin, WallFileMax; Gap{AZc,ATwo,B,C,D}SigWord; CoverBSigWord; Small{AZc,ATwo,B,C,D}SigThreeFiveWord; ForcedMin, ForcedMax; StrictMin, StrictMax; Fan{AOne,B,C,D}DiffAbs; PressAccMax; Scope{ATwoD,BD}Vs{AOne,ATwo,B}Abs. Of these, the text uses WallFileMin/Max, GapATwoSigWord, CoverBSigWord, SmallAZcSigThreeFiveWord, ForcedMin/Max, StrictMin/Max, FanBDiffAbs, FanAOneDiffAbs, PressAccMax, ScopeATwoDVsATwoAbs, and ScopeATwoDVsAOneAbs. The rest come from the same loops. Regeneration wrote 458 macros (431 before) and skipped no section. A diff against the old numbers.tex shows additions only.
