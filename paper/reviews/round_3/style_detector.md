# Style detector review (round 3)

## Overall: 6/10 (reads as partly machine-written)

The paper has no banned words (no "notably", "crucially", "leverage", "novel"), no em-dashes, and no nested parentheses. Several sentences sound like a person wrote them: "These results are conditional.", "Message channels cannot race, because each agent's output is its own message.", "the agent's `readv`", "the prefix cache plays zero-copy, and the index plays the directory." The tells are in the density and the template. The body has 35 semicolons (plus 5 in captions), 41 colons, and 71 parentheticals. 17 sentences carry six or more number macros, and 7 sentences run past 50 words. Every Results and Sensitivity paragraph has the same shape: a sentence-long claim as the bold heading, then a sentence packed with numbers and parenthesized intervals. Four headings and six more sentences use the "X, not Y" reversal. Most Results paragraphs give the reason for their finding, which is the strongest human move in the draft. Sensitivity and Methodology often do not.

Counts (body, abstract through conclusion, captions excluded):

| Measure | Count | Where it concentrates |
| --- | --- | --- |
| Semicolons | 35 | Channels 7, Methodology 7, Results 5, Sensitivity 5, Related Work 4, Intro 4 |
| Parentheticals | 71 (none nested) | Results 25, Sensitivity 25, Methodology 13 |
| Parentheticals that contain a semicolon | 6 | Channels, Metrics, Harness, Results (3), Sensitivity |
| Sentences with 6 or more macros | 17 | Results and Sensitivity |
| Sentences over 50 words | 7 | Abstract, Intro bullet, Channels, Harness, Results (2), Sensitivity |
| "X, not Y" reversals | 10, 4 of them in headings | Results and Sensitivity |

### Top 5 tells

1. **Number-dense sentences with stacked parentheticals.** Examples:
   - Harness: "this rescue saves B's Writer in \nForcedBWriter\% of runs (mostly, \nForcedBWriterReply\%, a Writer that answered in its reply instead of the file) and B's and C's Reviewers in \nForcedBReviewer\% and \nForcedCReviewer\% (\nForcedBReviewerBudget\% and \nForcedCReviewerBudget\% after using the whole budget); counting every rescued run as wrong would leave B, C, and D at ...": 9 numbers, two parentheticals, a semicolon, and a triplet.
   - Results: "C's Writer skips them in \nNoNotesC\% ..., delivery rises to ..., and C's accuracy comes within \nPooledGapC points of broadcast (\nAccC\% vs \nAccAOne\%; at most \nGapCMax in one setting), while B loses ... (C is significantly above B in \nCoverBSig of six settings)": 10 numbers.
   - Sensitivity, cache ablation and pipeline length: 10 numbers each.

   A human author with six pages would keep one or two numbers per sentence and leave the rest to the figure.
2. **"X, not Y" reversals as a house style (10).** In headings: "The tool call, not the file, shortens the notes", "It is the shared cache, not the payload", "A longer pipeline multiplies copies, not cached ones". In body text: "not from the channel alone", "not through access to the sources", "not one obvious one", "not because one prompt is long", "not from the payload", "breaks \nScopeATwoDBroke\% of answers, not \nScopeATwoBroke\%". The intro adds the parallel "A copy is not free: ... A file read is not free either: ...". Keep the A1w heading, where the contrast is the finding. Rewrite the others as plain statements.
3. **Colon-then-list cramming and semicolon chains.**
   - Abstract end: "zero-copy saves nothing and the cheap pipe loses little; with three Researchers ..., plain files lose ...; and a 4B model loses ...".
   - Contribution 2: "...per condition: copying is the most accurate; zero-copy ordering makes it ...; files cost more ...; an index helps ...".
   - Channels: "(C: head each file with its questions; D: write a handoff; A1-zc: the instruction comes last)".
   - Results: "files are also slower: a task takes ... (B), ... (C), and ... (D)".

   41 colons in about 3,800 words is high. Many of them introduce a list of results rather than an explanation.
4. **Coined labels used before they are defined, and too many of them.** The Channels intro uses C, D, and A1-zc in a parenthesis before their paragraphs define them. After that the reader must track A1, A1-zc, A2, B, C, D, A2d, Bd, A1w, "handoff", "handles", "rescue", "fact delivery", "stage at fault", and "zero-copy broadcast". The text also switches between letters and words for the same channel ("B" / "plain files" / "shared files", "D" / "handles"). The title promises *five* channels ("over five channels", "Five Channels"), but the section defines six paragraphs.
5. **Every result paragraph has the same shape, and several give no reason.** 13 of 14 run-in headings in Results and Sensitivity are full-sentence claims, and each is followed by the same "number (number, number to number)" sentence. The guide's DistServe headings name the workload or question instead. Several results stop at the number:
   - "It helps the pipe": why does a Fact-checker help a pipe?
   - "The tool call ... shortens the notes": why?
   - "accuracy does not move": the change is 4 points on 10 tasks.
   - "\nAAGapRepeat vs \nAAGapMain": no reason is given for the nondeterminism.

### Missing moves from the style guide

- **World, then pain with someone else's number (move 1).** Intro paragraph 1 has the world but no number. The pain ("every copied token is prefilled again", "each tool call resends the whole conversation") arrives in paragraph 2 with no cited magnitude. If \cite{anthropic-multiagent} reports how many more tokens multi-agent systems use than single agents, put that figure in paragraph 1. It is the "10% of items" sentence this paper lacks.
- **Alternatives dismissed with a because-clause (move 2).** "Prior work ... cuts tokens by pruning who talks to whom or by compressing what they say ..., but it keeps the channel fixed." There is no because-clause. Write: "...but it keeps the channel fixed, so it cannot tell whether copying or sharing is the cheaper way to pass the same result."
- **"This paper presents" (move 3).** "This paper replays the comparison under control." is close, but "under control" is odd and names no artifact. Write: "This paper presents a controlled comparison of five inter-agent channels on one pipeline, ...".
- **"Our key observation is ... Specifically" (move 4).** The observation is present but broken: "cost has to be counted *three* ways", and the next sentences give only two (tokens sent and tokens computed). The reader will look for a third. Either say "two ways", or name all three (tokens sent, tokens computed, facts delivered) and start the next sentence with "Specifically,".
- **"The challenge is" (move 5).** This is missing. The real challenge is buried in contribution 1 ("controls that separate what a channel carries from how"). Add one sentence before the bullets: "The challenge is that changing the channel also changes what reaches the next agent, so we add controls that hold one fixed (A2d, Bd, A1w, replayed notes)." To pay for it, cut the five-item metric list from contribution 1.
- **Contributions as verbs on artifacts (move 7).** The bullets are noun phrases ("A testbed ...", "A measurement ...", "Sensitivity results ..."). Make them "We build ... (§3)", "We measure ... and find ... (§5)", "We vary ... (§6)". Bullet 2 is also a semicolon list of four findings. Give it one finding.
- **What the work is not (move 8).** The only instance is the last sentence of the paper (code bases). Add one sentence to the intro or Related Work, for example: "We do not propose a new protocol; zero-copy broadcast needs only a prompt order, and the point is to measure the channels as deployed."
- **Limitations in one place (move 8).** The conclusion's last sentence does this well. But the hedges are also spread through the body:
  - "The split is coarse"
  - "treat fact-level numbers as approximate"
  - "although the interval against B does not exclude that it is all of it"
  - "we have not separated them"
  - "not significant at this size"
  - "a plausible cause, which we have not tested"
  - "under our shared load" / "under the shared load"

  Keep the ones that qualify a specific number. Drop the second "shared load" mention.
- **Evaluation paragraphs as figure, result with baseline, reason (move 9).** Results mostly follow this. Sensitivity usually skips the figure reference and the reason (see below).

## Section by section

### Abstract: 5
- "ordering the prompt so the prefix cache reuses the shared history, a zero-copy broadcast, keeps its accuracy at \nZcRatioMin--\nZcRatioMax\% of its compute": the appositive coins the term mid-sentence, and the two "its" have different referents. Fix: "Zero-copy broadcast, which orders the prompt so the prefix cache reuses the shared history, keeps copying's accuracy at 38-49% of its compute."
- "These results are conditional. Once ... saves nothing and the cheap pipe loses little; with three Researchers ..., plain files lose \nGapBKSixteen points while an index loses \nGapCKSixteen; and a 4B model loses ...": a three-part semicolon chain after a good short sentence. Keep the short sentence. Then use two sentences: (1) cache overflow erases zero-copy's saving; (2) parallel writers and a smaller model hurt files. Drop "the cheap pipe loses little" and "while an index loses 5"; the abstract does not need them.
- Good: "This is the message-passing versus shared-memory question of operating systems." Keep it.

### Introduction: 6
- Paragraph 1 has no number (see move 1). Its last sentence dismisses prior work without a because-clause (see move 2).
- "A copy is not free: ... A file read is not free either: ... And the serving engine changes both, because ...": paired reversal plus two reveal colons. Fix: "Each copied token is prefilled again. Each file read is a model call that resends the whole conversation, because the model is stateless. And the engine's prefix cache changes both costs ..."
- "Our key observation is that cost has to be counted *three* ways": only two follow (see the missing moves).
- "The second observation is that these savings come from the cache and the model, not from the channel alone: they disappear when ...": reversal plus a colon. Fix: "The second observation is that the savings depend on the cache and the model. They disappear when ..., and the file channels need a model that uses tools well."
- Contribution 1: "accounts for tokens sent, tokens computed, latency, file I/O, and where each supporting fact is lost": a five-item list that Methodology repeats. Cut it to "with controls that separate what a channel carries from how it carries it."
- Contribution 2 (54 words): "...per condition: copying is the most accurate; zero-copy ordering makes it as cheap ...; files cost more tokens and lose ...; an index helps ...". This is a colon plus a four-part semicolon chain that repeats the abstract. Fix: "We measure five channels on two multi-hop QA benchmarks (§5) and find where each loses information."
- Contribution 3: "which turn the comparison into rules for when each channel is the right choice" is fine.

### Five Channels: 6
- "Every Researcher receives the same user message, the questions and all documents; its instructions differ in where its notes go (a reply, or files written with a `write_file` tool) and in what the channel asks of it (C: head each file with its questions; D: write a handoff; A1-zc: the instruction comes last).": 53 words, two parentheticals, and a semicolon list inside a parenthesis that names C, D, and A1-zc before they are defined. Fix: end the sentence after "the questions and all documents". Move "head each file with its questions" into the C paragraph; Sensitivity relies on it later. Drop the other two items, because the D and A1-zc paragraphs already say them.
- Count: the heading and intro say five channels, but there are six paragraphs. Say "five channels and one ordering of broadcast", or retitle.
- "The copy it avoids is the recomputation: every token is still sent." This is good and plain. Keep it.
- "The *Researcher* reads ...; the *Writer* drafts ...; the *Reviewer* checks ...": a three-part semicolon chain, but it lists real roles. Acceptable. Periods would read better and cost nothing.
- Letter labels: pick words or letters and use them consistently in running text. "Files", "index", and "handles" read better than B, C, and D, and the figures can keep the letters.

### Methodology: 7
- **Metrics** is about 400 words doing five jobs: define accuracy, define tokens, define fact delivery, attribute errors, and validate AlignScore twice. The validation alone carries 11 macros:
  - "labels them correctly \nSynAPresent, \nSynADropped, and \nSynASwapped\% of the time (AUC \nSynAAuc), while Qwen3-8B used as a judge also accepts \nSynQAcceptDropped\% of removed and \nSynQAcceptSwapped\% of altered sentences (Llama-3-8B-Instruct is similar)"
  - "($\kappa$ = \nAsQKappa; \nAsLexKappa with lexical matching)"
  - "(\nEntBNotes--\nEntCNotes\% vs \nEntAOneNotes\%) ... \nEntDDeliv\%"

  The section's claim needs two numbers: AlignScore's AUC on known pairs, and the judge's acceptance of removed facts. Cut the Llama parenthetical and the lexical kappa. Shrink the entity check to one sentence: "An exact-match check on gold-chain entities agrees on the direction." Split Metrics into "Metrics" and "Validating fact delivery".
- "the Reviewer if the draft answer was right; otherwise the Researcher if ..., delivery if ..., and the Writer if ...": a colon and semicolon cascade for the error attribution. Fig. 3's caption already explains the bias. Fix: "We charge each wrong answer to the first stage that lost something: the Researcher, delivery, the Writer, or the Reviewer."
- "by this measure \nRightMissAOne\% of broadcast's correct answers also come from notes that miss a fact": a surprising number with no reason. Add the reason in a clause (the Writer reads the documents too) or cut it. "The split is coarse" already makes the point.
- **Harness**: the 58-word rescue sentence is quoted in tell 1. Fix: "This rescue saves 34-59% of file-channel Writers and Reviewers at $k=3$. Counting every rescued run as wrong would leave B, C, and D at 18-41%." Drop "(mostly, \nForcedBWriterReply\%, ...)": "mostly" followed by a percentage of a percentage needs two readings.
- "We report 95\% bootstrap intervals over tasks and paired differences against A1; each (task, channel) runs once." Split at the semicolon. The tuple in parentheses reads like code; write "each task runs once per channel".

### Results: 7
- **Zero-copy paragraph.** "Zero-copy broadcast is within \nGapAZcMax points of it in every dataset and $k$ (\nAccAZc\%), no difference significant, though under exact match it is up to \nZcEmGapMax points lower on 2Wiki, and computes \nCompAZc tokens per task instead of \nCompAOne, ...": 59 words. The "though" clause separates "is" from its second verb "computes". Fix: give accuracy and compute separate sentences, and move the exact-match caveat to Fig. 2's caption. The reason ("because the Writer and the Reviewer reuse the documents the Researcher already prefilled") and the scope ("so the gain is for self-hosted serving or APIs that discount cached input") are both good; keep them.
- **Pipe paragraph.** "a pipe that also passes them (A2d) answers \nScopeATwoDVsATwo points more (..., \nScopeATwoDN runs), \nScopeATwoDVsAOne below broadcast, and its Reviewer breaks \nScopeATwoDBroke\% of answers, not \nScopeATwoBroke\%, but it then computes ...": 8 numbers. It renders as "+6.8 points more" and "-3.0 below broadcast". The signed macros double the sign words, and "-3.0 below" reads as above. Fix: "Passing the documents too (A2d) recovers 7 points and stops most of the Reviewer's errors, but then it computes as much as broadcast (0.96x)." Drop the interval and the n; the claim does not need them.
- "significantly in \nGapATwoSig of six settings" renders as "5 of six". The same mix appears in "4 of six" and "3 of four". Use numerals for both.
- **Files cost more tokens.** The reason clause ("because their pipelines make ... model calls instead of three and each call resends the conversation") is the guide's move 9; keep it. The latency sentence lists five ratios: "a task takes \nWallB$\times$ (B), \nWallC$\times$ (C), and \nWallD$\times$ (D) broadcast's \nWallAOne\,s ..., against \nWallAZc$\times$ ... and \nWallATwo$\times$ ...". The claim is only "files are slower because calls are sequential". Fix: "File channels take 1.4-1.8x broadcast's 31 s per task."
- **Files lose information.** The heading has a semicolon. Use "Files lose information when written and when read." The last sentence (quoted in tell 1) has 10 numbers. Fix: "With the index, C's Writer skips the notes in only 7% of tasks, and C comes within 6 points of broadcast while B loses 6-14." The settings count can go to the caption. "the files B's Writer reads state only \nDelivBMin--\nDelivBMax\% of the facts in its notes": "its" is ambiguous (Writer or Researcher?). Write "of the Researcher's facts".
- **Missing documents.** The heading "do not explain the file channels" is vague; write "...do not explain the file channels' loss." "files lose through their notes, not through access to the sources" is a reversal, but here the contrast is the finding, so it may stay. Drop the interval in the parenthesis.
- **The tool call paragraph** does two jobs (A1w, then replayed notes) in about 250 words. Split it at "To measure reading alone".
  - "Writing the result as a tool-call argument therefore costs accuracy by itself, a large part of B's loss, although the interval against B does not exclude that it is all of it; the rest comes from reading.": this hedge contradicts itself. If the effect may be all of B's loss, "the rest comes from reading" does not follow. Fix: "Writing through a tool call alone costs 5 points, at least half of B's loss; replaying fixed notes (below) shows that reading costs the rest." State only what the two intervals support.
  - No reason is given for why a tool call shortens notes. The result is the paper's most quotable, and the reader will ask why. Give one clause, even if hedged once, or say plainly that it is unexplained.
  - "An index pays off when there are many files written by others, not one obvious one.": a closing restatement plus a reversal. Cut it; Sensitivity (parallel writers) makes the point with data.
- "(\nNotesCharsFile vs \nNotesCharsMsg characters at $k=3$)" and "(\nWChars vs \nWCharsB characters; \nWCharsAOne in A1)" each restate the 27% shorter. Keep one pair.

### Sensitivity: 8 (densest section)
- **Order and headings contradict each other.** "It is the shared cache, not the payload." comes before "Larger payloads leave the cache behind." So the explanation precedes the result it explains, "It" has no antecedent, and the two headings say opposite things. Fix: put "Larger payloads" first. Then fold the ablation into it as the reason: "The cause is the shared cache: with two runs per server instead of six, B computes 0.23 of what it sends instead of 0.83." This cuts one heading and about four macros.
- Cache-ablation paragraph:
  - "With two, B computes \nPressBCTwo of the tokens it sends instead of \nPressBCSix, C \nPressCCTwo instead of \nPressCCSix, and zero-copy broadcast \nPressAZcCTwo instead of \nPressAZcCSix": a 10-number chain. These are compute/sent ratios, while every other ratio in the paper is relative to broadcast. Say so, or use one channel.
  - "with one and two runs per server" reports only two.
  - "accuracy does not move (B \nPressBAccTwo\% vs \nPressBAccSix\% ...)" is a 4-point change on 10 tasks. Write "changes by under 4 points on 10 tasks".
- "At sixteen questions, which we split among three parallel Researchers, zero-copy broadcast saves nothing (...), the pipe matches broadcast's accuracy (...) at ... its compute, and plain files collapse: B answers ..., while the index holds C to ... and handles hold D to ...": 54 words, 6 numbers, colon, and the parallel "holds ... to / hold ... to". Split into the cache result and the files result. The 34-point collapse is the headline, so give it its own sentence.
- **Parallel writers** is about 280 words with roughly 25 macros and seven jobs. Keep four things: the clash rate, the notes kept with and without a clash (34% vs 67%), C's zero clashes and the two candidate causes, and the $k=3$ control's non-significant difference-in-differences.
  - "B answers \nLargeClashAcc\% and \nLargeNoClashAcc\% of those tasks' questions, as its Reviewer also runs out of budget": "as" can mean "while" or "because". Write "because".
  - "The clashes come from the parallel writers, not from the payload: with three Researchers on three-question tasks (\nFanN tasks) B's writers clash in ...": a reversal plus a colon plus a 49-word list. Fix: "Three Researchers clash just as often on three-question tasks (91%)." The DiD sentence can then stand alone.
  - Cut the D clash and accuracy numbers ("D's writers clash as often ... D changes by ...") or move them to Fig. 4's caption. The handoff reason is one clause; keep that.
- **Longer pipeline.** The heading "multiplies copies, not cached ones" is a reversal. Use "A fourth agent." The pipe result ("It helps the pipe (\nChainATwoAccRef\% to \nChainATwoAcc\%, \nChainATwoLo to \nChainATwoHi)") has no reason. Presumably the Fact-checker sees the notes the Reviewer otherwise lacks; say so. "(..., \nChainBLo to \nChainBHi; \nChainN tasks)" has a semicolon inside a parenthesis; move n to the first sentence.
- **Cheaper reads** is the best paragraph in the section: it gives a figure, a baseline, and a reason, and "the agent's `readv`" is an OS touch a human adds. "costs \nBbAccLo--\nBbAccHi points of accuracy" presents an interval as the cost; state the point estimate (12 points) instead.
- **Smaller model.**
  - "whose smaller weights leave a larger cache (\nSmallKv tokens vs \nBigKv)" never says why it matters. Add "so cache pressure cannot explain the gap", or cut the parenthesis.
  - "Handles lose ... and the pipe at most \nSmallATwoGapMaxThreeFive (but up to \nSmallATwoGapMax at one question)": the "but" aside in parentheses is a stacked hedge. Drop it.
  - "...(significant in \nSmallAZcSigThreeFive of four settings); a plausible cause, which we have not tested, is that ...": a semicolon plus a hedge appositive. Fix: "We suspect, without having tested it, that the small model loses its instruction when it comes last, after thousands of tokens of documents."
- **Tool budget.** "so the large-payload collapse is that of B under this budget" is awkward. Write "so at $k=16$ the budget is part of B's collapse."
- **Run-to-run noise** is short and plain. One clause of reason would help: batch composition changes the order of floating-point sums.

### Related Work: 4
- Plain and specific. "They change who talks or what is said over a fixed channel; we change the channel and count what the engine computes." is the contrast this paper needs. Consider moving it into intro paragraph 1 as the move-2 dismissal; it already has the because-shape.
- "The agent analogues are the same:" is odd, since the analogues are not "the same". Write "The agent versions map directly:".
- 4 semicolons, all in comma-chains of citations. Acceptable.

### Conclusion: 5
- Four imperatives in a row ("copy it and order prompts", "Let agents write", "Share files only with", "Count the cost") with the same "When X, do Y: evidence" shape. As design rules this is acceptable, but vary one. The "Count the cost" sentence repeats the abstract's numbers; cut the numbers.
- Tense changes from "matched", "computed", "shortened" to "plain files cost more tokens and lost accuracy". Use one tense.
- The last sentence is the guide's move 8 done well: "artifacts larger than a context window, such as code bases, are where files should be indispensable, and we have not measured them." Keep it. Its semicolon could be a period.

## Hard to follow on first reading
- "three ways" in the key observation, followed by only two ways.
- "Five channels", followed by six channel paragraphs.
- C, D, and A1-zc are used in the Channels intro before they are defined. A2d, Bd, and A1w are defined only in parentheses at first use.
- "under control" (intro paragraph 3) reads as an idiom, not as "controlled".
- "(mostly, \nForcedBWriterReply\%, a Writer that ...)": a percentage of a percentage.
- "+6.8 points more", "-3.0 below broadcast": doubled signs.
- "the facts in its notes": whose notes?
- "It is the shared cache, not the payload" appears before any payload result, and contradicts the next heading.
- The cache ablation's ratios are compute/sent, while the rest of the paper uses ratios relative to broadcast.
- "does not exclude that it is all of it; the rest comes from reading": self-contradictory.
- "the large-payload collapse is that of B under this budget".

## Page budget
Every fix above cuts or splits; only the "challenge" sentence and two reason clauses add text. The cuts that pay for them:
- the contribution-1 metric list (about 20 words)
- the AlignScore and judge side numbers (about 40 words)
- the Harness breakdown (about 35 words)
- the A2d intervals (about 15 words)
- the latency ratios (about 25 words)
- the merged Sensitivity heading and cache paragraph (about 40 words)
- the Parallel-writers D sentence and fan-out list (about 50 words)

Together these free more than the additions need. The body will still end on page 6.
