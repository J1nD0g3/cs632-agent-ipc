# Round 14: figure integration log

Snapshot before any edit: `/mnt/sda/heojin/cs632-store/main_pre_figs.tex`. Nothing was committed.

## Figure fixes

- **Fig. 1** (`paper/figs/fig_mechanism.py`):
  - The Writer→notes read now has the same two-line label in both file panels: "unread in 42% of tasks" for B (bold, red, dashed arrow) and "unread in 8% of tasks" for C (regular weight, gray, solid navy arrow).
  - The label sits inside the elbow of the read. To make room, the file panels place the Writer at 0.54 of the panel width instead of 0.5.
  - The message row is now 51 pt tall instead of 59, and the top strip 13 pt instead of 14. The file row stays at 59 pt, because shrinking it squeezed the doc boxes. The figure went from 139 to 130 pt.
- **Fig. 3b** (`paper/figs/fig_split.py`):
  - Model size is encoded twice, by shape and by color: a gray circle for 14B and a teal square for 32B.
  - All six markers are filled. Hollow markers now appear only in (a), where they mean "not Holm-significant", as the legend says.
  - Every point has its own label in its size's color: "14B/32B tool-written", "14B/32B untold", and the told points.
  - The paired change now sits on each told point. 32B reads "32B told: +14.2 pts (+10.2 to +18.4)" in green, at the head of the green arrow. 14B reads "14B told: +0.9 pts (−2.0 to +4.0)" in gray, directly above the 14B told marker.
  - The y range is now 38–76.
- **figdata**: `fig3_cause()` and `fig4_limits()` are added to the end of `main()`. The existing calls were not reordered.
  - `python -m agentipc.figdata` rewrote every JSON in `paper/figs/data/` with identical content (md5 unchanged).
  - `fig1_mechanism`, `fig3_cause`, and `fig4_limits` JSON/CSV fall under the `data` ignore rule and need `git add -f`.

## Lint and number check

- All four figures were re-rendered, and each lints clean with 0 defects and 0 advisories. I viewed each PNG.
- I compared every number printed in the SVGs with `numbers.tex`, and all of them match:
  - 42, 8
  - −9.6, −6.0, −10.2, −61, −0.8 (−2.9 to +1.4), 1.09, 0.99, 1.00, 0.82
  - −22.0, −2.9, −8.9, −8.2, +14.2 (+10.2 to +18.4), +0.9 (−2.0 to +4.0)
  - 0.39, 0.83, 1.00, 35k, 100k, 0.36, −20.4, +19.8, +15.1, +18.1, 99%, −30.4

## main.tex

- I replaced all four captions. Each opens with its claim. The proposed captions added about 14 full-width lines and pushed the Conclusion onto page 7, so I trimmed them to 2, 3, 3, and 4 lines.
- What I cut, because the text already says it:
  - Fig. 1: C's heading-rule caveat (said in §4.3 next to the new Fig. 1 reference), and the hatch note (the legend has it).
  - Fig. 2: the definition of tokens sent (Methodology).
  - Fig. 3: the Table 1 family size and the 4B rescue note (said next to the "Figure 3a" citation).
  - Fig. 4: the RTX 3090 cache size and concurrency (§5.1), the DiD and folder intervals, the "same path" definition, the guard and heading shares, and the 59-task heading N (all in §5.2).
- What I kept: run, model, k, task counts, 95% intervals, paired, cross-run, exploratory, and Holm-significant.
- Reference changes. All of them still matched after the restructure.
  - Fig. 2c is cited twice in the §4.1 timing paragraph. The optional cite in the §4.1 opening sentence was not added.
  - §4.2 now has "(Figure 2a, $k=3$)", a shorter form of the note's wording.
  - Fig. 3a is cited in two places, the split sentence and the read-cost sentence.
  - The coverage sentence's "(Figure 3a)" was removed. The sentence and its "weak measure" caveat stay.
  - Fig. 3b is cited at the told-runs sentence.
  - §4.3(c) now cites Figure 1 for the 42%.
  - The §5.1 cache control reads "(cross-run, Figure 4a, hollow stars)". This is a comma, not the note's semicolon.
  - §5.2 has "(Figure 4b, right)" at k=16, and "Figure 4b, left" goes inside the DiD interval parentheses.
- The Fig. 4 float moved from before §4.3 to before the "At 14B, final accuracy …" paragraph. It now lands on page 6, right after its first mention on page 5. Before the move it sat on page 5 ahead of §5.

## Build

- `latexmk` completes and produces 7 pages, with no undefined references or citations.
- The body ends on page 6, with the last Conclusion line as the last line of the page, so there is no slack.
- References start on page 7.
- Figure placement: Fig. 1 is on p2 (first mention p1), Fig. 2 on p3 (p3), Fig. 3 on p4 (p4), and Fig. 4 on p6 (p5).
- The body has no semicolons and does not mention a modified vLLM.

## Caption self-audit

- **Fig. 1.** "B's Writer never opened the notes in 42%" matches the figure's "unread in 42% of tasks" and `\nNoNotesB`. The caption scopes it to the main run (Qwen3-8B, k=3).
- **Fig. 2.**
  - Direction holds. Files are rightmost in (a), and broadcast is rightmost in (b).
  - The −61% matches `\nZcCut`, and "same accuracy" matches −0.8 (−2.9 to +1.4).
  - "Without shortening runs" matches (c): run time is 1.09× with six tasks at a time and 1.00× with 32. The median task is 0.82× with 32, and the figure shows it in green. The text covers it.
- **Fig. 3.**
  - "8–22 points at 4B, 14B, and 32B" equals the AbsMin/AbsMax macros (8.2–22.0). The 8B point is hollow in the figure, which matches "not significantly at 8B".
  - "Which naming its path fixed only at 32B" holds: at 32B the Writer's opens went from 26% to 86% and accuracy rose 14.2 points, while at 14B opens went from 9% to 5% and accuracy changed by +0.9, not significantly.
  - The caption labels (b) exploratory and paired.
- **Fig. 4.**
  - (a) The saving disappears as the cache fills: 0.39 → 0.83 → 1.00, and back to 0.36 with the 100k cache.
  - (b) "Lose about 20" equals the DiD of −20.4, and "win back" equals +19.8.
  - The 1-Researcher bar comes from a separate run, which is consistent with "paired by task within each run".
  - The caption marks the cache control as cross-run.

## Open issues

- With the body ending on the last line of page 6, any added body or caption text will push the Conclusion onto page 7.
- Fig. 1's caption says "Qwen3-8B" and Fig. 2's says "8B", for the same main run.
