# Style and grammar review, round 10

Paper: `paper/main.tex` (line numbers are source lines), checked against `main.pdf` via `pdftotext`.
Guide: `cs632-store/style_guide.md`, with most weight on "Clarity and grammar". Items already raised in
round 9 and declined in the round 10 revision log are not repeated unless the new text reintroduces them.

## Assessment

The round 10 text is cleaner than round 9: the banned words are gone, the 2x2 now lives in Table 1 instead of
a 25-number ledger, and most terms are defined before their numbers. What still reads as machine-edited is
structural. The Runs paragraph is a run of five rhetorical question-answer pairs, which the guide forbids
and no human systems paper does five times in a row. Results paragraphs end with a lead-in to the next
question ("The next question is whether it reaches serving time.", "We turn to accuracy.", "The next
questions are where ... this accuracy goes and why."), and both section openers announce their questions as
a list. The tag "a cross-run comparison" appears four more times after its definition, "unless stated
otherwise" three times, and most Results and Sensitivity paragraphs still follow one shape (claim heading,
setup, number with interval, second number with interval, caveat). The clarity problems are fewer but some
are serious. The Figure 3 caption says copied notes "keep accuracy high however they were written", which the
text and Table 1 contradict at 4B, 8B, and 32B. "The interaction, above zero at all sizes but 8B" is wrong
for the point estimate (8B is +2.2; only its interval includes zero). The abstract's "three of four model
sizes" is the uncorrected count, while the text stresses that only 4B survives Holm. "Run" means both an
experiment and one agent's execution ("34--59% of the runs of B's Writer", "6 concurrent runs", "200 B runs"),
"broadcast's tokens" means tokens sent in one place and tokens generated in another, and "arm", "an earlier
run", and "the crossed runs" are never introduced. Several sentences are garden paths ("B's state 32%",
"B's Writer reads go", "KV cache interleaved channels share", "which supporting sentences a text states with
AlignScore"). One interval breaks the sign convention ("trails broadcast by 3.0 points (-5.3 to -0.7)"), and
point precision varies inside one sentence ("7 points (3 to 11)" next to "5.8 points (2.5 to 9.5)"). The
fixes below keep or cut length overall. Deleting the three lead-in sentences (R6, R11, R16), the Results
"Each run-in heading answers one." (R1), the serving-time range (R9), the Holm gapping clause (R22), and the
conclusion restatement (K4) frees about 60 words, which pays for the additions in the abstract and Methods
(A1-A4, M6, M13, M16). Apply cuts and additions in the same pass, then check that body text still ends on
page 6.

**Machine-likeness score: 4/10.** The sentence-level voice is human. The rhetorical Q&A block, the closing
lead-ins, the repeated tags, and the uniform paragraph shape are what a careful reader would still notice.

Types: **bare-ref** = cited system or prior result used without saying what it does; **comma** = comma,
punctuation, or typesetting; **term** = unclear antecedent, or term used before definition or in two senses;
**anthro** = anthropomorphic or figurative metric verb; **grammar** = articles, agreement, parallelism,
tense, hyphenation, dangling modifier, number without unit or baseline, wrong qualifier; **AI-tell** = stacked
parentheses, colon reveals, "X, not Y", ledgers, uniform paragraph shape, repeated tags, findings without a
reason; **2nd-read** = sentence that needs a second read.

## Title

| # | line | original | type | corrected |
|---|---|---|---|---|
| T1 | 18, 54 | "Revisiting IPC ..." (IPC is never expanded; the body uses it only as the Related Work heading) | term | Optional: L54 "Operating systems face an analogous choice in inter-process communication (IPC)." (+4 words). The title itself is fine. |

## Abstract

| # | line | original | type | corrected |
|---|---|---|---|---|
| A1 | 26-27 | "We vary only this channel in a Researcher--Writer--Reviewer pipeline of Qwen3 models on vLLM, on multi-hop QA tasks whose state fits in the context." | term | "Channel" is never defined in the abstract, and "on vLLM, on multi-hop" stacks two "on"s. Write "We vary only this choice, the channel, in a Researcher--Writer--Reviewer pipeline of Qwen3 models served by vLLM, using multi-hop QA tasks whose state fits in the context." |
| A2 | 28-31 | "... computes \nZcRatioMin--\nZcRatioMax\% of broadcast's prefill at up to five questions per task, with a paired accuracy difference of \nZcPooledDiffLo to \nZcPooledDiffHi points at three, but saves no serving time." | 2nd-read | A range reads as the difference itself, "at three" is elliptical, and the serving-time clause comes after the accuracy aside. Write "... computes 38--49% of broadcast's prefill at up to five questions per task but saves no serving time. At three questions, the 95% interval of its accuracy difference from broadcast is -2.9 to 1.4 points." |
| A3 | 32-34 | "A tool-call write of the notes costs accuracy at \nRTenWriteCopySigWord of \nRFourSizesWord model sizes when the notes are copied forward, but a plain reply stored as a file does no better than tool-written files." | term | "The notes" are never introduced, and "three of four" is the uncorrected count while §4 says only 4B survives Holm. Write "Writing the Researcher's notes through a tool call lowers accuracy at three of four model sizes before correction when the notes are copied forward, but a plain reply stored as a file does no better than tool-written files." |
| A4 | 34-35 | "Three parallel Researchers sharing one folder cost files \nREightFanBAbs accuracy points at eight questions, and a folder each recovers \nREightFoldersOverB." | grammar | No baseline (against one Researcher), "cost files" is clipped, and "a folder each" is an odd subject. Write "At eight questions, three parallel Researchers sharing one folder cost shared files 21.2 accuracy points against one Researcher, and giving each its own folder recovers 19.8." |

## 1 Introduction

| # | line | original | type | corrected |
|---|---|---|---|---|
| I1 | 49-50 | "cuts tokens by pruning who talks to whom or by compressing what they say" | term | "They" has no antecedent in the sentence. Write "... or by compressing what agents say". |
| I2 | 50-51 | "Most of it keeps the channel fixed, and the one study that varies it compares ..." | term | Two "it"s with different antecedents (prior work, the channel). Write "Most of this work keeps the channel fixed, and the one study that varies the channel compares ...". |
| I3 | 55-56 | "and Lauer and Needham argued that the two are duals and that neither wins everywhere" | bare-ref | Lauer and Needham's duality is between message-oriented and procedure-oriented systems, not message passing and shared memory as stated. Write "and Lauer and Needham argued that message-oriented and procedure-oriented systems are duals and that neither wins everywhere" (+3 words), or keep "the two" and add "(roughly)". |
| I4 | 57-60 | "The engine must \emph{prefill} every prompt token ... The serving engine changes both costs, because its prefix cache reuses ..." | term | "The engine" appears two sentences before "the serving engine" introduces it. Write "The serving engine must \emph{prefill} every prompt token ..." and "Its prefix cache changes both costs, because it reuses the KV of a repeated prefix." |
| I5 | 63-65 | "and add controls for what changes with it, such as replaying the same notes into every channel" | term | "It" is unclear and "notes" is defined only in §2. Write "and add controls for side effects of that change, such as replaying one agent's notes unchanged into every channel". |
| I6 | 66-68 | "shared files send \nSentRatioB$\times$ the tokens that copying does ... Copying with the shared history first (zero-copy broadcast) cuts prefill ..." | term | The intro never names broadcast, yet names zero-copy *broadcast* and later uses "broadcast" as the baseline. Write "shared files send 2.9x the tokens that copying the whole conversation (broadcast) does". |
| I7 | 70 | "Through files, a reply stored as a file does as well as tool-written notes or worse." | 2nd-read | "Through files ... as a file" repeats, and "as well as ... or worse" makes the reader stop. Write "When notes reach the Writer through files, a plain reply stored as a file does no better than tool-written notes." |
| I8 | 71-72 | "causes most of the extra loss of files without an index, and that a folder per writer recovers \nREightFoldersOverB of those points at eight questions" | term | "Files without an index" (B) is undefined here, "extra" has no baseline, and "19.8 of those points" does not say of how many. Write "Our third is that at eight questions, parallel writers sharing one folder cost shared files 21.2 accuracy points, and a folder per writer recovers 19.8 of them." (about 3 words shorter) |
| I9 | 73-74 | "and vary payload, parallel writers, cache size, and tool budget" | grammar | Parallelism: one cannot vary "parallel writers". Write "and vary payload size, the number of parallel writers, cache size, and tool budget". |

## 2 Channels

| # | line | original | type | corrected |
|---|---|---|---|---|
| F1 | 82-83 | Fig. 1: "copy content into the next prompt, drawn as bars" | grammar | Dangling modifier: "drawn as bars" attaches to "prompt". Write "copy content (bars) into the next prompt". |
| C1 | 89-90 | "writes down the facts each question needs, its \emph{notes}" | term | "Its" reads as the question's. Write "The \emph{Researcher} reads the task's documents and writes \emph{notes} that state the facts each question needs." |
| C2 | 92-94 | "Its instructions differ across channels in wording and in where the notes go, a reply or files written with a \texttt{write\_file} tool." | term | "Its" follows "user message", and the trailing appositive needs a second read. Write "The Researcher's instructions differ across channels in wording and in where the notes go (a reply, or files written with a \texttt{write\_file} tool)." |
| C3 | 99-100 | "ends with the role's instruction, moved out of the system prompt" | term | The reader has not been told that A1 puts the instruction in the system prompt (that appears only at L198). Write "ends with the role's instruction, which A1 puts first in the system prompt". |
| C4 | 102-103 | "lengthens the Researcher's notes at three questions per task, from \nNotesCharsAOne to \nNotesCharsAZc characters" | grammar | Says neither that these are means nor that the cause is unknown. Write "... from 1,570 to 1,992 characters on average". |
| C5 | 108 | "The Writer and Reviewer receive only the questions." | grammar | L94 and L105 use "the Writer and the Reviewer". Write "The Writer and the Reviewer ...". |
| C6 | 112-113 | "an \texttt{index.md} file that the workspace keeps current with each file's author, size, and first line" | 2nd-read | "Keeps current with" reads as "keeps up to date with". Write "C adds to B an \texttt{index.md} file listing each file's author, size, and first line, which the workspace updates as a file system updates a directory." |

## 3 Methodology

| # | line | original | type | corrected |
|---|---|---|---|---|
| F2 | 124-125 | Fig. 2: "In (a), broadcast is the most accurate channel and the file channels are the most expensive." | comma | Two independent clauses with different subjects. Write "... the most accurate channel, and the file channels ...". |
| M1 | 130 | "2WikiMultihopQA~\cite{2wiki} (2Wiki)" | comma | Renders "[8] (2Wiki)", a bracket followed by a parenthesis. Write "2WikiMultihopQA (2Wiki)~\cite{2wiki}". |
| M2 | 131-132 | "Each question comes with ten paragraphs, most of them distractors, and the sentences that support its answer." | 2nd-read | Reads as extra text that comes with the question; these are labels on sentences inside the paragraphs. Write "Each question comes with ten paragraphs, most of them distractors, with the sentences that support its answer marked." |
| M3 | 138 | "with thinking disabled and greedy decoding" | grammar | Non-parallel pair (absolute phrase plus noun). Write "with greedy decoding and thinking disabled". |
| M4 | 139, 153, 208, 321 | "runs \nConc tasks at a time", "at \nConc and \nConcHi tasks", "run \nConc at a time", "the KV of \nConc concurrent runs" | grammar | Render as "6" while the paper spells out other small counts ("ten paragraphs", "three questions"). Add a word macro (`\nConcWord` = six) and use it in running text; keep "32" as a numeral. |
| M5 | 145 | "The same servers ran its controls" | grammar | Tense: the paragraph describes runs in the present ("serves", "answers"). Write "The same servers run its controls". |
| M6 | 145-147 | "ran its controls on \nRepN three-question tasks (documents for file agents, replayed notes, a rerun) and the larger payloads of Figure~\ref{fig:scaling}" | 2nd-read | The telegraphic list cannot be decoded here, and "ran ... the larger payloads" is a zeugma. Write "run three controls on 200 three-question tasks (file agents given the documents, replayed notes, and a rerun) and the larger-payload runs of Figure 4". |
| M7 | 147-148 | "Each later run answers a question the main run leaves open, on one RTX PRO 6000 per server with a \nKvPro-token cache unless stated otherwise." | 2nd-read | The hardware is tacked onto an unrelated clause. Write "Later runs use one RTX PRO 6000 per server with a 100k-token cache unless stated otherwise, and each answers a question the main run leaves open." |
| M8 | 148-153 | "Does the cache or the payload limit prefill savings? We sweep ... Do the results hold across model size? We run ... Where do files lose accuracy? ... Do parallel writers cause the loss at large payloads? ... Does less prefill mean less serving time? We serve ..." | AI-tell | Five rhetorical question-answer pairs in a row; the guide bans rhetorical questions. Same length, declarative: "We sweep 35k-, 100k-, and 400k-token caches to see whether the cache or the payload limits prefill savings, and run Qwen3-4B, 8B, 14B, and 32B to test model size. A run per size crosses how notes are written with how they reach the Writer, to find where files lose accuracy. Varying the number of Researchers tests whether parallel writers cause the file channels' loss at large payloads, and serving each channel alone with Qwen3-8B, at six and 32 tasks at a time, tests whether less prefill means less serving time." |
| M9 | 160-161 | "We judge which supporting sentences a text states with AlignScore~\cite{alignscore}, a factual-consistency model, at its 0.5 threshold." | 2nd-read | Garden path: "a text states with AlignScore". Write "We use AlignScore~\cite{alignscore}, a factual-consistency model, at its 0.5 threshold to judge which supporting sentences a text states." |
| M10 | 162-163 | "on real notes it agrees only weakly with a Qwen3-8B judge" | anthro | Low priority, since "agreement" is the kappa term of art. If changed: "on real notes its labels match a Qwen3-8B judge's only weakly". |
| M11 | 166 | "(\nCapSplit in the crossed runs)" | term | Three names for one experiment: "the crossed runs" (L166), "one interleaved run per model size" (L266), "Figure~\ref{fig:split}'s runs" (Table 1). Name it once in M8 ("the crossed runs") and use that name in the Table 1 caption and L266. |
| M12 | 168-169 | "this rescue is used in \nForcedMin--\nForcedMax\% of the runs of B's Writer and of B's and C's Reviewers" | term | "Run" means an experiment everywhere else. Write "in 34--59% of tasks for B's Writer and for B's and C's Reviewers". |
| M13 | 169 | "Scoring every rescued run as wrong leaves B at \nStrictB\% and C at \nStrictC\%." | grammar | No metric and no baseline: 18.0% of what, against what? Write "Scoring every rescued task as wrong cuts B's accuracy from \nAccB\% to 18.0% and C's from \nAccC\% to 22.9%." (both macros exist) |
| M14 | 169-171 | "we report paired differences against A1 with 95\% bootstrap intervals over tasks in parentheses, and do not correct" | comma | Reads as "tasks in parentheses". Set off the phrase: "we report paired differences against A1, with 95% bootstrap intervals over tasks in parentheses, and do not correct ...". |
| M15 | 171 | "The question sets for $k=1$, 3, and 5 overlap." | AI-tell | A fact with no consequence. Write "The question sets for $k=1$, 3, and 5 overlap, so settings are not independent." |
| M16 | 171-172 | "Each task runs once per channel, and we call comparisons across runs cross-run." | term | Circular, and it does not say why the label matters. Write "Each task runs once per channel. We mark comparisons between separate runs as cross-run, since they may include run-to-run drift." This lets G1 drop the later tags. |
| M17 | 268, 353 | "in an earlier run", "Against an earlier run on these tasks" | term | The Runs paragraph introduces every run except these two. Either add "Two earlier runs give a wording control and a tool-budget control." to Runs (+11 words), or name them in place (see R18, S7). |

## 4 Results

| # | line | original | type | corrected |
|---|---|---|---|---|
| R1 | 177-179 | "This section uses Qwen3-8B ... unless stated otherwise. It asks what each channel costs, which is most accurate, where files lose accuracy, and why file readers miss the notes. Each run-in heading answers one." | AI-tell | A roadmap list that mirrors the Sensitivity opener, a third "unless stated otherwise", an undefined "file readers", and a headings meta-sentence. Write "This section uses Qwen3-8B at $k=3$ with datasets pooled, except where noted. It covers what each channel costs, which is most accurate, where files lose accuracy, and why the file channels' Writer misses the notes." Drop the last sentence. |
| R2 | 194-197 | "B and C send \nSentRatioB$\times$ and \nSentRatioC$\times$ broadcast's tokens, and \nFileSentMin--\nFileSentMax$\times$ across settings, because they make \nCallsB and \nCallsC model calls per task to broadcast's one per agent, and each call resends the conversation." | AI-tell | A six-number ledger, with the baseline in another unit (per agent against per task). Write "In Figure 2a, B and C send 2.9x and 2.8x broadcast's tokens (1.8--4.8x across settings). They make 17.0 and 15.9 model calls per task against broadcast's three, and each call resends the conversation." |
| R3 | 198-199 | "Broadcast puts each role's instruction first, so the cache reuses almost none of its prompt." | 2nd-read | The step between cause and effect is missing (different instructions mean the prompts differ from the first token). Write "Broadcast starts each prompt with a different role instruction, so consecutive prompts share almost no prefix." |
| R4 | 202 | Heading: "Zero-copy computes a pipe's prefill ..." | grammar | Article: the pipe is a specific channel. Write "... computes the pipe's prefill ...". |
| R5 | 202-203 | "It computes \nCompAZc tokens per task ..." | term | The paragraph opens with "It", whose antecedent is only in the heading. Write "Zero-copy computes 4.8k tokens per task ...". |
| R6 | 205 | "The next question is whether it reaches serving time." | AI-tell | A lead-in closer; "it reaches serving time" is figurative, and "it" is unclear (the gain?). Delete it (-9 words); the next heading asks the question. |
| R7 | 207-209 | "We served each channel alone with Qwen3-8B on one RTX PRO 6000, three times, on \nRSixAloneN three-question tasks run \nConc at a time." | 2nd-read | "Three times" sits between two "on" phrases. Write "We served each channel alone three times with Qwen3-8B on one RTX PRO 6000, on 100 three-question tasks run six at a time." |
| R8 | 210-211 | "Zero-copy's agents generate \nRSixGenAZc$\times$ broadcast's tokens" | term | Everywhere else, "broadcast's tokens" means tokens *sent* (13.6k). Write "Zero-copy's agents generate 1.2x as many output tokens as broadcast's". |
| R9 | 211-212 | "(\nRSixTimeAZcMin--\nRSixTimeAZcMax$\times$ over the runs)" | AI-tell | The ninth number in one paragraph, and the claim does not need it. Delete it (-5 words), or move it to the Runs paragraph. |
| R10 | 212-214 | "In two runs at \nConcHi tasks at a time with a \nKvProHi-token cache, its median task takes ..." | 2nd-read | "At ... at" stacks, and "its" points two sentences back. Write "In two runs with 32 tasks at a time and a 400k-token cache, zero-copy's median task takes 0.82x broadcast's time, but its batch takes 1.00x as long." |
| R11 | 215-216 | "Cost thus favors zero-copy mainly where prefill is paid for. We turn to accuracy." | anthro | "Cost favors" gives the metric agency, and "We turn to accuracy." is another lead-in closer. Write "Zero-copy thus saves cost mainly where prefill is billed." and drop the second sentence (-4 words). |
| R12 | 221 | "Its estimate stays within \nGapAZcMax points of broadcast's in every setting" | term | "Its estimate" makes the reader look back for the noun. Write "Zero-copy's accuracy stays within 3 points of broadcast's in every setting". |
| R13 | 226 | "The pipe sends the fewest tokens (\nSentATwo)" | grammar | The number has no unit. Write "(5.6k per task)". |
| R14 | 228-229 | "against at most \nPipeBrokeAOne\% in broadcast, where it also sees the notes and documents" | term | "It" grammatically points to the pipe's Reviewer ("Its Reviewer"), but means broadcast's. Write "where the Reviewer also sees the notes and documents". |
| R15 | 230-232 | "Against the main run, a cross-run comparison, it gains \nScopeATwoDVsATwoAbs points over the pipe (...) but still trails broadcast by \nScopeATwoDVsAOneAbs points (\nScopeATwoDVsAOneLo to \nScopeATwoDVsAOneHi)." | grammar | "A cross-run comparison" is an appositive to "the main run", which is not a comparison (dangling). "Trails by 3.0 (-5.3 to -0.7)" also breaks the sign convention every other "trails by" follows (L347: "trails ... by 30.4 points (25.7 to 35.1)"). Write "Compared across runs, it gains 6.8 points over the main run's pipe (3.5 to 10.2) but still differs from broadcast by \nScopeATwoDVsAOne points (-5.3 to -0.7)." |
| R16 | 236-237 | "The next questions are where in the file channel this accuracy goes and why." | AI-tell | A lead-in closer that repeats R1's list; "where accuracy goes" is figurative; and "the file channel" is singular. Delete it (-14 words). |
| TB1 | 240-241 | Table 1: "Each effect is the second arm minus the first." | term | "Arm" is never defined, and "second" and "first" do not map to the arrow labels. Write "Each effect is the arm right of the arrow minus the arm left of it." Define the four arms once in the Fig. 3 caption ("four arms: reply or tool write, copied or through files"). |
| TB2 | 241-242 | "Interaction: row two minus row one. \dag: significant after Holm correction of \nRTenHolmTests paired permutation tests." | term | The 16 tests are the simple effects, so the Interaction row can never carry a dagger, and readers may read its absence as non-significance. Write "Interaction (not tested): row two minus row one." |
| F3 | 187 | Fig. 3: "(a) Supporting facts in the notes (AlignScore)." | grammar | The y-axis is a share. Write "(a) Share of supporting facts the notes state (AlignScore)." |
| F3b | 188-189 | "Copied notes keep accuracy high however they were written, but through files the stored reply does no better than tool-written files." | 2nd-read | Contradicts the text and Table 1: with copied notes, the tool write lowers accuracy at 4B, 8B, and 32B. Write "Copied notes beat files however they were written, but through files the stored reply does no better than tool-written files." |
| F3c | 186-187 | "where the system saves a reply as \texttt{notes.md}" | term | "The system" is vague (harness, workspace, or vLLM?). Write "where the harness saves a reply as \texttt{notes.md}". |
| R17 | 266 | "Splitting these step by step gives shares that depend on the order, so we cross them" | 2nd-read | "Shares" of what? Write "Changing them one at a time would split the loss in an order-dependent way, so we cross the two in one interleaved run per model size (the crossed runs, Figure 3)." |
| R18 | 267-269 | "All arms use B's Researcher wording, which in an earlier run was within $\pm$\nRSixWordingNullBound points of broadcast's at 8B to 32B and \nRSixFourWording points (...) above it at 4B." | 2nd-read | "Arms" and "an earlier run" are undefined, and "within 3.1 points of broadcast's" leaves the noun out (broadcast's *what*?). Write "All four arms give the Researcher B's instructions. In an earlier run, swapping in broadcast's instructions changed accuracy by at most 3.1 points at 8B to 32B but cost 6.2 points (2.9 to 9.6) at 4B." |
| R19 | 269-272 | "With copied notes, the tool-call write lowers accuracy at 4B, 8B, and 32B (Table~\ref{tab:cross}), where its notes state fewer supporting facts (Figure~\ref{fig:split}a), \nRTenEightNotesToolCopy\% against \nRTenEightNotesReplyCopy\% at 8B." | 2nd-read | The trailing number appositive follows two parentheticals. The Holm caveat on this very effect sits in the next paragraph (L281-282). Write "With copied notes, the tool-call write lowers accuracy at 4B, 8B, and 32B (Table 1), though only 4B survives Holm correction. At these sizes, its notes state fewer supporting facts (Figure 3a): 32% against 43% at 8B." Then delete the write clause in R22. |
| R20 | 272 | "At 14B, the notes keep their facts and accuracy does not change." | comma | Two independent clauses with different subjects. Write "At 14B, the notes keep their facts, and accuracy does not change." |
| R21 | 275-276 | "The interaction, above zero at all sizes but 8B, makes a stepwise split order-dependent." | grammar | Wrong qualifier: at 8B the interaction is +2.2, also above zero; only its interval (-2.2 to 6.7) includes zero. The sentence also restates L266. Delete it (-13 words), or write "The interaction's interval excludes zero at every size but 8B." |
| R22 | 280-282 | "these delivery effects stay significant at \nRTenHolmFileReplySigWord sizes for replies and \nRTenHolmFileToolSigWord for tool-written notes, but the write effect on copied notes only at 4B" | 2nd-read | The gapped clause "but the write effect on copied notes only at 4B" belongs to the previous paragraph's topic. Write "After Holm correction, both delivery effects stay significant at three sizes each." (-13 words; the write clause moves to R19). |
| R23 | 282-284 | "The Writer's reads differ most at 32B, where it opened the stored \texttt{notes.md} in \nRTenThirtyTwoOpenReplyFile\% of tasks, against \nRTenThirtyTwoOpenToolFile\% for the Researcher's own named files." | grammar | Tense switches from "differ" to "opened", "it" points to a possessive, and "own named files" is awkward. Write "The Writer's reads differ most at 32B, where the Writer opens the stored \texttt{notes.md} in 24% of tasks but files the Researcher named itself in 95%." |
| R24 | 284-286 | "At 4B and 14B, it seldom opens notes in either file arm (...)." | AI-tell | The paragraph ends on rates with no reason and no link to its heading. At 14B both arms rarely open notes, yet the stored reply is 21.3 points worse, so the open rates explain 32B only. Replace "it" with "the Writer" and add one clause saying what the rates do and do not explain, or cut the sentence. |
| F4 | 291-292 | Fig. 4: "on the RTX 3090 servers, whose \nBigKv-token KV cache interleaved channels share (datasets pooled)" | 2nd-read | Garden path: "KV cache interleaved channels" parses as one noun. Write "on the RTX 3090 servers, where interleaved channels share a 34,864-token KV cache (datasets pooled)". |
| R25 | 298-299 | "and B's state \nNotesB\% of the supporting facts" | 2nd-read | Garden path: "B's state" reads as a noun phrase. Write "and B's notes state 32% of the supporting facts". |
| R26 | 299-300 | "so \nDocReadsB\% of B's Writer reads go to source documents" | 2nd-read | Garden path: "B's Writer reads" reads as subject plus verb. Write "so 83% of the reads by B's Writer go to source documents". |
| R27 | 304-306 | "B's accuracy changes by \nScopeBDVsB points (...) against the main run's B, a cross-run comparison." | AI-tell | A repeated tag and a dangling appositive (as in R15). With M16 in place, write "... against the main run's B, across runs." or "(cross-run)". |
| R28 | 306-309 | "When broadcast's notes are replayed unchanged into every channel ..., both are \nRepBGap points less accurate than broadcast (...), as large a loss as the stored reply's at 8B (a cross-run comparison), and the pipe is \nRepATwoGap points less." | 2nd-read | Five numbers, a parenthetical tag, and an elliptical "both" in one sentence. Split: "When broadcast's notes are replayed unchanged into every channel on 200 tasks, as one file \texttt{notes.md} in B and C, B and C are both 5 points less accurate than broadcast (2 to 8), and the pipe 8 points. Across runs, the file channels' loss matches the stored reply's at 8B." |
| R29 | 310 | "C's Writer, whose index also lists the documents, opens the notes less often" | term | "Whose" makes the index the Writer's. Write "C's Writer, which also sees the documents listed in the index, opens the notes less often". |

## 5 Sensitivity

| # | line | original | type | corrected |
|---|---|---|---|---|
| S1 | 316-318 | "This section asks when its picture changes: as payloads outgrow the KV cache, when Researchers write in parallel, and with model size." | AI-tell | A colon reveal, a non-parallel list ("as ...", "when ...", "with ..."), a figurative "its picture", and the same shape as the Results opener. Write "This section varies payload size against the KV cache, the number of parallel Researchers, and model size." (-6 words) |
| S2 | 321 | "the KV of \nConc concurrent runs no longer fits" | term | These are concurrent tasks, not runs. Write "the KV of six concurrent tasks no longer fits". |
| S3 | 326-327 | "while accuracy changes by at most \nPKvAccShiftMax points" | term | Whose accuracy, and between what? The macro is the largest range of any channel across the three caches. Write "while no channel's accuracy moves by more than 1.6 points across the three caches". |
| S4 | 328-329 | "the pipe stays within \nGapATwoKSixteen point of broadcast's accuracy at \nCompATwoKSixteen$\times$ its prefill" | term | "Its" can be read as the pipe's own prefill. Write "the pipe stays within 1 point of broadcast's accuracy while computing 0.37x as much prefill". |
| S5 | 341-342 | "at least two Researchers wrote the same path" | grammar | Write "wrote to the same path". |
| S6 | 345 | Heading: "At sixteen questions, a write guard recovers about half of B's loss." | 2nd-read | The paragraph's other repair, the heading rule, recovers more (18.1 against 15.1), so the heading names the weaker result. Write "At sixteen questions, a write guard or the heading rule recovers half or more of B's loss." |
| S7 | 352-354 | "Against an earlier run on these tasks, where B trails broadcast by \nRFourKSixteenGapB points, \nTurnsHi tool calls instead of \nTurns change B's accuracy by \nRFourBTwentyFour points (...), a cross-run comparison." | 2nd-read | The baseline comes first, "24 tool calls ... change" makes the calls the agent, and the tag repeats. Write "Raising the budget from 12 to 24 tool calls changes B's accuracy by 3.3 points (-0.5 to 7.4) against an earlier run on these tasks, where B trails broadcast by 33.9 points." |
| S8 | 358-360 | "For Qwen3-32B these ranges count a rerun ... since the first harness missed its output in \nPRescueThirtyTwoBMoved of the \nPSizeThirtyTwoN B runs." | comma | The introductory phrase needs a comma, "its output" is unclear (the harness's?), and "B runs" means tasks. Write "For Qwen3-32B, these ranges use a rerun that treats a leading \texttt{workspace/} as the root, since the first harness missed the agents' output files in 51 of the 200 B tasks." |
| S9 | 361-362 | "The pipe loses only with Qwen3-8B (\nPSizeEightGapATwo points, \nPSizeEightGapATwoLo to \nPSizeEightGapATwoHi)." | comma | The only place where the point estimate and interval share one parenthesis. Write "The pipe loses only with Qwen3-8B, by 10 points (7 to 13)." |
| S10 | 362-365 | "lowers accuracy only at 4B, by \nPSizeFourGapAZc points (3 to 11), and still loses \nRFourZcReplayFour points (2.5 to 9.5) there ..." | grammar | The same quantity is given at two precisions in one sentence, and "ordering ... loses" gives the ordering agency. Split, and render both at one decimal: "Zero-copy ordering significantly lowers accuracy only at 4B, by 7.x points (3.x to 11.x). It still costs 5.8 points (2.5 to 9.5) there when broadcast's notes are replayed into both channels, so its longer notes are not the main cause." |
| S11 | 360-361 | "At 14B, C trails broadcast by more than B does (\nPSizeFourteenGapC against \nPSizeFourteenGapB points)." | AI-tell | A finding with no reason. Add the reason if known (e.g., C's Writer opening the index instead of notes), or cut it. |
| S12 | 368-369 | "A Researcher given the same prompt in two channels writes identical notes in \nSamePrompt\% of tasks." | term | The macro compares A1 with A2, but the text never says which two channels share a Researcher prompt. Write "The Researchers of broadcast and the pipe, whose prompts are identical, write identical notes in 59% of tasks." |
| S13 | 370 | "a B--A1 gap of \nAAGapRepeat points" | comma | The en dash reads as a range "B to A1". Write "a gap between B and A1 of 7.0 points", or "B$-$A1". |

## 6 Related Work

| # | line | original | type | corrected |
|---|---|---|---|---|
| W1 | 377-378 | "PACT compares which content a message should carry~\cite{pact}. They keep the channel fixed, and we change it." | term | "They" follows PACT alone but means all five systems, and the symmetric "they ..., and we ..." reads as a flourish. Write "All of these keep the channel fixed; we vary it." |
| W2 | 382-386 | Four sentences in one shape: "X does A [..], and Y does B [..]." ending with "InferCept keeps a request's KV while it waits on a tool call, and CacheBlend reuses KV of non-prefix text." | AI-tell | A uniform list with no tie to this paper. Tie at least the last pair to the file channels: "InferCept keeps a request's KV while it waits on a tool call, which the file channels' many calls would need, and CacheBlend reuses KV of non-prefix text." (+7 words; fund from R21) |

## 7 Conclusion

| # | line | original | type | corrected |
|---|---|---|---|---|
| K1 | 398 | "such as code bases" | grammar | Write "such as codebases". |
| K2 | 400-401 | "with a paired accuracy difference of \nZcPooledDiffLo to \nZcPooledDiffHi points" | 2nd-read | The same interval-as-difference problem as A2. Write "with a 95% interval for its accuracy difference of -2.9 to 1.4 points". |
| K3 | 399-409 | "computed", "was the cheapest", "lost accuracy", "lowered", "did not help", "did as well", "recovered" | grammar | The body uses the present for what the data show; the conclusion switches to the past. Use the present for findings ("computes", "is", "loses", "lowers", "does", "recovers") and keep the past only for what was or was not tested ("we did not test"). |
| K4 | 404-405 | "A tool-call write lowered accuracy when its notes were copied, and storing the reply as a file did not help. The stored reply did as well as tool-written files or worse, and much worse at 14B and 32B." | AI-tell | The second sentence restates the first, and "as well as ... or worse" repeats I7. Write "A tool-call write lowers accuracy when its notes are copied. Through files, the stored reply does no better than tool-written files, and much worse at 14B and 32B." (-8 words) |
| K5 | 406-407 | "which recovered \nREightFoldersOverB points of B's fan-out loss at eight questions" | grammar | The number lacks its baseline. Write "which recovers 19.8 of B's 21.2-point fan-out loss at eight questions" (\nREightFanBAbs). |
| K6 | 410 | "why a tool call drops facts" | anthro | Write "why writing through a tool call drops facts". |

## Whole paper

| # | line | original | type | corrected |
|---|---|---|---|---|
| G1 | 230, 306, 309, 354 | "a cross-run comparison" (after the definition at L172) | AI-tell | Repeated tag. Define once (M16), then use "across runs" or "(cross-run)" only where a reader could mistake the comparison for a paired one (R15, R27, R28, S7). |
| G2 | 148, 169, 177 | "unless stated otherwise" | AI-tell | Three uses in one page. Keep it in Runs and Statistics, and write "except where noted" in R1. |
| G3 | 193-372 | Results and Sensitivity paragraphs: claim heading, then setup, number (interval), number (interval), caveat | AI-tell | Uniform paragraph shape. Delete the lead-in closers (R6, R11, R16), let some paragraphs open with the reason (e.g., R3's mechanism before the 0.79x), and merge the two zero-copy cost paragraphs (L202-216) under one heading. |
| G4 | 231, 235, 308, 362-363 | "6.8 points (3.5 to 10.2)" next to "5 points (2 to 8)"; "6.0 points ... at most 8"; "7 points (3 to 11)" beside "5.8 points (2.5 to 9.5)" | grammar | Point differences use integers in some places and one decimal in others, sometimes within one sentence. Have the generator emit point differences and intervals at one decimal everywhere (same values, no change in meaning). |
