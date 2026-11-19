# Round 3 rewrite: meaning audit, second pass

Scope: the 8 fix items from `rewrite_audit.md`, the four extra cuts (a)–(d), and a scope check of every abstract and conclusion claim against the body. Sources: `paper/main.tex` (current), `cs632-store/body.tex` (the text the first audit reviewed), `cs632-store/main_pre_style.tex`, `numbers.tex`, `paper_numbers.py`, `paper/figs/data/fig4_scaling.json`, and per-cell values recomputed from `results/t07_main` and `t08_large` with `paper_numbers` helpers. The PDF is 6 pages. A sentence diff of `body.tex` against `main.tex` shows the fixes and cuts listed below, plus one restored item: the entity-match parenthetical. No other sentence changed.

## Fix items

| # | Verdict | Current text | Check |
|---|---|---|---|
| 1 | resolved | Abstract: "With sixteen questions split among three parallel Researchers, plain files lose \nGapBKSixteen points and files with an index \nGapCKSixteen, and a 4B model loses up to \nSmallCGapMax points with files even with an index." | The sentence now states k=16 and the index result (34 and 5). These match `fig4_scaling.json` (−33.9 and −5.1, both significant). `SmallCGapMax` (all k) and the body's `SmallCGapMaxThreeFive` are both 35. |
| 2 | resolved | "This cost is a large part of B's loss but, by a small margin, not all of it: A1w stays \nWOverB points above B (\nWOverBLo--\nWOverBHi)." | `a1w()` now prints one decimal: 3.2 (0.3–6.2), computed as A1w − B, so "above" is correct. The old "It is ... above B" sentence is gone. On these 200 tasks B's loss is 7.8 points (72.0 − 64.2) and A1w's is 4.7, about 60%, so "a large part" holds. Cosmetic: the sentence before gives the A1 gap as an integer, "5 (2–8)". |
| 3 | resolved | "leaves B's accuracy unchanged (\nScopeBDVsB points, 95\% interval \nScopeBDVsBLo to \nScopeBDVsBHi, \nScopeBDN tasks)" | Renders as +0.5, −2.8 to +3.8, 200 tasks. |
| 4 | resolved | "(A2d) answers \nScopeATwoDVsATwoAbs points more than the pipe on \nScopeATwoDN tasks (\nScopeATwoDVsATwoLo to \nScopeATwoDVsATwoHi), which still leaves it \nScopeATwoDVsAOneAbs points below broadcast (\nScopeATwoDVsAOneLo to \nScopeATwoDVsAOneHi)" | Renders as 6.8 (+3.5 to +10.2), 200 tasks, and 3.0 below (−5.3 to −0.7). The words match the signs. "What it lacks is the documents" is now qualified by the significant remaining gap. |
| 5 | resolved | "D's writers clash about as often, but its handoffs still carry each Researcher's findings, and D changes by \nFanDDiff{} points (\nFanDLo{} to \nFanDHi{})." | The overclaim is gone (+4, −2 to +10). The suggested "(\nFanClashD\%)" was not added. "About as often" is still true (89% vs B's 91%) but has no number behind it. Optional. |
| 6 | resolved | "The lost savings, not the accuracy collapse, come from the cache that concurrent runs share." | Consistent with "Accuracy changes by at most \nPressAccMax points" (3.8, B; C 0.6; zero-copy 0). |
| 7 | resolved | "Broadcast answers \nAccAOne{}\% of the questions at $k=3$, pooled, more than any other channel (Figure~\ref{fig:tradeoff})." | Pooled k=3: A1 72.3, A1-zc 71.6, C 66.3, D 65.1, B 62.8, A2 62.1. The abstract's "copying is the most accurate channel" and the conclusion's "broadcast, the most accurate channel" also hold pooled at k=1 and k=5. At k=1, A1 and A1-zc are both 74.0 and C is 73.7 (−0.3, −5.0 to +4.3). That is a tie, but not a reversal. |
| 8 | resolved | "Pooled at $k=3$, C comes within \nPooledGapC points of broadcast and trails it by at most \nGapCMax in any one setting, while B loses \nGapBMin--\nGapBMax points." | 6.0 pooled, and 8 is the 2Wiki k=3 cell (8.4), so there is no contradiction now. See new issue N4 for the B clause. |

Counts: 8 resolved, 0 partly, 0 not resolved.

The 10 note items (9–18) are unchanged in the text. Item 17 (`*Abs` macros without sign asserts) now covers one more sentence, since the item 4 fix pairs `\nScopeATwoDVsAOneAbs` "below" with a signed interval. Item 18 (the conclusion's `FileComp*` range covers B and C only, while D computes 0.53–1.00x at k ≤ 5) still stands.

## Extra cuts

| Cut | Loses a claim the paper relies on? | Check |
|---|---|---|
| (a) Intro: dropped ", and our aim is to measure what each channel costs"; kept "We propose no new protocol or engine change. Zero-copy broadcast needs only a prompt order." | No | The two sentences are still in `main.tex` (line 84), so only the aim clause was cut. The aim is already stated by "This paper presents a controlled comparison of inter-agent channels" and by the contributions. "No engine change" is also backed by §2 ("the engine is unmodified") and Related Work. |
| (b) Tool budget: kept B's Reviewer at k=16 (\nLargeBReviewerLimit = 52%), dropped B's Writer (32%) | No | The race paragraph says only "its Reviewer also runs out of budget", so the Writer number was not relied on. One remaining weakness is that "binds harder" has no k=3 comparator in the text (N3). |
| (c) Run-to-run noise: dropped "the same score on \nAABSame--\nAAAOneSame\% of tasks" | No | No sentence depends on per-task score agreement. "Each task runs once per channel" rests on the accuracy and B–A1 gap repeatability, which are still there. The `AABSame`/`AAAOneSame` macros are now unused. |
| (d) Conclusion: dropped "and cheaper bulk reads made it worse"; reworded the code-base limitation | No | The bulk-read result is still in §5 (8–16 point drop, 95%). The limitation keeps its meaning: artifacts larger than a context window are unmeasured, and files should matter most there. The only loss is that the conclusion's rules now cite nothing from the batched-read or pipeline-length experiments, which the third contribution bullet ties to the rules. That is acceptable, since the "naming discipline" rule covers the batched-read lesson. |

## New issues

| # | Where | Issue | Severity | Suggested fix |
|---|---|---|---|---|
| N1 | Conclusion: "In our runs zero-copy broadcast matched broadcast, the most accurate channel, and computed about as little as a pipe." | "In our runs" was added in the style rewrite (the old text had no such scope), and the first audit missed it. It overclaims: with Qwen3-4B, zero-copy costs \nSmallAZcGapMinThreeFive--\nSmallAZcGapMaxThreeFive points (3–11), significantly in three of four settings (§5, "A smaller model"). The abstract has a related gap. Its list of conditions ("These results are conditional ...") covers the 4B loss with files but not the 4B loss with zero-copy. The pipeline sentence scopes the abstract to Qwen3-8B, but a reader of the conditions list will assume zero-copy is model-independent. The conclusion's first sentence also ties the model dependence only to "how well its model uses tools", and the zero-copy loss is not a tool effect. | medium | Conclusion: "With Qwen3-8B, zero-copy broadcast matched ...". If space allows, add to the abstract's conditions: "... and zero-copy ordering costs the 4B model up to \nSmallAZcGapMaxThreeFive." |
| N2 | Abstract "Once the prompts of concurrent runs outgrow the KV cache, zero-copy saves nothing"; intro "They disappear when the agents' prompts no longer fit the KV cache" | This is carried over from the old text, but it now conflicts more visibly with §5. At k=8, §5 says six concurrent runs "no longer fit ... together", yet zero-copy still computes \nCompAZcKEight$\times$ (0.83, a 17% saving). "Nothing" is true only at k=16 (1.00). | low | Abstract: "... outgrow the KV cache, zero-copy's savings shrink and at sixteen questions vanish." Or in §5: "no longer fit ... together, and zero-copy keeps only part of its saving." |
| N3 | Tool budget: "At $k=16$ it binds harder (B's Reviewer hits it in \nLargeBReviewerLimit{}\% of runs)" | After cut (b), and after the earlier removal of \nForcedBReviewerBudget from Harness, the text gives no k=3 rate to compare against. Recomputed from `t07_main`, B's Reviewer hits the limit in 28.7% of runs at k=3 (Writer 8.7%), against 52% (Writer 32%) at k=16. The claim is true, but the reader cannot see it. | low | "... (B's Reviewer hits it in \nLargeBReviewerLimit{}\% of runs, against 29\% at $k=3$)". Add a macro from `hit_turn_limit` on `t07_main`, k=3, B reviewer. |
| N4 | Item 8 fix: "Pooled at $k=3$, C comes within ... in any one setting, while B loses \nGapBMin--\nGapBMax points." | The B range is per setting over all six (dataset, k) cells, not pooled at k=3 (pooled k=3 is 9.6). Because it follows "in any one setting" it is mostly readable, but the leading "Pooled at $k=3$" can be read as covering it. | low | "... while B trails it by \nGapBMin--\nGapBMax points in every setting." |
| N5 | Conclusion: "When the history does not fit, the pipe is the cheap choice, but its savings come from dropping the documents, which costs the Reviewer." | This is carried over. The Reviewer evidence (A2d, reviewer breaks) is from k=3. Where the history does not fit, the pipe loses 3 points at k=8 and 0.5 (not significant) at k=16, so "which costs the Reviewer" is not measured in the setting the sentence names. | low | "... but its savings come from dropping the documents, which at three questions costs the Reviewer." Or leave it and accept the k=3 mechanism as general. |

## Abstract and conclusion claims against the body

| Claim | Body support and scope | OK? |
|---|---|---|
| Cost counted as tokens sent and tokens computed | Metrics | yes |
| With small payloads, copying is the most accurate | Copying and zero-copy (k=3 pooled), Fig. 2. It also holds pooled at k=1 and k=5 (see item 7) | yes |
| Zero-copy keeps copying's accuracy at \nZcRatioMin--\nZcRatioMax\% of the tokens computed | Accuracy: "no difference is significant" (Qwen3-8B). The 38–49% range itself appears only in the abstract. The body gives 4.8k vs 12.4k and the intro gives 61% less (both k=3). The range spans the six (dataset, k) cells. | yes, but see N1 (4B) |
| Shared files send \nFileSentMin--\nFileSentMax$\times$ the tokens | Files cost more: "B and C ... across settings" | yes |
| 27% shorter notes through a tool call | Files lose information, "at $k=3$", and A1w | yes |
| Readers without an index skip notes | B's Writer never opens the notes in 42% of tasks, C's in 7% | yes |
| Zero-copy saves nothing once concurrent prompts outgrow the cache | Larger payloads at k=16, and the cache-pressure rerun | partly (N2) |
| k=16: plain files lose 34 points, files with an index 5 | Larger payloads | yes |
| 4B loses up to 35 points with files even with an index | A smaller model (C 19–35 at k=3,5) | yes |
| Conclusion: choice depends on payment, payload vs KV, model's tool use | Sections 4–5 | yes, but zero-copy also depends on the model (N1) |
| Zero-copy matched broadcast and computed about as little as a pipe | Copying and zero-copy (Qwen3-8B) | overclaims "in our runs" (N1) |
| When the history does not fit, the pipe is cheap but loses at review | k=8 and k=16 cost; Reviewer mechanism at k=3 | partly (N5) |
| Long results better as plain replies | A1w | yes |
| Files need naming discipline and a tool-capable model | C vs B, race paragraph, 4B | yes |
| Plain files cost more tokens and lost accuracy in every setting | B sends 1.8–3.4x at k ≤ 16 (fig4 data) and loses 6–14 points (6/6 significant), 8 at k=8, 34 at k=16, 21–31 at 4B | yes |
| Files sent more but computed \nFileCompMin--\nFileCompMax$\times$ at k ≤ 5 | Files cost more (B, C) | yes for B and C. D computes 0.53–1.00 (item 18 note) |
| Limitations: one model family, linear pipelines, multi-hop QA, no artifacts larger than a context window | Methodology | yes |
