# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (methods and statistics)

## Summary

The paper compares how results pass between three LLM agents (Researcher, Writer, Reviewer) on bundled
HotpotQA/2Wiki questions, with Qwen3 models served by vLLM. There are five channels: broadcast (A1),
zero-copy broadcast (A1-zc), pipe (A2), shared files (B), and files with an index (C). The main run uses
Qwen3-8B on RTX 3090s with a 35k-token KV cache. Later runs use RTX PRO 6000s and add:
- a 2x2 "crossed" design at four sizes: the Researcher writes notes as a reply or through a tool call (A1r/A1w
  vs Bs/B), and the notes are then copied forward or reached through files;
- fan-out controls at k=8 and k=16: per-Researcher folders (Bf), a write guard (Bn), and a heading rule (Bh);
- a replay control, cache-size sweeps, serving-time runs, and rerun drift checks.

The headline claims are:
1. Zero-copy cuts prefill by about 61% at k=3 with a 95% interval for its accuracy difference of -2.9 to 1.4.
2. File channels send 1.8-4.8x more tokens, though the prefix cache absorbs most of them.
3. Delivering the Researcher's reply through files costs 20-34 points at three of four sizes after Holm
   correction, more than writing the notes through a tool call.
4. At k=8, parallel Researchers sharing one folder cost B 21.2 points, and per-Researcher folders recover 19.8.

All numbers come from a script (`paper_numbers.py`). I re-derived several of them from `results_raw/`, and the
macros match the code. The 8B prefill and cost claims and the fan-out result look solid. The main problems are
in the crossed design that carries the second headline claim:
- what the "delivery" factor actually changes;
- an information asymmetry in the stored-reply arm (Bs);
- a 4B cell in which every file task was rescued by the harness;
- arms that were run but are not reported.

## Score and confidence

- **Score: 3/5** (borderline; publishable at a workshop if the delivery claim is rescoped)
- **Confidence: 4/5** (I read the pipeline, workspace, metrics and number code and recomputed key quantities from
  the raw records)

## Strengths

1. **Paired, interleaved design.** Every channel runs the same tasks. Jobs are shuffled across channels and task
   sizes. Each pipeline gets its own `cache_salt` (`SaltedClient` with `time_ns`), so no KV leaks across tasks or
   arms.
2. **Reproducible numbers.** All numbers are generated from raw records by one script (`numbers.tex`), and the
   setup constants are read from the configs. I found no hand-edited values.
3. **Drift and nondeterminism are measured, not assumed:**
   - the main-run A1/B rerun (+/-2.2);
   - crossed vs wording-run repeats on PRO 6000 (max 0.9 points);
   - identical-prompt Researchers produce identical notes in only 59% of tasks.
4. **Holm-corrected sign-flip permutation tests on the 2x2.** The test is valid under dependence, and the paper
   reports both corrected and uncorrected counts. Intervals are paired bootstraps over tasks, and the Figure 2
   caption correctly says its whiskers are marginal intervals, not paired ones.
5. **Useful mechanism controls:**
   - replayed notes (t09_replay);
   - documents in later prompts (A2d/Bd);
   - the zero-copy replay at 4B;
   - cache-size sweeps (p01);
   - a write guard and a heading rule separated from C's index.
6. **Fan-out isolated cleanly.** The paper notices that k=16 changes both payload and writer count, and separates
   them at k=8. One and three Researchers run back to back on the same server, broadcast serves as an in-run drift
   reference (-0.9, CI -3.9 to 2.0), and the clash rate (99%) gives a concrete mechanism.
7. **Careful serving-time protocol.** One channel at a time on the same GPU (GPU 3 for all p06/p11 runs), run
   order shuffled with a recorded seed, and vLLM's prefill and decode counters reported. This keeps the paper from
   claiming that prefill savings shorten batches (decode is 96% of time). The median-task ratio of 0.82 at 32
   concurrent tasks replicates: I get paired per-task median ratios of 0.84 and 0.83 in the two runs.
8. **Caveats are mostly stated honestly:**
   - AlignScore's weak agreement with the judge (kappa = 0.29);
   - the rescue rates;
   - the confounds of the stored file;
   - the untested moved instruction;
   - single model family.

## Weaknesses (most important first)

1. **The "delivery" factor of the 2x2 is not what the text says it is, so the headline 20-34-point
   "delivery" cost is mislabeled.**
   - **What the paper says.** The factor is "how [notes] reach the Writer (copied, or as files)".
   - **What the code does.** In `build_messages`, the copied arms (A1r, A1w) are full broadcast. The Writer and
     the Reviewer get all ~30 documents, the notes, and (for the Reviewer) the draft in their prompts, and they
     answer in a reply with no tool loop.
   - In the file arms (Bs, B), the Writer and Reviewer get only the questions. They must find the documents, the
     notes and the draft with tools under a 12-call budget, and must emit outputs through `write_file`. Missing
     outputs are rescued by a forced call.
   - So the factor bundles six things: notes delivery, document delivery, draft delivery, output-by-tool, the
     tool budget, and different Writer/Reviewer instructions. The only document control (Bd, +0.5) was run at 8B
     on the main run, cross-run, where the delivery effects are smallest.
   - **Fix (text/analysis only):** rename the factor (e.g., "downstream channel: broadcast vs file tools"). State
     in Section 3 that the Writer and Reviewer in the copied arms also receive the documents and the draft.
     Restate the abstract's claim accordingly.
   - **Fix (needs new runs):** add an arm, at least at 14B and 32B, that delivers only the notes through a file
     while copying the documents and the draft and taking the outputs as replies. Even better, run the full Bd
     control inside the crossed run.

2. **The stored-reply arm (Bs) withholds information that the harness has, and it drives the headline
   number.**
   - The Bs Researcher is told "the system saves it as notes.md". The Bs Writer gets B's generic instruction,
     "Find the notes with list_files", and is never told the path.
   - By contrast, the Reviewer instruction does name the previous output ("The latest draft (draft.md)"), so the
     harness names files when it knows them, except here.
   - In the raw records, the 14B Bs Writer lists the workspace (31 entries, with notes.md sorted after all 30
     `docs/` files) and then reads source documents. It opens notes.md in 9% of tasks, and 100% of Bs tasks need
     the rescue.
   - The 30-point 14B "Copy->files, reply" effect, and therefore the abstract's upper range and the claim "more
     than the tool-call write", rests largely on this design choice. A real system that stores a reply as a file
     would tell the reader where it is.
   - The paper lists name, number and location as confounds, but not the asymmetry with the Reviewer's
     instruction.
   - **Fix (needs new runs):** rerun Bs at four sizes x 150 tasks with the Writer told "the Researcher's notes are
     in notes.md". Report both variants. If the gap shrinks, the headline should use B (tool-written files),
     whose delivery effect is 8-22.
   - **Fix (text only):** until that run exists, lead the abstract with the B column, not the Bs column.

3. **The 4B cells of the file arms measure a tool-protocol failure rather than a channel, yet they set the
   upper end of the headline range.**
   - At 4B, 150/150 Writers in both file arms were force-written, and the Writer opened the notes in only 5% (Bs)
     and 13% (B) of tasks.
   - The -34.2 "delivery" effect at 4B is therefore "a 4B Writer that cannot drive the tools, rescued by the
     harness". The paper says "the accuracy of these arms rests on the rescue". Even so, the abstract and the
     conclusion fold 4B into "20-34 points at three sizes".
   - **Fix (text/analysis only):** report the delivery range without 4B (14B/32B: 20-30 for Bs, 8-9 for B). Flag
     the 4B file cells in Table 1 as rescue-only, and drop "34" from the abstract.
   - **Fix (needs new runs, cheap):** add a closed-book floor (Writer and Reviewer see only the questions, no
     tools) at each size, so readers can tell whether 4B file-arm accuracy (34-37%) is above answering from priors.

4. **Arms that were run are not reported.** The paper says "We compare five channels". However:
   - **D (handles).** It was run in the main run (all six settings), the timing runs, the size runs and k=8/16.
     At k=3 it scores 65.1%, between B and C.
   - **The p14 "read" runs with Br.** The Writer and Reviewer read through tools but answer by reply. Br is
     22-40 points below A1w at all sizes and 12-31 points below B at 8B-32B. At 32B, the Br Writer calls
     `list_files` once and replies without opening any file in 150/150 tasks (`REightReplyThirtyTwoOpen` = 0).
   - Br matters for interpretation. It shows that file-arm accuracy depends heavily on how the harness ends the
     tool loop: the `write_file` requirement plus the rescue keeps agents reading. That is exactly the harness
     sensitivity that weakens a general recommendation.
   - D matters because the introduction motivates files with research agents that "pass references", which is
     what D is.
   - **Fix (text/analysis only):** list every arm run on these tasks (D, Br, Bb, A2d/Bd) with a one-line result,
     either in an appendix or in a table note, and say why each was excluded from the main comparison.

5. **The rescue is analyzed with the wrong counterfactual.**
   - "Scoring every rescued task as wrong cuts B's accuracy from 62.8% to 18.0%" is an uninformative bound. In the
     main run, rescued and non-rescued B tasks have nearly the same accuracy (62.5% vs 63.5%, n = 215/85), and
     the same holds for C (65.8% vs 67.3%). So at 8B the rescue mostly transcribes a reply into the file and does
     not change the comparison.
   - At 14B and 32B, rescued B tasks are 11-16 points less accurate than non-rescued ones (14B: 62.9 vs 74.3;
     32B: 55.7 vs 71.3). There the rescue correlates with failure.
   - At 32B, the final answers written by a forced Reviewer differ from its plain reply in most rescues, often
     because the reply is empty after a repeated-call stop. In that case the rescue is not a neutral
     transcription.
   - A second fallback is undocumented: `stage["final"] = reviewer reply` when final.md is still missing. It is
     rarely used (0-3 tasks per run).
   - **Fix (text/analysis only):** replace the strict bound with:
     - accuracy split by rescued vs not rescued, per arm and size;
     - the rescue cause (budget exhausted vs plain reply vs repeat-stop);
     - a "reply-scored" variant that scores the agent's plain reply where one exists;
     - a mention of the final-from-reply fallback.

6. **The tool budget binds at k=3, and it is tested only at k=16.**
   - In the main run, 34% of B and C tasks hit the 12-call limit. Reviewers hit it in 86/300 (B) and 101/300
     (C) tasks at k=3.
   - The 24-call test is cross-run, at k=16 only, against a different run's gap.
   - At k=3, part of B's 7.8-point deficit may be budget, which a deployment would simply raise.
   - The B Researcher also hits the 2,048-token cap in 22/300 main-run tasks, against 1/300 for A1. That
     asymmetric truncation feeds the "notes in files are 27% shorter" observation.
   - **Fix (needs new runs):** run B and C at 24 calls (and a 4,096-token cap) on the 200-task k=3 subset, in the
     same run as A1.
   - **Fix (text):** report the budget-hit rate at k=3 and the per-channel cap-truncation rate.

7. **"Interaction (not tested)" hides the main finding of the 2x2, and "costs more than" is never tested.**
   - The interaction intervals exclude zero at 4B (7.1 to 17.8), 14B (15.3 to 26.7) and 32B (6.7 to 17.6). So
     the "delivery" cost depends strongly on how the notes were written, and the decomposition into "delivery"
     vs "write" is not additive. The paper's own argument for the 2x2 (avoiding order-dependence) implies this.
   - The abstract's comparative claim, delivery "more than" the tool write, compares magnitudes of two simple
     effects without a test of their difference.
   - **Fix (text/analysis only):** test the interaction (it is one more permutation test; add it to the Holm
     family or report it separately). Test the difference of the compared effects, or drop "more than" and
     report the cells.

8. **The confirmatory tests reuse the exploratory tasks.**
   - The crossed runs use the same 150 tasks (seed 2, 75 per dataset) as the wording run (p10) and the read run
     (p14). Those earlier runs motivated the 2x2 and the Holm family, and the drift check confirms near-identical
     arm outcomes. The 16-test Holm family is therefore confirmatory only nominally: it guards against
     multiplicity within the table, not against choosing the analysis after seeing the same tasks.
   - Elsewhere the paper leads with uncorrected counts, e.g. "lowers accuracy at three sizes" before "at one after
     the correction", and the post-hoc 2Wiki/HotpotQA split at 8B.
   - **Fix (needs new runs):** rerun the four 2x2 arms on a fresh task draw (a new seed) at 14B and 32B at least.
   - **Fix (text):** state that the family was fixed after the earlier runs, and lead with the corrected counts.

9. **The validity of fact coverage and of "notes opened" is weaker than the prose implies.**
   - **AlignScore.** It is validated only on synthetic perturbations (AUC 0.996). On real notes it agrees with a
     Qwen3-8B judge at kappa = 0.29, and that judge is from the same model family and is not itself validated.
     The paper still uses fact coverage causally ("Where the effect appears, the notes state fewer supporting
     facts", and "drops facts" in the conclusion).
   - **"Notes opened".** `writer_opened_notes` is a binary any-read of any Researcher-authored file:
     - a one-line partial read counts;
     - it ignores the Reviewer;
     - in B it counts reading any one of three per-question files;
     - it says nothing about whether the content was used.
     For B at 14B, 385 of the Researcher's writes went under `docs/` (e.g. `docs/Q1_facts.txt`). Authorship-based
     detection handles this correctly, but it shows how much file layouts vary across sizes.
   - **Accuracy.** The lenient containment rule (gold inside a prediction at most four words longer) is not
     validated. EM is reported for only a few claims.
   - **Fix (text/analysis only):** report the 2x2 and the main gaps under EM as well. Define "opened" as the share
     of notes characters read by the Writer, and report the Reviewer's reads too.
   - **Fix (needs annotation, not runs):** human-label about 200 fact/notes pairs to calibrate AlignScore and the
     judge, or stop using fact coverage as the mechanism in the conclusion.

10. **Some sample sizes are small, some comparisons are cross-run, and an "equivalence" claim has no margin.**
    - Zero-copy "stays close" to broadcast with an interval of -2.9 to 1.4 but no pre-stated margin. A TOST with
      an explicit margin (e.g., +/-3 points) would make the claim testable.
    - The k=16 repairs use 60 tasks (Bh on 59). "About half or more" of a 30.4-point gap is a ratio whose interval
      (guard: roughly 32-67%) is not reported.
    - One vs three Researchers at k=8 are two separate runs (p15_k8_one, p15_k8_three), and Bf vs
      one-Researcher B (-1.5) is cross-run, but neither is labeled cross-run, contrary to the paper's own rule.
      The A1 reference helps, but the label is missing.
    - In the main run, the channels of one task are dispatched round-robin to three different RTX 3090 servers
      (`clients[i % len(clients)]`), so pairs are cross-server. That probably does not matter for accuracy, but
      it affects per-task prefill through each server's cache pressure.
    - **Fix (text/analysis only):**
      - add a TOST for zero-copy;
      - report a bootstrap interval for the recovered fractions;
      - label the p15 comparisons cross-run;
      - note the per-server dispatch.

11. **The serving-time comparison mixes the layout's mechanics with changed model behavior.**
    - Zero-copy agents generate 1.2-1.25x more tokens, so "run takes 1.09x" and "batch 1.00x" fold a behavioral
      change into a systems measurement.
    - "Per-task latency under load" is supported at a single load level (32 tasks). At 6 concurrent tasks the
      median ratio is 0.99 (`RTenMedAZc`, computed but not reported).
    - **Fix (needs new runs):** replay recorded completions (or fix the output lengths) under both layouts to
      isolate the prefill effect, and sweep the concurrency (6/16/32).
    - **Fix (text):** report the 0.99 at 6 concurrent tasks next to the 0.82.

12. **The generality is narrow, and the recommendations read broader than the evidence.**
    - The evidence covers one model family, short-answer multi-hop QA with about 30 short paragraphs that fit in
      the prompt, a three-tool interface with no search, a 12-call budget, and a harness whose stop and rescue
      rules visibly change outcomes (Br, weakness 4).
    - File channels are designed for state that does not fit in the prompt, and this setting favors copying by
      construction.
    - "Agents should copy results forward as replies" is scoped to Qwen3 and the tested tools, but not to "state
      fits in the context" or "this harness".
    - **Fix (text only):** add both qualifiers to the abstract and conclusion recommendations.
    - **Fix (needs new runs, optional):** one non-Qwen model at a single size on the 2x2 would strengthen the
      claim considerably.

## Questions for the authors

1. Why is the Bs Writer not told the path of the stored notes when the Reviewer is told `draft.md`? What happens
   to the 14B and 32B Bs gaps when it is?
2. Why were D (handles) and Br (read with tools, reply output) dropped? Br's 0% notes-opened rate at 32B suggests
   that file-arm accuracy depends mainly on the harness's stopping rule. How do you reconcile that with a general
   recommendation?
3. In the main run, what is the accuracy of B and C restricted to tasks where no agent hit the 12-call limit? What
   does B score at k=3 with 24 calls in the same run as A1?
4. Was the 16-effect Holm family specified before the p16 runs? Have the 2x2 arms been run on any task draw other
   than seed 2?
5. Is the main-run B deficit explained by the token cap? (22/300 B Researcher calls truncated at 2,048, against
   1/300 for A1.)
6. What is the closed-book accuracy of each Qwen3 size on these tasks (questions only)? Several file cells (4B;
   Bs at 14B) may be near it.
7. Under EM rather than the lenient rule, do the zero-copy and pipe gaps keep their ordering? The 2x2 effects
   appear to.
8. What is the bootstrap interval of the "recovered" fractions at k=16 (guard 15.1/30.4, heading 18.1/30.4)?

## Sentences that overclaim or mismatch the code or numbers

1. Abstract: *"delivering the Researcher's reply through files instead of copying it costs 20--34 accuracy points
   at three sizes after Holm correction, more than writing copied notes through a tool call"*
   - "Delivering through files" also moves the documents and the draft out of the prompt and adds tool-call
     outputs and the rescue (weakness 1).
   - The 34 is the 4B cell, where every file task was rescued (weakness 3).
   - The Bs Writer is never told where the notes are (weakness 2).
   - "More than" is not tested (weakness 7).
2. Abstract: *"With Qwen3-8B, copying the whole conversation (broadcast) is the most accurate channel."*
   - Zero-copy, which also copies the whole conversation, is statistically tied at k=3 (-0.8, -2.9 to 1.4).
   - Its point estimate is above broadcast's in three of six settings (2Wiki k=1, HotpotQA k=3 and k=5).
   - C is above broadcast at 2Wiki k=1 (+1.3).
   - The claim holds for the pooled point estimate at k=3, not as a ranking.
3. Section 3, Runs: *"The crossed runs ... cross how notes are written (a reply or a tool call) with how they
   reach the Writer (copied, or as files ...)"*
   - In the code, the copied arms also copy the documents and the draft to the Writer and Reviewer. The file arms
     also move the documents and the draft into the workspace and require `write_file` outputs.
4. Introduction: *"at three of four model sizes, delivering notes through files costs more accuracy than writing
   them through a tool call."* This has the same mislabeling as item 1, and the interaction is significant
   (weakness 7).
5. Section 4: *"We compare five channels on two multi-hop QA benchmarks"* (Introduction). A sixth channel (D)
   was run in the same main run and in the size, timing and scaling runs, and the Br variant was run at four
   sizes. Neither is mentioned.
6. Section 3: *"Scoring every rescued task as wrong cuts B's accuracy from 62.8% to 18.0%"*
   - The numbers are correct, but the implication is misleading. Rescued B tasks are as accurate as non-rescued
     ones at 8B (62.5% vs 63.5%).
   - The second fallback (the final answer taken from the Reviewer's reply) is not mentioned.
7. Section 4: *"Zero-copy thus pays off where prefill is billed and in per-task latency under load."* This is
   shown at one load level (32 tasks, 2 runs). At 6 concurrent tasks the median-task ratio is 0.99 (computed, not
   reported).
8. Section 4: *"Where the effect appears, the notes state fewer supporting facts by AlignScore"* and the
   conclusion's *"why writing through a tool call drops facts"*. These rest on a measure with kappa = 0.29 against
   an unvalidated same-family judge, and the conclusion presents the fact drop as established.
9. Section 5 heading: *"When work fans out, parallel writers sharing one folder cause most of B's loss."*
   - The decomposition was done at k=8. At k=16, where the heading's "B's loss" (33.9) is reported, separate
     folders were not tested.
   - The one- vs three-Researcher comparison is between two separate runs but is not labeled cross-run.
10. Section 5: *"against B's 33.9-point gap in an earlier RTX PRO 6000 run on these tasks"*. This is correct (the
    p07_k16_kv100k run), but the main-run (RTX 3090) k=16 gap two paragraphs earlier is also 33.9. Readers will
    assume they are the same number from the same run. Say which run each comes from.
11. Table 1 caption: *"Except at 8B, delivery through files costs more accuracy than the tool-call write."* No
    test of this comparison is reported, and the "Interaction (not tested)" row shows that the delivery cost
    itself depends on the write mode.
12. Conclusion: *"With Qwen3 models and tool-call file access as tested, agents should copy results forward as
    replies."* It should add "when the shared state fits in the context" and "under this harness's stop and
    rescue rules", given the Br result and the 12-call budget binding at k=3.
