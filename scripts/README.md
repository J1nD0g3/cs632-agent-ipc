# scripts/

Shell scripts that served the models and ran the experiments, kept as the record of how each run was launched.
They `source env.local.sh` (not committed; see the main README) and write logs to `logs/`. The run configs in
`results/` refer to these paths, so the scripts stay where they are.

| Script | Use |
| --- | --- |
| `serve.sh <gpu> [port]` | Start one vLLM server with this project's flags. Environment overrides: `SERVE_MODEL`, `SERVED_NAME`, `MAX_LEN`, `GPU_UTIL`, `KV_BLOCKS` (fixes the KV cache in 16-token blocks). Writes `logs/vllm_gpu<gpu>.pid`. |
| `stop_servers.sh` | Stop the servers started by `serve.sh` (by PID) and wait until their GPUs are free. |
| `alignscore_score.py IN OUT [gpu]` | Score (context, fact) pairs with AlignScore-large; runs in AlignScore's own environment ([../docs/pro6000/README.md](../docs/pro6000/README.md)). |
| `watchdog.sh`, `watchdog_pro6000.sh` | Exit when a queue logs a new line, dies, or its servers stop logging, so a long queue can be watched. |

One-off queues, in the order they ran (each lists its runs in its header):

| Queue | Runs |
| --- | --- |
| `queue_t08.sh` | Judge the main run; `t08_k8`, `t08_chain4`, `t08_qwen4b`; judge them. |
| `queue_g6.sh`, `queue_g6_tail.sh` | `t08_batch`, `t08_turns24`, `t08_large`, judged on one GPU. |
| `queue_morning.sh` | `t08_pressure_c1`, `t08_pressure_c2`, `t08_fanout`. |
| `queue_fix.sh` | `t09_a1w`, `t09_replay`, `t09_repeat`. |
| `queue_g6_rejudge.sh` | Re-judge the main run with the per-question judge. |
| `queue_judgex.sh` | Fact-judge cross-check, Qwen3-8B against Llama-3-8B-Instruct. |
| `queue_scope.sh` | `t09_scope` and its AlignScore scoring. |
| `queue_pro6000.sh`, `queue_pro6000_multi.sh` | `p01_cache_*` and `p02_size_*` on the RTX PRO 6000 server (one or several GPUs). |
| `queue_p03_corner.sh` | `p03_corner_32b_35k`. |
| `queue_p0_align.sh`, `queue_p0_align_par.sh`, `queue_p0_align_more.sh` | AlignScore for the RTX PRO 6000 runs. |

The queues for the later RTX PRO 6000 runs (`p05`-`p18`) are on the `pro6000` branch.
