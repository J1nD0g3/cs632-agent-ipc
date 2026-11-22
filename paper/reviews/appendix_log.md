# Appendix log

Snapshot before any edit: `/mnt/sda/heojin/cs632-store/main_pre_appendix.tex`. Nothing committed.

## Build state

- `latexmk`: 16 pages. The body still ends on page 6 (the Conclusion's last sentence is on page 6, and
  References start on page 7). The appendix runs from the right column of page 7 to page 16, about 9 pages.
- No undefined references or citations, and no overfull boxes. A `\clearpage` before `\end{document}` flushes
  the appendix floats before acmart balances the last page. Without it, three tables were dropped and the log
  showed a 647pt overfull vbox.
- `pytest -q`: 17 passed. `python -m agentipc.paper_numbers`: nothing skipped. Every pre-existing macro in
  `numbers.tex` is identical to before (checked with a diff that leaves out the new `\nApp*` lines).
- Body floats (Figures 1-4, Table 1) are on the same pages as before. The pointers below reflow the text of
  pages 2-5 but move no float.

## What was added

- Preamble: `multirow`, `fvextra` (wrapping verbatim, 6.5pt), `\input{appendix_tables}`, and a `Listing`
  counter (`\applisting`). These change nothing in the body. Page 1-6 text was identical before the pointers
  went in.
- `\appendix` after `\bibliography`, with float-packing settings that start after the body has shipped.
- Sections: A Tasks and data (`app:tasks`), B Prompts and harness (`app:prompts`), C Models and serving
  (`app:serving`), D Worked example (`app:example`), E Fact measures (`app:facts`), F Statistics
  (`app:stats`), G Full results (`app:results`), H Results cut for space (`app:cut`).
- Body pointers, each kept only if the body still ended on page 6 (tested one at a time):
  Tasks (App. A), Serving (App. C), Harness (App. B), Metrics (App. E), Statistics (App. F),
  §4.2 broadcast accuracy (App. G), D (App. H), and B's Writer skipping the notes (App. D). One pointer in the
  Runs paragraph was tried and reverted because the body then ran onto page 7.

## Scripts and macros

- New `src/agentipc/appendix_tables.py` writes `paper/appendix_tables.tex` (11 table bodies as
  `\appTab<Name>` macros) and `paper/appendix/*.txt` (17 verbatim files). `paper_numbers.main()` calls it at the
  end, so the one regeneration command builds everything.
  Tables: Tasks, Runs, Example, Facts, Stage, Main, Size, Cache, Arms, Timing, Cut.
  Listings: raw HotpotQA and 2Wiki questions, the task's Researcher message, B's `list_files` output (rebuilt
  with the real `Workspace` class), every instruction (`prompts.txt`, from the `pipeline.py` constants), the
  tool schemas, the judge prompt, a synthetic triple, and the worked example per channel.
- New section `appendix` in `paper_numbers.py` (macro prefix `App`): dataset sizes before the filter
  (`AppHotpotAll` 7,405, `AppWikiAll` 12,576), the PRO 6000 block counts and exact KV sizes from
  `queue_pro6000.sh`, the memory utilization from the ledgers and the main-run flags (0.92, 0.95, 0.90), the
  vLLM version, the synthetic and real pair counts (150 per kind, 360 units, 864 facts, 16,000 chars), the
  worked-example rule (`AppExHits` 11 of `AppExTotal` 300), D's tokens and prefill relative to broadcast (1.32,
  0.59) and Writer skip rate (87%), the k=16 clash split (43 vs 17 tasks), and the fact-checker chain's largest
  move in another channel (`AppChainOtherMax` 1.3).
- `pro6000_kv()` reads every `results/pro6000*_kv_used.txt` ledger. It keeps only rows whose run directory
  exists, so setup checks (the smoke server at 0.9) are left out.

## Worked example

`2wiki-k3-s2-0117`. The rule: a k=3 main-run task that ran in A1, A1-zc, A2, B, and C, where broadcast answers
every question, the pipe's Reviewer turns a right draft answer wrong, and B's Writer never opens the notes.
11 of the 300 tasks meet it. The text says the rule selects the failures of §4, so the task is not typical, and
it gives the main-run rates next to it (broadcast 72.3%, B's Writer skips the notes in 42%). Among the 11, this
task was picked because all its errors in the five channels fall on Q3. Outcomes: A1, A1-zc, and C get 3/3,
while A2 and B get 2/3. Checked by script: the years 1886 and 1915 in B's draft appear in no document of
the task, and every channel's notes state both directors and their birth dates. D (not shown) got Q1 wrong in this
task.

## Self-audit (each claim checked against code or data, fixes applied)

- Fresh server per PRO 6000 run: false for `p15_k8_one`/`p15_k8_three` (back to back on one server, ledger).
  Fixed.
- "Timing runs went in a shuffled order": true only for the p11 runs (round 6 order file). The p06 runs ran in
  channel order. Fixed to name the shuffled runs. The host-monitor claim is limited to them too.
- The Llama judge "served the same way": its context was 8k (`queue_judgex.sh`). Changed to "also served with
  vLLM".
- Rescue: the harness appends the agent's reply only if it replied (`plain_reply`). Fixed.
- The tool budget "24 in one k=16 run" missed `t08_turns24`. It now points to the run table.
- Concurrency "at most 6": the timing and load runs used 32, 1, and 2. Fixed.
- `ChainOtherMax` prints 1 (integer) while the largest move is 1.3 (C). The appendix uses the new
  `AppChainOtherMax`.
- "Reads six documents": a hand-typed count. Removed.
- AlignScore `nli_sp`: the description now includes the averaging over the fact's sentences.
- Holm table: every cell is an existing macro (`RTenHolm*P*`, `RTenMark*`, `RTwelve*P`, `RTwelveMark*`,
  `RTwelve*Dvw`). Contrast = 2·A1w − B − A1r = (A1w − B) − (A1r − A1w), as in `round12`.
- Generated tables were spot-checked against body macros: size-run gaps (B 24.8/10.0/7.5, rerun 11.7), told-run
  open rates (32B 86/26), crossed-run open rates (14B 99/9), timing ratios (A1-zc 1.09, generated 1.23),
  stage table sums (wrong = sum of the stages, for example A1 27.7), and the AlignScore validation
  (recomputed from `factcheck/real_as.jsonl`: κ 0.29/0.22/0.54).
- Style: no semicolons in the appendix prose (the verbatim prompts keep theirs). Nothing mentions a modified
  vLLM, a venue, or an author. The vLLM source commit and dirty flag in `env.json` are not used.

## Length

The appendix is about 9 pages, against a target of 4-6. Most of it is material the author asked for: every
prompt verbatim (about a column), five per-channel excerpts, the run list (31 rows), and full per-setting
tables. Candidates to cut if 6 pages is firm:
(1) pool datasets in Table 9 (main run), about 0.25 page;
(2) drop the 6 superseded rows of the run table;
(3) drop Listing 1 (raw questions), since Listing 2 shows the same task;
(4) drop the stage-attribution table.

## Not included

- No plan item was skipped for missing data. The stage-attribution result is a table, not the old figure.
- Superseded runs (`t09_a1w`, `p05_*`, `p13_k8_fanout`, `t08_turns24`, `t08_pressure_*`) appear in the run
  table with their settings, but their results are not reported, since the plan did not list them.

## Cuts, 2026-11-22

Two cuts from the length candidates above (items 2 and 3); nothing else changed.

- Run table: removed the 5 superseded rows (`t09_a1w`; `p05_a1r_*`/`p05_a1w_*`; `p13_k8_fanout`;
  `t08_turns24`; `t08_pressure_c1`/`c2`) from `RUNS` in `appendix_tables.py`, so the table now has 25 rows.
  The caption sentence on superseded runs now reads "Earlier pilot and superseded runs are omitted." No
  macro used in `main.tex` comes from these runs (the `TwFour*`, `Press*`, `RSixFan*`, `W*` macros are still
  written to `numbers.tex` but unused), and no text or table refers to the removed rows. The note under
  "Not included" above no longer holds: these runs are no longer listed.
- Appendix A: removed the raw-questions listing (old Listing 1, `lst:raw`) and the sentence pointing to it.
  `raw_question_listing` and the writes of `appendix/raw_hotpot.txt` and `appendix/raw_2wiki.txt` are gone
  from the generator, and the two files are deleted. The "From questions to tasks" paragraph and the worked
  task listing (now Listing 1) are unchanged. Listings renumber from 1.
- Regenerated with `python -m agentipc.paper_numbers` (no "skipped"; `numbers.tex` unchanged). Build has no
  LaTeX warnings and no undefined references. The body still ends on page 6 (References start on page 7).
  Total: 15 pages (was 16). `pytest -q`: 17 passed.
