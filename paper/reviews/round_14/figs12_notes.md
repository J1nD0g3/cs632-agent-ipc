# Round 14: Figures 1 and 2, as implemented

Scripts: `paper/figs/fig_mechanism.py`, `paper/figs/fig_tradeoff.py`. Data: `python -m agentipc.figdata`
writes `paper/figs/data/fig1_mechanism.json` (new) and adds `gap_vs_a1` and `zc_time` to
`fig2_tradeoff.json`. Both renders lint clean. Heights are unchanged: 139 pt and 134.03 pt.

Note: `paper/figs/data/` is matched by the `data` rule in `.gitignore`. The new `fig1_mechanism.json`/`.csv`
need `git add -f`, like the files already tracked there.

## Printed numbers against `numbers.tex`

A script checked every printed number against `numbers.tex`, and all of them match:

| Printed | Macro |
| --- | --- |
| Fig. 1 B `skipped 42%` | `\nNoNotesB` = 42 |
| Fig. 1 C `skipped 8%` | `\nNoNotesC` = 8 |
| Fig. 2a `−9.6 vs A1` (B) | `\nGapBKThree` = 9.6 |
| Fig. 2a `−6.0 vs A1` (C) | `\nGapCKThree` = 6.0 |
| Fig. 2a `−10.2 vs A1` (A2) | `\nGapATwoKThree` = 10.2 |
| Fig. 2b `−61% prefill` | `\nZcCut` = 61 |
| Fig. 2b `accuracy −0.8 (−2.9 to +1.4)` | `\nZcPooledDiff`, `Lo`, `Hi` |
| Fig. 2c 6 at a time, run time `1.09×`, whisker 1.08–1.10 | `\nRSixTimeAZc`, `Min`, `Max` |
| Fig. 2c 6 at a time, median task `0.99×`, whisker 0.99–1.00 | `\nRTwelveSixMedAZc`, `Min`, `Max` |
| Fig. 2c 32 at a time, run time `1.00×` | `\nRSixHiTimeAZc` |
| Fig. 2c 32 at a time, median task `0.82×`, whisker 0.81–0.83 | `\nRTenHiMedAZc`, `\nRThirteenHiMedAZc{Min,Max}` |

The "% cached" sublabels in Fig. 2b (1, 62, 1, 73, 73) were already in the figure. No macro holds them. They
are computed from `fig2_tradeoff.json` as 1 − prefill / prompt tokens.

## Figure 1 (`fig:channels`)

Proposed caption:

> Message channels copy earlier results into each prompt, while file channels leave them in a workspace
> where later agents must find them, and B's Writer never opened the notes in \nNoNotesB{}\% of tasks.
> Hatched prompt segments are reused from the prefix cache (zero-copy). Skip rates are from the main run
> (Qwen3-8B, $k=3$). C's index lists the notes, but C also adds the heading rule (\S\ref{sec:channels}).

Text reference (optional), §4.3(c), line 353:
"B's Writer never opens the notes in \nNoNotesB{}\% of tasks" → append "(Figure~\ref{fig:channels})".

## Figure 2 (`fig:tradeoff`)

Proposed caption:

> The costs rank the channels differently: files send the most tokens (a), broadcast computes the most
> prefill (b), and zero-copy cuts broadcast's prefill by \nZcCut{}\% at the same accuracy but does not shorten
> its runs (c). (a, b) Main run (Qwen3-8B, $k=3$, \nZcPooledDiffN tasks per channel). Tokens sent count
> prompt and completion tokens without cache discounts. Whiskers are 95\% intervals of each channel's mean,
> and the gaps beside the labels in (a) and the accuracy change in (b) are paired against A1. (c) Separate
> timing runs, each channel served alone on one RTX PRO 6000 (three runs with \nConcWord tasks at a time and
> two with \nConcHi), with min--max whiskers over runs (cross-run).

Text references:
- §4.1, timing paragraph, line 230: "With \nConcWord concurrent tasks, zero-copy's runs take ..." → cite
  "(Figure~\ref{fig:tradeoff}c)" after "its median task \nRTwelveSixMedAZc{}$\times$", and again after
  "but its batch \nRSixHiTimeAZc{}$\times$" (line 235).
- §4.2, line 244–245: "B's gap to broadcast ranges from ..." → add "(Figure~\ref{fig:tradeoff}a gives the
  gaps at $k=3$)". Line 242's existing "(Figure~\ref{fig:tradeoff})" can stay.
- §4.1 opening sentence ("though zero-copy's runs are no shorter") can cite Fig. 2c.
