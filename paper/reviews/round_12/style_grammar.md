# Round 12 style and grammar review

Sources: `paper/main.tex` (line numbers below), `paper/numbers.tex`, `paper/main.pdf` (6 pages, built 2026-11-21 16:44).
Quotes show rendered numbers for readability; keep the macros when applying a fix. Fixes are written to be
length-neutral unless marked "+words"; section "Space" at the end lists cuts that pay for them.

## Assessment

The paper now reads mostly like a careful human systems paper: sentences are short, "we" acts, most results carry
a baseline and an interval, and the run-in headings state claims. What still marks it as machine-edited is
texture rather than vocabulary. The same connective ("X against Y", 21 times) and the same opener ("With
Qwen3-8B," five headings and sentences; "With tool-written notes," three times plus the table caption) recur
until they read as tags. Several paragraphs are number ledgers that report a ratio without its reason (the
serving-time paragraph, the rescued-task accuracies, the size paragraph). The abstract, introduction and
conclusion repeat one 25-word sentence almost verbatim. The remaining clarity problems are concentrated in a few
places: two terms carry two senses ("writer" vs the Writer role; "file channel" as B-and-C vs the crossed-run
factor level), several labels are used before they are defined (payload, token cap, the size runs, arms,
factors, final.md), three pronouns ("Its", "it", "which") point to the wrong noun, and the crossed-runs
subsection never says in words what its key test (the file channel's cost exceeding the tool-call write's cost)
means for the paper's second observation. Figure 2's and Figure 3's captions state claims that are not the
claims the text makes from them.

**Machine-likeness: 4/10** (1 = clearly human, 10 = clearly generated). Down from earlier rounds; the residue is
repeated tags, uniform paragraph shape in Results (bold claim, then three to six numbers with parenthesized
intervals, no closing reason), trailing appositives ("a confound of this arm"), and one "X, not Y" heading.

## Structure

- **Results as an argument.** The roadmap (L191) promises cost, accuracy, why files lose, and sizes, and the
  bold headings mostly deliver claims. Four gaps:
  1. The first paragraph's heading is about files, but half the paragraph is about zero-copy. The intro's first
     observation ("the channels rank differently by prefill than by tokens sent") is the claim this paragraph
     and Figure 2 prove; use it as the heading (item 54).
  2. The files paragraph (L240-252) does four jobs: the gap, what B's Writer reads, the harness limits, and the
     rescue. Readers lose the thread at "The harness also binds." Either break before that sentence or move the
     budget/cap/rescue counts to the Harness paragraph of Section 3, where they answer "does the harness decide
     the result?" (item 72).
  3. The crossed-runs block (L291-326) opens with a method sentence, not a question, and never states its
     answer. The question is "do files cost accuracy beyond how the notes are written?" (intro, observation 2).
     The evidence is the 4B/14B excess over the tool-call write's cost; the answer sentence is missing (item 82).
     The block also uses "the file channel's two changes" and "the two factors" before Section 3 defines them
     as factors (items 41, 78).
  4. The "stored reply" heading ("is an observation, not a channel cost") is unreadable in a skim; a skimmer
     cannot tell what was observed (item 85).
- **Sensitivity as an argument.** Headings are claims and each paragraph gives a reason, which is good. Two
  paragraphs carry a second job their heading does not name: the k=16 repair paragraph ends with the tool-budget
  result (item 103), and the model-size paragraph inserts a 32B bug-fix caveat and "C does not beat B at every
  size" mid-paragraph (items 107-108). The size runs (200 tasks per size) are never introduced in Runs (item 106).
- **Skim test (headings + first sentences + captions).** A reader who skims gets: files send the most tokens;
  zero-copy helps latency only at high concurrency; broadcast and zero-copy are most accurate; the pipe loses at
  the Reviewer; files trail and the Writer reads documents; files lose even with documents or notes; the file
  channel costs accuracy at three sizes; the stored reply's loss is "an observation"; the tool write costs
  accuracy "at some sizes"; prefill savings need the cache; shared folders cause most of the fan-out loss; repairs
  recover half; size changes which channels lose; noise is small. That is the story, except that (a) the
  cost-ranking flip (the paper's first observation) is not in any heading, (b) "With Qwen3-8B" in three headings
  makes the scope look like a hedge rather than the default (state it once in L191), and (c) the last two Results
  headings are vague.
- **Captions.** Figure 2's claim "Files are the most expensive" is true only for panel (a); in (b) broadcast
  computes the most (item 32). Figure 3's claim ("Copied replies are the most accurate arm") is not the claim the
  text draws from it, and panel (a) is not mentioned (item 52). Figure 4 has no claim in the caption, but its
  panel titles carry one; panel (a)'s "35k-token cache" collides with the separate 35k-token RTX PRO 6000 cache in
  Section 5 (item 95). Table 1's caption is fine apart from its last sentence (item 77).
- **Abstract and intro.** The abstract holds nine numbers and omits the cost-ranking flip; "Shared files send
  1.8-4.8x broadcast's tokens" stands alone as a bare number (item 4). Intro paragraph 3 holds seven numbers.
  The abstract's last sentence is repeated in the conclusion (items 7, 118).

## Problems by section

Types: **Struct** (structure), **Read2** (needs a second read), **Ante** (unclear antecedent), **Def** (term used
before definition or undefined), **Sense2** (term used in two senses), **Comma**, **Gram** (articles, agreement,
parallelism, tense, hyphenation, dangling modifier), **Num** (number lacks unit or baseline, sign convention),
**AI** (AI-writing tell), **Bare** (bare reference), **Anthro** (anthropomorphic metric verb), **Claim**
(caption or sentence states something the data do not say).

| # | Section | Line | Original | Type | Corrected |
| --- | --- | --- | --- | --- | --- |
| 1 | Abstract | 25-27 | "in a Researcher--Writer--Reviewer pipeline of Qwen3 models on vLLM, on multi-hop QA tasks whose state fits in the context." | Read2 | "in a Researcher--Writer--Reviewer pipeline that runs Qwen3 models on vLLM over multi-hop QA tasks whose state fits in the context window." |
| 2 | Abstract | 27-29 | "copying the whole conversation (broadcast) and zero-copy broadcast, which puts the shared history first so the prefix cache reuses it, are the most accurate channels." | Read2 | Put the verb near the subject: "With Qwen3-8B, the most accurate channels are copying the whole conversation (broadcast) and zero-copy broadcast, which puts the shared history first so that the prefix cache reuses it." |
| 3 | Abstract | 30 | "and at three its accuracy difference from broadcast" | Comma | "and, at three questions, its accuracy difference from broadcast" |
| 4 | Abstract | 31-32 | "Shared files send 1.8-4.8x broadcast's tokens." | Struct | Bare number that hides the paper's first observation. "Shared files send 1.8-4.8x broadcast's tokens, but the prefix cache absorbs most of the resending." (+8 words; pay with item 7) |
| 5 | Abstract | 32-35 | "Replacing copying with a file channel, where later agents use tool calls for inputs and outputs, costs 8-22 accuracy points on tool-written notes at three of four Qwen3 sizes after Holm correction." | Sense2, Def | "Shared files" then "a file channel" look like two things, and "tool-written notes" is undefined. "When the Researcher writes its notes with a tool call, making later agents read and write files through tool calls instead of copying costs 8-22 accuracy points at three of four Qwen3 sizes (Holm-corrected)." |
| 6 | Abstract | 35-37 | "files without an index lose 21.2 points against one Researcher when three Researchers share one folder, and separate folders recover 19.8." | Read2, Num | "against one Researcher" reads as an opponent; "19.8" lacks its unit. "files without an index lose 21.2 points when three Researchers share one folder instead of one writing alone, and separate folders recover 19.8 of them." |
| 7 | Abstract | 37-38 | "When state fits in the context, with Qwen3 and tool-call file access under our harness, agents should copy the conversation forward." | AI | Three stacked scope qualifiers, repeated in the conclusion. "Under our harness, Qwen3 agents whose state fits in the context should copy the conversation forward." |
| 8 | Intro | 45-46 | "one agent gathers facts, another writes, a third checks" | Gram | "one agent gathers facts, another writes, and a third checks" |
| 9 | Intro | 49-50 | "production research agents store subagent results and pass references" | Bare | "production research agents store subagent results in files and pass references to them" |
| 10 | Intro | 50-52 | "Prior work cuts tokens ... mostly with the channel fixed, and the one study that varies the channel compares references, summaries, and KV caches~\cite{toap} but not files accessed through tool calls." | Read2 | Split: "... mostly with the channel fixed. The one study that varies the channel compares passing references, summaries, and KV caches~\cite{toap}, but not files accessed through tool calls." |
| 11 | Intro | 52 | "Which is cheaper remains open." | Ante | The last nouns are references, summaries, KV caches, files. "Whether copying or sharing files is cheaper remains open." |
| 12 | Intro | 56-57 | "map onto each other, so what each primitive costs decides between them" | Ante | "them" can be the systems or the primitives. "map onto each other, so the choice between the two comes down to what each primitive costs" |
| 13 | Intro | 59-60 | "Each file read is a tool call, and because the model is stateless, each call resends the conversation." | Comma | "Each file read is a tool call, and, because the model is stateless, each call resends the conversation." |
| 14 | Intro | 60-61 | "The engine's prefix cache changes both costs, because it reuses the KV of a repeated prefix" | Gram | Vague verb; no comma before a restrictive because-clause. "The engine's prefix cache lowers both costs because it reuses the KV of a repeated prefix" |
| 15 | Intro | 65-66 | "such as replaying one agent's notes into every channel" | Def | "notes" is defined in Section 2. Low priority; "such as replaying one agent's output into every channel" or keep. |
| 16 | Intro | 69 | "because broadcast's layout defeats the prefix cache" | Anthro, Read2 | Says neither what the layout is nor why. "because consecutive broadcast prompts share almost no prefix" |
| 17 | Intro | 70 | "files compute 2.0x the prefill" | Ante | "files compute 2.0x its prefill" |
| 18 | Intro | 71 | "files cost accuracy beyond how the notes are written" | Read2 | "files cost accuracy even when the notes are written the same way" |
| 19 | Intro | 71-73 | "With tool-written notes, replacing copying with a file channel, where later agents use tool calls for inputs and outputs, costs ..." | AI, Def | Verbatim copy of the abstract; "tool-written" undefined here. "When the Researcher writes its notes with a tool call, moving later agents from copying to reading and writing files through tool calls costs 8-22 accuracy points at three of four model sizes." |
| 20 | Intro | 74-75 | "lose 21.2 points against one writer when three writers share one folder, and a folder per writer recovers 19.8 of them" | Sense2 | "writer" here is a Researcher, not the Writer role. "lose 21.2 points when three Researchers share one folder instead of one, and a folder per Researcher recovers 19.8 of them" |
| 21 | Intro | 76-77 | "vary payload, writers, cache, and tool budget" | Def, Sense2 | "payload" is never defined; "writers" as in item 20. "vary the payload, the number of Researchers, the KV-cache size, and the tool budget" (define payload in item 33) |
| 22 | Intro | 63-77 | Paragraph with seven numbers (2.9, 0.79, 61, 2.0, 8-22, 21.2, 19.8) | AI | Number ledger. Keep one number per observation (0.79x, 8-22, 21.2/19.8); move 2.9x and 2.0x to Section 4, where they appear anyway. |
| 23 | Ch. | 94-95 | "(a reply, or files written with a \texttt{write\_file} tool)" | Comma | "(a reply or files written with a \texttt{write\_file} tool)" |
| 24 | Ch. | 95-96 | "The channels differ in what the Writer and the Reviewer receive" | Read2 | The previous sentence just said the Researcher's instructions also differ. "Otherwise, the channels differ only in what the Writer and the Reviewer receive" |
| 25 | Ch. | 96-97 | "each given its questions and their documents" | Ante | "its questions" is unclear. "each given a share of the questions and their documents" |
| 26 | Ch. | 105-106 | "The tokens are still sent, so only their recomputation is saved, and the instruction moves to the end of the prompt." | Read2 | The last clause repeats the first sentence and does not follow from "so". "The tokens are still sent, so only their recomputation is saved." (If the moved instruction matters for accuracy, say "Moving the instruction is the only other change.") |
| 27 | Ch. | 111-113 | "The documents, the notes, and the draft are files in a workspace, accessed through the ... tools" | Gram | Dangling participle (files or workspace?). "... are files in a workspace that agents access through the \texttt{list\_files}, \texttt{read\_file}, and \texttt{write\_file} tools" |
| 28 | Ch. | 116-117 | "an \texttt{index.md} file listing each file's author, size, and first line, which the workspace updates as a file system updates a directory" | Ante | "which" attaches to "first line". "an \texttt{index.md} file that lists each file's author, size, and first line. The workspace keeps it current, as a file system does a directory." |
| 29 | Ch. | 118-120 | "We also ran a handoff channel, which sends ..., and a variant of B whose later agents reply instead of writing files, and leave both to the appendix." | Read2 | Three "and"s; the last joins a second verb. "... instead of writing files. Both are in the appendix." |
| 30 | Method | 128 | Figure 2 caption "(main run, Qwen3-8B, ...)" | Def | The float sits above the Runs paragraph that defines "main run". Low priority; acceptable if the figure moves after Runs. |
| 31 | Method | 129-130 | "Whiskers are 95% intervals of each channel's mean, not of paired differences." | AI | Keep: here the contrast is the information. Listed only to mark it as checked. |
| 32 | Method | 130 | "Files are the most expensive (a), and zero-copy computes about the pipe's prefill (b)." | Claim | False for (b), where broadcast computes the most. "Files send the most tokens (a), but broadcast computes the most prefill and zero-copy about the pipe's (b)." |
| 33 | Method | 137-138 | "so the amount passed between agents grows with $k$" | Def | Define the term used in L76, L354 and Fig. 4: "so the payload passed between agents grows with $k$" |
| 34 | Method | 146-148 | "so channels share its KV cache. Each pipeline gets its own cache namespace ..., so no KV is reused across tasks or channels." | Sense2 | "share" reads as reuse, then is denied. "so channels compete for its KV-cache capacity" |
| 35 | Method | 148 | "Jobs rotate across servers" | Def | "Pipelines rotate across servers" |
| 36 | Method | 150-151 | "each call may generate up to 2,048 tokens" | Def | "token cap" is used in L162, L249, L323 but never named. "each call may generate up to 2,048 tokens (the token cap)" |
| 37 | Method | 153 | "If \texttt{final.md} is still missing" | Bare | "If the Reviewer's \texttt{final.md} is still missing" |
| 38 | Method | 154 | "This fallback decides at most one task per channel" | Anthro | "This fallback supplies the answers of at most one task per channel" |
| 39 | Method | 157-158 | "three RTX 3090 servers with a 34,864-token KV cache" | Read2 | Per server or total? "three RTX 3090 servers, each with a 34,864-token KV cache" |
| 40 | Method | 158-160 | "The same servers run three controls ... and the larger payloads of \S5." | Gram | Servers do not run payloads. "... and the larger-payload runs of \S5." |
| 41 | Method | 161-163 | "The crossed runs, one per size on 150 three-question tasks with a 4,096-token cap, cross how the Researcher writes its notes ... with how later agents get their inputs" | Read2, Def | "crossed runs ... cross"; "size" and "factor" undefined. "The crossed runs, one per model size on 150 three-question tasks with a 4,096-token cap, vary two factors: how the Researcher writes its notes (a reply or a \texttt{write\_file} call) and how later agents get their inputs, by copying or through the file channel." |
| 42 | Method | 164-166 | "The file channel is B, with inputs read through tool calls within the tool budget and outputs written as files, with the rescue." | Read2 | Three stacked "with"s. "In the file channel, later agents read inputs through tool calls within the tool budget and write outputs as files, as in B, with the rescue." |
| 43 | Method | 166 | "There, a reply is stored as \texttt{notes.md}, the \emph{stored reply}." | Ante, Def | "There" is vague and the definition is circular. "In the file channel, a Researcher's reply is saved as \texttt{notes.md}, which we call the \emph{stored reply}." |
| 44 | Method | 166-167 | "An earlier \emph{wording run} on these tasks has broadcast and the other crossed arms." | Def, Read2 | "arms" is undefined and "the other" has no referent. Suggested (author to confirm the design): "An earlier \emph{wording run} on the same tasks ran broadcast with its own Researcher instructions alongside three of the crossed arms." |
| 45 | Method | 173-174 | "\emph{Serving time} is the wall time of a run ..." | Def | Defined but never used; Section 4 says "broadcast's time". Use the term in L216-220 (item 59) or delete the definition (saves a line). |
| 46 | Method | 174-178 | "It separates kept from removed or altered sentences in 450 synthetic pairs (AUC 0.996), but on real notes its labels match a Qwen3-8B judge's only weakly (Cohen's $\kappa$ = 0.29), so fact-level numbers are approximate." | Ante, Read2 | "It" can be fact coverage or AlignScore; two parentheticals in one sentence. "AlignScore separates kept from removed or altered sentences in 450 synthetic pairs (AUC 0.996). On real notes, its labels match a Qwen3-8B judge's only weakly (Cohen's $\kappa$ = 0.29), so fact coverage is approximate." |
| 47 | Method | 180 | "paired differences against A1" | Sense2 | The prose calls this channel "broadcast" everywhere else; also L391-393. "paired differences against broadcast (A1)" |
| 48 | Method | 181-182 | "settings with $k=1$, 3, and 5 share questions" | Read2 | Says a fact without why it matters. "settings with $k=1$, 3, and 5 draw on the same questions, so they are not independent" |
| 49 | Method | 184 | "both fixed after earlier runs on the same tasks" | Sense2 | "fixed" can mean repaired. "both chosen after earlier runs on the same tasks" |
| 50 | Method | 185-186 | "We mark comparisons across runs as cross-run, which may include drift (\S5)." | Ante | "We mark comparisons across runs as cross-run, because they may include drift between runs (\S5)." |
| 51 | Results | 191-192 | "find why files lose, and test this loss across sizes" | Gram | "find why files lose accuracy, and test this loss across sizes". Also add the scope once here ("All results are with Qwen3-8B unless a size is named") and drop "With Qwen3-8B," from the headings at L212, L232, L240 (saves about two lines). |
| 52 | Results | 197-199 | Figure 3 caption "Copied replies are the most accurate arm at every size, tied with copied tool writes at 14B." | Claim, Struct | Not the claim the text draws; panel (a) unmentioned; "tool writes" is a third name for tool-written notes. "With tool-written notes, the file channel lowers accuracy at 4B, 14B, and 32B (b), and the tool-call write lowers fact coverage at every size but 14B (a)." |
| 53 | Results | 197-199 | Figure 3 legend "Tool write, copied", "Tool write, file channel" | Sense2 | Match the prose: "Tool-written, copied", "Tool-written, file channel" (figure script). |
| 54 | Results | 203 | Heading "Files send the most tokens, but the prefix cache absorbs most of them." | Struct | Half the paragraph is zero-copy, and the intro's first observation never becomes a heading. "The channels rank differently by prefill than by tokens sent." |
| 55 | Results | 205-206 | "against broadcast's 3.0 and each call resends the conversation" | Comma | Garden path ("3.0 and each call"). "against broadcast's 3.0, and each call resends the conversation" |
| 56 | Results | 213 | "To see whether lower prefill shortens serving" | Def | "To see whether lower prefill shortens serving time" |
| 57 | Results | 214-216 | "By vLLM's per-request counters, which time requests under batching, decoding takes 96% of broadcast's summed prefill and decode time in two runs." | Read2 | "in two runs" dangles at the end. "In two of these runs, by vLLM's per-request counters, which time requests under batching, decoding takes 96% of broadcast's summed prefill and decode time." |
| 58 | Results | 216 | "Zero-copy's agents generate 1.2x as many output tokens" | Num | No baseline. "Zero-copy's agents generate 1.2x broadcast's output tokens" |
| 59 | Results | 216-217 | "and its run takes 1.09x broadcast's time and its median task 0.99x" | Read2 | Two "and"s plus gapping. New sentence: "Its run takes 1.09x broadcast's serving time, and its median task 0.99x." |
| 60 | Results | 217-219 | "The pipe's run takes 0.78x broadcast's time, and B's and C's take 1.80x and 1.56x." | AI | Number ledger without a reason. "B's and C's runs take 1.80x and 1.56x as long because they make over five times as many model calls, and the pipe's takes 0.78x." |
| 61 | Results | 221-222 | "Zero-copy thus pays off where uncached prompt tokens cost more than cached ones and in per-task latency under heavy load." | Gram | Not parallel ("where ... and in ..."). "Zero-copy thus pays off when uncached prompt tokens cost more than cached ones or when per-task latency under heavy load matters." |
| 62 | Results | 226-227 | "Its 90\% interval, ... lies inside a $\pm$3-point equivalence margin." | Ante | "Its" follows "a difference" but the previous "Its"-sentences mean zero-copy. "The difference's 90\% interval, $-$2.4 to 1.0, lies inside a $\pm$3-point equivalence margin." |
| 63 | Results | 228 | "Its point estimates are within 2.7 points of broadcast's" | Ante | "Zero-copy's accuracy is within 2.7 points of broadcast's in every setting" |
| 64 | Results | 229-230 | "Its Researcher writes longer notes (1,992 characters against 1,570)." | Struct | Orphan fact; its use is in \S5 (L386-387). Move it there: "so its Researcher's longer notes (1,992 characters against 1,570 at 8B) are not the main cause." |
| 65 | Results | 236-238 | "Given the documents as well, in a separate run on 200 tasks, the pipe still trails broadcast by 3.0 points ($-$5.3 to $-$0.7, cross-run)." | Gram, Num | Dangling "Given" (the pipe is not given anything; its later agents are). Positive gap with a negative interval, while L257, L368, L382 give positive intervals for "trails by". "In the documents control on 200 tasks, where later agents also get the documents, the pipe still trails broadcast by 3.0 points (0.7 to 5.3, cross-run)." (needs sign-flipped macros, or write "differs by $-$3.0") |
| 66 | Results | 240 | Heading "With Qwen3-8B, files trail broadcast, and, without an index, the Writer mostly reads documents." | Comma, AI | Comma-heavy; repeated opener. "Files trail broadcast, and B's Writer mostly reads documents." |
| 67 | Results | 242-243 | "C trails it by 6.0 points at $k=3$ and by $-$1.3 to 8.4 across settings" | Num, Gram | "trails by $-$1.3" means leads; no unit on the range; B gets no k=3 value or significance count, so the two are not parallel. "C trails it by 6.0 points at $k=3$, and its gap ranges from $-$1.3 to 8.4 points across settings" |
| 68 | Results | 246-247 | "and C's Writer skips them in only 8\% of tasks, though C also adds the heading rule" | Read2 | "and C's Writer skips them in only 8\% of tasks, but C also adds the heading rule, so the index is not the only change" |
| 69 | Results | 247 | "The harness also binds." | Read2 | Jargon. "The harness's limits also bind." |
| 70 | Results | 247-248 | "Some agent uses up its tool budget in 34\% of B's and 34\% of C's tasks" | Gram | "At least one agent uses up its tool budget in 34\% of both B's and C's tasks" |
| 71 | Results | 251-252 | "(B: 62.5\% against 63.5\%, C: 65.8\% against 67.3\%)" | AI | Colons inside parentheses. "(62.5\% against 63.5\% for B, 65.8\% against 67.3\% for C)" |
| 72 | Results | 240-252 | Files paragraph | Struct | Four jobs (gap, reads, limits, rescue). Break before "The harness's limits also bind." or move those two sentences to the Harness paragraph in \S3. |
| 73 | Results | 254-256 | "Giving B's later agents the documents in that separate run changes B's accuracy by 0.5 points" | Ante, Read2 | "that separate run" points two paragraphs back, and the sentence does not say B still trails, which is the heading's claim. "In the documents control, giving B's later agents the documents changes B's accuracy by only 0.5 points (...), so B still trails broadcast." |
| 74 | Results | 256-257 | "B and C trail broadcast by 5.2 points (2.2 to 8.0)" | Read2 | One number for two channels: each, or pooled? Author to confirm; if pooled, "B and C, pooled, trail ..." |
| 75 | Results | 257-259 | "C's Writer, whose index also lists the documents, opens the notes less often than B's (63\% against 76\%)." | Read2 | Reverses the main-run result (L246-247) without a signal. "Unlike in the main run, C's Writer, whose index also lists the documents, opens the notes less often than B's (63\% against 76\%)." |
| 76 | Table 1 | 265-266 | "or among the 8 tests of \S4 for the interaction" | Def | The table is in \S4; the family is defined in \S3. "or among the 8 further tests (\S3) for the interaction" |
| 77 | Table 1 | 266 | "Rescued: tasks (\%) rescued (stored reply/tool-written)." | AI | Stacked parentheses, "rescued" twice. "Rescued: \% of tasks rescued, stored reply / tool-written notes." |
| 78 | Results | 291-293 | "A stepwise split of the file channel's two changes would make each change's share depend on the order" | Sense2, Def, Struct | Here "the file channel" means B against broadcast (both factors); elsewhere it is one level of one factor. Also a method sentence where the topic sentence should be. "To separate how the notes are written from how later agents get them, the crossed runs vary both at once, because a stepwise split would make each one's share depend on the order (Figure 3, Table 1)." |
| 79 | Results | 293-295 | "All four arms give the Researcher B's instructions, whose wording alone changed accuracy by 6.2 points at 4B (2.9 to 9.6) and by at most $\pm$3.1 at larger sizes in the wording run." | Gram, Read2 | Tense mix; "in the wording run" dangles; "at most $\pm$". "All four arms give the Researcher B's instructions. In the wording run, this wording alone changed accuracy by 6.2 points at 4B (2.9 to 9.6) and by at most 3.1 points either way at larger sizes." |
| 80 | Results | 295-297 | "With tool-written notes, the file channel lowers accuracy by 8-22 points at 4B, 14B, and 32B, all significant after Holm correction." | AI | Restates the heading word for word. "On tool-written notes, the file channel lowers accuracy by 8-22 points at 4B, 14B, and 32B, all Holm-significant." |
| 81 | Results | 297-300 | "this cost exceeds the tool-call write's cost on copied notes by 13.3 (6.2 to 20.2) and 9.1 points (4.4 to 14.2), significant in the second family, but not at 32B (4.2, $-$1.1 to 9.6)." | Read2, AI | "but not at 32B" attaches to "significant"; "(4.2, $-$1.1 to 9.6)" stacks a value and an interval. "... by 13.3 points (6.2 to 20.2) and 9.1 points (4.4 to 14.2), both significant in the second family. At 32B, the excess is 4.2 points ($-$1.1 to 9.6)." |
| 82 | Results | 297-301 | (missing answer after item 81) | Struct | Add the sentence that answers the intro's second observation: "So at two sizes, files cost more accuracy than writing the notes with a tool explains." (+15 words; pay with Space cuts) |
| 83 | Results | 300-301 | "Both file-channel effects are smallest at 8B, where neither survives the correction." | Ante | Which two? "At 8B, both Copy$\to$files effects are smallest, and neither survives the correction." |
| 84 | Results | 302-305 | "At 14B and 32B, rescued tasks with tool-written notes score below the others (62.9\% against 74.3\% and 55.7\% against 71.3\%), unlike at 8B (66.3\% against 64.1\%)." | AI, Struct | Six numbers and no stated consequence. Drop the parentheses ("score below the others, 62.9\% against 74.3\% and 55.7\% against 71.3\%, but not at 8B") and add one clause saying what the reader should conclude (author to supply; e.g. whether part of the cost comes from agents that failed to write). |
| 85 | Results | 307 | Heading "The stored reply's larger loss is an observation, not a channel cost." | AI, Read2 | "X, not Y" flourish; "an observation" says nothing. "A stored reply adds a loss that the file channel alone does not explain." |
| 86 | Results | 308 | "the stored reply scores 21.3 and 8.2 points below tool-written notes" | Anthro, Gram | A reply does not score; hyphenate the compound. "the stored-reply arm scores 21.3 and 8.2 points below the tool-written arm" |
| 87 | Results | 309-311 | "so the file channel's cost depends on how the notes are written, and the stored reply's loss is not the channel's." | Read2 | Elliptical end. "so the file channel's cost depends on how the notes are written, and the extra loss belongs to the stored reply." |
| 88 | Results | 314-315 | "This findability gap is not a tested cause, since the stored reply also changes the file's name, number, and location." | AI, Read2 | Coined label; "is not a tested cause" is awkward; "number" is unclear. "We did not test this naming gap as a cause, because the stored reply also changes the file's name, its location, and the number of notes files." |
| 89 | Results | 316 | "The Writer opens \texttt{notes.md} more than tool-written notes at 8B" | Gram | "more often than" |
| 90 | Results | 318 | "% TODO p17: ..." | Struct | Source-only placeholder; remove or resolve before submission. |
| 91 | Results | 320 | Heading "The tool-call write costs accuracy on copied notes at some sizes." | Struct | Hedge in a heading. "Writing notes with a tool call lowers fact coverage and, at 4B, accuracy." |
| 92 | Results | 320-322 | "... but only the 4B loss survives Holm correction, and at 8B its exact-match interval includes zero ($-$6.4 to 0.2)." | Read2 | Split: "... but only the 4B loss survives Holm correction. At 8B, its exact-match interval includes zero ($-$6.4 to 0.2)." |
| 93 | Results | 322-324 | "shrinks the 4B effect to $-$6.6 points ($-$10.1 to $-$3.3)" | Num | No baseline. "shrinks the 4B effect from $-$8.7 to $-$6.6 points ($-$10.1 to $-$3.3)" (plain, non-bold macro for $-$8.7) |
| 94 | Results | 324-326 | "Where the effect appears, fact coverage is also lower (Figure 3a), 32\% against 43\% at 8B. At 14B, neither drops." | Read2, Ante | Vague "Where"; numbers trail the figure reference; "neither" ambiguous. "Fact coverage falls with accuracy, from 43\% to 32\% at 8B (Figure 3a). At 14B, neither accuracy nor coverage drops." |
| 95 | Fig. 4 | 331-333 | Panel (a) title "Prefill on a 35k-token cache" | Read2 | Collides with \S5's separate RTX PRO 6000 run "with 35k tokens" (L348). "Prefill on the main run's 34.9k-token cache" |
| 96 | Fig. 4 | 331-333 | Panel (b) title "where both payload and writers change" | Sense2 | "where both payload and Researchers change" |
| 97 | Sens. | 347-349 | "against 0.85x with 35k tokens, and no channel's accuracy moves by more than 1.6 points across the three caches" | Read2, Gram | Two ideas; "with 35k tokens" lacks its noun. "... against 0.85x with a 35k-token cache. Across the three caches, no channel's accuracy moves by more than 1.6 points." |
| 98 | Sens. | 349-350 | "while the pipe computes 0.37x broadcast's prefill within 0.5 points of broadcast's accuracy" | Gram | Attachment and parallelism. "while the pipe computes 0.37x broadcast's prefill and stays within 0.5 points of its accuracy" |
| 99 | Sens. | 352 | Heading "parallel writers sharing one folder cause most of B's fan-out loss" | Sense2 | "parallel Researchers sharing one folder cause most of B's fan-out loss" |
| 100 | Sens. | 352-354 | "but both the payload and the number of writers change" | Sense2, Read2 | Change relative to what? "but from $k=5$ to $k=16$ both the payload and the number of Researchers change" |
| 101 | Sens. | 359-362 | "It recovers 19.8 points over three-Researcher B (15.6 to 23.6) and differs from one-Researcher B by $-$1.5 (...), which does not exclude a residual loss of a few points." | Read2, Ante | Interval separated from its number; "which" points to the interval only by guess. "It scores 19.8 points (15.6 to 23.6) above three-Researcher B and differs from one-Researcher B by $-$1.5 points ($-$5.8 to 3.0, cross-run), an interval that allows a residual loss of a few points." |
| 102 | Sens. | 364 | "Separate folders also change the paths the Writer sees, a confound of this arm." | AI | Trailing appositive tag. "This arm is confounded, because separate folders also change the paths the Writer sees." |
| 103 | Sens. | 366-376 | Heading names the guard and the heading rule; the paragraph ends with the tool budget | Struct | Second job. Heading: "At sixteen questions, a write guard or the heading rule recovers about half of B's loss, and a larger tool budget does not." |
| 104 | Sens. | 371 | "recovers 18.1 points on 59 tasks" | Read2 | 59 of the run's 60 tasks, unexplained. Add the reason in a word or drop the count. |
| 105 | Sens. | 373-376 | "24 calls instead of 12 move B's accuracy by 3.3 points (...), against B's gap of 33.9 points (...) in the 12-call run, which equals the main run's gap by coincidence." | Read2, Ante | Odd subject; "which" can be the gap or the run; trailing aside. "Raising the budget from 12 to 24 calls moves B's accuracy by 3.3 points ($-$0.5 to 7.4, cross-run), small next to B's 33.9-point gap (28.7 to 39.2) in the 12-call run." Drop the coincidence clause or make it its own short sentence. |
| 106 | Sens. | 378 | "On 200 three-question tasks per size" | Def | These size runs are never introduced in Runs (\S3). Add there: "The \emph{size runs} serve each Qwen3 size on 200 three-question tasks." |
| 107 | Sens. | 380-381 | "At 32B, these ranges compare a rerun that fixes a harness path bug with the first run's broadcast (cross-run)." | Read2 | "At 32B, B and C come from a rerun that fixes a harness path bug and are compared with broadcast from the first run (cross-run)." |
| 108 | Sens. | 381-383 | "C does not beat B at every size. At 14B, C trails broadcast by 16.0 points (12.0 to 19.8), against B's 7.5 (4.0 to 10.8)." | Struct | Weak topic sentence with no reason. "At 14B, C trails broadcast by 16.0 points (12.0 to 19.8), more than B's 7.5 (4.0 to 10.8)." (saves a sentence) |
| 109 | Sens. | 384-387 | "Zero-copy ordering significantly lowers accuracy only at 4B, by 7.0 points (3.0 to 11.2), and by 5.8 (2.5 to 9.5) with broadcast's notes replayed into both channels, so its longer notes are not the main cause." | Read2, Def | New term "zero-copy ordering"; three claims in one sentence. "Zero-copy significantly lowers accuracy only at 4B, by 7.0 points (3.0 to 11.2). With broadcast's notes replayed into both channels, it still loses 5.8 (2.5 to 9.5), so its Researcher's longer notes are not the main cause." |
| 110 | Sens. | 390-391 | "two Researchers with identical prompts write identical notes in 59\% of tasks" | Read2 | Which two? "the Researchers of two channels that get identical prompts write identical notes in 59\% of tasks" (author to confirm which channels) |
| 111 | Sens. | 391-393 | "Rerunning A1 and B ... and gives a gap of 7.0 points between B and A1, against the main run's 7.8" | Sense2 | Use one name. "Rerunning broadcast and B on 200 main-run tasks keeps both channels' rerun-minus-original intervals within $\pm$2.2 points, and B's gap to broadcast is 7.0 points against the main run's 7.8." |
| 112 | Sens. | 393-395 | "three arms of the wording run repeated in the crossed runs move by at most 0.9 points" | Read2 | Reduced relative clause. "the three wording-run arms that the crossed runs repeat move by at most 0.9 points" |
| 113 | Sens. | 395 | "We did not measure drift across GPUs or caps." | Def | "across GPUs or token caps" |
| 114 | Related | 402-403 | "MAST catalogs inter-agent failures, including ignored input, such as our unopened notes." | Gram | "such as" makes MAST catalog our notes. "MAST catalogs inter-agent failures, including ignored input, of which our unopened notes are an instance." |
| 115 | Related | 409-410 | "Zero-copy broadcast uses the layout these systems assume" | Claim | KVCOMM, TokenDance and CacheBlend target prefixes that differ. "Zero-copy broadcast uses the shared-prefix layout that Prompt Cache, Parrot, and KVFlow assume" |
| 116 | Related | 414 | "per-writer folders as per-process namespaces" | Sense2 | "per-Researcher folders as per-process namespaces" |
| 117 | Concl. | 421 | "depends on the cost a deployment pays" | Read2 | "depends on which cost a deployment pays for, tokens sent or prefill" |
| 118 | Concl. | 423-424 | "When state fits in the context, with Qwen3 and tool-call file access under this harness's tool budget and rescue, agents should copy the conversation forward." | AI | Repeats the abstract with four stacked qualifiers. "Under this harness's tool budget and rescue, Qwen3 agents whose state fits in the context should copy the conversation forward." |
| 119 | Concl. | 422-427 | "With Qwen3-8B, ... When state fits ... With tool-written notes, ... With Qwen3-8B, ..." | AI | Four of five sentences open with a with-phrase. Vary: "The file channel costs 8-22 accuracy points on tool-written notes at three of four sizes, ..." and "Per-Researcher folders recover most of B's fan-out loss at eight questions with Qwen3-8B." |
| 120 | Concl. | 430 | "why zero-copy costs 4B accuracy" | Gram | "why zero-copy lowers accuracy at 4B" |
| 121 | Global | many | "X against Y" used 21 times as the only comparison connector | AI | Repeated tag. Keep it for paired percentages; elsewhere use "from X to Y" (items 93, 94), "more than" (item 108), or "compared with". |
| 122 | Global | 212, 232, 240, 422, 427 | "With Qwen3-8B," as an opener (5 times) | AI | State the scope once in L191 and drop it from the three headings (item 51). |
| 123 | Global | many | "tool-written notes", "tool-call write", "tool write" (Fig. 3), "\texttt{write\_file} call" | Sense2 | Four names for one factor level. Use "tool-written notes" for the level and "the tool-call write" for the effect only. |
| 124 | Global | 85, 150, 389, 402 vs 163-166, 291-317 | "file channel(s)" means B and C (Fig. 1 caption, Harness, noise heading, Related Work) and also the crossed-run factor level | Sense2 | Use "file-based channels" or "B and C" for the family; keep "the file channel" for the factor level defined in Runs. |
| 125 | Global | 141-160, 213, 355, 302 | Methods mix present ("The main run serves", "runs") and past ("we timed", "we ran", "needed", "wrote") for what was run | Gram | Per the guide: past for what was run, present for what the data show. E.g. "The main run served Qwen3-8B ... and ran every channel and setting." |

## Count by type

Items with two types count under both.

| Type | Count |
| --- | --- |
| Read2 (needs a second read) | 40 |
| Def (term before definition or undefined) | 18 |
| AI (AI-writing tell) | 18 |
| Gram (grammar) | 17 |
| Sense2 (term in two senses) | 15 |
| Ante (unclear antecedent) | 15 |
| Struct (structure) | 12 |
| Comma | 5 |
| Num (unit, baseline, sign) | 5 |
| Anthro (metric verb) | 3 |
| Claim (caption or sentence overstates) | 3 |
| Bare (bare reference) | 2 |

125 items; item 31 is a checked "keep".

## Space

Fixes marked +words (items 4, 82, and a few one-clause additions) need about three lines. Cuts that pay for them
without losing meaning: drop "With Qwen3-8B," from three headings (item 51, about two lines); delete the redundant
clause in A1-zc (item 26); delete the unused Serving-time definition or the coincidence clause (items 45, 105);
merge "C does not beat B at every size" into the next sentence (item 108); move 2.9x and 2.0x out of the intro
(item 22).
