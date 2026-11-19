# Style detector review 2 (round 3)

Reviewed: `paper/main.tex` and `numbers.tex` as built in `main.pdf` (6 pages; body ends in the left column
of page 6, so there are only a few lines of slack). I judged this version on its own and did not read the
earlier reviews.

## Score: 4 / 10 (10 = obviously machine-written)

Most of the paper reads like a careful human systems researcher wrote it. Sentences are mostly
subject-verb-object, "we" does the work, the method is concrete, and the body has no rhetorical questions
and none of the banned words. What gives it away is a set of small habits that repeat often enough to form
a pattern. The worst is the comparison frame "N instead of M" / "N against M" (10 + 7 uses), which turns many
paragraphs into a ledger of numbers. Others are colon reveals, an "X, not Y" reversal in about every
second Results paragraph, a "We have not tested ..." refrain, and three pieces of wording that a reader has
to parse twice. None of these is hard to fix, and most fixes make the text shorter.

## Top tells

1. **Number ledgers built on "instead of" / "against".** "instead of" appears 10 times and "against" 7 times,
   nearly always between two numbers, e.g. "computes 4.8k tokens per task instead of 12.4k",
   "breaks 4% of answers instead of 10%", "B then computes 0.23 ... instead of 0.83, and zero-copy broadcast
   0.67 instead of 0.93", "opens the notes in 63% of the tasks against B's 76%, and receives 75% of their facts
   against 90%". Several sentences carry 4 to 7 numbers (the A2d sentence has seven).
2. **"X, not Y" reversals as section-level flourishes.** "The tool call, not the file, shortens the notes."
   (heading); "Files lose through their notes, not through access to the sources."; "The lost savings, not the
   accuracy collapse, come from the cache ..."; "rather than because one prompt is long"; "as a variant of
   broadcast rather than a sixth channel". Keep one where the contrast is the finding (A1w) and rephrase the rest.
3. **Colon and pseudo-cleft reveals.** "The copy it avoids is the recomputation: every token is still sent.";
   "The cache absorbs most of it: B and C compute ..."; "Plain files collapse: B answers ..."; "not all of it:
   A1w stays ..."; "is the simplest member of this family: it needs ..."; "The agent versions map directly: ...";
   "What it lacks is the documents."
4. **The "We have not ..." refrain.** "We have not tested why the tool call shortens the notes." / "We have not
   tested why it helps." / "We suspect, but have not tested, that ..." / "We have not separated them, but ..." /
   "We have not measured artifacts larger ...". There are five of these, each as its own short sentence closing a
   paragraph. Each caveat is honest, but the identical shape reads like a template.
5. **Aphoristic or restating closers.** "Writing to a file changes the writer."; "The reader also has to know
   where the result is."; "These results are conditional."; "The clashes come from the parallel writers."
   Each is a short sentence that restates the paragraph's point in a quotable form.
6. **Echoed phrases across sections.** "keeps copying's accuracy while computing" (abstract and intro, word for
   word); "about as little as the pipe" (Results) / "at a pipe's cost" (Fig. 2) / "about as little as a pipe"
   (Conclusion); "needs only a prompt order" (intro) / "Only the order changes, and the engine is unmodified" (§2) /
   "needs no engine change, only a prompt order" (Related). Each of these is said three times.
7. **Uniform openings.** Seven sentences open with "With ..." (and three of four Sensitivity paragraphs open
   "With <condition>, ..."); "Zero-copy broadcast" is the subject 13 times; there are 13 uses of "also" and 15 of "only".
8. **Unclear on first reading.** (a) "Specifically, shared files send 2.9x the tokens of copying the history at
   three questions per task, which is what an API bills." Here "which" first attaches to "three questions per
   task". (b) "The lost savings, not the accuracy collapse, come from the cache that concurrent runs share."
   (c) "By this measure 76% of broadcast's correct answers also come from notes that miss a fact." It is not clear
   which measure is meant. (d) "At k=16 it binds harder", where "it" could be the 12-call or the 24-call budget.

## Section by section

Each item quotes the sentence, then gives a fix that is the same length or shorter.

### Abstract

- "We replay it on a Researcher–Writer–Reviewer pipeline" — "replay" later names a specific control (replaying
  notes). Fix: "We test it on ...".
- "They also lose information on both sides: agents write 27% shorter notes when they write through a tool call,
  and readers without an index skip them." This is a colon reveal, and "write ... write" repeats. Fix: "They also
  lose information twice. Notes written through a tool call are 27% shorter, and readers without an index skip them."
- "These results are conditional. Once the prompts of concurrent runs outgrow the KV cache, zero-copy saves
  nothing." The two-word-claim opener is a tell. Fix: merge into one sentence without a colon: "Zero-copy saves nothing once the prompts of concurrent runs outgrow the KV cache."
- Last sentence: "plain files lose 34 points and files with an index 5, and a 4B model loses up to 35 points with
  files even with an index." This has three numbers and "with ... with ... with". Fix: "With sixteen questions split
  among three parallel Researchers, plain files lose 34 points. A 4B model loses up to 35 points with files even when
  they have an index." This drops the "index 5" figure from the abstract only; it stays in §5. If the authors want to
  keep it, split it into its own short sentence instead.
- "keeps copying's accuracy while computing 38–49% as many tokens" — the same clause appears in the intro with "61%
  less". Readers see two framings of one result. Fix: use one framing in both places, or rephrase the intro (below).

### 1 Introduction

- "Specifically, shared files send 2.9x the tokens of copying the history at three questions per task, which is what
  an API bills. Yet the engine computes only 0.79x as much prefill, which is what a self-hosted deployment pays."
  The relative clause attaches to the wrong noun, and "which is what" appears twice in parallel. Fix: "Specifically, at
  three questions per task shared files send 2.9x the tokens that copying does, the cost an API bills. Yet the engine
  computes only 0.79x as much, the cost of a self-hosted deployment."
- "Copying the history with the shared part first (zero-copy broadcast) keeps copying's accuracy while computing 61%
  less." This echoes the abstract word for word. Fix: "Putting the shared history first (zero-copy broadcast) cuts
  computed tokens by 61% at the same accuracy."
- "The choice of channel is the IPC question of operating systems." echoes the abstract's "This is the message-passing
  versus shared-memory question of operating systems." Fix: keep the abstract sentence and open the paragraph with
  the content instead: "Operating systems face the same choice. Message passing copies data ..."
- "Each copied token is prefilled again. Each file read is a tool call, and because the model is stateless, each tool
  call resends the whole conversation." This has three "each" in a row. The parallelism is earned, but the third can
  go: "... and because the model is stateless, the call resends the whole conversation."
- "We propose no new protocol or engine change. Zero-copy broadcast needs only a prompt order." This is the first of
  three statements of the same point (see §2 and Related Work). Keep this one.

### 2 Five Channels

- "Every Researcher receives the same user message, the questions and all documents." The appositive reads as a
  three-item list. Fix: "... the same user message, which holds the questions and all documents."
- "Its instructions differ in where its notes go, a reply or files written with a write_file tool, and in what each
  channel asks of it, as described below." The appositive is ambiguous again, and "as described below" is filler. Fix:
  "Its instructions differ only in where its notes go (a reply, or files written with write_file) and in what each
  channel asks of it."
- "so we count it as a variant of broadcast rather than a sixth channel." This is a "rather than" flourish. Fix:
  "so we count it as a variant of broadcast."
- A1-zc: "Only the order changes, and the engine is unmodified. The copy it avoids is the recomputation: every token
  is still sent." This repeats the intro and ends in a colon reveal. Fix (shorter): "Only the order changes. It saves
  computation only; every token is still sent."

### 3 Methodology

- Metrics: "The split is coarse. By this measure 76% of broadcast's correct answers also come from notes that miss a
  fact." "This measure" has no clear referent. Fix: "The split is coarse, since 76% of broadcast's correct answers also
  come from notes that miss a supporting fact." This keeps the caveat and loses the dangling reference.
- Validating: "as answer-string recall is used in retrieval [10]" is awkward. Fix: "(as in answer-string recall for
  retrieval [10])".
- Validating: "It agrees that the Researcher's output keeps fewer of them in file channels. It credits D's handoffs ..."
  These two sentences open with "It" after a sentence whose subject was "we", so the pronoun dangles. Fix: "This check
  agrees ... It credits ...".
- Harness: "as frameworks take an agent's last message as its output" uses "as ... as" with two senses. Fix: "since
  frameworks take an agent's last message as its output".
- Harness: "this rescue saves 34–59% of the runs of B's Writer and of B's and C's Reviewers" is hard to parse. Fix:
  "the rescue fires in 34–59% of runs for B's Writer and for the Reviewers of B and C". (Check that "saves" meant "is needed in"; if it meant something
  else, say that instead.)
- Intervals are written five ways in the paper: "(95% interval -2.8 to +3.8)", "(95% interval 2–8)",
  "(+3.5 to +10.2)", "(0.3–6.2)", "a drop of 8–16 points at 95%", "within 2 points at 95%". Fix that also cuts words:
  state once here, "Ranges in parentheses after a difference are 95% intervals", then write every interval the same
  way, e.g. "(-2.8 to +3.8)", and drop each "95% interval" and "at 95%".

### 4 Results

- Copying and zero-copy: "Broadcast answers 72.3% of the questions at k=3, pooled, more than any other channel." The
  bare "pooled" dangles. Fix: "At k=3, with both datasets pooled, broadcast answers 72.3% ..." The phrase can also be
  dropped here, since the Fig. 2 caption states it.
- Copying and zero-copy: "It computes 4.8k tokens per task instead of 12.4k, about as little as the pipe (4.7k)" — one
  of the three "as little as a pipe" echoes. Fix: "It computes 4.8k tokens per task to broadcast's 12.4k, close to the
  pipe's 4.7k". In the Conclusion, change "computed about as little as a pipe" to "computed 61% less".
- Pipe: "What it lacks is the documents. A pipe that also passes them (A2d) answers 6.8 points more than the pipe on 200
  tasks (+3.5 to +10.2), which still leaves it 3.0 points below broadcast (-5.3 to -0.7), and its Reviewer breaks 4% of
  answers instead of 10%. But A2d then computes 0.96x broadcast's tokens." This is the densest sentence in the paper
  (seven numbers), and it is preceded by a pseudo-cleft. Fix (same length, two sentences, no cleft):
  "The Reviewer lacks the documents. When the pipe also passes them, its Reviewer breaks 4% of answers instead of 10%
  and accuracy rises 6.8 points on 200 tasks (+3.5 to +10.2), still 3.0 below broadcast (-5.3 to -0.7) at 0.96x its
  compute." Dropping the label "A2d", which is used only here, also lowers the coined-term count.
- Files cost more tokens: "The cache absorbs most of it: B and C compute 0.79x the tokens of broadcast." Colon reveal.
  Fix: "The cache absorbs most of it, so B and C compute only 0.79x broadcast's tokens."
- Files cost more tokens: "The calls are sequential, so file channels are also slower. They take 1.4–1.8x broadcast's
  31 s per task." Fix (merge, shorter): "Because the calls are sequential, file channels also take 1.4–1.8x broadcast's
  31 s per task."
- Files lose information: "Writing to a file changes the writer." This aphoristic opener is the most quotable-sounding
  line in the paper. Fix: cut it; the next sentence makes the point.
- Files lose information: this paragraph carries 14 numbers. "Pooled at k=3, C comes within 6.0 points of broadcast and
  trails it by at most 8 in any one setting, while B loses 6–14 points. C is significantly above B in four of six
  settings." "Pooled at k=3" dangles, and the comparison is accuracy rather than information loss. Fix: move these two
  sentences to the end of "Files cost more tokens", or open them with "In accuracy, C ...".
- Files lose information: "With handles the Writer trusts the handoff and opens even less (46–54% delivered)." It is
  unclear what "opens even less" refers to. Fix: "With handles the Writer trusts the handoff, opens fewer files, and
  receives 46–54% of the notes' facts."
- Files lose information: the text gives delivery as a share of *the notes' facts* (87–94%), while Fig. 3a plots the
  share of *supporting facts* (B: 32 -> 29). A reader comparing the two will be confused. Fix: one clause in the Fig. 3
  caption: "(a) ... as a share of all supporting facts; §4 reports delivery as a share of the notes' facts."
- Missing documents: the heading "Missing documents do not explain the file channels' loss." is followed by "Files lose
  through their notes, not through access to the sources." That pairs a negative heading with an X-not-Y closer. Fix:
  use a topic heading, "Giving files the documents.", and replace the closer with "The loss lies in the notes." Also
  drop the one-use label "(Bd)".
- Tool call heading: "The tool call, not the file, shortens the notes." Fix: "Writing without reading." or "Separating
  writing from reading." Then cut the first sentence, "To separate writing from reading we ran A1w.", and start "In A1w
  the Researcher writes ..."
- Tool call: "They state 31% of the supporting facts, against 30% in B and 46% in A1." The previous paragraph gave B as
  32% and A1 as 45%. The difference comes from the 200-task subset, but a reader sees two different "B" numbers. Fix:
  "On these 200 tasks they state 31% of the supporting facts, as in B (30%) and well below A1 (46%)." Then delete "On
  200 paired tasks" from the next sentence.
- Tool call: "This cost is a large part of B's loss but, by a small margin, not all of it: A1w stays 3.2 points above B
  (0.3–6.2). We have not tested why the tool call shortens the notes." This has a colon reveal and the "have not"
  refrain. Fix: "It accounts for most of B's loss but not all: A1w stays 3.2 points above B (0.3 to 6.2)." Move the
  "why" caveat to the Conclusion (see below).
- Reading the same notes: "With a single, clearly named notes file the index does not help. C's Writer reads the
  index, which also lists thirty source documents, in 53% of the tasks. It opens the notes in 63% of the tasks against
  B's 76%, and receives 75% of their facts against 90%." This gives four "against"-style pairs in two sentences. Fix:
  "C's Writer opens the notes less often than B's (63% vs 76% of tasks) and receives fewer of their facts (75% vs 90%)."
  The 53% index-read figure can go to the end of the clause if needed.

### 5 Sensitivity

- Openings: "With eight questions ...", "With Qwen3-4B ...", "With 24 tool calls ..." (and "With three Researchers",
  "With sixteen questions" in the abstract). Fix: vary two of them. For example, "Qwen3-4B leaves the file channels far
  behind broadcast ..." and "Doubling the tool budget to 24 calls makes B and C send 22–32% more tokens ...".
- Larger payloads: "Plain files collapse: B answers 34 points fewer questions than broadcast, while C loses 5 and D 11."
  Fix: "Plain files collapse, answering 34 points fewer questions than broadcast; C loses 5 and D 11." Or drop the colon
  with "B collapses, ...".
- Unheaded paragraph: "The lost savings, not the accuracy collapse, come from the cache that concurrent runs share."
  This is the hardest sentence in the paper to parse on first reading. Fix: "Cache sharing among concurrent runs
  explains the lost savings, but not B's accuracy loss."
- Same paragraph: "Unlike the other ratios in this paper, these divide a channel's computed tokens by its own tokens
  sent." The definition comes after the numbers it defines. Fix: move it before them by folding it into the clause: "B
  then computes 0.23 of its own tokens sent instead of 0.83 ..." The phrase "of the tokens it sends" already says this,
  so the separate "Unlike ..." sentence can be cut, which saves a line. If the authors want the warning kept, put it in
  parentheses before the numbers.
- Same paragraph: "The savings vanish when the prompts of concurrent runs together outgrow the cache, as at six runs per
  server, rather than because one prompt is long." This restates the paragraph's opening line and adds a "rather than"
  reversal. Fix: cut it, or reduce it to "One long prompt alone does not cause it."
- Parallel writers: "The race is not the whole loss, though." / "We have not separated them, but either is the kind of
  naming discipline that shared memory needs." / "The clashes come from the parallel writers." These are three
  hedge-or-restate sentences in one paragraph. Fix: cut "The clashes come from the parallel writers." and start the next
  sentence "To isolate the writers, we ran three Researchers on 100 three-question tasks ...". Cut "but either is the
  kind of naming discipline that shared memory needs" (the Conclusion says it).
- Parallel writers: "In C no two Researchers ever wrote the same path (0%)." The "(0%)" restates "no two ... ever". Fix:
  drop "(0%)".
- A fourth agent: "On 200 tasks it helps the pipe (62.2% to 67.7%, +3 to +9)" has stacked parentheses with two kinds of
  numbers. Fix: "On 200 tasks it raises the pipe from 62.2% to 67.7% (+3 to +9)". Do the same for the plain-files clause.
  "We have not tested why it helps." should move to the Conclusion.
- Cheaper reads: "a drop of 8–16 points at 95%" is terse. With the single interval convention above, use "(-16 to -8)".
  "The reader also has to know where the result is." is an aphoristic closer. Fix: cut it.
- Smaller model: "B by 22–29 points and C by 19–35. ... Handles lose 5–12 points and the pipe at most 4. Zero-copy
  ordering ... costs the smaller model 3–11 points there". This is eight numbers across three sentences with the same
  shape. Fix: move the handles and pipe range to the Fig. 4 caption, or drop "and the pipe at most 4" if the section's
  claim (files need a tool-capable model) does not need it. Replace "there" with "at three and five questions" or cut it.
- Smaller model: "We suspect, but have not tested, that the cause is reading its instruction last, after thousands of
  tokens of documents." Fix: "A likely cause, untested, is that the instruction comes last, after thousands of tokens of
  documents." This keeps the hedge in a different shape from the others.
- Tool budget: "At k=16 it binds harder (B's Reviewer hits it in 52% of runs), so B's collapse there is a result for
  this budget." It is unclear whether "it" means the 12-call or the 24-call budget. Fix: "At k=16 the 12-call budget
  binds harder (B's Reviewer hits it in 52% of runs), so B's collapse there holds for this budget only."
- Run-to-run noise: "within 2 points at 95%". Use the single interval convention.

### 6 Related Work

- "and MAST catalogs inter-agent failures such as ignored input [3], which our stage attribution measures." The
  relative clause attaches ambiguously. Fix: "MAST catalogs inter-agent failures [3]; our stage attribution measures one
  of them, ignored input."
- "Zero-copy broadcast is the simplest member of this family: it needs no engine change, only a prompt order that makes
  the shared prefix exact, and we use it to measure ..." This is a colon reveal, a grand "member of this family", and the
  third "no engine change". Fix: "Zero-copy broadcast is the simplest such reuse, and we use it to measure what the
  channel costs once reuse is in place."
- "The agent versions map directly: the prefix cache plays zero-copy, and the index plays the directory." The colon and
  the symmetric pair make it read as a slogan. Fix: "In agents, the prefix cache plays the role of zero-copy and the
  index that of the directory."

### 7 Conclusion

- "Which channel a pipeline of LLM agents should use depends on what it pays for, how large its payloads are next to
  the KV cache, and how well its model uses tools." The triplet is earned (three real factors), but it echoes the intro's
  "depend on the cache and the model as well as on the channel". Fine to keep; trim the intro sentence instead if space
  is needed.
- "Finally, a deployment should count the cost it actually pays" — "actually" is filler. Fix: "Finally, a deployment
  should count the cost it pays".
- "Plain files cost more tokens and lost accuracy in every setting." The tense mixes; use "lost ... and cost".
- "where files should be indispensable" is speculation stated as an expectation. Fix: "where files may be the only
  option".
- Collect the moved "why" caveats here in one sentence. It replaces three separate "We have not tested ..." sentences, so
  the net effect is shorter: "We have not tested why a tool call shortens notes, why a Fact-checker helps the pipe, or why
  the 4B model loses with zero-copy order." This is a triplet, but it lists three real items.

### Figures (captions)

- Fig. 2: "Counted by tokens sent (a), copying the history is the accurate choice ...; counted by tokens computed (b),
  zero-copy broadcast keeps that accuracy at a pipe's cost." This is a dangling modifier ("copying" is not counted) plus a
  semicolon chain. Fix: "By tokens sent (a), copying is accurate and files are expensive. By tokens computed (b),
  zero-copy broadcast keeps that accuracy at a pipe's cost."
- Fig. 4 panel titles: "(b) Accuracy: plain files collapse at large k; the pipe recovers" is a colon plus a semicolon,
  but panel titles are a reasonable place for a claim. Low priority.

## Things that already work (do not change)

- The intro move "Prior work ... keeps the channel fixed, so it cannot tell whether copying or sharing is the cheaper
  way" dismisses the alternative with a specific reason.
- "Our key observation is that cost has to be counted two ways, because ..." followed by "Specifically, ..." is the
  target voice.
- The Methodology is concrete and plain. The validation paragraph states its own weakness ("treat fact-level numbers as
  approximate") once.
- Short sentences land points in several places ("C behaves like B.", "The index names the notes.", "Its losses come at
  the end."). Keep them; they are the main source of rhythm variation.
- There are no rhetorical questions in the body and none of the banned words.

## Net length

Most fixes above cut words: removing closers and echoes, the "Unlike ..." sentence, the "(Bd)" and "(A2d)" labels,
"95% interval" repeated six times, and three "have not tested" sentences, offset by one consolidated sentence in the
Conclusion. Applying the bulk of them should free roughly 6–10 lines, which is enough headroom on page 6.
