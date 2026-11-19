# Review (methods / statistics): "Pipes, Files, or Handles? Revisiting IPC for LLM Agent Pipelines"

## Summary

The paper compares five ways of passing results between a Researcher, a Writer and a Reviewer: broadcast (A1), broadcast with the shared history first so the prefix cache reuses it (A1-zc), a pipe (A2), shared files (B), files with an index (C), and handles (D). It uses Qwen3-8B on vLLM with HotpotQA and 2Wiki tasks of k bundled questions, 150 tasks per dataset and k. Cost is counted two ways, as tokens sent and as prefill tokens computed. The headline results at 8B, k=3: broadcast is the most accurate channel (72.3%). Zero-copy keeps that accuracy while computing 39% of broadcast's tokens. Files send 2.8-2.9x the tokens but compute 0.79x, and lose 6-10 points.

The paper decomposes the file channels' loss with several controls:
- A1w: B's Researcher, with the notes copied forward.
- Replay: A1's notes placed into every channel.
- Scope: documents also placed in the prompts of later agents (A2d, Bd).
- Fan-out: three parallel Researchers.

Sensitivity runs vary k (up to 16), KV size, concurrency, tool budget, a fourth agent, batched reads, and model size (4B-32B on an RTX PRO 6000). One post-hoc rescore covers the 32B misplaced-final-file failure.

The experimental hygiene is better than most agent papers:
- Comparisons are paired by task.
- Channel order is shuffled across servers.
- Each run gets its own `cache_salt`.
- An A/A rerun is included.
- Every number is generated from logs.

My concerns are about identification and generality, not about the 8B main table. Several causal sentences ("the tool call, not the file, shortens the notes"; "missing sources do not explain the loss, which lies in their notes"; "cache sharing explains the lost savings but not the accuracy collapse") go further than their controls allow. Several one-size effects are partly or mostly artifacts of the scoring or the harness. I checked this against the logs:
- The 4B zero-copy loss is largely unanswered final questions plus answers rejected by the length rule.
- The 32B file loss is mostly the path slip.
- 7.5% of A1w runs have empty notes because the tool call hit `max_tokens`.

## Score: 3 / 5 (weak accept; would be a clear accept if W1-W4 are fixed)
## Confidence: 4 / 5

I read `main.tex`, `numbers.tex` and the figures, and the code in `pipeline.py`, `workspace.py`, `metrics.py`, `alignfacts.py`, `rescue.py`, `factpairs.py`, `stats.py`, `analyze.py`, `paper_numbers.py`, `run.py` and `llm.py`. I recomputed the key quantities quoted below from `results_raw/*/rows.jsonl.gz` and `records.jsonl.gz`.

## Strengths

1. **A clean main design.** The tasks, model, roles and order are fixed and only the channel changes. Comparisons are paired over 150 tasks per (dataset, k). The job order is shuffled across channels and servers. There is a per-run `cache_salt`, so channels never share KV, and there were zero errored runs in any experiment I checked.
2. **Two cost measures.** Counting both tokens sent and tokens computed (from `cached_tokens`) is the right framing, and the reversal (B: 2.9x sent, 0.79x computed) is a real and useful observation.
3. **Controls that separate what a channel carries from how it carries it.** Replay, A1w, A2d/Bd and fan-out are the right kinds of control, and the replay is especially convincing. With one file named `notes.md`, B's Writer still never opens it in 24% of tasks.
4. **An A/A rerun.** It reruns A1 and B on 200 tasks. Means agree within +-2 points and the B-A1 gap reproduces (7.0 vs 7.8). That makes the cross-run comparisons credible as a noise floor.
5. **Honest qualifiers in many places.** Examples: the pipe's loss is specific to 8B, notes are not shorter at 14B, the fan-out difference-in-differences (DiD) is not significant, and the list of untested mechanisms.
6. **AlignScore checked several ways.** It is validated on synthetic pairs and cross-checked against an LLM judge and a model-free entity match, and all three agree in direction on the notes-recall gap. The disagreement on D (51% vs 94%) is disclosed.

## Weaknesses (most important first)

**W1. The writing-side claim is confounded with the Researcher's instruction text and with a token-cap failure.**
The paper says: "The tool call, not the file, shortens the notes". In `pipeline.py`, A1w gives the Researcher B's whole instruction, `OUTPUT_FILES["researcher"]` plus `DONE_RULE`, not just a tool. That instruction says:
- "The other agents cannot see your reply; they see only the shared workspace, where the source documents also are (under docs/)."
- "Save your notes there with write_file, in one or a few calls (choose the file names and how to split them)".

After each write the tool result also adds ". If you are finished, reply without calling a tool." A Researcher told that downstream agents can read the source documents has a reason to write less. So A1w vs A1 changes the output mechanism, the instruction wording, and the stop nudge all at once.

Note length is clearly sensitive to prompt placement. The A1-zc Researcher gets A1's instruction as a final user turn instead of in the system prompt. It writes notes 27% longer (1,992 vs 1,570 chars at 8B, and longer at every size: 1,662/1,377 at 4B, 1,674/1,392 at 14B, 2,037/1,465 at 32B), with higher AlignScore recall (50 vs 45; 64 vs 46 at 32B). That is the same magnitude as the "tool call" effect.

There is also a mechanical component. In 15 of 200 A1w runs (7.5%) the `write_file` call ends with `finish_reason=length` at `max_tokens=2048` and the forced write also fails, leaving empty notes. A reply-mode Researcher almost never hits the cap (0.3%), and when it does, it still delivers its truncated text. B has the same failure (5.0% empty notes in the main run, 7.0% in p02_size_8b). If those 15 runs are excluded, the A1w gap to A1 shrinks from 4.7 to about 3.6 points (69.4 vs 73.0). The notes are still shorter, with a median length ratio of 0.76.

*Fix:*
- Run an instruction-matched control (E1).
- Report empty-notes runs separately from shorter-but-present notes.
- Reword the claim to "writing through B's tool-call instruction".

**W2. The model-size generality claims rest partly on scoring and harness artifacts.**
- *4B zero-copy (-7 points).* A1-zc's `answered` rate at 4B is 93.5% vs 99.8% for A1. In 39 of 200 runs the final drops Q3 entirely. Another 6.1% of answered A1-zc questions contain the gold answer but are rejected by the `len(pred) <= len(gold)+4` rule, vs 1.8% for A1. Accuracy on answered questions is 60.1 vs 63.3. So about half of the "zero-copy costs only the 4B model" effect is completeness and verbosity, not wrong answers. Stage logs locate it at the Reviewer: drafts are equal (52.7 vs 52.7), but A1's Reviewer fixes 10.7% of questions and A1-zc's fixes 4.3%.
- *32B B/D.* `answered` is 73.3% and 69.0%. Empty drafts occur in 61 (B) and 134 (D) of 200 runs, because the Writer also writes `workspace/draft.md`. The post-hoc rescore fixes only runs with no final answer at all. It does not repair the Reviewer working without the draft, so it is a lower bound on what a path-robust harness would give. Even so, "Files trail broadcast at every size, B by 8-28 points" uses the 28. Rescored, B is about 11 points behind.
- *14B.* D has 7.2% gold-contained-but-too-long answers (A1: 1.3%) and B has 3.5%.

At 8B the length-rule rejections are balanced, about 1% per channel, so the main table is safe.

*Fix:*
- Report `answered` and accuracy-on-answered for every size.
- Add a length-rule or judge sensitivity analysis.
- Replace the rescore with a path-normalized rerun (E2).
- Qualify the 4B zero-copy sentence.

**W3. "Cache sharing explains the lost savings but not the accuracy collapse" rests on 10 tasks, and the text omits the channel that moved.**
`t08_pressure_c1/c2` use `use_tasks: 5` per dataset, so n=10. The macro `PressAccMax` (3.8 points) is the maximum over B and C only. D moves +6.2 points (bootstrap CI 0 to +15.6) at both concurrency 1 and 2, and B's CI is -3.8 to +13.8. The KV-size sweep cannot rescue the claim, because it is at k=8, where there is no collapse (B -8). No run tests a large KV cache at k=16.

*Fix:* Run k=16 at 100k KV on the full 60 tasks (E4). Until then, write "we could not detect", give the CIs, and include D.

**W4. The k=16 collapse (B -34, CI -39 to -29, n=60) is a single-budget result whose mechanisms are untested.**
- B's Reviewer hits the 12-call budget in 52% of runs, and B overall hits it in 73% (C: 32%).
- The 24-call budget was tested only at k=3, where it does not bind (14-16% hits).
- The clash analysis splits 43 vs 17 tasks, with accuracy 38% vs 41%.

The paper is right to call this "a result for this budget". But this is the most dramatic number in the abstract, and it is not decomposed.

*Fix:* E3, covering budget, no-clobber writes, and each of C's two differences.

**W5. "The loss lies in their notes" contradicts the paper's own reading control.**
§Results says: "Missing sources therefore do not explain the file channels' loss, which lies in their notes." The replay shows that with identical, clearly named notes, B and C still lose 5 points (2 to 8). The A1w control attributes about 5 points to writing. The two roughly add up to B's 10-point gap at k=3. That is a writing-plus-reading story, which is fine, but the sentence says notes only.

The decomposition also uses three different runs (main, A1w, replay) on the same 200-task subset without a joint model. A small 2x2 analysis on the shared tasks would make the "half writing, half reading" statement explicit: Researcher mode (reply vs tool) by delivery (copy vs file), using the cells A1, A1w, replay-B and B.

*Fix:* Rewrite the sentence and add the 2x2 table, with paired CIs on the shared tasks.

**W6. The mechanism differs by model size, but the paper generalizes the 8B mechanism.**
Per-size stage accuracy from the logs (draft -> final):
- *8B.* B's draft is 52.2 vs A1's 72.2, and the Reviewer recovers 12.7 points. The loss is at writing and reading.
- *14B.* B's draft is 70.8 (about the same as A1's 72.0), and the Reviewer breaks 6.8% of right answers. D shows the same pattern. The loss is at review, not at notes; B's notes are longer (1,756 chars) and state more facts (48 vs 44).
- *14B, C.* The index channel is worse than plain files (57.7 vs 66.2), because C's draft is 51.0.
- *32B, C.* The draft is 54.3 vs A1's 75.0.

So the conclusion's advice, "Files need a naming discipline, such as an index", does not hold at 14B. It also does not hold in the replay, where the index lowers notes opening (63% vs 76%).

*Fix:*
- Add a per-size stage table (no runs needed).
- Run the replay at 14B (E5).
- Scope the index recommendation to 8B/32B.

**W7. Multiple comparisons and equivalence claims.**
The paper reports about 30 main-cell comparisons, about 20 model-size comparisons, and many control comparisons, all as uncorrected 95% intervals. I applied Holm to the 30 main-cell paired t-tests (my computation):

| Channel | Paper says | Significant after Holm |
| --- | --- | --- |
| A2 | 5 of 6 settings | 4 of 6 (hotpot k=1, k=5 and 2wiki k=1 drop out) |
| B | each of 6 settings | 5 of 6 (hotpot k=1 drops out) |
| C | 2 of 6 | 2 of 6 |
| D | 4 of 6 | 4 of 6 |

Conversely, "no difference is significant" is used as evidence of equality for A1-zc, for 24 turns ("at most 3 points", no CI), for KV size ("at most 1.6"), and for the index in the replay. The right tool is an equivalence statement. The pooled k=3 A1-zc minus A1 difference is -0.8 points (CI -2.9 to +1.3); under exact match it is -1.8 (-3.8 to +0.2). That supports equivalence within a 3-point margin under the paper's accuracy metric, which is a stronger and more honest statement than "no difference is significant".

*Fix:*
- Name the primary comparisons and apply Holm to them.
- Report pooled equivalence CIs.
- Give CIs for every "at most" statement.

**W8. A1-zc is described as "only the order changes", but the Researcher's prompt differs too.**
For A1-zc the role instruction moves out of the system message into a trailing user message, for every role including the Researcher (`build_messages`). This changes Researcher behavior (W1) and is the likely cause of the 4B Reviewer dropping the last question (W2). The 8B result is robust to it, but the description should be accurate, and the 4B question in the conclusion ("why the 4B model loses with zero-copy order") can now be partly answered from the logs.

*Fix:* Describe the change accurately and run the E6 variant.

**W9. The attribution and delivery metrics are hard to interpret.**
- *Attribution.* It charges the Researcher whenever any supporting fact is missing. The paper notes that 76% of A1's correct answers also have such notes, so "Researcher missed" is mostly a base rate. Fig. 4b therefore shows the AlignScore strictness more than the stage at fault.
- *Delivery.* In file channels delivery counts facts found in source documents the Writer read: 83% of B's reads are `docs/`, and those contain the supporting sentences verbatim. So 87-94% "delivery" partly measures re-reading the sources, not receiving the notes.

*Fix:*
- Report P(wrong | notes complete) vs P(wrong | notes incomplete) per channel.
- Report delivery restricted to text read from non-`docs/` paths, which `io_ops` already logs.
- Relegate the stacked attribution to a footnote, or base it on the replay counterfactual.

**W10. "Tokens computed" omits decode, and Fig. 3 shows marginal rather than paired intervals.**
- *Decode.* File channels generate about twice the completion tokens (B: 1.6k vs 0.8k per task at 8B). A self-hosted deployment pays for decode in latency and GPU time. The conclusion's "plain files ... cost more tokens in every setting" holds only for tokens sent; B computes 0.67-0.79x at k=3 and 5.
- *Fig. 3.* Its marginal CIs overlap (for example A1-zc and C) even where the paired differences are clearly significant.
- *Fig. 4b.* It has no intervals at all, including k=16 with n=60.

*Fix:*
- Add decode tokens or GPU-seconds.
- Show paired-difference CIs.
- Add intervals to Fig. 4.

**W11. The AlignScore validation does not match the use.**
The synthetic validation (AUC 0.996) uses verbatim sentences in short contexts, while the real inputs are paraphrased notes and multi-document Writer inputs. On real pairs, kappa with the Qwen3-8B judge is 0.29. The notes-recall direction is corroborated three ways, so I do not doubt the sign. But absolute numbers such as "B's notes state 32%", "D 51%" and "13%" in Fig. 4a are threshold-dependent.

*Fix:*
- Run a threshold sweep (0.3-0.7) on the stored scores.
- Validate on about 200 human-labelled real pairs, or with a stronger judge such as Qwen3-32B (E9).
- Say how long contexts are chunked.

**W12. Cross-run controls are not flagged as such.**
A1w, scope (A2d/Bd), Bb, chain4, fan-out and turns24 are each compared against main-run arms collected in a different session with a different server mix. Some also used a single server (`t09_a1w`: only A1w jobs on one server). The A/A result covers the noise in this, but the text should say which comparisons are within-run.

*Fix:* State it per control. Where cheap, rerun the reference arm in the same session (E1, E5).

## Requested experiments (prioritized)

Run counts are pipeline runs (one task through one channel) at k=3 with 200 tasks (100 per dataset) unless noted.

**E1 (required). An instruction-matched writing control, run with the planned A1w sweep.**
- *What to run.* Two new Researcher variants, both followed by A1's Writer and Reviewer (copied notes plus documents):
  - **A1r**: B's Researcher instruction verbatim, but with no tools; the Researcher replies with its notes.
  - **A1t**: A1's instruction with only "Reply with your notes" replaced by "Save your notes with write_file". It does not mention that documents are in the workspace, and drops the "If you are finished" nudge.

  Run A1, A1w, A1r, A1t and B in the same session at 4B/8B/14B/32B. Set the Researcher's `max_tokens` to 4096 in all arms, or keep 2048 and add one 4096 arm of A1w at 8B, so truncation is separated from shortening.
- *Claim tested.* "The tool call, not the file, shortens the notes", and whether it does so at every size.
- *Runs.* New arms: 2 x 200 x 4 = 1,600. A1/A1w/B reference arms rerun in the same session: 3 x 200 x 4 = 2,400. Most arms are three-call message pipelines, so this is cheap.
- *Planned (b).* The A1w-only sweep is necessary but not sufficient. Without A1r/A1t it cannot support the causal sentence. Merge it into E1.

**E2 (required). A path-normalized harness at 32B instead of the post-hoc rescore.**
- *What to run.* Treat a leading `workspace/` (and `/workspace/`) as the root in `Workspace._path`, then rerun A1, B, C and D at 32B.
- *Why it is fair.* The logs show this is a no-op at the other sizes: zero Writer/Reviewer prefixed writes at 4B and 8B (p02), 3 D runs at 14B, and 9 of 900 D runs in the 8B main run.
- *Claim tested.* "Files trail broadcast at every size" at 32B, and the 32B notes and stage story, without the draft-path damage the rescore cannot repair.
- *Runs.* 4 x 200 = 800.
- *Planned (a).* Use the same fix for the 32B, k=8, 100k-KV run.

**E3 (strongly wanted). Decompose the k=16 collapse.**
- *What to run.* The 60 k=16 tasks, with three parallel Researchers, at the 3090-equivalent 35k KV, with these arms:
  - (i) B with 24 tool calls;
  - (ii) B with no-clobber writes (writing to a path that another agent created returns an error);
  - (iii) B plus only C's "head each file with its questions" instruction;
  - (iv) B plus only the index;
  - plus A1 and B references in the same session.
- *Claims tested.* That the collapse is a budget result. That "the race is not the whole loss". "Whether one or both of C's two differences prevent the clash" (listed as untested).
- *Runs.* 6 x 60 = 360 at k=16.

**E4 (strongly wanted; replaces the n=10 pressure test). k=16 with a large KV cache.**
- *What to run.* A1, A1-zc, A2, B, C and D at k=16 on the PRO 6000 at 100k KV, six concurrent, on all 60 tasks.
- *Claim tested.* "Cache sharing ... explains the lost savings but not the accuracy collapse" at the k where the collapse occurs.
- *Runs.* 360.

**E5 (strongly wanted). Replay at 14B, and at 32B with E2's fix.**
- *What to run.* A1's notes replayed into A1, A2, B and C, all in one session.
- *Claim tested.* Whether the 5-point reading loss generalizes. At 14B the logs put B's loss at review rather than at notes, and C is 8.5 points below B; the replay shows whether C's Writer fails to read or the Reviewer breaks answers.
- *Runs.* 4 x 200 = 800 per size; 1,600 for both.

**E6 (wanted). Zero-copy without moving the instructions out of the system prompt.**
- *What to run.* An "A1-zc-sys" arm. One shared system prompt holds all roles' instructions and the output format, so it is part of the cached prefix, and the trailing user turn says only "You are the Reviewer." Run it next to A1 and A1-zc at 4B and 8B.
- *Claim tested.* Whether the 4B loss (dropped last question, verbose answers, fewer Reviewer fixes) comes from the instruction-last placement. This would give a zero-copy recipe that is safe across sizes.
- *Runs.* 3 x 200 x 2 = 1,200, or 400 if A1 and A1-zc are reused cross-run.

**E7 (useful). A/A at 14B.**
- *What to run.* A rerun of A1, B and C at 14B.
- *Claim tested.* Whether the one-size effects (C below B at 14B; the review-stage loss) are stable, not run-to-run noise. The A/A exists only at 8B, and greedy decoding is non-deterministic: 41% of identical Researcher prompts give different outputs.
- *Runs.* 600.

**E8 (useful). A fan-out run with enough power.**
- *What to run.* Extend from 100 to 300 tasks for A1, B and D.
- *Claim tested.* The DiD (-4, CI -10 to +2) is underpowered for an effect of that size; 300 tasks would give about +-3.5.
- *Runs.* About 600.

**E9 (cheap). Judge validation on real pairs.**
- *What to run.* Score the 864-fact `judge_cross` sample with Qwen3-32B as judge, plus about 200 human-labelled pairs, and calibrate AlignScore's threshold on paraphrased notes.
- *Claim tested.* The absolute fact-recall and delivery numbers.
- *Runs.* About 1.3k short judge calls.

**Not needed / lower priority.** Planned (a), 32B at k=8 with 100k KV, is useful only if the paper reports the 32B corner: the `PCorner*` and `PRescueCorner*` macros are computed but never used in `main.tex`. As it stands it tests a cost claim the text does not make. I would run it after E1-E5, with E2's fix, or drop it and the corner together.

## Analyses that need no new runs

1. **Holm-corrected significance counts** for the primary comparisons (my numbers are in W7), and pooled equivalence CIs for A1-zc: accuracy -0.8 (-2.9, +1.3) and exact match -1.8 (-3.8, +0.2) at k=3.
2. **`answered` and accuracy-on-answered per channel and size.** 4B A1-zc answered is 93.5%, with 39/200 runs missing Q3. 32B B/D answered is 73%/69%.
3. **Sensitivity of the answer-length rule.** Count the questions where the gold answer is contained but rejected for length (8B: about 1% in every channel; 4B A1-zc 6.1%; 14B D 7.2%, B 3.5%). Rescore these with a judge or a relaxed rule as a sensitivity check.

   *Should the scoring change?* Keep the current metric as primary at 8B, where it is balanced across channels. At the other sizes, report the relaxed or judge variant beside it, because the error rate of the rule depends on the channel there.
4. **The 32B rescore.** Keep the measured number as "harness outcome", but make channel-quality statements at 32B from the path-robust number. Do not quote "8-28 points". Ideally, E2 replaces the rescore entirely, since the rescore cannot repair runs where the draft was misplaced.
5. **Split A1w and B Researcher failures** into (a) empty notes after a `finish_reason=length` tool call (A1w 7.5%, B 5-7% at 8B) and (b) shorter notes that are present. The A1w-A1 gap without (a) is about 3.6 points.
6. **A1-zc Researcher note length and recall** at every size (27-39% longer, higher recall), plus a sentence correcting "only the order changes".
7. **A per-size stage table**: draft accuracy, Reviewer fixed and Reviewer broke, for each channel. It localizes the 4B zero-copy loss to the Reviewer and the 14B file loss to review, and it shows C's Writer failing at 14B and 32B.
8. **The pressure test.** Report D (+6.2, CI 0 to +15.6) and all CIs, or drop the accuracy half of the claim.
9. **A 2x2 decomposition** on the shared 200 tasks: Researcher mode (reply vs tool) by delivery (copy vs file), using the cells A1, A1w, replay-B and B. Use paired CIs and report the interaction.
10. **Delivery restricted to notes files** (non-`docs/` reads), separated from re-reading the sources.
11. **Conditional error rates** P(wrong | notes complete) and P(wrong | notes incomplete) per channel, to replace or support Fig. 4b.
12. **An AlignScore threshold sweep** (0.3-0.7) for Fig. 4a and the delivery numbers, plus the chunking procedure for long Writer inputs.
13. **Decode tokens and GPU-seconds per channel**, next to tokens computed.
14. **Figures.** Paired-difference intervals in Fig. 3, and CIs in Fig. 4b (k=16: B -33.9 (-38.8, -29.0); C -5.1 (-8.6, -1.9); D -11.4 (-15.2, -7.7); A2 -0.5 (-3.3, +1.9)).
15. **Within-run vs cross-run**: a table listing, for each control, its n, its reference run, and whether the comparison is within-run.

## Questions for the authors

1. Why does B's Researcher instruction say the source documents are in the workspace? Was any variant tried without that sentence, or without "one or a few calls"?
2. What do the `finish_reason=length` Researcher calls in B and A1w contain: degenerate repetition inside the JSON argument, or genuinely long notes? Would `max_tokens=4096` remove the empty-notes runs?
3. How does AlignScore handle Writer inputs of several thousand tokens: chunking with a max over chunks, or truncation?
4. The PRO 6000 configs say `flags: see scripts/queue_pro6000.sh` with no `vllm_src`. Were the vLLM version, the tool parser (hermes) and the chat template identical to the 3090 runs? The 8B check (p02_size_8b vs t07_main) suggests yes; please state it.
5. At 14B, why is C's draft accuracy 51% when B's is 71%? Does C's Writer read `index.md` and then stop, or does it read the documents?
6. In the replay, why does the presence of the index lower notes opening (63% vs 76%)? Is `notes.md` listed first under "Agent files"?
7. For the fourth-agent result, the pipe's Fact-checker is told to check "against the Researcher's facts and the documents", which it does not have. Did you check whether the gain comes from the Reviewer receiving a reformatted draft?

## Sentences that overclaim or mismatch the code or numbers

1. Abstract: "Notes written through a tool call are \nNotesShorter{}\% shorter, and readers without an index skip them."
   - 27% holds at 8B only; at 14B B's notes are longer (1,756 vs 1,392 chars).
   - In the replay, readers *with* an index open the notes less (63% vs 76%).
2. §Results: "Given the same questions and documents, the Researcher writes \nNotesShorter{}\% shorter notes ..."
   - The user message is the same, but the system instructions differ (W1).
3. §Results heading and text: "The tool call, not the file, shortens the notes." / "Writing the result as a tool-call argument therefore costs accuracy by itself."
   - Confounded with the instruction text and with 7.5% token-cap truncations (W1).
4. §Channels, A1-zc: "The same content as A1 ... Only the order changes."
   - The instruction moves from the system role to the last user turn, and the Researcher's output changes (W8).
5. §Results: "Missing sources therefore do not explain the file channels' loss, which lies in their notes."
   - The replay shows a 5-point loss with identical notes (W5).
6. §Sensitivity: "Cache sharing among concurrent runs explains the lost savings but not the accuracy collapse ... accuracy changes by at most \nPressAccMax points."
   - n=10.
   - `PressAccMax` excludes D, which moves +6.2.
   - B's CI reaches +13.8 (W3).
7. §Sensitivity, model size: "Files trail broadcast at every size, B by \nPSizeFourteenGapB--\nPSizeThirtyTwoGapB points."
   - The 28 at 32B is mostly the path slip (rescored, about 11).
8. "Zero-copy ordering costs only the 4B model (\nPSizeFourGapAZc points ...)."
   - About half is the unanswered last question and length-rule rejections (W2).
9. "Shorter notes are not universal. At 4B, 8B, and 32B file channels' notes state \nPSizeFileNotesMin--\nPSizeFileNotesMax\% of the supporting facts ..."
   - This conflates length with recall. At 4B, C's notes are longer than A1's (1,662 vs 1,377 chars) but state fewer facts.
10. Conclusion: "Files need a naming discipline, such as an index, and a model that handles tools."
    - At 14B, C trails B (57.7 vs 66.2), and in the replay the index does not help.
11. Conclusion: "Plain files lost accuracy and cost more tokens in every setting."
    - True for tokens sent only. B computes 0.67-0.79x broadcast at k=3 and 5, which the same paragraph says.
12. §Results: "... significantly in \nGapATwoSigWord of six settings" (five).
    - Four after Holm over the 30 main-cell tests.
13. §Methodology: "We report 95\% bootstrap intervals ... unless the text names another reference."
    - Several claims have no interval: tool budget "at most 3", KV "at most 1.6", fourth agent "others move at most 1 point", the pressure test, and the k=16 gaps in the text and Fig. 4.
14. Fig. 3 caption: "zero-copy broadcast keeps that accuracy at a pipe's cost."
    - This is 8B only; at 4B it costs 7 points. Say so in the caption, or point to §Sensitivity.
