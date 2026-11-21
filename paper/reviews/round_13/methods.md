# Review: "Messages or Files? Revisiting IPC for LLM Agent Pipelines" (methods and statistics)

## Summary

The paper compares inter-agent channels in a fixed Researcher-Writer-Reviewer pipeline (Qwen3 on vLLM,
HotpotQA and 2Wiki, k = 1-16 questions per task). The channels are broadcast (A1), zero-copy broadcast
(A1-zc), pipe (A2), shared files (B), and files with an index (C). The paper makes four claims. (1) Ranking
channels by prefill gives a different order than ranking them by tokens sent, and zero-copy cuts
broadcast's prefill by 61% at k = 3 with an accuracy difference of -2.9 to +1.4 points. (2) In a 2x2
"crossed" design (how notes are written x how later agents receive inputs), moving later agents to files
costs 8-22 points on tool-written notes at 4B, 14B, and 32B (Holm-corrected). (3) A "told" run shows that
naming `notes.md` rescues the stored reply at 32B but not at 14B. (4) At k = 8, separate folders for
parallel Researchers recover the fan-out loss. I re-derived most of the reported numbers from
`paper_numbers.py` and the raw records. They match the text. The paper is unusually open about post-hoc
choices, cross-run comparisons, and harness limits. My main concerns are about what the crossed-design
effects mean, not about whether they are computed correctly. The "how notes are written" factor is
confounded with how easy the notes are to find (their name, their location, and their position in the file
listing). The headline magnitude depends on the harness rescue. Two variants that were run (Br and D) are
left out even though they bear on the mechanism.

**Score: 3 / 5** (borderline accept for a workshop: careful and honest, but the mechanism claims go beyond
what the controls show)
**Confidence: 4 / 5**

## Strengths

1. The comparisons are paired by task with task-level bootstrap intervals, so question clustering within
   a task is handled. Channels are interleaved within a run, and per-pipeline `cache_salt` prevents KV
   leaking across conditions.
2. The 2x2 crossed design runs in one interleaved run per size. Simple effects, the interaction, and
   "Dvw" are tested with sign-flip permutation tests, Holm-corrected. The paper states that family 1 was
   chosen after earlier runs and that family 2 is post hoc. All macros are generated from raw records
   (`paper_numbers.py`), and I could reproduce them.
3. Several controls address specific confounds: wording (A1r vs A1), documents in later prompts, replaying
   broadcast's notes, told path (Bt), write guard (Bn), heading rule (Bh), and per-Researcher folders (Bf).
4. Drift is checked: a 200-task rerun on the RTX 3090s, and repeated arms on the PRO 6000 (p10 vs p16,
   at most 0.9 points). The paper also says what it did not measure (drift across GPUs or token caps).
5. Prefill is measured from vLLM's per-request `cached_tokens` rather than modeled. The serving-time runs
   are repeated (three runs at six tasks at a time, two at 32), and their spread is small (A1-zc run-time
   ratio 1.08-1.10; c32 median ratios 0.83 and 0.81).
6. Accuracy is robust to the lenient matcher. I recomputed the crossed effects with exact match, and they
   keep their sign and significance (for example, 14B B-A1w is -8.4 EM vs -8.9 acc; 32B is -7.3 vs -8.2).
   Answer lengths are similar across arms, and where they differ, the file arms are longer, which the
   containment rule would favor.

## Weaknesses (most important first)

### W1. The "how notes are written" factor is confounded with whether later agents can find the notes. The interaction and "the cost depends on how notes are written" are not identified. (text/analysis only, plus one cheap run)

In Bs (stored reply), the notes sit at the root as `notes.md`, and the Writer is not told this.
`list_files` sorts paths lexicographically and shows no authors (`workspace.py: files()`), so `notes.md`
is listed after all ~30 `docs/d0NN_*` files and `draft.md`. In B (tool-written), the Researcher picks
self-describing names. At 14B, 79% of Researchers write `docs/Q1_facts.txt`, `docs/Q2_facts.txt`, and so
on. Because uppercase `Q` sorts before `d`, these files appear at the very top of the listing, inside the
folder the Writer reads anyway. The told run confirms that findability drives the 32B result: told, the
Writer opens notes 86% vs 26%, and accuracy rises by 14.2 points. At 14B, the pointer does nothing (the
Writer opens notes 5% told vs 9% untold). The listing-order explanation fits that pattern better than
"writing modality" does.

So row 4 of Table 1 and the significant interaction (12.2/21.1/12.2 at 4B/14B/32B) measure "Researcher-chosen
names and locations vs a fixed, unannounced root file". They do not measure reply vs tool-call writing.

- Fix (text): rename the factor or the claim. State plainly that Reply→tool in the file channel bundles
  writing modality with file name and location. Drop "the cost depends on how notes are written" from the
  Table 1 caption and the Conclusion, or qualify it as "where and under what name notes end up".
- Fix (cheap run, needs new runs): one 14B run of Bs with the stored file named so it sorts first (for
  example `00_notes.md` or `docs/00_notes.md`), or with `list_files` listing agent-written files first.
  This would test the placement hypothesis the paper says it did not test.

### W2. The headline file-channel cost rests mostly on the rescue and on tasks the harness had to repair. Its locus also differs by size, so the Writer-opens-notes story explains only part of it. (text/analysis only)

At 4B, 100% of file-arm tasks were rescued, and the Writer opened tool-written notes in only 13% of
tasks. The "22" at the top of the abstract's "8-22 points" is therefore a 4B harness-regime number. At 14B
and 32B, most of the cost sits in rescued tasks (11.3 and 15.1 points vs 1.0 and 3.1). "Rescued" is a
post-treatment subset, so this split is descriptive only. My stage-wise recomputation from the raw records
(draft vs final accuracy) shows the cost arises at different stages at different sizes:

| Size | A1w draft → final | B draft → final | Where B loses |
| --- | --- | --- | --- |
| 14B | 73.8 → 74.4 | 71.6 → 65.6 | Reviewer stage |
| 32B | 71.1 → 72.9 | 57.1 → 64.7 | Writer stage |

At 14B, B's Writer opens tool-written notes in 99% of tasks. Of the B tasks whose Reviewer replied and was
rescued (104), final.md scores 63.1 while their drafts score 69.2, so the Reviewer turns right answers
wrong. The rescue's forced write itself does not degrade answers: final.md vs reply is 63.1 vs 61.5. At
32B, 14% of B drafts have no parseable answers (98% for A1w).

- Fix: report the headline as "8-9 points at 14B and 32B" and give 4B separately as "with every
  file-channel task rescued". Add a stage-wise attribution row (draft and final accuracy per arm) to Table 1
  or a footnote. Say which agent loses the accuracy at each size.

### W3. Selective reporting: two variants that were run and bear on the mechanism are omitted. (text/analysis only)

The paper says it ran but does not report a handoff channel (D) and "a variant of B whose Writer and
Reviewer reply instead of writing files" (Br, `p14_read_*`). Br is the natural control for separating
input access from output-by-tool-call and the rescue, which W2 shows matter. Its results are large and
informative. I computed paired Br - A1w accuracy from the raw records:

| Size | Br - A1w (points) |
| --- | --- |
| 4B | -25.6 |
| 8B | -24.0 |
| 14B | -22.2 |
| 32B | -40.2 |

At 32B, the Br Writer calls `list_files` once and then replies without reading anything (0% opened notes).
When nothing forces agents to stay in the tool loop, they stop reading.

The same runs also replicate the B - A1w contrast a third time (-23.1, -4.9, -10.0, -9.1). With p10 and
p16, that gives three runs per size. At 8B, the three estimates are -1.6, -2.9, and -4.9, a stable small
effect that the paper reports only as "not Holm-significant". D trails broadcast in four of six settings
and is consistent with the conclusion. Omitting it while the Introduction motivates files with
reference-passing production systems is still a gap.

- Fix: add two sentences and a footnote with Br's and D's paired effects. State why they are excluded.
  Use p10/p14/p16 as replications of Copy→files on tool-written notes, ideally pooled with a task random
  effect, since the runs share tasks.

### W4. The fan-out headline in the abstract is a cross-run number, and the in-run difference-in-differences is not reported. (text/analysis only)

"Files without an index lose 21.2 points when three Researchers share one folder instead of one" compares
`p15_k8_three` against `p15_k8_one` (back-to-back runs). The abstract does not mark it as cross-run.
`numbers.tex` already contains the difference-in-differences against broadcast's own change (REightFanDiD
= -20.4, -26.0 to -14.6), which corrects for drift and is the better estimate.

The section heading "parallel Researchers sharing one folder cause most of B's fan-out loss" is shown at
k = 8 on a PRO 6000. The fan-out loss in Figure 4 is at k = 16 on the RTX 3090s. At k = 16, only the
guard and the heading rule were tested, and they recover 50% and 59%. "Most" is not shown there.

- Fix: report the difference-in-differences in the abstract and §5, mark 21.2 as cross-run, and scope the
  heading to k = 8.

### W5. AlignScore fact coverage is a weak mechanism metric and may be biased by arm. (text/analysis only, optional small annotation)

The metric is validated on synthetic pairs whose contexts are verbatim source sentences (AUC 0.996). On
real notes, it agrees weakly with a Qwen3-8B judge (κ = 0.29). Tool-written notes are JSON-escaped,
split across files, and differently formatted, so measurement error could differ between reply and
tool-written notes. That alone could produce part of the 10-26-point coverage gaps.

Coverage also does not track accuracy. On copied notes, coverage falls by 11 points at 8B and 15 points
at 32B, while accuracy moves by -4.7 and -4.0 (not Holm-significant). The sentence "Fact coverage falls at
the same sizes" follows directly after "lowers accuracy significantly only at 4B", which reads as if the
sizes match.

- Fix: report κ per arm (reply vs tool-written) on the existing judge sample, or hand-label about 50 notes
  per arm. Rephrase the "same sizes" sentence. Treat coverage as suggestive in Figure 3a's caption.

### W6. The rescue is described too narrowly, and the main-run reassurance about it uses unpaired accuracies. (text/analysis only)

The Harness paragraph says the rescue fires when an agent "stops without leaving its output file … so
replying instead of writing does not fail the task". In `run_agent`, it also fires when an agent exhausts
its tool budget. In the main run's B channel at k = 3, 79 Reviewer and 19 Writer rescues were budget
exhaustions, against 158 and 22 that were replies.

"Rescued tasks are about as accurate as the others (62.5% against 63.5%)" compares raw accuracies on a
post-treatment subset. The relevant quantity is the paired gap to broadcast within each subset. I computed
it: 9.5 vs 9.8 points for B and 6.2 vs 5.6 for C. It supports the claim at 8B but contrasts with the
crossed runs (11.3 vs 1.0 at 14B).

- Fix: describe both triggers, split them in the rescue rates, and report paired gaps by subset in both
  places, noting the contrast across sizes.

### W7. The told-run claim is a single-run result, and the heading invites a larger reading than the data supports. (text only; a within-run copy arm would need new runs)

"At 32B, the stored reply loses because later agents are not told where it is" holds for the comparison
with tool-written notes. It does not hold for the comparison with copying. Told stored reply scores 70.2;
copy-reply (A1r) in p16 scores 76.9, about 6.7 points higher (cross-run). The told sentence also changes
the Writer's behavior beyond opening notes: calls drop from 6.65 to 4.11 and Writer rescues from 35% to
15%. The told comparisons are uncorrected (fine for one planned contrast, but there are four). The run was
designed after seeing the crossed runs, which is good practice, but it is n = 150 in one run.

- Fix: change the heading to "loses to tool-written notes because…". Report the cross-run gap to copying.
  Add a within-run A1r arm if a run is affordable (needs new runs).

### W8. Post-hoc analyses still carry claims. (text only)

Family 2 (interaction and Dvw) was chosen after the crossed runs, but its result supports "makes this loss
specific to the stored reply". The Dvw contrast 2·A1w - B - A1r compares two simple effects that share an
arm, and the text gives it a causal reading. The ±3-point equivalence margin was chosen after the run, yet
the result is stated as "lies inside".

- Fix: move post-hoc results to clearly labeled exploratory sentences. Drop the equivalence sentence or
  give the 90% CI without a verdict. Avoid "makes … specific" for a post-hoc test that the told run
  explains at only one of two sizes.

### W9. The serving-time evidence is thin for its conclusion. (text/analysis only)

"Zero-copy thus pays off … when per-task latency under heavy load matters" rests on two runs at 32
concurrent tasks on one GPU with 100 tasks, so about three waves. Going from six to 32 concurrent tasks also
changed the KV cache from 100k to 400k tokens. The 96% decode share sums per-request intervals under
batching, which is not GPU-time share. Zero-copy generates 1.2× more output tokens, a confounder the text
mentions but does not adjust for. At six tasks at a time, zero-copy's p90 task time is worse (about 21 s
vs 18 s).

- Fix: give per-run ratios and tail percentiles. State that two factors changed between the six- and
  32-task settings. Soften "pays off" to "shortened the median task in our 32-task runs".

### W10. Generality, and fairness of prompts across channels. (text only)

The file channels are handicapped in ways a practitioner would fix:
- the listing shows no authors and the notes path is not announced (W1);
- documents are removed from later prompts (controlled only at 8B and cross-run);
- a 12-call budget binds in 34% of tasks (only a k = 16 increase is tested, and 47% of Reviewers still
  exhaust 24 calls, so "a larger tool budget does not [recover]" shows doubling is not enough, not that
  budget does not matter).

With one model family, thinking disabled, greedy decoding, two short-context QA datasets, and one harness,
the recommendation "should copy the conversation forward" is close to true by construction for
state that fits in the context. The "most accurate channels" claim also fails at k = 1, where C ties
(pooled 73.7 vs 74.0; on 2Wiki, C scores 80.7 vs broadcast's 79.3).

- Fix: frame the result as "under a minimal file harness". List the harness choices that favor copying.
  Scope "most accurate" to k ≥ 3.

## Questions for the authors

1. Does `list_files` ordering explain the 14B told failure? What does the 14B Writer read first in Bt? If
   it reads in listing order, a sort-first name for `notes.md` should fix it.
2. Why are Br and D excluded? Br's 32B Writer reads nothing. Is that why?
3. Can you give per-size stage attribution (draft vs final, Writer vs Reviewer) for the crossed runs? At
   14B, the loss appears at the Reviewer.
4. What is the per-arm agreement (κ) of AlignScore with the judge, reply notes vs tool-written notes?
5. For the k = 8 fan-out, why is the cross-run B difference in the abstract rather than the
   difference-in-differences?
6. Are the three replicate runs of B vs A1w (p10, p14, p16) usable as a pooled estimate at 8B? The three
   point estimates (-1.6, -2.9, -4.9) all point the same way.
7. In the 32-task timing runs, how do the results change when the cache is held at 100k tokens?

## Sentences that overclaim or mismatch the code or numbers

1. Abstract: "moving later agents from copying to tool-call file access costs 8--22 accuracy points at three of four Qwen3 sizes (Holm-corrected)."
   The 22 is 4B, where 100% of file tasks were rescued and the Writer opened notes in 13% of tasks (W2).
2. Abstract: "files without an index lose 21.2 points when three Researchers share one folder instead of one"
   This is cross-run and unmarked. The in-run difference-in-differences is -20.4 (W4).
3. Table 1 caption: "the cost depends on how notes are written"
   It is confounded with file name, location, and listing position (W1).
4. §4: "the significant interaction makes this loss specific to the stored reply"
   This comes from the post-hoc family, and the specificity is about how findable the file is, not how the
   notes were written (W1, W8).
5. §4 heading: "At 32B, the stored reply loses because later agents are not told where it is."
   This holds against tool-written notes. Against copying, the told stored reply still trails by about 6.7
   points (cross-run) (W7).
6. §3 Harness: "An agent that stops without leaving its output file gets one forced write call (the rescue), so replying instead of writing does not fail the task."
   The code also rescues agents that exhausted their tool budget (98 of 300 B tasks in the main run) (W6).
7. §4: "rescued tasks are about as accurate as the others (62.5% against 63.5% for B …)"
   These are unpaired accuracies on a post-treatment subset. The paired gaps should be given (W6).
8. §4: "Fact coverage falls at the same sizes, from 43% to 32% at 8B"
   This directly follows "significantly only at 4B", and coverage falls where accuracy does not
   significantly fall (W5).
9. §4: "Zero-copy's accuracy is within 2.7 points of broadcast's in every setting"
   These are point estimates. Per-setting intervals are wider.
10. §4: "The difference's 90% interval … lies inside a ±3-point equivalence margin that we chose after the run."
    This gives a verdict from a post-hoc margin (W8).
11. §4 heading: "Broadcast and zero-copy are the most accurate channels."
    At k = 1, C ties both (W10).
12. §4: "Zero-copy thus pays off when uncached prompt tokens cost more than cached ones or when per-task latency under heavy load matters."
    This rests on two runs, with the cache size also changed (W9).
13. §5 heading: "At eight questions, parallel Researchers sharing one folder cause most of B's fan-out loss."
    "B's fan-out loss" in Figure 4 is at k = 16 on other GPUs (W4).
14. §5: "a write guard or the heading rule recovers about half of B's loss, but a larger tool budget does not."
    With 24 calls, 47% of Reviewers still exhaust the budget, so the run shows doubling is not enough, not
    that budget does not matter (W10).
15. §2: "We also ran, but do not report here, … a variant of B whose Writer and Reviewer reply instead of writing files."
    Its results (-22 to -40 points vs copying) bear directly on the mechanism (W3).
