# Round 14 figure plan: one claim per figure, magnitude on the figure

This is a plan only. No script, data file, or `main.tex` was changed. It targets the restructured outline:
§4.1 cost, §4.2 accuracy, §4.3 why files lose (a/b/c), §5.1 larger tasks, §5.2 parallel writers, §5.3 model size.
Every mark below comes from `results/` (via `src/agentipc/figdata.py`) or from `paper/numbers.tex`. No new
experiments are needed.

## Summary

| Fig | Section | One claim (what the eye must get in 3 s) | Key change |
| --- | --- | --- | --- |
| 1 | §2 (sets up §4.3c) | Message channels put results in the prompt. File channels make later agents find them, and B's Writer never opens the notes in **42%** of tasks. | Keep the mechanism. Redraw the file panels' reads so that the Writer→notes read is the drawn read. Label it with the measured skip rate (B 42%, C 8%). |
| 2 | §4.1, §4.2 | The three costs rank the channels differently. Files send the most tokens, broadcast computes the most prefill, and zero-copy cuts prefill **61%** at broadcast's accuracy but runs **1.09×** as long. | Keep panels (a) and (b), narrower. Add a slim panel (c) for zero-copy's serving time against broadcast. Put the paired accuracy gaps to A1 on the labels in (a). |
| 3 | §4.3 (a), (c) | Reading tool-written notes as files costs **8–22 points** at 4B, 14B, and 32B, but not significantly at 8B. Later agents rarely open a stored `notes.md` unless told its path, and telling the path helped only at 32B (**+14.2**). | **Swap.** Drop (a), fact coverage (AlignScore, κ 0.29). Replace (b), the raw 4-bar accuracy, with a paired-effect plot. Add a new (b) for finding the notes (told runs). |
| 4 | §5.1, §5.2 | Larger tasks expose two limits. Zero-copy's saving vanishes once the history outgrows the cache (0.39× → 0.83× → 1.00×, and 0.36× again with a 100k cache). Three Researchers sharing one folder lose about 20 points, which separate folders win back (**+19.8**). | Keep (a) and re-emphasize zero-copy. Add the cache-size control. **Swap** (b), accuracy against k, for parallel writers (k=8 folders, k=16 guard and heading). |

The total figure area stays the same: four `figure*` floats at the current heights (139, 134, 120, and 128 pt).
Fig. 1 can lose about 8 pt (see below) if page 6 gets tight. Table 1 stays. Its rows 1–3 become the glance
version in Fig. 3a, so they could later be relabeled in plain English (text work, see the last section).

Shared encoding across all four figures (unchanged from the current set): broadcast navy4 circle, zero-copy
gold star `#F2B53A`, pipe gray circle, B teal2 square, C teal4/5 square. Red (`bad`/red4) is used only for a
problem (a skipped read, the shared-folder loss). Green (`good`) is used only for a gain arrow (prefill cut,
told path, folders). Each figure has one or two call-outs with numbers.

---

## Figure 1: channel mechanisms (§2; the number serves §4.3c)

**(1) Claim.** Message channels copy earlier results into each prompt (zero-copy reuses that prefix from the
cache). File channels leave results in a workspace that later agents must find, and B's Writer never opens
the notes in 42% of tasks. This is the paper's IPC framing: shared memory avoids the copy but makes the
receiver find what it needs (Intro, para. 2).

**(2) Now.** The figure is a clean and correct definition of the five channels, but it carries no finding. In
the file panels, B's Writer is drawn reading only `d01..d30`, and both Reviewers only `draft`. Round-13 systems
W10 flagged this: the read that matters, Writer→notes, is not drawn. The 3-second read is "five pipelines",
not "files must be found".

**(3) Changes** (`paper/figs/fig_mechanism.py`):
- Message row: unchanged.
- File panels (B, C):
  - Replace the single generic "read, write" pair under the Writer with two reads from the Writer: one to
    `notes` and one to `d01..d30`. Keep the Writer's write to `draft`, and keep the Reviewer's read of
    `draft`.
  - Route the Writer→notes read so that it ends on the `notes` doc. The folder slots are already
    left-to-right (notes, docs, draft), and the read can start from the Writer's left side.
- B: draw the Writer→notes read dashed in red4 (`bad`) and label it beside the run: `skipped: 42%`
  (6.5 pt, red4). Source: `\nNoNotesB` = 42 (main run `results/t07_main/20261118-212337-5d6c70f`, k=3,
  B's Writer never reads a Researcher-written file, `writer_opened_notes`).
- C: draw the same read solid in navy4 from the Writer, and label it `skipped: 8%` (`\nNoNotesC`).
  Optionally add a short read from the Writer to `index` (navy5), so the index visibly leads to the notes.
- No other numbers. The caption carries the caveat that C also adds the heading rule.
- Optional, if page 6 is tight: `PANEL_H` 59 → 55 and the top strip from 14 to 13 save about 8 pt. The robots
  and strips have slack under the "to Writer" labels.
- 3-second check: the eye goes to the only red mark, the dashed B→notes read with "42%".

**(4) Caption.**
First sentence: *Message channels copy earlier results into each prompt, while file channels leave them in a
workspace where later agents must find them, and B's Writer never opened the notes in 42% of tasks.*
Rest: *Hatched prompt segments are reused from the prefix cache (zero-copy). Skip rates are from the main run
(Qwen3-8B, k=3). C's index lists the notes, but C also adds the heading rule (§2).*

---

## Figure 2: what copying costs (§4.1), with accuracy (§4.2)

**(1) Claim.** The three costs rank the channels differently. Files send the most tokens (a). Broadcast
computes the most prefill (b). Zero-copy cuts broadcast's prefill by 61% at the same accuracy, but its runs are
not shorter (c). The shared accuracy axis also carries §4.2: broadcast is on top, and files and the pipe trail
it by 6–10 points.

**(2) Now.** Reviewers rated it the best figure (round-13 systems S6, round-14 S1). It makes the sent-versus-prefill
inversion at a glance, with the −61% arrow and paired CI. Two gaps remain:
- The new §4.1 answer has a third part, "though not its run time", which has no mark.
- §4.2 has no figure of its own, and the per-channel whiskers are unpaired, so the reader cannot see how far B,
  C, and the pipe trail broadcast.

**(3) Changes** (`paper/figs/fig_tradeoff.py`):
- Layout: three panels in one row at the same height (118 pt body). Use `body.cols([1.0, 1.05, 0.62],
  gap=12)`, so (a) ≈ 175 pt, (b) ≈ 185 pt, and (c) ≈ 110 pt. Keep the y axis (accuracy 56–78%) in (a) and (b).
  (c) has its own axes.
- (a) Tokens sent: keep the markers and whiskers. Shorten the title to **"(a) Tokens sent per task"** (the
  billing note moves to the caption).
  - Append the paired gap to A1 to each non-A1 label, in gray5 at 6 pt on the second line:
    `B files` / `−9.6 vs A1`, `C files+index` / `−6.0`, `A2 pipe` / `−10.2`.
  - Do not add a gap line for A1-zc. (b) carries it.
  - Source: `figs/data/fig4_scaling.json` rows with k=3, `acc_diff` (paired, t07_main, same 300 tasks), which
    equal `\nGapB`-type main-run values at k=3. Check that they match the §4.2 ranges.
- (b) Tokens computed: keep the points, the "% cached" sublabels, and the green arrow. Collapse the call-out to
  two lines:
  - `−61% prefill` (bold), source `\nZcCut` / `fig2_tradeoff.json` prefill A1zc/A1
  - `accuracy −0.8 (−2.9 to +1.4)`, source fig4_scaling k=3 A1zc `acc_diff`, lo, hi
  
  Title: **"(b) Tokens computed (prefill) per task"**.
- (c) New: **"(c) Zero-copy time vs A1"**. Horizontal bars, ratio to broadcast, with a dashed line at 1 labeled
  `A1 = 1`. The x range is 0.6–1.2×, so the differences are visible. There are four rows in two groups,
  labeled at the left:

  | Row | Value | Whisker (min–max over runs) | Source |
  | --- | --- | --- | --- |
  | 6 at a time: run time | 1.09× | 1.08–1.10 | `\nRSixTimeAZc{,Min,Max}`. `elapsed_s` in `run_time.json` of `p06_alone_{A1,A1zc}`, `p11_alone_{A1,A1zc}_r{2,3}` |
  | 6 at a time: median task | 0.99× | 0.99–1.00 | `\nRTwelveSixMedAZc{,Min,Max}`. Median `wall_s` per run, same runs |
  | 32 at a time: run time | 1.00× | per-run min–max (compute) | `\nRSixHiTimeAZc`. `p11_c32_{A1,A1zc}_r{1,2}` |
  | 32 at a time: median task | 0.82× | 0.81–0.83 | `\nRThirteenHiMedAZc{Min,Max}`. Point = mean of the two per-run ratios (compute) |

  - Color: the bar the claim rests on (6 at a time, run time) is gold `#F2B53A` with an ink outline. The
    32-at-a-time median bar, the one gain, is `good` green. The other two are gray2.
  - Write each value at the bar end (6.5 pt).
  - Do not draw prefill tokens here. (b) already carries −61%. Putting both in (c) invites a ratio-of-ratios
    reading.
- Legend: unchanged (message, file, zero-copy, 95% CI). (c) needs no legend, because its rows are labeled.
- 3-second check:
  - (a): squares far right.
  - (b): circle far right, star far left, green arrow "−61%".
  - (c): the gold bar crosses the A1 = 1 line.

**Data plumbing.** Extend `figdata.fig2` to write `fig2_tradeoff.json["zc_time"]` = list of
`{row, value, lo, hi, runs:[...]}`. Use the same `latest()` runs and the same formulas as
`paper_numbers.round6`, `round12`, and `round13` (quoted above), so that the figure equals the macros. Copy the
k=3 `acc_diff`/lo/hi per channel into `fig2_tradeoff.json["gap_vs_a1"]` from the `fig4` computation, rather than
reading the other JSON in the script.

**(4) Caption.**
First sentence: *The costs rank the channels differently: files send the most tokens (a), broadcast computes
the most prefill (b), and zero-copy cuts broadcast's prefill by 61% at the same accuracy but does not shorten
its runs (c).*
Rest:
- *Main run (Qwen3-8B, k=3, \nZcPooledDiffN tasks per channel).*
- *Tokens sent count prompt and completion tokens without cache discounts.*
- *Whiskers are 95% intervals of each channel's mean. Gaps beside the labels are paired against A1.*
- *(c) uses separate timing runs, each channel served alone on one RTX PRO 6000 (three runs with six tasks at a
  time, two with 32), with min–max whiskers over runs (cross-run).*

---

## Figure 3: why files lose (§4.3a, §4.3c) — swap the fact-coverage panel

**(1) Claim.**
- (a) Reading tool-written notes as files instead of copying them costs 8–22 points at 4B, 14B, and 32B
  (Holm-significant), but not significantly at 8B.
- (b) Later agents rarely open a stored `notes.md` that nobody points them to. Telling them the path made the
  32B Writer open it (26% → 86%) and gained 14.2 points, while the 14B Writer still ignored it.

Both halves serve §4.3's question. (a) is the confirmatory answer. (b) is the "finding the notes" thread, which
the Conclusion turns into a rule ("naming the notes' path ... helped at 32B but not at 14B") and which has no
figure today.

**(2) Now.**
- (a), fact coverage: rests on AlignScore. That measure agrees with an 8B judge at κ 0.29 (round-13 systems
  W6, round-14 systems W6 "drop Figure 3a"). It shows the paper's weakest measure first.
- (b), accuracy: shows four raw-accuracy bars per size. The claim needs bar 2 against bar 4 (non-adjacent), the
  two pale colors are hard to tell apart, and no paired difference or Holm mark is visible (round-13 W10,
  round-14 W7).
- The figure does not say "−8 to −22" anywhere. The reader has to subtract bar heights.

**(3) Changes** (`paper/figs/fig_split.py`; keep the name and label `fig:split`, or rename to `fig_cause.py`
with label `fig:cause`):

- **Drop panel (a) fact coverage entirely.** The text keeps its one caveated sentence (see the text notes).

- **New (a): "(a) Accuracy change, per size (points)"**, paired effects with 95% intervals. Categories are
  4B, 8B, 14B, 32B, with three dodged series. The y range is −40 to +5, with a zero line labeled `no change`.

  | Series | Style | Source (`numbers.tex`, from `results/p16_store_{4b,8b,14b,32b}`) |
  | --- | --- | --- |
  | Files instead of copying, **tool-written notes** (the claim) | teal5, d=4.6, value printed beside: −22.0, −2.9, −8.9, −8.2 | `\nRTen{Four,Eight,Fourteen,ThirtyTwo}FileTool{,Lo,Hi}` |
  | Files instead of copying, stored reply | teal2, d=3.4, no labels | `\nRTen*FileReply{,Lo,Hi}` |
  | Tool-call write instead of reply, copied | gray3, d=3.4, no labels | `\nRTen*WriteCopy{,Lo,Hi}` |

  - Holm significance: a filled marker means Holm-significant in the 16-effect family, and a hollow marker means
    not. The flags come from the `\textbf...\dag` wrapping of `\nRTenCell{FileReply,FileTool,WriteCopy}{size}`,
    so they cannot disagree with Table 1. Add one legend entry, "hollow = not Holm-significant".
  - The 8B tool-written marker is hollow (CI −6.2 to +0.4). This is the point of the "but not at 8B" half, so it
    keeps its "−2.9" label.
  - Tick label `4B` becomes the two-line `4B\nall rescued` in gray5 6 pt. Every 4B file task was rescued
    (`\nRTenFourRescueToolFile` = 100). This keeps the paper's caveat attached to the −22.0 point in the
    figure.
  - The y extent, from −34.2 (4B stored reply) to +2.7, fits −40…+5 without clipping.
  - 3-second check: four dark teal points with numbers, three filled below zero and the 8B one hollow near
    zero.

- **New (b): "(b) Finding the stored notes (told runs, exploratory)"**. A scatter that shares the accuracy idiom
  of Fig. 2:
  - x: Writer opens the notes (% of tasks), 0–100.
  - y: accuracy, 40–75%.
  - Six points, from one run per size (`results/p17_told_14b/20261121-162008-269814b`,
    `results/p17_told_32b/20261121-162025-269814b`). Each run holds all three arms on the same 150 tasks.

  | Point | x (Writer opens) | y (accuracy) | Macros |
  | --- | --- | --- | --- |
  | 14B tool-written | 99 | 63.8 | `\nRToldFourteenOpenTool`, `\nRToldFourteenAccTool` |
  | 14B stored, untold | 9 | 43.3 | `...OpenUntold`, `...AccUntold` |
  | 14B stored, told path | 5 | 44.2 | `...OpenTold`, `...AccTold` |
  | 32B tool-written | 93 | 63.6 | `\nRToldThirtyTwoOpenTool`, `...AccTool` |
  | 32B stored, untold | 26 | 56.0 | `...OpenUntold`, `...AccUntold` |
  | 32B stored, told path | 86 | 70.2 | `...OpenTold`, `...AccTold` |

  - Marker shape encodes size: circle for 14B, square for 32B. Fill encodes the arm: teal4 for tool-written,
    white with a teal4 outline for stored untold, teal2 for stored told. Label every point directly. With six
    points, no legend is needed.
  - Call-out (the claim): a `good` green arrow from 32B untold to 32B told, labeled
    `+14.2 pts (10.2 to 18.4)`. Source: `\nRToldThirtyTwoToldOverUntold{,Lo,Hi}`, paired, N=150.
  - A short gray5 arrow from 14B untold to 14B told, labeled `+0.9 (−2.0 to 4.0)`. Source:
    `\nRToldFourteenToldOverUntold{,Lo,Hi}`.
  - 3-second check: one long green arrow up-right (32B), one stub that barely moves (14B), and the tool-written
    notes at the top right.
  - Considered and rejected as (b): the draft/final stage panel. It is solid, but it explains only the 14B/32B
    "different stages" detail, and Table 1's draft/final rows already hold it.

- Panel split: `body.cols([1.15, 1], gap=18)`. (a) needs room for four groups of three dodged whiskers.
- Legend strip: replace the current 4-arm legend with the (a) series legend (3 entries plus the hollow
  convention). (b) is labeled directly.
- Remove `fig.ignore.add("grayscale")`. The new encodings differ in shape, fill, and tone, so they no longer
  depend on two pale hues.

**Data plumbing.** Replace `figdata.fig3_split()` with `fig3_cause()`, which writes `fig3_cause.json` and `.csv`
with:
- `effects`: per size and effect, `mean`, `lo`, `hi`, `holm` (bool). Parse these from `paper/numbers.tex`, so
  that Fig. 3, Table 1, and the text are one source. Alternatively, call the same routine `paper_numbers.round10`
  uses. Parsing is simpler and guarantees agreement.
- `told`: the six points and the two paired arrows, from the `RTold*` macros, with the run paths copied from
  `paper_numbers.round12_told`'s `latest("p17_told_*")`.
- `source` paths for both.

**(4) Caption.**
First sentence: *Reading tool-written notes as files instead of copying them costs 8–22 points at 4B, 14B, and
32B but not significantly at 8B (a), and later agents rarely open a stored `notes.md` unless told its path,
which helped at 32B only (b).*
Rest:
- *(a) Crossed runs (k=3, \nRTenN tasks), paired effects with 95% intervals. Filled markers are
  Holm-significant (§3), and at 4B every file task was rescued.*
- *(b) Told runs (one per size, \nRToldThirtyTwoToldOverUntoldN tasks), exploratory and uncorrected. Arrows give
  the paired change from telling later agents the path.*

---

## Figure 4: what breaks as tasks grow (§5.1, §5.2) — swap the accuracy-vs-k panel

**(1) Claim.**
- (a) Zero-copy's prefill saving needs the shared history to fit in the cache. It goes from 0.39× of
  broadcast's prefill at k=3 to 0.83× at k=8 and 1.00× at k=16. On the same k=8 tasks, a 100k-token cache brings
  it back to 0.36×.
- (b) Three Researchers sharing one folder trail broadcast by about 28 points at k=8, against about 8 with one
  Researcher. Separate folders win 19.8 points back. At k=16, a write guard or the heading rule recovers about
  half of the loss.

This is two findings under one heading, "limits as tasks grow". A single-claim version would need a fifth float,
which page 6 cannot afford. Each panel title states its own claim.

**(2) Now.**
- (a) carries §5.1, but its subtitle ("savings fade as payloads grow, except the pipe's") describes a
  correlation with k. The paper's actual claim is about cache capacity, and the decisive evidence, the
  35k/100k/400k cache control, is text-only. All four series have equal weight.
- (b) shows accuracy against k. Its only striking mark is B at k=16, and the subtitle itself admits that this
  confounds payload with three Researchers. The paper resolves that confound in §5.2 (k=8 one versus three
  Researchers, folders, guard, heading), but none of that is drawn. Round-14 systems: "the k = 8 folder result,
  which is an abstract claim, has no figure."

**(3) Changes** (`paper/figs/fig_scaling.py`):

- **(a) keep, re-weighted. Title: "(a) Prefill vs A1: zero-copy's saving needs cache room"**
  - Zero-copy line: gold, sw 1.6, stars d 5. The other lines go pale and thin (sw 0.8): pipe gray2, B teal2,
    C teal3. Keep the markers so that the series stay identifiable through the legend.
  - Value labels on zero-copy only, from `fig4_scaling.json` `comp_rel` (`\nCompAZcK{Three,Eight,Sixteen}`):
    `0.39×` at k=3, `0.83×` at k=8, `1.00×` at k=16.
  - New cache-size control at k=8 (cross-run, one RTX PRO 6000, \nPKvThirtyFiveN tasks), drawn just right of the
    k=8 tick (x + 0.18):
    - a hollow gold star at 0.85×, labeled `35k cache` (`\nPKvThirtyFiveCompAZc`, `results/p01_cache_35k/20261119-123811-4c8ded9`)
    - a hollow gold star at 0.36×, labeled `100k cache` (`\nPKvHundredCompAZc`, `results/p01_cache_100k/20261119-123813-4c8ded9`;
      400k gives the same 0.36×, `\nPKvFourHundredCompAZc`)
    - a `good` green arrow down between them
    
    This makes "the cache, not k" visible.
  - Keep the dashed separator and change the k=16 tick to `16 (3 Researchers)`, which matches (b) and the text.
  - Keep `A1 = 1`.
  - 3-second check: the bold gold line climbs to the A1 line, and the green arrow at k=8 drops back down with
    "100k cache".

- **(b) replace. Title: "(b) Parallel Researchers: one shared folder loses"**. Vertical bars of accuracy minus
  broadcast (points), paired by task within each run, with 95% intervals. Two groups separated by a dashed
  `seps` line:

  | Group | Bar | Value (pts) | Source |
  | --- | --- | --- | --- |
  | k = 8 (one server, \nREightFanBN tasks) | 1 Researcher, B | ≈ −7.8 (compute) | `results/p15_k8_one/20261120-162056-574056f`, B − A1 per task |
  | | 3 Researchers, shared folder (B) | ≈ −28.1 (compute) | `results/p15_k8_three/20261120-164612-574056f`, B − A1 |
  | | 3 Researchers, own folders (Bf) | ≈ −8.3 (compute) | same run, Bf − A1 |
  | k = 16 (one RTX PRO 6000, \nRSixKSixteenBGapN tasks) | 3, shared folder (B) | −30.4 (−35.1 to −25.7) | `\nRSixKSixteenBGap{,Lo,Hi}` negated, `results/p12_k16_clobber/20261120-114319-f9cd71b` |
  | | + write guard (Bn) | −15.3 (−20.3 to −10.3) | `\nRSixKSixteenGuardGap{,Lo,Hi}` negated |
  | | + heading rule (Bh, 59 tasks) | −12.6 (−18.2 to −7.2) | `\nRSixKSixteenHeadingGap{,Lo,Hi}` negated |

  The ≈ values are the unpaired differences of the existing macros (`\nREightOneBAcc` − `\nREightOneAOneAcc`,
  and so on). `figdata` computes the paired means and CIs with `agentipc.stats.paired`, the function
  `paper_numbers.round8.gap` uses.

  - Colors: 1 Researcher gray3 (reference). Shared-folder bars red4 (the problem). Own folders, guard, and
    heading teal4 (file-channel fixes). Print the value under each bar end (6.5 pt).
  - Call-outs:
    - k=8: a green `ax.gain`-style arrow from the shared-folder bar top to the own-folders bar top, labeled
      `+19.8` (`\nREightFoldersOverB`; its CI 15.6–23.6 goes in the caption).
    - Under the shared-folder bar: `same path: 99%` (gray5 6 pt, `\nREightClashB`).
    - k=16: one bracket over guard and heading, labeled `recover ½` (`\nRTwelveShareGuard` 50%,
      `\nRTwelveShareHeading` 59%). If the bracket crowds the bars, use two small `+15.1` and `+18.1` labels
      (`\nRSixKSixteen{Guard,Heading}OverB`).
  - y range −40 to +5, with a zero line labeled `A1`.
  - 3-second check: two red bars plunge, and the teal bars beside them come back up, the k=8 one with "+19.8".

- Legend: keep the four-series line legend for (a) only, centered over (a). (b) is labeled by its x tick labels,
  which are two-line, for example `3 Res.\nshared`. This drops "Paired 95% CI" from the shared legend, so
  mention whiskers in the caption.
- Height: unchanged (112 pt body).

**Data plumbing.** Extend `figdata.fig4` with:
- `cache_ctrl`: the three PKv values, recomputed as `paper_numbers.pro6000` does: mean A1zc prefill over mean A1
  prefill per `p01_cache_*` run.
- `writers`: the six bars above, with `mean`, `lo`, `hi`, `n`, `source`.
- `gains`: FoldersOverB and the two OverB values, plus the shares, from `numbers.tex`.

**(4) Caption.**
First sentence: *Larger tasks expose two limits: zero-copy's prefill saving disappears once the shared history
outgrows the KV cache (a), and three Researchers sharing one folder lose about 20 points that separate folders
win back (b).*
Rest:
- *(a) RTX 3090s, each with a \nBigKv-token cache that \nConcWord concurrent tasks of mixed channels share
  (\nScaleNMain tasks at k ≤ 5, \nScaleNEight at 8, \nScaleNSixteen at 16 with three Researchers). Hollow stars
  are the same k=8 tasks on one RTX PRO 6000 with a 35k or 100k cache (cross-run).*
- *(b) Accuracy minus broadcast in the same run (paired, 95% intervals). At k=8, the one- and three-Researcher
  runs ran back to back on one server, and separate folders gain \nREightFoldersOverB points (\nREightFoldersOverBLo
  to \nREightFoldersOverBHi) but also change the Writer's paths.*

---

## What has no figure, and why that is acceptable

- **§4.2 pipe's Reviewer** (turns right answers wrong in up to \nPipeBrokeMax%): one number. The pipe's −10.2
  label in Fig. 2a carries its accuracy cost.
- **§4.3(b) rescues**: descriptive and channel-dependent (the text calls the split descriptive). Fig. 3a's
  "4B: all rescued" tick keeps the one caveat that changes a claim.
- **14B Reviewer reading `draft.md` in 1–8%**: kept in text and Table 1's draft/final rows. Adding it to Fig. 3b
  would mix a per-size rate with per-arm points.
- **§5.3 model size**: three ranges and two exceptions (pipe at 8B, zero-copy at 4B), which read fine in text. A
  size panel would need a fifth float.
- **Accuracy against k** (old Fig. 4b): §4.2 already gives the six-setting ranges. The k=16 B drop it showed is
  now explained by Fig. 4b instead of being left confounded. Lost: the pipe's gap shrinking with k (round-13
  question 10), which the text does not discuss.

Not adopted: a cached-input API-price panel for Fig. 2 (round-14 systems), because it is a new claim and not a
revision. Old `fig_loss.py` and `fig_channels.py` (unused, Nov 18–20) stay unused.

## Text changes these figures need (for whoever edits `main.tex` after the restructure)

- §4.1: cite Fig. 2c in the timing paragraph ("... and its median task \nRTwelveSixMedAZc× (Figure 2c)").
- §4.2: cite Fig. 2a for the gaps.
- §4.3(a), coverage sentence: drop "(Figure~\ref{fig:split}a)". Keep the sentence with its "a weak measure"
  caveat, or cut it.
- §4.3(a): cite Fig. 3a for the read cost.
- §4.3(c): cite Fig. 3b at the told-run sentences.
- §5.1: cite Fig. 4a for the cache-size control as well ("Figure 4a, hollow stars").
- §5 k=8 and k=16 paragraphs: "B's loss (Figure~\ref{fig:scaling}b)" now refers to the parallel-writer panel.
  The sentence "At sixteen questions, B's loss mixes ..." can cite Fig. 4b directly.
- The Fig. 1 caption now carries `\nNoNotesB`. §4.3(c) can refer back to it.
- Table 1 (optional, text work): give rows 1–3 the plain labels used in Fig. 3a's legend, so the two read as one
  source.

## Build and acceptance checks

1. `python -m agentipc.figdata`, then `archfig run` on each of the four scripts. Fix every lint defect, and
   justify any advisory with `fig.ignore`.
2. `archfig run ... --gray` (or view the gray render) for Fig. 3a. The three series must separate by size and
   fill, not by hue alone.
3. Every printed number must equal its macro: −61, −0.8, 1.09, 0.99, 1.00, 0.82, −22.0, −2.9, −8.9, −8.2,
   +14.2, +0.9, 0.39, 0.83, 1.00, 0.85, 0.36, +19.8, 99%, −30.4, −15.3, −12.6, 42%, 8%. Diff the figure JSON
   against `numbers.tex` with a small script before rendering.
4. Rebuild the paper. The body must still end on page 6, and figure heights must not grow. If they do, apply the
   Fig. 1 `PANEL_H` trim.
5. For each PNG, write one sentence saying what it shows in 3 s. It must match the caption's first sentence.
