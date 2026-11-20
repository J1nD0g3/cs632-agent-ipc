# Round 8 revision log

Build: `latexmk -pdf main.tex` gives 6 pages including references, no undefined references.
Numbers: every number in the new text is a macro from `paper/numbers.tex`; `paper_numbers.py` regenerates with no skipped sections.

## New macros (added to `round8` in `src/agentipc/paper_numbers.py`)

- `REightHolmWriteSigWord` (two), `REightHolmReadSigWord` (three): Holm correction over the 12 writing-control
  tests (4 sizes x wording / tool write / rest of file channel, p10 runs), using a paired sign-flip permutation
  test (20,000 flips, seed 0) on per-task accuracy differences. The write effect survives at 4B and 8B; 32B fails.
  The later step survives at 4B, 14B, 32B. This matches the methods reviewer's own computation.
- `REightHolmWritePEight` (0.006), `REightHolmWritePThirtyTwo` (0.010): permutation p-values of the 8B and 32B write effects.

The other round-8 macros (`REightFan*`, `REightFolders*`, `REightReply*`, `REightDecodeMs*`, `REightHiDecodeMs*`) were already defined.

## Item 1: k=8 fan-out on one server (p15)

- Replaced the cross-run k=8 paragraph (`RSixFan*`) with the p15 result: broadcast `REightFanAOne`, B `REightFanB`,
  DiD `REightFanDiD`, per-Researcher folders `REightFoldersOverB` over plain B and `REightFoldersVsOne` from
  one-Researcher B, notes `REightThreeBNotes` vs `REightThreeFoldersNotes`. Broadcast's change is described as the
  drift check between the two back-to-back runs. `RSixFan*` no longer appears.
- New heading: "Parallel writers sharing one folder cause the fan-out loss."
- k=16 paragraph kept (`RSixKSixteen*`), retitled "At sixteen questions, a write guard recovers about half the loss",
  adds that guarded B still trails broadcast by `RSixKSixteenGuardGap`, that preventing overwrites recovers about half
  where the payload also grows, and that separate folders were not tested at k=16.
- Abstract, intro (third observation) and conclusion now give the guidance: own folder per parallel writer, or a
  write guard / heading rule. Removed "much of the loss", "drive the collapse", "largely", and
  "behind the largest loss we saw".

## Item 2: reply-output variant (p14) and renaming the "reading" step

- New short paragraph "Answering by reply" (limitation plus observation): `REightReplyEightVsB`,
  `REightReplyThirtyTwoVsB` with intervals and N, open rates `REightReply*Open` vs `REightFile*Open`, and the
  observation that how an agent ends its turn changes whether it reads.
- The B-minus-A1w step is now "the rest of the file channel" everywhere, defined in the text and the Fig. 3 caption as
  everything after the notes are written (questions only, tool-call reads, tool-call output writes, rescue, budget).
- `figs/fig_split.py`: bar label "Reading files" -> "Rest of file channel"; panel (a) title -> "(a) Facts in the
  Researcher's notes"; docstring updated. Re-rendered with archfig, lint clean.
- Conclusion: the replay result is now "lost points in the rest of the file channel", not "at reading".

## Item 3: round-7 text and analysis fixes

- Serving time: heading now "Zero-copy decodes faster but generates more." Gives decode time per generated token
  (`REightDecodeMsAZc` vs `REightDecodeMsAOne` at 6, `REightHiDecodeMsAZc` vs `REightHiDecodeMsAOne` at 32), the
  `RSixGenAZc` output growth, and the `RSixTimeAZc` result. Counters are described as summed per-request counters that
  overlap and do not split wall time. Removed the 96% decode-share argument (`RSixDecodeShareAOne`) and every claim
  that decode dominance explains the result (abstract, intro, results, conclusion). The serving GPU (RTX PRO 6000)
  is now named in the paragraph. Added the pipe's per-token decode time.
- Multiple testing: added the Holm result (write survives at two sizes, 32B p = 0.010 does not; later step at
  three) and cited the earlier separate run on 200 tasks per size (`RFour*WMinusR`). Abstract and conclusion
  now say "two of four sizes after correction". Removed the size-dependent ordering claim. At 8B the text now says
  the two steps' intervals overlap and are not ranked.
- Kappa 0.29: "agrees only weakly" (was "moderately").
- Zero-copy accuracy: the pooled interval (`ZcPooledDiffLo` to `ZcPooledDiffHi`) is stated as equivalence only
  within that range in the results, abstract, and conclusion. The Fig. 2 caption says "not significantly lower".
  The Fig. 2 arrow label changed from "same accuracy" to "no sig. loss". "Zero-copy costs only the 4B model" is now
  "significantly costs only the 4B model" in our accuracy measure, next to the existing EM caveat on 2Wiki.
- Scope: the abstract says the tasks' state fits in the context and that larger state was not tested. The
  conclusion says the same in its second sentence. The title is unchanged.
- Delivery: Methodology says it counts every file the Writer read, and that `DocReadsB`% of B's Writer reads are
  source documents. Results says "the files it reads, mostly documents".
- Cross-run labels: the A2d and Bd scope controls are now labeled as a separate run compared with the main run.
  Removed the intro claim that serving time ranks channels as tokens sent does, which compared timing and token runs.
  The heading-rule vs C comparison stays labeled cross-run.
- Other quoted overclaims fixed: "message-passing versus shared-memory question" -> "an analogue of"; the TOAP
  qualification in the intro; "Missing sources do not explain the loss" -> "most of the loss"; the cache/budget
  paragraph is renamed "Cache size and tool budget", and the 24-call result "cannot exclude a gain of a few points";
  "C's smaller loss likely comes largely" -> "may come partly"; the pipe is "the cheapest channel, or tied for it";
  "The loss is not the longer notes" -> "not mainly"; Fig. 2 caption "Bars" -> "Whiskers"; Fig. 2a axis
  "(API billing)" -> "(uncached billing)" and the metric is now defined as an API bill without cached-input
  discounts; the rescue rationale no longer cites frameworks taking the last message; the `workspace/` harness
  sentence no longer appears before it is explained; the interleaving caveat (shared cache capacity) is applied to
  the k=8 prefill ratios.
- Related work: one sentence mapping per-writer folders and the write guard to per-process namespaces and exclusive
  file creation.

## Cuts to stay at 6 pages

- Abstract: dropped the cost-metric sentence and the isolated 4B fact at the end. It now ends on the guidance and
  scope.
- Intro: contributions are inline sentences instead of a list. Dropped the serving-time ranking sentence.
- Methods: shortened the list of PRO 6000 runs and the delivery definition.
- Results: dropped broadcast's absolute serving seconds (`RSixTimeAOneMin/Max`) and 32-task prefill ratio
  (`RSixHiPrefillTimeAZc`), C's replay delivery numbers (`RepCDeliv`, `RepBDeliv`), and the 8B/14B point-estimate
  ranking sentences.
- Sensitivity: dropped headed-notes share (`RSixKSixteenHeadingNotes`), the sentence attributing the 4B zero-copy loss
  to prompt arrangement (the conclusion says this is untested), and the A/A "same accuracy" wording.
- Fig. 4 moved earlier in the source so it is placed on page 4 with Figs. 2 and 3.

## Not done (need new runs or annotation, or out of scope here)

- Renaming "zero-copy broadcast" (systems W9) was not requested and would touch every figure.
- New runs: workload with state larger than the context, output-length-controlled timing, A/A on the PRO 6000,
  per-writer folders at k=16, a second model family, human labels for AlignScore, served-alone tokens computed.
- Analyses not requested this round: tool-call breakdowns, rescued vs non-rescued accuracy, reply-as-output
  rescoring, TOST per dataset, billed-cost row, analytic cost model, extra related work (CacheBlend, InferCept, etc.).

## Audit fixes

Snapshot before these fixes: `cs632-store/main_pre_audit8.tex`. New macros (all in `paper_numbers.py`):
`ZcPooledLossMax`, `REightFanBAbs` (and `REightFanAOneAbs`), `REightClashB`, `REightOneLeftB`, `REightHiGenAZc`,
`REightHiReqAZc`.

1. Abstract: "plain files change accuracy by REightFanB points, and a folder per Researcher recovers all of it" -> "plain files lose REightFanBAbs points against one Researcher, and a folder per Researcher recovers REightFoldersOverB of them".
2. Intro: "cause plain files' loss when work fans out, and that a folder per writer removes it at eight questions" -> "cause most of the extra loss of plain files when work fans out, and that at eight questions a folder per writer recovers REightFoldersOverB points of it".
3. Sensitivity: "thus comes from parallel writers sharing one folder, where they pick the same file names. At sixteen questions on the RTX 3090 servers, two Researchers wrote the same path in ClashB% of B's tasks." -> "thus comes from sharing one folder. In REightClashB% of B's three-Researcher tasks at least two Researchers wrote the same path, and in REightOneLeftB% only one Researcher's notes were left. Separate folders also change the paths the Writer sees, which this arm does not separate." Both shares from p15_k8_three B io_ops. REightOneLeftB = 58, not the audit's 75: the audit's "last write per path" ignores that 49 of the Researcher writes were appends, which keep the earlier Researcher's notes (workspace.py appends to the existing file). Heading: "cause the fan-out loss" -> "cause most of the fan-out loss".
4. Sensitivity: deleted "At eight, the notes left in the workspace state REightThreeBNotes% ... REightThreeFoldersNotes% with separate folders." (In the 58 append-aware one-Researcher tasks AlignScore still credits 44% of facts, above the 37.5% ceiling, so the audit's reason holds.)
5. Conclusion: "which removed that loss, or ... which recovered about half of the larger loss at sixteen" -> "which recovered REightFoldersOverB points of that loss, or ... which recovered RSixKSixteenGuardOverB and RSixKSixteenHeadingOverB of B's RSixKSixteenBGap points at sixteen". Also "caused B's fan-out loss" -> "caused most of B's fan-out loss".
6. Abstract: "Served alone, it decodes ... so it takes RSixTimeAZc x" -> "Served alone at six tasks at a time, it decodes ... and it takes RSixTimeAZc x"; "within ... of copying's accuracy" -> "... at three questions per task" (item 16).
7. Intro: "which offsets its faster decoding, so it saves no serving time" -> "and served alone it saves no serving time".
8. Results (timing): appended "There it generates REightHiGenAZc x the tokens, yet its summed request time is REightHiReqAZc x broadcast's, so these counters do not explain its wall time." Also dropped the six-task "which offsets the gain" (same untested causal claim as 6/7/9).
9. Conclusion: "generated more, so it saved no serving time" -> "generated more. It saved no serving time at six or 32 tasks at a time".
10. Results: "With a Holm correction over all tests ... ($p$ = ...)" -> "With a paired permutation test and a Holm correction over the 12 tests ... (uncorrected $p$ = ...)".
11. Results: "An earlier, separate run on N tasks per size found write effects of ..." -> "An earlier pair of runs per size on N tasks, one per arm with a 2,048-token cap, a cross-run comparison, found write effects of ... significant at RFourWSigWord sizes".
12. Abstract: "and again in the rest of the file channel" -> "and in the rest of the file channel, at REightHolmReadSigWord".
13. Intro: "the tool-call write of the notes and everything after it" -> "..., each at some model sizes".
14. Results (reply): "answered before opening the notes, which it did in ... it thus scores ... How an agent ends its turn changes whether it reads." -> audit text: "answered without opening the notes. It opened them in ... at 32B, where it listed the files and answered without reading any, against B's ... it scores ... In this variant, an agent that could end its turn with a reply often answered without reading, though its tools and instructions also differ from B's."
15. Results: "so the two are equivalent only within that range" -> "so a loss of up to ZcPooledLossMax points is not excluded".
16. Abstract: see 6 ("at three questions per task").
17. Results (pipe): "trails broadcast by ScopeATwoDVsAOneAbs (lo to hi)" -> "trails broadcast by ScopeATwoDVsAOneAbs points (a paired difference of lo to hi)".
18. Methods: "All other runs use one RTX PRO 6000 ..." -> "The main run, its scope, replay, and rerun controls, and the runs of Figure 4 use these servers. All other runs use one RTX PRO 6000 ..." (checked env.json of every run: t07/t08/t09 on RTX 3090, all p* runs on RTX PRO 6000). Shorter than the audit's list and equivalent.
19. Methods: "what an API would bill without cached-input discounts" -> "the tokens an API would bill without cached-input discounts, not their price"; Fig. 2a axis "(uncached billing)" -> "(billed tokens, no cache discount)" (re-rendered, lint clean).

Cuts to stay at 6 pages: Channels "Zero-copy broadcast counts as a variant ..."; intro "We build a testbed ..." merged; Related Work's TOAP sentence (TOAP stays cited in the intro); duplicate "the rest of the file channel" in the split paragraph (kept in the caption); k=16 AlignScore notes sentence (RSixKSixteen{B,Guard,AOne}Notes, same overwrite-inflated measure as item 4); "zero-copy broadcast" -> "zero-copy" twice in Sensitivity and once in timing; small wording trims in Channels C, Harness, pipe, files, fan-out, and run-to-run paragraphs.
