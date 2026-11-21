# Review (methods and statistics): "Messages or Files? Revisiting IPC for LLM Agent Pipelines"

## Summary

The paper compares five ways of passing state between three LLM agents (Researcher, Writer, Reviewer) on
multi-hop QA tasks (HotpotQA, 2Wiki): copying the whole conversation (A1, broadcast), broadcast with the
shared history placed first so the prefix cache reuses it (A1-zc), passing only the previous output (A2,
pipe), and shared files read through tools, without (B) and with (C) an index. Qwen3 4B to 32B run on
vLLM. Paired task-level bootstraps and sign-flip permutation tests with Holm correction support the
headline claims:
(i) channels rank differently by prefill than by tokens sent, and zero-copy computes 38–49% of broadcast's
prefill with a paired accuracy difference of −2.9 to +1.4 points;
(ii) "much of the files' accuracy cost comes with the tool protocol", from a 2×2 crossed design
(notes written as a reply or by a tool call × copied or file channel) at four sizes;
(iii) at k=8, parallel Researchers sharing a folder lose about 20 points, and per-Researcher folders win
this back;
(iv) at 32B, telling later agents where the stored notes are raises accuracy by 14 points, and at 14B,
listing the notes first helps the Writer, but "the Reviewer ... undid the Writer's gain".

I re-derived the main numbers from `paper_numbers.py` and the raw records. The macros match the code. The
problems are in interpretation, not arithmetic. The most serious one is a Reviewer behaviour at 14B that
the paper does not report, and it changes the mechanism story of §4.

## Score and confidence

- **Score: 3/5** (borderline; accept only if the 14B mechanism and the "tool protocol" framing are fixed)
- **Confidence: 4/5** (I read the pipeline, the workspace, the metric and numbers code, and recomputed
  rates from `results_raw/`)

## Strengths

1. **Careful paired design.** Every channel runs the same tasks. Bootstraps resample tasks, so a task's
   questions stay together. Cross-run comparisons are labelled, and the k=8 fan-out uses a
   difference-in-differences to remove drift common to both channels.
2. **The crossed 2×2 is the right way to split B.** It avoids the order dependence of a stepwise
   decomposition. It is also run at four sizes, and B − A1w is repeated in three runs, with a spread of
   ≤3.3 points.
3. **Many relevant controls:** a documents control, a replay control (broadcast's notes in every channel),
   a wording control (A1r), a stored reply (Bs), a told path (Bt), first-listed names (Bs0/Bt0), a write
   guard and the heading rule at k=16, separate folders at k=8, and a cache-size sweep.
4. **Statistical hygiene above the norm for a workshop.**
   - Sign-flip permutation tests with Holm correction.
   - Post hoc families are declared as such.
   - Draft-versus-final accuracy is used to place losses at a stage.
   - Prefill and tokens sent are kept separate, and the prefill claim is checked against cache size.
5. **The timing runs are well done.** Channels run alone on one GPU, in a randomized order
   (`pro6000_round6_timing_order.txt`). The paper honestly concludes that prefill savings barely move wall
   time when decoding takes about 96% of request time.
6. **Numbers are machine-generated** (`numbers.tex` from `paper_numbers.py`). I found no transcription
   errors.

## Weaknesses (most important first)

### 1. At 14B the Reviewer almost never reads the draft, and the harness writes its final answers. §4's 14B mechanism is misattributed. [needs new runs]

From the raw records, the share of file-channel tasks whose Reviewer read `draft.md`:

| Run | Arm | Reviewer read draft.md | Reviewer rescued |
| --- | --- | --- | --- |
| 14B crossed (p16) | B | 6% | 70% |
| 14B crossed (p16) | Bs | 3% | 100% |
| 14B told (p17) | B / Bs / Bt | 5% / 3% / 1% | 70% / 100% / 100% |
| 14B first-listed (p18) | B / Bt / Bs0 / Bt0 | 5% / 1% / 2% / 8% | 73% / 100% / 99% / 95% |
| 14B size run (p02) | B / C / D | 6% / 27% / 5% | 71% / 94% / 90% |
| 32B crossed and told | B / Bs / Bt | 98–100% | 7–15% |
| 8B main run | B | 93% | 34% |

The 14B Reviewer's typical trace is the same in every arm: `list_files`, several reads under `docs/`, a
plain-text reply, then the forced `write_file`. It answers the questions again from the documents. It does
not revise the draft, even though its instruction names `draft.md`.

This changes several claims:

- **"At 14B, B's drafts are about as accurate as with copying, and the loss appears at the Reviewer."**
  The loss appears because the final answers no longer come from the draft.
- **"The Reviewer opens it in only 15% of tasks and revises the gain away"** and the Conclusion's
  **"undid the Writer's gain"**. Bt0's Reviewer read the draft in 8% of tasks. There was nothing to
  "revise". Final accuracy is about 44% in every 14B stored-reply arm (Bs 44.2, Bt 43.6, Bs0 45.3,
  Bt0 44.7), whatever the draft scored (44.7 to 62.0). That pattern fits a Reviewer that ignores the
  draft.
- **The observational split (23 versus 127 tasks)** is confounded by whether the Reviewer read the draft.
- **14B tool-written notes sit under `docs/`.** 14B Researchers save them there in 79–83% of B tasks
  (p16, p17, p18; the macro `RToldFourteenToolNotesUnderDocs` = 79 is computed but never printed). The
  document-reading Writer and Reviewer then read them as documents (the Reviewer opened them in 80% of
  tasks, against 3% for the stored `notes.md`). So the 21.3-point "Reply→tool, files" effect at 14B, and
  the interaction, are largely about where the file sits relative to `docs/`.
- **The first-listed run did not test this.** `00_notes.md` is still at the root.

**Fix.**
- Report draft-read and notes-read rates per role, arm and size, and rewrite the 14B paragraphs and the
  Conclusion.
- New runs at 14B on the same 150 tasks:
  - (a) Bt0 with "Read draft.md first" in the Reviewer's instruction, or with the draft in its prompt as
    Br does;
  - (b) a stored-reply arm whose file is placed under `docs/` (e.g. `docs/00_notes.md`), to test "place".
- Without these, the rule "lead every later agent ... to the stored notes" has no intervention that worked
  at 14B, even for the draft the instruction already names.

### 2. "Much of the files' accuracy cost comes with the tool protocol" is close to true by definition, and at 8B the cost sits elsewhere. [text/analysis only]

The paper defines the tool protocol as "the reads, writes, and tool budget that files impose". Against
copying, that covers almost everything B changes, except the information in context. The documents and
replay controls address the information part (8B only, cross-run).

The decomposition at the paper's main model points somewhere else:

| 8B effect | Run | Estimate (points) | Significance |
| --- | --- | --- | --- |
| A1w − A1r (Researcher's tool-call write) | crossed | −4.7 | p = 0.013 |
| A1w − A1r | wording | −5.6 | |
| B − A1w (later agents' file channel) | crossed | −2.9 | p = 0.12 |
| B − A1w | wording | −1.6 | (−5.3, 2.2) |

At 8B, B's gap to broadcast therefore comes mostly from the Researcher writing its notes through a tool
call (coverage 43% → 32%), not from later agents reading files.

The second Holm family includes "the file channel's cost on tool-written notes minus the tool-call write's
cost on copied notes" (`Dvw`), but the paper never reports it. Its values:

| Size | Dvw (points) | 95% interval | p |
| --- | --- | --- | --- |
| 4B | 13.3 | | 0.001 |
| 8B | −1.8 | | 0.59 |
| 14B | 9.1 | | <0.001 |
| 32B | 4.2 | (−1.1, 9.6) | 0.14 |

So at 8B and 32B, the file channel's cost cannot be told apart from the cost of a tool-call write.

**Fix.**
- Name the competing hypotheses (information in context, finding the notes, the act of writing through a
  tool, budget and rescue) and show which run tests each one.
- Add the Dvw row to Table 1.
- Restate the abstract so that at 8B the cost is in the Researcher's write and at 14B in the Reviewer and
  harness (W1).

### 3. The harness rescue dominates the file arms, and the rescue split is post-treatment. [needs new runs, plus text]

The Writer or Reviewer is rescued in many file-arm tasks:

| Size | Stored reply | Tool-written notes |
| --- | --- | --- |
| 4B | 100% | 100% |
| 8B | 44% | 66% |
| 14B | 100% | 77% |
| 32B | 43% | 43% |

The forced write is a fresh generation under `tool_choice=write_file`. The plain reply is not saved as
the output.

- **What is compared.** The comparison is "copying versus files with this particular rescue". At 4B and
  14B the file arms' accuracy is essentially the rescue's accuracy.
- **"Mostly in tasks where the harness rescued an agent" (abstract).** This conditions on an outcome of
  the B arm. Rescue marks tasks where the model failed to call a tool, and those are likely harder or
  longer.
- **The split disagrees across runs.** It also points the other way in the 8B main run (9.4 points on
  rescued tasks, 10.0 on the others).
- **Two definitions of "rescued".** The main-run split counts any agent, including the Researcher; the
  crossed-run split counts only the Writer or Reviewer.

**Fix.**
- Add one file arm whose rescue saves the agent's plain reply as the output file, as the system already
  does for Bs's Researcher. This would bound how much of the cost is in the forced write itself.
- Use one definition of "rescued".
- Drop "mostly in rescued tasks" from the abstract, or call it explicitly descriptive.

### 4. The file channels get weaker prompts and a weaker harness than the copy channels, yet the paper draws a general rule from them. [text, plus optional new runs]

In the copy arms, later agents get the documents and notes in their prompt. In B, the Writer is told to
"read a source document only to check a doubtful fact". The Reviewer is never told to read the draft
first, and 14B ignores it (W1). The 12-call budget sits against about 30 document files.

The 2,048-token cap of the main run hits B's tool-call note writes in 22 of 300 tasks, against 1 for
broadcast. At 8B on the RTX PRO 6000, B − A1 is −10.0 at a 2,048 cap (size run) and −6.4 at a 4,096 cap
(wording run). That comparison is cross-run, but it suggests the main run's headline B gaps (5.6–13.6)
include truncation.

The Introduction nevertheless states "copy rather than share files" without condition.

**Fix.**
- Scope the rules to "a minimal file harness whose state fits in context" in the Introduction and abstract,
  not only in the last paragraph.
- Report B's main-setting gap at the 4,096 cap.
- Optionally run a "reasonable practitioner" B (read the draft first, a batched read, a larger budget) at
  8B and 14B.

### 5. The told and first-listed tests: a failed manipulation check, an unreported arm, small post hoc subsets. [text/analysis only]

- **The 14B told test did not change behaviour.** The Writer opened the told `notes.md` in 5% of tasks,
  against 9% untold (p18 against p16). The Reviewer opened it in 1% against 3%. The 0.9-point null
  ("naming the path alone moves accuracy by only 0.9 points") therefore says nothing about whether reading
  the notes matters at 14B. The text should say the instruction was ignored.
- **The Bs0 arm (first-listed, untold) was run but not reported.** Writer opened it in 21% of tasks; draft
  accuracy 51.8%, final 45.3%. It is needed for the claim "the Writer followed it only when the file was
  also listed first".
- **The first-listed evidence is thin.** All first-listed results come from one post hoc run at one size,
  uncorrected. The 23-versus-127 split is observational, and confounded as noted in W1.

**Fix.**
- Report the manipulation checks next to each accuracy effect.
- Add Bs0.
- Label the 14B Reviewer analysis exploratory.

### 6. Drift is reported by point estimate, while several cross-run claims fall inside the drift band. [text/analysis only]

"Move by at most 0.9 points" is the largest point drift. The drift intervals (`RTenDriftLo/Hi`) run from
−3.6 to +3.1, and the 3090 rerun intervals reach ±2.2. Cross-run claims of similar size are read as
findings:

- the pipe with documents "still differs from broadcast by −3.0 (−5.3 to −0.7, cross-run)", where the
  documents-control run has no A1 of its own;
- Bf against one-Researcher B, −1.5;
- doubling the budget, 3.3 points;
- the told 32B arm against copied reply notes, −6.7 (this one exceeds the band).

Drift across GPUs and caps is unmeasured. Yet the abstract combines the 3090 main run (cap 2,048, KV
34,864 tokens) with PRO 6000 runs (cap 4,096, KV 100k).

**Fix.**
- Report drift intervals.
- Treat cross-run differences smaller than about 4 points as inconclusive.
- In the abstract, say which hardware and cap each number comes from.

### 7. Fact coverage (AlignScore) is too weak for the causal language attached to it. [needs new annotation, not GPU runs]

AlignScore agrees with a Qwen3-8B judge at κ = 0.29 on real notes. Broadcast's notes state only 45% of
supporting facts, yet broadcast answers 72% of questions, so the measure likely misses paraphrases and
facts combined across sentences.

The paper still uses it for:
- "B's notes state 32% ... against broadcast's 45%";
- "lower for tool-written notes at 4B, 8B, and 32B" (point estimates, no test; 14B goes the other way);
- the Conclusion's "We do not know why a tool-call write lowers fact coverage", which presents the effect
  as established.

**Fix.**
- Hand-label about 100 notes for calibration.
- Report the paired coverage contrasts with intervals.
- Otherwise downgrade the wording to "may".

### 8. The notes-opened metric and the "mostly reads documents" statistic are confounded by file layout. [text/analysis only]

- **"83% of B's Writer's reads go to source documents"** is a share of read operations. With about 30
  document files and 1–3 notes files, it is dominated by file count.
- **`writer_opened_notes` is a binary "any successful read"** of a file the Researcher wrote. At 14B,
  notes under `docs/` are opened incidentally while browsing documents. So "opened" means different things
  at 14B (incidental) and 32B (deliberate).

**Fix.**
- Report per task: whether the notes were read before the draft was written, the share of characters read
  that came from the notes, and the rank of the first notes read in the call sequence.

### 9. The serving-time claims rest on two or three runs, with output length as a confound. [needs new runs, cheap]

- **Few runs, no spread.** "Shortened the median task only with many concurrent tasks" rests on two runs
  at 32 concurrent tasks (0.81 and 0.83) and three at 6 concurrent tasks, with no interval.
- **Output length differs.** Zero-copy generates 1.2× broadcast's output tokens.
- **The decode share is not a compute share.** vLLM's per-request prefill/decode counters do not measure
  GPU compute shares under continuous batching, so "decoding takes 96%" should not be read as one.

**Fix.**
- Report per-run values with their spread.
- Equalize output (a fixed output length with `ignore_eos`), or report time per output token, so that the
  prefill effect is isolated.

### 10. Statistical reporting gaps. [text/analysis only]

- **The first Holm family is a replication, not a confirmation.** It was "chosen after earlier runs on the
  same tasks": the wording run had already measured B − A1w and A1w − A1r. Say so, and give the wording
  run's p-values as the discovery set.
- **"Only at 4B does the tool-call write change accuracy significantly" holds only after Holm.** At 8B and
  32B the intervals exclude zero (−4.7 [−8.0, −1.1], p = 0.013; −4.0 [−7.1, −0.9], p = 0.018).
- **Size-run "significantly" claims are uncorrected** (4 sizes × 5 channels), and the Statistics paragraph
  does not say so.
- **Zero-copy's equivalence is computed but not stated.** A 90% interval of (−2.4, 1.0) lies inside ±3
  (`RTwelveZcEquiv`). Either claim equivalence with a margin, disclosed as post hoc, or soften "the most
  accurate channels". Zero-copy is also never tested against C at k=3.

### 11. Generality. [text only, or one more model family as new runs]

The study uses one model family with thinking disabled, one task family whose state fits in context, a
linear three-agent chain, and a minimal harness. The Conclusion states this, but the Introduction's
rules and the abstract are unconditional. A second open model family (Llama or Mistral) on the crossed
design at one size would show whether the 14B Reviewer behaviour and the 8B write cost are specific to
Qwen.

### 12. Minor points

- **The Researcher prompts differ by more than wording.** §2 says the Researcher's instructions "differ
  only in wording and in where the notes go". A1-zc also moves the Researcher's instruction after the
  documents, into a second user message (`build_messages`, A1zc branch).
- **Br is a failed manipulation, not a comparison.** At 32B, Br's Writer reads no file in 100% of tasks,
  so Br's −40.2 measures a Writer answering without notes. Say so rather than "Br loses more".
- **The k=16 pipe is not the k=3 pipe.** "Qwen3-8B at sixteen" uses three Researchers, and its pipe hands
  all three outputs to the Writer.
- **Provenance.** "Nearly all others had replied without writing" is not generated by `paper_numbers.py`.
  I confirmed it from the records: 173 plain replies against 7 repeated calls. Add it to the generator.
- **One run is missing per-question scores.** `p18_first_14b` has no `alignscore.json`. This is fine, but
  Figure 3a cannot be extended to it.

## Questions for the authors

1. **The 14B Reviewer.** Why does it skip `draft.md`? Its plain replies look like fresh answers built from
   `docs/`. Does putting the draft in its prompt, as Br does for the Reviewer, close the 14B gap?
2. **The forced write.** How often does its content differ from the agent's preceding plain reply? If they
   usually match, saving the reply would be an equivalent and simpler rescue.
3. **The cap.** What is B − A1 at 8B, k=3, on the main tasks with a 4,096-token cap? Is the main run's
   9.5-point pooled gap partly truncation?
4. **The Bs0 arm.** Why is it omitted, and does it change the reading of "listed first"?
5. **Rerun agreement.** What share of tasks changed accuracy between the wording run and the crossed run in
   arms run under identical settings? A per-task flip rate is more informative than mean drift.
6. **The equivalence margin.** Was ±3 points chosen before seeing the zero-copy result?
7. **The k=8 fan-out.** Which paths clashed? If it was mostly the same default name (`notes.md`), say so.
   The rule "separate folders" is then a fix for naming collisions.

## Sentences that overclaim or do not match the code or numbers

1. Abstract: "Much of the files' accuracy cost comes with the tool protocol."
   - The term is undefined against the alternatives.
   - At 8B the cost is mainly the Researcher's tool-call write (A1w − A1r = −4.7; B − A1w = −2.9, not
     significant).
   - The Dvw contrasts in the Holm family are not reported (W2).
2. Abstract: "mostly in tasks where the harness rescued an agent". This is a post-treatment, descriptive
   split, and the main 8B run shows the opposite (9.4 on rescued tasks against 10.0 on the others) (W3).
3. "At 14B, B's drafts are about as accurate as with copying, and the loss appears at the Reviewer." The
   14B Reviewer read `draft.md` in 6% of B tasks and was rescued in 70%. The loss comes from re-answering
   without the draft (W1).
4. "The Reviewer opens it in only 15% of tasks and revises the gain away." Bt0's Reviewer read the draft in
   8% of tasks and was rescued in 95%. It did not revise anything (W1).
5. Conclusion: "the Reviewer, which opened it in only 15% of tasks, undid the Writer's gain". Same issue.
6. Conclusion: "We do not know ... why a 14B Reviewer skips notes listed first and named". It also skips
   the draft that its instruction names, in every 14B file arm, so this is not specific to the notes.
7. "The stored reply trails tool-written notes partly because later agents do not find it." At 14B the
   contrast coincides with tool-written notes saved under `docs/` (79–83%), so place, not reply versus
   tool, may drive it. This is untested (W1).
8. "At 14B, naming the path alone moves accuracy by only 0.9 points." The Writer opened the told file in
   5% of tasks against 9% untold. The manipulation did not take (W5).
9. Conclusion: "Our runs support four runtime rules: ... lead every later agent that edits the answer to
   the stored notes". At 14B, no tested intervention led the Reviewer to the notes or the draft.
10. Introduction: "From it we draw four runtime rules: ... and copy rather than share files." This is
    unconditional, though it rests on a minimal harness, one model family, and state that fits in context
    (W4, W11).
11. "On copied notes, only at 4B does the tool-call write change accuracy significantly". True only after
    Holm. At 8B and 32B the 95% intervals exclude zero (W10).
12. "On the RTX PRO 6000, the wording-run arms that the crossed runs repeat move by at most 0.9 points."
    This is the point estimate. The intervals run from −3.6 to +3.1 (W6).
13. "the pipe still differs from broadcast by −3.0 (−5.3 to −0.7, cross-run)". The documents-control run
    has no A1, and the gap lies inside the drift band (W6).
14. Conclusion: "We do not know why a tool-call write lowers fact coverage". This presents as established an
    untested point-estimate pattern from a measure with κ = 0.29 that does not hold at 14B (W7).
15. "Of B's Writer's reads, 83% go to source documents". This is a per-operation share dominated by file
    count (W8).
16. §2: "its instructions differ only in wording and in where the notes go". A1-zc also moves the
    instruction after the documents.
17. Abstract and §4: "With Qwen3-8B at three questions per task, the most accurate channels are ...
    broadcast and zero-copy". Zero-copy is not tested against C, and the computed equivalence result is not
    reported (W10).
