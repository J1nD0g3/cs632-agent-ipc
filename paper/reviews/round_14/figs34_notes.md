# Figures 3 and 4 (round 14): implementation notes, captions, and main.tex changes

This implements `figure_plan.md` for Fig. 3 and Fig. 4. `main.tex` was not edited. Everything it needs is listed
below.

## Files

- `paper/figs/fig_split.py` → `paper/figs/out/fig_split.{svg,pdf,png}` (506 × 118.0 pt; was 120.0 pt).
  The label stays `fig:split`.
- `paper/figs/fig_scaling.py` → `paper/figs/out/fig_scaling.{svg,pdf,png}` (506 × 127.5 pt; was 127.8 pt).
- `src/agentipc/figdata.py`: four new functions (`_numbers`, `_num`, `fig3_cause`, `fig4_limits`). No existing
  function was changed or moved. They write `paper/figs/data/fig3_cause.{json,csv}` and
  `paper/figs/data/fig4_limits.{json,csv}`. Fig. 4a still reads `fig4_scaling.json` (from the existing `fig4`).
- `main()` is unchanged, so `python -m agentipc.figdata` does not yet write the two new files. To regenerate them:
  `PYTHONPATH=src .venv/bin/python -c "from agentipc.figdata import fig3_cause, fig4_limits; fig3_cause(); fig4_limits()"`.
  Once the Fig. 1–2 edit to `figdata.py` has landed, add `fig3_cause()` and `fig4_limits()` to `main()`.
  `fig3_split()` and `fig3_split.json` are no longer used by any script. They were left in place.

## Data sources: one source per number

- `fig3_cause` runs `paper_numbers.round10`, `round10_text`, and `round12_told` on a fresh `Macros` object and reads
  the macro values back. The plotted numbers therefore are the macros, not a re-implementation.
  - The Holm flag is `RTenMark{Effect}{Size}`, the same macro that bolds and daggers Table 1's `RTenCell` cells
    (`round10_text`'s Holm family of 16 tests).
  - `round10_text` also reads `configs/` and `scripts/queue_pro6000.sh` for setup constants. The figure does not
    use those values.
- `fig4_limits`:
  - k=16 bars, gains, shares, the clash rate, and the k=8 difference in differences come from
    `paper_numbers.round6`, `round8`, and `round12`, run the same way.
  - The cache control repeats `paper_numbers.pro6000`'s formula: mean A1zc prefill over mean A1 prefill in each
    `p01_cache_*` run.
  - The k=8 bars (B or Bf minus A1, per task within each `p15` run) use `analyze.paired` and the same error
    filter as `round8`. They are plotted but not printed (see "Deviations").

## Number check (`numbers.tex` against the figure data, all equal)

| Printed on the figure | Macro |
| --- | --- |
| 3a: −22.0, −2.9, −8.9, −8.2 | `\nRTen{Four,Eight,Fourteen,ThirtyTwo}FileTool` |
| 3a: filled or hollow, all 12 markers | `\nRTenMark*` = bold/dagger of `\nRTenCell*` (Table 1). Filled: FileTool and FileReply at 4B, 14B, and 32B, and WriteCopy at 4B. Hollow: the rest. |
| 3a: "all rescued" (4B) | `\nRTenFourRescueToolFile` = 100 |
| 3b: +14.2 (+10.2 to +18.4) | `\nRToldThirtyTwoToldOverUntold{,Lo,Hi}` |
| 3b: 14B +0.9 (−2.0 to +4.0) | `\nRToldFourteenToldOverUntold{,Lo,Hi}` |
| 3b: point positions | `\nRTold{Fourteen,ThirtyTwo}{Open,Acc}{Tool,Untold,Told}` |
| 4a: 0.39×, 0.83×, 1.00× | `\nCompAZcK{Three,Eight,Sixteen}` |
| 4a: 35k cache (star at 0.85), 100k cache 0.36× | `\nKvProSmall`, `\nPKvThirtyFiveCompAZc`, `\nKvPro`, `\nPKvHundredCompAZc` |
| 4b: −20.4 (k=8 red arrow) | `\nREightFanDiD` |
| 4b: +19.8 | `\nREightFoldersOverB` |
| 4b: same path: 99% | `\nREightClashB` |
| 4b: −30.4 | `\nRSixKSixteenBGap` (negated; bar is B − A1) |
| 4b: +15.1, +18.1 | `\nRSixKSixteen{Guard,Heading}OverB` |
| 4b: k=16 bar ends and whiskers | `\nRSixKSixteen{B,Guard,Heading}Gap{,Lo,Hi}` (negated) |

The check script compared every effect's mean, Lo, and Hi, every told point, and every value in the table above.
There were no mismatches.

The k=8 bars have no macros:
- one Researcher: −7.8
- three, shared folder: −28.1
- three, own folders: −8.4

They equal the differences of the existing accuracy macros, except own folders, which is −8.3 unpaired. The arrow
between the first two bar ends spans 20.3 and is labeled with the DiD macro, 20.4.

## Lint

Both figures lint clean, with 0 defects and 0 advisories, and no `fig.ignore`. `fig.ignore.add("grayscale")` was
removed from Fig. 3. I checked grayscale views (`out/views/fig_*.print.gray.png`): Fig. 3a's series separate by
shape and tone, and Fig. 4's zero-copy line separates by width and star markers.

## Proposed captions (claim first)

**Figure 3** (`fig:split`):

```latex
\caption{Reading tool-written notes as files instead of copying them costs
\nRTenHolmFileToolAbsMin--\nRTenHolmFileToolAbsMax points at \nRTenHolmFileToolSizes but not significantly at 8B
(a), and later agents rarely open a stored \texttt{notes.md} unless told its path, which helped only at 32B (b).
(a)~Crossed runs ($k=3$, \nRTenN tasks), paired effects with 95\% intervals. Filled markers are Holm-significant
in the \nRTenHolmTests-test family of Table~\ref{tab:cross}, and at 4B the harness rescued
\nRTenFourRescueToolFile{}\% of the file tasks. (b)~Told runs, one per size on \nRToldThirtyTwoToldOverUntoldN
tasks, exploratory and uncorrected. The arrow and the 14B note give the paired change from telling later agents
the path.}
```

**Figure 4** (`fig:scaling`):

```latex
\caption{Larger tasks expose two limits: zero-copy's prefill saving disappears once the shared history outgrows
the KV cache (a), and three Researchers sharing one folder lose about 20 points, which separate folders win back
(b). (a)~RTX 3090s, each with a \nBigKv-token cache that \nConcWord concurrent tasks of mixed channels share
(datasets pooled, \nScaleNMain tasks at $k \le 5$, \nScaleNEight at 8, \nScaleNSixteen at 16 with three
Researchers). Hollow stars are the same eight-question tasks on one RTX PRO 6000 with a \nKvProSmall- or
\nKvPro-token cache (\nPKvHundredN tasks, cross-run; \nKvProHi gives \nPKvFourHundredCompAZc$\times$).
(b)~B's accuracy minus broadcast's in the same run, paired by task, with 95\% intervals. At $k=8$, one and
three Researchers ran back to back on one server (\nREightFanBN tasks). The red arrow is the difference in
differences (\nREightFanDiDLo to \nREightFanDiDHi). Separate folders gain \nREightFoldersOverB points
(\nREightFoldersOverBLo to \nREightFoldersOverBHi) but also change the Writer's paths, and ``same path'' is the
share of tasks in which two Researchers wrote one path. At $k=16$ (one RTX PRO 6000, \nRSixKSixteenBGapN tasks,
\nRSixKSixteenHeadingOverBN for the heading rule), the write guard and the heading rule recover
\nRTwelveShareGuard{}\% and \nRTwelveShareHeading{}\% of the gap.}
```

## main.tex changes

1. **L210–212, Fig. 3 caption**: replace `\caption{Crossed runs ($k=3$, \nRTenN tasks). On tool-written notes, files
   lower accuracy at \nRTenHolmFileToolSizes (b).}` with the Figure 3 caption above.
2. **L296–299, Fig. 4 caption**: replace the current caption ("Prefill and accuracy relative to A1 on RTX 3090s ...")
   with the Figure 4 caption above.
3. **L311**: `(Figure~\ref{fig:split}, Table~\ref{tab:cross})` → `(Figure~\ref{fig:split}a, Table~\ref{tab:cross})`.
4. **L316–317, read cost**: `... the file channel lowers accuracy by \nRTenHolmFileToolAbsMin--\nRTenHolmFileToolAbsMax
   points at \nRTenHolmFileToolSizes, all Holm-significant,` → add `(Figure~\ref{fig:split}a)` after
   "all Holm-significant".
5. **L328, coverage sentence**: remove ` (Figure~\ref{fig:split}a)`, so that the sentence ends `... at
   \nRTenNotesToolLowerSizes by point estimate.` Keep the "a weak measure" caveat. The coverage panel no longer
   exists.
6. **L361–362, told runs**: `The told runs add ``The Researcher's notes are in \texttt{notes.md}.'' to both later
   agents' instructions.` → add ` (Figure~\ref{fig:split}b)` before the final period. Fig. 3b plots the Writer-open
   rates and accuracies cited in L362–373.
7. **L405–407, cache control**: after `... \nPKvThirtyFiveCompAZc{}$\times$ with \nKvProSmall (cross-run` add
   `; Figure~\ref{fig:scaling}a, hollow stars`. L401's `(Figure~\ref{fig:scaling}a)` stays.
8. **L417, k=16**: `At sixteen questions, B's loss (Figure~\ref{fig:scaling}b) mixes ...`. The reference now points
   to the parallel-writer panel, whose k=16 group shows B's loss and the two repairs. Keep it, or write
   `(Figure~\ref{fig:scaling}b, right)`.
9. **L421, k=8 DiD**: after `\nREightFanDiD points (\nREightFanDiDLo to \nREightFanDiDHi)` add
   `(Figure~\ref{fig:scaling}b, left)`.
10. No other references to `fig:split` or `fig:scaling` exist. Nothing in the text cites the old accuracy-against-k
    panel (old Fig. 4b) except L417, which item 8 covers.

## Deviations from the plan, and why

- **Fig. 3a**:
  - The series differ in marker shape (circle, square, diamond) as well as size and tone.
  - Hollow markers are outlined one tone darker (teal3, gray4), because a teal2 or gray3 outline vanishes in
    print.
  - The y-axis title is "Change (points)", because the long title ran into the legend strip.
  - The "no change" label sits at the left, under the zero line.
- **Fig. 3b**:
  - There is no 14B arrow. Its two points are 8 pt apart, so an arrow would not show. The paired change is printed
    in gray instead ("14B told: +0.9 pts (−2.0 to +4.0)").
  - The two tool-written points share one label, "tool-written", plus their size labels.
  - The y range is 38–75 to leave room for the 14B labels.
- **Fig. 4a**:
  - The x axis is numeric with categorical tick labels (1, 3, 5, 8, 16), so an extra slot right of k=8 holds the
    cache control and its labels before the k=16 separator.
  - The 35k star is labeled "35k cache" without its value. Its 0.85 is visually the same as the 0.83 star beside
    it, and the caption carries the number.
  - 400k is not drawn, because it equals 100k (0.36). It is in the caption.
  - The k=16 tick reads `16 (3 Res.)`, because `16 (3 Researchers)` is too wide.
  - The legend lists zero-copy first.
- **Fig. 4b**:
  - The k=8 bars have no printed values, because no macro exists for them.
  - The k=8 loss is instead the red arrow labeled with the DiD macro (−20.4), which is the number the text cites.
    The gain is the green arrow (+19.8).
  - At k=16, "−30.4" is printed under the shared-folder bar. The guard and heading gains are green arrows (+15.1,
    +18.1) rather than a "recover ½" bracket. The shares (50%, 59%) are in the caption.
  - Fills are tone 3 (red3, teal3, gray2), not tone 4, so the black whiskers stay visible across the bar ends.
  - Group separators under the axis were dropped. The dashed in-plot separator divides k=8 from k=16.
  - Tick labels are `1 Res.`, `3 Res.`, `own folders`, `3 Res.`, `+ guard`, `+ heading`, with group labels
    `k = 8` and `k = 16`.
- **Exploratory marking**: Fig. 3b's title says "(told runs, exploratory)". Fig. 4a's hollow stars are marked
  cross-run in the caption.

## 3-second reads (they match the captions' first sentences)

- **Fig. 3**: four dark teal circles carry −22.0, −2.9, −8.9, and −8.2. Three are filled and well below zero, and
  the 8B circle is hollow near zero. In (b), one long green arrow climbs up and right (32B, +14.2), while the 14B
  points sit at the bottom left and barely move.
- **Fig. 4**: the bold gold line climbs from 0.39× to the A1 = 1 line. A green arrow at k=8 drops to "100k cache
  0.36×". In (b), two red bars plunge to about −30, and the teal bars beside them come back up with +19.8, +15.1,
  and +18.1.
