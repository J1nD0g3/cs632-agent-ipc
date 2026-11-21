# Round 10 revision log

Snapshot before this round: `cs632-store/main_pre_round10.tex` (untouched). Build: 6 pages including
references (`pdfinfo`), no undefined references, no overfull boxes. Every number in the body is a macro from
`paper/numbers.tex`; `python -m agentipc.paper_numbers` reports no skipped section.

## 1. The 2x2 replaces the step-by-step writing split

- Results now cross how the notes are written (reply vs tool call) with how they reach the Writer (copied vs
  files): arms A1r, A1w, Bs, B, one interleaved run per size (p16, 150 tasks, 100k-token KV, 4,096-token cap).
- New Table 1 gives the four simple effects (WriteCopy, WriteFile, FileReply, FileTool) and the interaction
  with 95% intervals for all four sizes, so the text no longer carries a 25-number ledger.
- Text claims: the tool-call write lowers accuracy on copied notes at 4B, 8B and 32B (not 14B), where its
  notes hold fewer facts. Through files the stored reply does no better: B - Bs is 3.6 (4B) and -2.4 (8B), both
  intervals include zero, and +21.3 (14B) and +8.2 (32B). Delivery through files lowers accuracy for replies at
  all four sizes and for tool-written notes at all but 8B.
- Opening rates are reported only as rates: 32B Writer opens the stored notes.md in 24% of tasks vs 95% for
  the Researcher's own named files. At 4B and 14B it seldom opens notes in either arm (5/13%, 9/17%). No
  naming mechanism is claimed.
- The order dependence the reviewers raised is stated as the interaction ("above zero at all sizes but 8B,
  makes a stepwise split order-dependent"). The 8B replay result (5 points) is now reconciled with the
  stored-reply effect at 8B (-5.1), labelled cross-run.
- Holm: recomputed over the 16 simple effects of the 2x2 (paired sign-flip permutation, as before). Survivors:
  FileReply at 4B, 14B, 32B; FileTool at 4B, 14B, 32B; WriteFile at 14B, 32B; WriteCopy only at 4B
  (8B p = 0.013, 32B p = 0.018 uncorrected). Text, table daggers and abstract ("three of four sizes" when
  copied) follow this. The earlier p10 Holm result is no longer cited.
- The wording control (earlier p10 run) is kept in one sentence because all 2x2 arms use B's wording.
- Fig. 3 caption rewritten for the 2x2 (from `fig_split.py`'s docstring). The figure itself was already
  rendered from p16 and is unchanged.
- Conclusion advice changed: write long results as plain replies and copy them forward. Storing the reply as a
  file did not help (as well as tool-written files or worse, much worse at 14B and 32B). The old suggestion
  to store a plain reply as a file is gone.

## 2. Methodology introduces every setup before use

- New "Serving" and "Runs" paragraphs: the main run (Qwen3-8B, RTX 3090, 34,864-token KV, every setting), its
  three controls on 200 tasks and the Fig. 4 payload runs on the same servers, and the RTX PRO 6000 runs
  (100k-token KV unless stated). Each later run is introduced by the question it answers: cache vs payload
  (35k/100k/400k sweep), model size (Qwen3-4B, 8B, 14B, 32B), where files lose accuracy (2x2), whether
  parallel writers cause the large-payload loss (one vs three Researchers, repairs), and whether less prefill
  means less serving time (alone at 6 and 32 tasks at a time).
- `cache_salt` is now described per task pipeline (methods W10). Prefill is defined from each response's
  cached-token count.
- Defined on first use: channel, prefill and KV (intro), notes, heading rule, message/file channels
  (Fig. 1 caption), setting, main run, cross-run, fan-out (its paragraph).

## 3. Results and Sensitivity restructured

- Results opens with its four questions (cost, accuracy, where files lose, why readers miss the notes).
  Sensitivity opens with its three (payload vs cache, parallel writers, model size). Every run-in heading is a
  claim. Paragraphs follow figure, result with baseline, supported reason, lead-in to the next question.
- Serving-time paragraph now gives its reason from the data: decoding is 96% of broadcast's summed
  prefill+decode time, and zero-copy generates 1.2x the tokens. At 32 tasks at a time the median task takes
  0.82x broadcast's time but the batch 1.00x (methods W2). The decode-ms and prefill-time ratios were dropped
  (systems W1: the counters do not decompose wall time).
- Files' prefill is now also given against zero-copy (2.0x), and broadcast's near-zero cache reuse is stated
  (systems W1).
- Figure placement: figure* blocks moved in the source so Fig. 2 sits on p.3 (Results start), Fig. 3 and
  Table 1 on p.4 (2x2 text), Fig. 4 on p.5 (Sensitivity). No two of Figs. 2-4 share a page.
- Removed for space: the reply-output variant paragraph (Br, round 8) and the 32B path-fix rerun gaps (the
  ranges still count the rerun). The fan-out DiD number was dropped (the two changes it combines are given).

## 4. Style, grammar, and figures

- Fig. 4b retitled "B drops when three Researchers share a folder"; 4a "Prefill on a 35k-token cache";
  legend "A1-zc zero-copy". Fig. 2 arrow label "-61% prefill, no significant loss"; legend "A1-zc".
  Both re-rendered with archfig: fig_scaling lint clean, fig_tradeoff 0 defects (1 advisory: label near its
  own arrow, previously suppressed).
- Generator: signed Scope/AA macros no longer carry an explicit "+" (R8).
- Related work: added InferCept and CacheBlend (systems W8) with bib entries.

## Macros added (all in `round10_text`, `src/agentipc/paper_numbers.py`)

RTenHolmTests; RTenHolm{WriteCopy,WriteFile,FileReply,FileTool}SigWord; RTen{same four}SigWord (uncorrected);
RTenHolm{eff}P{Four,Eight,Fourteen,ThirtyTwo}; RTenMark{eff}{size} (table daggers); CapMain, CapSplit, Turns,
TurnsHi, Conc, ConcHi (from configs); KvProSmall, KvPro, KvProHi (from the PRO 6000 queue script's block
counts); CompRatioBAZc, CompRatioCAZc; RTenHiMedAZc, RTenMedAZc (median task latency ratios).

## style_grammar.md items not applied, and why

- Superseded by the 2x2 rewrite (the text they fix is gone): A8, A10, I15, R11, R12, R17-R20, R22, R23,
  R25-R27, S22.
- Removed with the reply-variant paragraph (cut for space): R34-R37.
- Removed with the delivery metric (replaced by open rates, systems W4): M11-M13.
- M17 (Researcher writes but reads none): sentence dropped for space.
- I16 partly: "payload, parallel writers, cache size, and tool budget" (kept short for the page budget).
- R3: kept "2Wiki" after defining it as the abbreviation in Tasks.
- R16: "copied forward" used with the A1 reference instead of "copied into the next prompts".
- S2: the neighbor caveat moved to the Fig. 4 caption ("KV cache interleaved channels share").
- S9 ("still fits in the context"): dropped the clause rather than assert the limit unverified.
- S18: "cross-run comparison" kept where a comparison crosses runs (now also on the replay-vs-2x2 and the
  tool-budget comparisons).
- G4: "the pipe recovers" removed with the new Fig. 4b title; arrow label now says prefill.
- All other items applied as written or in an equivalent shorter form.

## Not done

- Reviewer items that need new runs (trace replay, cache sweeps per channel alone, folders at k=16, a non-Qwen
  model, human labels for AlignScore, RTX PRO 6000 A/A rerun) are out of scope for this text revision.
- No run table (systems W9): the "Runs" paragraph introduces each run instead, for the page budget.
- `fig_split.py`'s docstring still says the stored reply is "under a generic name the Writer seldom opens";
  the open rates support that only at 32B, and the caption and text do not use it.
