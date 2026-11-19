# Rewrite log 2 (round 3)

Applies `style_detector_2.md` and `rewrite_audit_2.md` (N1-N5, item 18) to `paper/main.tex`.
Baseline: `cs632-store/main_pre_style2.tex`. Build: 6 pages including references, no undefined references.

## Macros

- Added in `paper_numbers.py` (`harness()`, from `t07_main`, k=3, same records as `Forced*`):
  `\nKThreeBReviewerLimit` = 29, `\nKThreeCReviewerLimit` = 34, `\nKThreeDReviewerLimit` = 1
  (share of runs whose Reviewer hit the 12-call limit). Only the B macro is used (N3).
  No existing macro changed name or value. No section skipped on regeneration.
- No longer used in the text: `\nClashC` (the "(0%)" after "never").
- Newly used in the abstract: `\nSmallAZcGapMaxThreeFive` (already used in §5).

## Labels dropped

- `A2d` (one use, Results) and `Bd` (one use, Results) are dropped. The sentences now say
  "a pipe that also passes them [the documents]" and "putting the documents in the prompts of B's later agents".

## Changed sentences (old -> new)

### Abstract
- "We replay it on ..." -> "We test it on ..."
- "They also lose information on both sides: agents write 27% shorter notes when they write through a tool call, and readers without an index skip them." -> "They also lose information on both sides. Notes written through a tool call are 27% shorter, and readers without an index skip them."
- "These results are conditional." -> cut.
- "Once the prompts of concurrent runs outgrow the KV cache, zero-copy saves nothing." -> "..., zero-copy's savings shrink, and at sixteen questions they vanish." (N2)
- "With sixteen questions split among three parallel Researchers, plain files lose 34 points and files with an index 5, and a 4B model loses up to 35 points with files even with an index." -> "When three parallel Researchers split sixteen questions, plain files lose 34 points and files with an index 5. A 4B model loses up to 35 points with files even when they have an index, and up to 11 with zero-copy ordering." (style split; N1 abstract addition)

### 1 Introduction
- "The choice of channel is the IPC question of operating systems." -> "Operating systems face the same choice." (echo of abstract)
- "... because the model is stateless, each tool call resends ..." -> "... the call resends ..."
- "Specifically, shared files send 2.9x the tokens of copying the history at three questions per task, which is what an API bills." -> "Specifically, at three questions per task shared files send 2.9x the tokens that copying the history does, the cost an API bills."
- "Yet the engine computes only 0.79x as much prefill, which is what a self-hosted deployment pays." -> "..., the cost a self-hosted deployment pays."
- "Copying the history with the shared part first (zero-copy broadcast) keeps copying's accuracy while computing 61% less." -> "... cuts the tokens computed by 61% at copying's accuracy." (echo of abstract)
- "They disappear when the agents' prompts no longer fit the KV cache, ..." -> "They shrink or vanish when ..." (N2)

### 2 Five Channels
- "Every Researcher receives the same user message, the questions and all documents." -> "..., which holds the questions and all documents."
- "Its instructions differ in where its notes go, a reply or files written with a write_file tool, and in what each channel asks of it, as described below." -> "Its instructions differ in where its notes go (a reply, or files written with a write_file tool) and in what each channel asks of it."
- "... so we count it as a variant of broadcast rather than a sixth channel." -> "... so we count it as a variant of broadcast."
- "Only the order changes, and the engine is unmodified. The copy it avoids is the recomputation: every token is still sent." -> "Only the order changes. It avoids recomputing the shared history, but every token is still sent." ("no engine change" stays in the intro)

### 3 Methodology
- "We score the Researcher's output and what the Writer received." -> "..., and call the share of the output's facts that the Writer received *delivery*." (delivery definition now matches the text and the Fig. 3a caption)
- "In message channels that is the copied notes, so ..." -> "In message channels the Writer receives the copied notes, so ..."
- "In file channels it is the text of the files the Writer read, ..." -> "In file channels it receives the text of the files it read, ..."
- "The split is coarse. By this measure 76% of broadcast's correct answers also come from notes that miss a fact." -> "The split is coarse, since 76% of broadcast's correct answers also come from notes that miss a supporting fact."
- "... by exact string, as answer-string recall is used in retrieval [10]." -> "... by exact string, like answer-string recall in retrieval [10]."
- "It agrees that the Researcher's output ..." -> "This check agrees that ..."
- "..., as frameworks take an agent's last message as its output." -> "..., since frameworks take ..."
- "At k=3 this rescue saves 34-59% of the runs of B's Writer and of B's and C's Reviewers." -> "At k=3 this rescue is used in 34-59% of the runs of B's Writer and of the Reviewers of B and C." (`Forced*` counts runs with a forced write, so "is used in" is the literal measure)
- New sentence after "We report 95% bootstrap intervals ...": "A range in parentheses after a difference is that interval." (single interval convention; every "95% interval" / "at 95%" in §4-§5 removed and ranges written "lo to hi")

### 4 Results
- "Broadcast answers 72.3% of the questions at k=3, pooled, more than any other channel (Fig. 2)." -> "At k=3, with both datasets pooled, broadcast answers 72.3% of the questions, more than any other channel (Fig. 2)."
- "It computes 4.8k tokens per task instead of 12.4k, about as little as the pipe (4.7k), because ..." -> "It computes 4.8k tokens per task to broadcast's 12.4k, close to the pipe's 4.7k, because ..."
- "The Reviewer sees only the draft and changes right answers to wrong ones in up to 16% of the questions, against at most 2% when it also sees the notes and documents (Fig. 3b)." -> two sentences: "... in up to 16% of the questions. In broadcast, where it also sees the notes and documents, it does so in at most 2% (Fig. 3b)."
- "What it lacks is the documents." -> "The pipe's missing input is the documents."
- "A pipe that also passes them (A2d) answers 6.8 points more than the pipe on 200 tasks (+3.5 to +10.2), which still leaves it 3.0 points below broadcast (-5.3 to -0.7), and its Reviewer breaks 4% of answers instead of 10%." -> "On 200 tasks, a pipe that also passes them cuts the answers its Reviewer breaks from 10% to 4% and answers 6.8 points more than the pipe (+3.5 to +10.2)." + "It still trails broadcast by 3.0 points (-5.3 to -0.7), yet computes 0.96x broadcast's tokens." (the 200-task scope now opens the sentence and governs all three results)
- "But A2d then computes 0.96x broadcast's tokens." -> merged into the sentence above.
- "Their pipelines make 17.1 and ... model calls instead of three, ..." -> "... model calls to broadcast's three, ..."
- "The cache absorbs most of it: B and C compute 0.79x ..." -> "The cache absorbs most of it, so B and C compute 0.79x ..."
- "The calls are sequential, so file channels are also slower. They take 1.4-1.8x broadcast's 31 s per task." -> "Because the calls are sequential, file channels are also slower, taking 1.4-1.8x broadcast's 31 s per task."
- Fig. 3 caption (a): "Share of supporting facts in the Researcher's output and share that reached the Writer (AlignScore)." -> "Shares of all supporting facts that the Researcher's output states and that reached the Writer (AlignScore). The second bar is the first times delivery, the share of the output's facts that reached the Writer, which §4 reports." (checked against `figdata.py`/`fig_loss.py`: bar 2 = `as_recall_notes * as_kept_writer_input`)
- "Writing to a file changes the writer." -> cut.
- "In B its notes state 32% of the supporting facts instead of 45% (Fig. 3a)." -> "..., where broadcast's state 45% (Fig. 3a)."
- "With handles the Writer trusts the handoff and opens even less (46-54% delivered)." -> "In D the Writer trusts the handoff, opens even fewer files, and receives 46-54% of the notes' facts."
- "Pooled at k=3, C comes within 6.0 points of broadcast and trails it by at most 8 in any one setting, while B loses 6-14 points." -> "In accuracy, C comes within 6.0 points of broadcast at k=3 with both datasets pooled, and within 8 in any one setting, while B trails it by 6-14 points in every setting." (N4)
- Heading "Missing documents do not explain the file channels' loss." -> "Giving files the documents."
- "Putting the documents in the later agents' prompts as well (Bd) leaves B's accuracy unchanged (+0.5 points, 95% interval -2.8 to +3.8, 200 tasks) at 2.2x its tokens." -> "Putting the documents in the prompts of B's later agents as well leaves B's accuracy unchanged on 200 tasks (+0.5 points, -2.8 to +3.8) at 2.2x its tokens."
- "Files lose through their notes, not through access to the sources." -> "Missing sources therefore do not explain the file channels' loss, which lies in their notes." (the heading's claim moves here)
- Heading "The tool call, not the file, shortens the notes." -> unchanged (the one kept X-not-Y, the A1w finding).
- "To separate writing from reading we ran A1w. The Researcher writes ..." -> "In A1w the Researcher writes ..."
- "Its notes are as short as B's (1,093 vs 1,145 characters). They state 31% of the supporting facts, against 30% in B and 46% in A1." -> "On a subset of 200 paired tasks, its notes are as short as B's (1,093 vs 1,145 characters) and state 31% of the supporting facts, where B's state 30% and A1's 46%." (says the B 30% vs 32% difference is the subset)
- "On 200 paired tasks A1w answers 67.3%, 5 points below broadcast (95% interval 2-8)." -> "A1w answers 67.3%, 5 points below broadcast (2 to 8)." (200-task scope moved to the sentence before, same paragraph)
- "This cost is a large part of B's loss but, by a small margin, not all of it: A1w stays 3.2 points above B (0.3-6.2)." -> "..., not all of it, since A1w stays 3.2 points above B (0.3 to 6.2)."
- "We have not tested why the tool call shortens the notes." -> moved to the Conclusion.
- "With the same notes, B and C both answer 5 points fewer ... (95% interval 2-8), ..." -> "Given the same notes, ... (2 to 8), ..."
- "With a single, clearly named notes file the index does not help." -> "When the notes are a single, clearly named file, the index does not help."
- "It opens the notes in 63% of the tasks against B's 76%, and receives 75% of their facts against 90%." -> "It opens the notes less often than B's Writer (63% vs 76% of tasks) and receives fewer of their facts (75% vs 90%)."

### 5 Sensitivity
- "With eight questions per task each prompt holds ..." -> "At eight questions per task ..."
- "Zero-copy broadcast then computes 0.83x the prefill of broadcast instead of 0.39x." -> "..., up from 0.39x at three questions."
- "Plain files collapse: B answers 34 points fewer questions than broadcast, while C loses 5 and D 11." -> "Plain files collapse, with B answering 34 points fewer ..., while C loses 5 and D 11."
- "The lost savings, not the accuracy collapse, come from the cache that concurrent runs share." -> "Cache sharing among concurrent runs explains the lost savings but not the accuracy collapse."
- "B then computes 0.23 of the tokens it sends instead of 0.83, and zero-copy broadcast 0.67 instead of 0.93." + "Unlike the other ratios in this paper, these divide a channel's computed tokens by its own tokens sent." -> "Measured as a share of each channel's own tokens sent, unlike the other ratios in this paper, B then computes 0.23, down from 0.83, and zero-copy broadcast 0.67, down from 0.93." (the ratio warning now precedes the numbers)
- "The savings vanish when the prompts of concurrent runs together outgrow the cache, as at six runs per server, rather than because one prompt is long." -> "A single long prompt does not remove the savings." (the concurrent-runs cause is stated in the paragraph's first sentence, the six-runs condition in the rerun sentence)
- "The race is not the whole loss, though." -> "The race is not the whole loss."
- "In C no two Researchers ever wrote the same path (0%)." -> "... the same path."
- "We have not separated them, but either is the kind of naming discipline that shared memory needs." -> cut here. The caveat moved to the Conclusion. The naming-discipline point is the Conclusion's "Files need a naming discipline, such as an index".
- "The clashes come from the parallel writers. With three Researchers on 100 three-question tasks, B's writers clash in 91% of tasks, and B loses 10 points against one Researcher." -> "To isolate the parallel writers, we ran three Researchers on 100 three-question tasks. B's writers clash in 91% of them, and B loses 10 points relative to one Researcher."
- "On 200 tasks it helps the pipe (62.2% to 67.7%, +3 to +9), although ..." -> "On 200 tasks it raises the pipe from 62.2% to 67.7% (+3 to +9), although ..."
- "We have not tested why it helps." -> moved to the Conclusion.
- "It hurts plain files, where one more agent must find the notes (64.2% to 56.3%, -12 to -4)." -> "It lowers plain files from 64.2% to 56.3% (-12 to -4), where one more agent must find the notes."
- "... lowers accuracy from 64.2% to 52.0%, a drop of 8-16 points at 95%." -> "... from 64.2% to 52.0% (a drop of 8 to 16 points)."
- "The reader also has to know where the result is." -> cut.
- "With Qwen3-4B, the file channels fall far behind ..." -> "On Qwen3-4B, the file channels fall far behind ..."
- "... costs the smaller model 3-11 points there, significantly in three of four settings." -> "... 3-11 points in the same settings, significantly in three of four."
- "We suspect, but have not tested, that the cause is reading its instruction last, after thousands of tokens of documents." -> moved to the Conclusion, still worded as an untested guess.
- "With 24 tool calls instead of 12, B and C send ..." -> "Doubling the tool budget to 24 calls makes B and C send ..."
- "At k=16 it binds harder (B's Reviewer hits it in 52% of runs), so B's collapse there is a result for this budget." -> "At k=16 the 12-call budget binds harder (B's Reviewer hits it in 52% of runs, up from 29% at k=3), so ..." (N3, new macro)
- "... gives the same accuracy within 2 points at 95% and the same B-A1 gap ..." -> "... gives the same accuracy, with each difference's interval inside ±2 points, and the same B-A1 gap ..."

### 6 Related Work
- "Blackboard designs give agents a shared state [..], and MAST catalogs inter-agent failures such as ignored input [3], which our stage attribution measures." -> "Blackboard designs give agents a shared state [..]. MAST catalogs inter-agent failures [3], and our stage attribution measures one of them, ignored input."
- "Zero-copy broadcast is the simplest member of this family: it needs no engine change, only a prompt order that makes the shared prefix exact, and we use it to measure what the channel costs once such reuse is in place." -> "Zero-copy broadcast is the simplest such reuse. It makes the shared prefix exact by prompt order alone, and we use it to measure what the channel costs once reuse is in place."
- "The agent versions map directly: the prefix cache plays zero-copy, and the index plays the directory." -> "In agents, the prefix cache plays the role of zero-copy and the index that of the directory."

### 7 Conclusion
- "In our runs zero-copy broadcast matched broadcast, the most accurate channel, and computed about as little as a pipe." -> "For Qwen3-8B, zero-copy broadcast matched broadcast, the most accurate channel, and computed 61% less at k=3." (N1; also removes the third "as little as a pipe" echo)
- "..., but its savings come from dropping the documents, which costs the Reviewer." -> "..., which at k=3 costs the Reviewer." (N5)
- "Plain files cost more tokens and lost accuracy in every setting." -> "Plain files lost accuracy and cost more tokens in every setting."
- "Finally, a deployment should count the cost it actually pays, because files sent more tokens than copying but computed 0.7-1.2x as much at up to five questions." -> "Finally, a deployment should count the cost it pays, because plain and indexed files sent more ..." (item 18: the range covers B and C only)
- "Our results come from one model family, linear pipelines, and multi-hop QA. We have not measured artifacts larger than a context window, such as code bases, where files should be indispensable." -> "Our results come from one model family, linear pipelines, and multi-hop QA, and we have not measured artifacts larger than a context window, such as code bases, where files may be the only option."
- New sentence: "Nor have we tested why a tool call shortens notes, why a Fact-checker helps the pipe, which of C's two differences prevents the clash, or our guess that the 4B model loses with zero-copy order because it reads its instruction last, after thousands of tokens of documents."

## Caveats moved

| Caveat | Old location | New location |
|---|---|---|
| Why the tool call shortens the notes is untested | §4, end of the A1w paragraph | Conclusion, last sentence |
| Why the Fact-checker helps the pipe is untested | §5 "A fourth agent" | Conclusion, last sentence |
| C's two differences (file heading, index) not separated | §5 "Parallel writers" | Conclusion, last sentence |
| 4B zero-copy loss: suspected cause (instruction last) untested | §5 "A smaller model" | Conclusion, last sentence |
| Artifacts larger than a context window unmeasured | Conclusion, own sentence | Conclusion, merged into the scope sentence |
| A1w numbers come from a 200-task subset | "On 200 paired tasks" on the accuracy sentence | "On a subset of 200 paired tasks" on the sentence before, which now also covers chars and fact shares |
| Pipe-with-documents results on 200 tasks | Inside the accuracy clause | Sentence opener "On 200 tasks," covering all three results |
| Ratio-to-own-tokens warning (cache-pressure rerun) | Sentence after the numbers | Clause before the numbers |
| 95% level of every interval | Repeated at each interval | Stated once in Methodology (Harness) |
| Bd scope (200 tasks) | Inside the parenthetical | "on 200 tasks" in the same sentence |

## Review items not applied

- Fig. 2 caption rewrite and Fig. 4 panel titles: captions and figures may only change for the two listed figure confusions.
- Smaller model: moving or dropping "handles lose 5-12 points and the pipe at most 4". Moving it into a caption is not allowed, and dropping it would remove a result.
- "A1w" heading replacement ("Writing without reading."): kept as the one X-not-Y, because the review's top-tells list says to keep the A1w contrast.
- "Zero-copy broadcast" as subject, and the counts of "also" and "only": only reduced where nearby edits touched them. No dedicated pass.
- Abstract "index 5": kept as its own clause, an option the review allows.
