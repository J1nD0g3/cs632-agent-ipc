# Experiments

Each experiment ID has one config, `configs/<id>.yaml`, and one finished run, `results/<id>/<run_id>/`. IDs
starting with `t` ran on RTX 3090s, IDs starting with `p` on RTX PRO 6000s. Appendix C of the paper (Table "Every
run") lists the same runs; this file adds the IDs and the runs the paper does not use.

Shared settings unless a row says otherwise: vLLM v0.33.0 with prefix caching, 16-token KV blocks, a 32,768-token
context, the `hermes` tool parser, greedy decoding with thinking disabled; token cap 2,048 per call, tool budget 12
calls per agent, 6 pipelines at a time per server, one Researcher per task. Tasks are counted over both datasets
(HotpotQA and 2Wiki, equal halves); a run with fewer tasks uses the first tasks of the same draw (`use_tasks`), so
it pairs with larger runs task by task. KV is the cache capacity in tokens: on the RTX 3090s (24 GB, memory
utilization 0.90) vLLM sized it from free memory; on the RTX PRO 6000 (96 GB, utilization 0.92, 0.95 for 32B) it
was fixed with `--num-gpu-blocks-override` (2,179 / 6,250 / 25,000 blocks = 34,864 / 100,000 / 400,000 tokens).

Status: **used** (in the paper body), **appendix** (only in the appendix), **superseded** (computed by
`paper_numbers.py` or kept for the record, but a later run replaced it), **setup** (smoke or pilot).

## RTX 3090 runs (Qwen3-8B unless noted)

| ID | Purpose | GPUs / KV | k | Tasks | Arms | Paper | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `t01_smoke` | Harness smoke test | 3x RTX 3090 | 1, 3 | 2 per k (HotpotQA only) | A1 A1zc A2 B C D | -- | setup |
| `t06_pilot` | Pilot of all channels | 3x RTX 3090 | 1, 3, 5 | 20 per k | A1 A1zc A2 B C D | -- (feeds the unused `fig_channels.py`) | setup |
| `t07_main` | **Main run**: every channel and setting | 3x RTX 3090, 34,864 | 1, 3, 5 | 300 per k | A1 A1zc A2 B C D | Figs. 1, 2a-b, 4a; Sec. 4.1-4.3; App. A-H | used |
| `t08_k8` | Larger payload, eight questions | 3x RTX 3090, 34,864 | 8 | 200 | A1 A1zc A2 B C D | Fig. 4a; Sec. 5.1 | used |
| `t08_large` | Sixteen questions, three parallel Researchers | RTX 3090, 34,864 | 16 | 60 | A1 A1zc A2 B Bb C D | Fig. 4a; Sec. 5.1; App. H (path clashes) | used |
| `t09_scope` | Documents control: documents in later prompts | RTX 3090, 34,864 | 3 | 200 | A2d Bd | Sec. 4.2 | used |
| `t09_replay` | Replay control: broadcast's notes in every channel | 3x RTX 3090, 34,864 | 3 | 200 | A1 A2 B C | Sec. 4.2 | used |
| `t09_repeat` | Rerun of A1 and B for decoding noise | 3x RTX 3090, 34,864 | 3 | 200 | A1 B | Sec. 3 (Noise) | used |
| `t08_batch` | Batched reads (`read_files` tool) | RTX 3090, 34,864 | 3 | 200 | Bb | App. H | appendix |
| `t08_chain4` | Four-agent chain with a Fact-checker | 3x RTX 3090, 34,864 | 3 | 200 | A1 A1zc A2 B C D | App. H | appendix |
| `t08_fanout` | Three Researchers at k = 3 | RTX 3090, 34,864 | 3 | 100 | A1 A1zc A2 B Bb C D | App. H | appendix |
| `t08_qwen4b` | All channels with Qwen3-4B | 3x RTX 3090, 89,504 | 1, 3, 5 | 200 per k | A1 A1zc A2 B C D | App. H | appendix |
| `t08_turns24` | Tool budget 24 at k = 3 | RTX 3090, 34,864 | 3 | 100 | B Bb C D | -- (budget 24 at k = 16 is `p07_k16_b24`) | superseded |
| `t08_pressure_c1`, `t08_pressure_c2` | k = 16 tasks at 1 and 2 pipelines per server (cache pressure) | RTX 3090, 34,864 | 16 | 10 | A1zc B C D | -- (replaced by the cache runs `p01_*`) | superseded |
| `t09_a1w` | Tool-written notes, copied (8B) | RTX 3090, 34,864 | 3 | 200 | A1w | -- (replaced by `p10_write_*`, `p16_store_*`) | superseded |

## RTX PRO 6000 runs (one GPU per run)

| ID | Purpose | Qwen3 / KV | k | Tasks | Arms | Paper | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `p01_cache_35k`, `p01_cache_100k`, `p01_cache_400k` | **Cache runs**: same tasks, three KV sizes | 8B; 34,864 / 100,000 / 400,000 | 8 | 100 | A1 A1zc A2 B C D | Fig. 4a (hollow stars); Sec. 5.1; App. G | used |
| `p02_size_4b`, `_8b`, `_14b`, `_32b` | **Size runs**: the main comparison at four sizes | 4B/8B/14B/32B; 100,000 | 3 | 200 | A1 A1zc A2 B C D | Sec. 5.3, Sec. 3 (GPU drift, 8B); App. G | used |
| `p08_norm_32b` | **32B path rerun**: B, C, D with `workspace/` stripped from paths | 32B; 100,000 | 3 | 200 | B C D | Sec. 5.3; App. G | used |
| `p09_zcreplay_4b`, `_8b` | **Zero-copy replay**: broadcast's notes replayed into A1 and A1-zc | 4B, 8B; 100,000 | 3 | 200 | A1 A1zc | Sec. 5.3 | used |
| `p10_write_4b`, `_8b`, `_14b`, `_32b` | **Wording runs**: B's Researcher wording, notes as reply or tool write (cap 4,096) | each size; 100,000 | 3 | 150 | A1 A1r A1w B | Sec. 4.3, Sec. 3 (drift); App. G | used |
| `p16_store_4b`, `_8b`, `_14b`, `_32b` | **Crossed runs**: 2x2 of how notes are written x how later agents get them (cap 4,096) | each size; 100,000 | 3 | 150 | A1r A1w Bs B | Fig. 3a; Table 1; Sec. 4.3; App. F | used |
| `p14_read_4b`, `_8b`, `_14b`, `_32b` | **Reply-output runs**: later agents read files but reply (cap 4,096) | each size; 100,000 | 3 | 150 | A1w Br B | Sec. 4.2-4.3; App. H | used |
| `p17_told_14b`, `p17_told_32b` | **Told runs**: the stored notes' path named in later agents' prompts (cap 4,096) | 14B, 32B; 100,000 | 3 | 150 | Bs Bt B | Fig. 3b; Sec. 4.3 (exploratory) | used |
| `p18_first_14b` | **First-listed run**: stored notes as `00_notes.md` (cap 4,096) | 14B; 100,000 | 3 | 150 | Bt Bs0 Bt0 B | Sec. 4.3 (exploratory) | used |
| `p06_alone_<ch>`, `p11_alone_<ch>_r2`, `_r3` | **Timing runs**: each channel alone on its own server, three runs (`<ch>` = A1, A1zc, A2, B, C, D) | 8B; 100,000 | 3 | 100 | one channel each | Fig. 2c; Sec. 4.1; App. G | used |
| `p11_c32_<ch>_r1`, `_r2` | Timing at 32 pipelines at a time (`<ch>` = A1, A1zc, B) | 8B; 400,000 | 3 | 100 | one channel each | Fig. 2c; Sec. 4.1 | used |
| `p07_k16_kv100k`, `p07_k16_b24` | **k = 16 budget runs**: tool budget 12 vs 24 (B only in `b24`) | 8B; 100,000 | 16 | 60 | A1 A1zc A2 B C D / B | Sec. 5.2 | used |
| `p12_k16_clobber` | **k = 16 guard run**: write guard and heading rule | 8B; 100,000 | 16 | 60 | A1 B Bn Bh | Fig. 4b (right); Sec. 5.2 | used |
| `p15_k8_one`, `p15_k8_three` | **k = 8 folder runs**: one vs three Researchers, and separate folders (back to back on one server) | 8B; 100,000 | 8 | 100 | A1 B / A1 B Bf | Fig. 4b (left); Sec. 5.2 | used |
| `p03_corner_32b_35k` | 32B with the smallest cache | 32B; 34,864 | 8 | 100 | A1 A1zc A2 B C D | App. G-H | appendix |
| `p05_a1r_<size>`, `p05_a1w_<size>` | Reply vs tool-written notes, copied, as separate runs | each size; 100,000 | 3 | 200 | A1r / A1w | -- (replaced by the in-run `p10_write_*`) | superseded |
| `p13_k8_fanout` | Three Researchers at k = 8, against `p01_cache_100k` across runs | 8B; 100,000 | 8 | 100 | A1 B C | -- (replaced by the in-run `p15_k8_*`) | superseded |

Section numbers follow the paper: 3 Methodology, 4.1 cost, 4.2 accuracy, 4.3 causes, 5.1 larger tasks, 5.2
parallel Researchers, 5.3 model size; appendices B (prompts), C (serving and every run), D (worked example),
E (fact measures), F (statistics), G (full results), H (cut results).

## Fact scoring

Fact coverage (`as_*` columns, AlignScore-large) was scored after the runs for `t07_main`, `t08_large`,
`t09_scope`, `t09_replay`, `t09_a1w`, and every RTX PRO 6000 run except the timing runs, `p07_*`, `p09_*`, and
`p18_first_14b`. The Qwen3-8B fact judge (`judge_*`, which the paper replaced with AlignScore) labeled the RTX 3090
runs other than `t01_smoke` and `t09_scope`. The
judge cross-check against Llama-3-8B-Instruct and the synthetic validation pairs belong to the main run
(`results/t07_main/<run_id>/judge_cross.json`, `judge_synthetic.json`, `alignscore_validation.json`).
