# Round 10 coverage and setup review

Reviewer role: newcomer reading for coverage (is every run, model, GPU, cache, budget and term introduced before
use, with its purpose) and flow. Checked against `configs/*.yaml`, `results/*/env.json`, the
`results/pro6000*_kv_used.txt` ledgers and `src/agentipc/paper_numbers.py`.

## Verdict

Much improved. The new Serving/Runs paragraphs introduce the main run, the RTX PRO 6000, the cache sweep, the
model sizes, the 2x2 and the alone runs by the question each answers, and every task count, cap, concurrency and
cache size in the text matches the configs (150 per dataset per k; 300/200/150/100/60 tasks; 6 and 32 at a time;
2,048/4,096 caps; 12/24 calls; 34,864/100k/400k tokens). Results and Sensitivity read as questions answered by
claim headings, and a skim of headings and captions carries the argument. Five gaps remain:
(1) k=8 and k=16 and the three-Researcher fan-out are never introduced in Methodology, though Figure 4 and three
Sensitivity paragraphs rest on them;
(2) several runs appear only at their point of use (wording check, k=16 all-channel and 24-call runs, k=16
repairs), and the Runs list describes the scope run wrongly;
(3) the four arms of the 2x2 are named only in the Figure 3 caption;
(4) Figure 2's caption does not say which run or hardware it shows;
(5) a setup fact the paper does not state: the main run's `env.json` records a modified vLLM source build
(`vllm_src: /mnt/sda/heojin/cs506-store/vllm`, `vllm_src_dirty: true`, a patch to `block_pool.py`,
`kv_cache_utils.py` and the model runners), while the PRO 6000 runs used the stock 0.33.0 wheel. The paper says
only "vLLM v0.33.0".
All fixes below are a clause or a reworded sentence. Nothing needs to grow by more than a line.

## Findings

| # | location | problem | suggested fix |
| --- | --- | --- | --- |
| 1 | §3 Tasks; Fig. 4; §5 ¶1–3 | Tasks says "draw 150 tasks for each dataset and each k ∈ {1,3,5}". The k=8 (100 per dataset, `t08_k8`, seed 3) and k=16 (30 per dataset, `t08_large`, seed 4) draws behind Fig. 4 and §5 are never introduced. Their task counts (200 and 60) appear nowhere for the main servers. | Append to Tasks: "For larger payloads we also draw 100 (k=8) and 30 (k=16) tasks per dataset." Add "n = 300/200/60 tasks at k ≤ 5/8/16" to the Fig. 4 caption. |
| 2 | §2 Channels; Intro ¶3; Fig. 4 caption | The pipeline is introduced as one Researcher → Writer → Reviewer. "Parallel writers" (Intro, abstract) and three Researchers at k=16 first appear in the Fig. 4 caption and §5. A newcomer does not know the pipeline can fan out, or why k=16 does. | One sentence at the end of §2's first paragraph: "At sixteen questions, the Researcher's work fans out to three parallel Researchers, each given its questions and their documents (§5)." Give the reason for the fan-out in a few words if it is not just a design choice. |
| 3 | §3 Runs | "(documents for file agents, replayed notes, a rerun)". The scope run (`t09_scope`) also gives the pipe the documents (A2d), and §4 uses it for the pipe first. | "(documents passed to later agents, replayed notes, a rerun)". |
| 4 | §3 Runs vs §4 2x2, §5 | Runs that first appear at their point of use, with no Methods introduction: the wording check, "an earlier run" (`p10_write_*`); the k=16 all-channel PRO 6000 run where B trails by 33.9 (`p07_k16_kv100k`); the 24-call run (`p07_k16_b24`); the k=16 write-guard/heading run (`p12_k16_clobber`); the 4B notes replay (`p09_zcreplay_4b`); the 32B path-fix rerun (`p08_norm_32b`). The text also gives three k=16 B gaps (34, 30.4, 33.9) from three runs, so the reader cannot tell which is which. | Extend the parallel-writer question in Runs: "We vary the number of Researchers and test repairs (separate folders, a write guard, the heading rule, more tool calls)." Close with one line: "Smaller controls are described where used." In §5 ¶3, name the earlier run: "an earlier all-channel run on these tasks on the RTX PRO 6000". |
| 5 | §4 "The tool-call write..."; §3 Runs | The four arms of the 2x2 (reply/copied, tool/copied, reply stored as `notes.md`/files, tool/files = B) are spelled out only in the Fig. 3 caption. The text then relies on "the stored reply". | In Runs: "A run per size crosses how notes are written (a reply or a tool call) with how they reach the Writer (copied, or as files, where a reply is saved as `notes.md`)." This is the same length as the current sentence. |
| 6 | §3 Serving; env.json of `t07_main` and the other RTX 3090 runs | The main run's `env.json` records `vllm_src: .../cs506-store/vllm`, `vllm_src_dirty: true`. That tree carries a ~400-line patch to the block pool, KV-cache manager and model runners (another project's label-key and refresh changes, with defaults read from env vars such as `VLLM_PREFIX_REFRESH`). The PRO 6000 runs used the stock wheel (`vllm_src: ''`). The paper presents both as "vLLM v0.33.0", and it compares across these two builds (34,864-token vs PRO 6000 results, cross-run comparisons). | Verify that the patch, in the state it had on 2026-11-18, leaves unlabeled requests on stock code paths (the default LRU refresh in particular). If it does, state "unmodified v0.33.0 behavior". If not, disclose it in Serving and in the noise paragraph's caveat. |
| 7 | §3 Runs; Serving | "a 100k-token cache" reads as the PRO 6000's capacity. In fact every PRO 6000 run is capped with `--num-gpu-blocks-override` (6,250 blocks), and the "35k" arm is the RTX 3090's 34,864 tokens (2,179 blocks). The reader does not learn that the cache is held fixed across model sizes or that 35k reproduces the main servers. | "...with its KV cache capped at 100k tokens for every model size unless stated otherwise. ...We sweep 35k (the RTX 3090's cache), 100k, and 400k-token caches." |
| 8 | §3 Runs vs §5 ¶1 | Methods promises a 35k/100k/400k sweep for "does the cache or the payload limit prefill savings", but §5 reports only 35k vs 100k. 400k reappears only in the 32-at-a-time serving runs. | Report the 400k zero-copy ratio in four words in §5 ¶1, or drop 400k from the sweep sentence and mention it only with the 32-at-a-time runs. |
| 9 | §3 Runs (question order) | The Runs questions run cache, size, 2x2, parallel writers, serving time. The paper answers them in the order serving time (§4), 2x2 (§4), cache (§5), parallel writers (§5), size (§5). | Reorder the questions to follow the paper: serving time, where files lose, cache, parallel writers, model size. |
| 10 | §4 serving-time ¶ | "The pipe takes 0.78×... B and C take 1.80× and 1.56×" follows the 32-at-a-time sentence, but these ratios come from the 6-at-a-time runs. Only A1, A1-zc and B ran at 32 (`p11_c32_*`). Methods says "each channel alone ... at 6 and 32". | Move the pipe/B/C sentence before "In two runs at 32 tasks at a time". In Methods: "at 6 tasks at a time (and 32 for A1, A1-zc, B)". |
| 11 | Fig. 2 caption | The caption gives "k=3, datasets pooled, 300 tasks" but not which run, model or GPU. Fig. 3 and 4 state theirs, and the serving-time and 2x2 numbers nearby come from other hardware. | "(main run: Qwen3-8B on the RTX 3090 servers, k=3, ...)". |
| 12 | §4 opening sentence | "This section uses Qwen3-8B at k=3 with datasets pooled unless stated otherwise". Two of its seven claim paragraphs (serving time, the 2x2) use other runs and hardware. | "...uses the main run (Qwen3-8B, k=3, datasets pooled) unless stated otherwise." |
| 13 | §3 Harness and statistics; Table 1 | Methods introduces only bootstrap intervals and "no correction". Table 1 uses Holm-corrected paired permutation tests, which are explained nowhere. | Add to Harness: "Table 1 also gives paired permutation tests with Holm correction across its 16 effects." This lets the caption drop its explanation. |
| 14 | §3 Harness and statistics | The 4,096-token cap "in the crossed runs" has no reason. A reader may suspect a confound with the main run's 2,048. | Add the reason in a few words, e.g. "(so a tool call carrying all the notes is not cut off)", if that is the reason. |
| 15 | §3 Harness; §5 ¶1 | "Run" means both an experiment and one agent's or task's execution: "34–59% of the runs of B's Writer", "the KV of 6 concurrent runs". This collides with "main run" and "cross-run". | Use "tasks" ("in 34–59% of tasks for B's Writer...", "the KV of 6 concurrent tasks"). |
| 16 | §3 Metrics | The fact metric plotted in Fig. 3a and used in §4 ("state 32% of supporting facts") has no name. κ is not named. "Short prediction" is undefined. | "...we report the share of supporting sentences a text states (*fact coverage*)". "Cohen's κ". Give a length for "short" (e.g. "≤ N words") or drop it. |
| 17 | §5 "Run-to-run noise" | This paragraph is not announced in the §5 opener, and it holds the only caveat on the cross-run comparisons used throughout §4. A newcomer meets "a cross-run comparison" five times before learning the noise level. | Add "and how large run-to-run noise is" to the §5 opener. Optionally add a pointer in Harness: "(noise: §5)". |
| 18 | §5 noise ¶ | "A Researcher given the same prompt in two channels". The reader is never told which two channels give the Researcher identical prompts. | "...given the same prompt in broadcast and the pipe...". |
| 19 | §3 Runs | "(the larger payloads of Figure 4)" is a forward reference from p. 2 to a figure on p. 5. | Replace with "and the larger payloads of §5". |
| 20 | Fig. 4 panel (a) title vs caption | The panel title says "35k-token cache" and the caption says "34,864-token". | Fine once #7 defines 35k as the RTX 3090's cache. Otherwise use one form in both. |
| 21 | §2 A1-zc ¶ | A result (notes grow from 1,570 to 1,992 characters at three questions per task) sits in the channel definitions, before tasks and k are defined. | Move it to the zero-copy result paragraph in §4, or say "(§4)". This is space-neutral. |
| 22 | §4 ordering (optional) | §4 goes from main-run accuracy to the PRO 6000 four-size 2x2, then back to main-run reading behavior and controls. The "why readers miss the notes" evidence (main run) would lead into the 2x2 more naturally. | Optional reorder: "Files are less accurate" → "Without an index..." → "Files lose accuracy even with..." → the 2x2 pair. Fig. 3 and Table 1 would then float to p. 4/5; check the page budget before doing this. |

## Checked and consistent (no action)

- Figure placement: Fig. 1 on p. 2 (cited p. 2), Fig. 2 top of p. 3 (first cited p. 3), Fig. 3 and Table 1 on
  p. 4 (first cited at the p. 3/4 boundary and on p. 4), Fig. 4 on p. 5 (§5 starts at the end of p. 4). No two
  figures share a page.
- Counts match the configs: 150/dataset/k main (`t07_main`); 200 for repeat/replay/scope (`use_tasks: 100`);
  150 per size in the 2x2 (`p16_*`, `use_tasks: 75`, `max_tokens: 4096`); 200 per size (`p02_*`); 100 for the
  cache sweep, alone runs and fan-out (`use_tasks: 50`); 60 at k=16 (`p12`, `t08_large`); concurrency 6 per server
  (per-server semaphore in `run.py`) and 32 (`p11_c32_*`); `max_turns` 12/24; `max-model-len` 32,768.
- KV sizes match the ledgers: 34,864 tokens (2,179 blocks), 100,000 (6,250, every size incl. 32B at 0.95 util),
  400,000 (25,000).
- Terms defined at first use: channel, prefill, KV, notes, heading rule, setting, main run, rescue, cross-run,
  write guard, fan-out, cache_salt, AlignScore, tokens sent, serving time. Every cited system in Related Work has a
  one-clause description.
- The Results and Sensitivity openers each list their questions, and every run-in heading is a claim. A skim of
  headings, first sentences and captions conveys the argument. The exceptions are #11 and #17.
