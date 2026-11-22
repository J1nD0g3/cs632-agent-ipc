"""Score (context, fact) pairs with AlignScore-large (Zha et al., ACL 2023).

Runs in its own venv (torch 1.x) after `uv pip install --no-deps $STORE/alignscore/src` there:
  $STORE/alignscore/venv/bin/python scripts/alignscore_score.py IN.jsonl OUT.jsonl [GPU]
Each input line needs "context" and "fact"; the output adds "alignscore" in [0, 1].
"""
import json
import os
import sys

if len(sys.argv) > 3:
    os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[3]
STORE = os.environ["STORE"]
os.environ.setdefault("HF_HOME", os.path.join(STORE, "hf"))

from alignscore import AlignScore  # noqa: E402

rows = [json.loads(line) for line in open(sys.argv[1])]
scorer = AlignScore(model="roberta-large", batch_size=16, device="cuda:0",
                    ckpt_path=os.path.join(STORE, "alignscore", "ckpt", "AlignScore-large.ckpt"),
                    evaluation_mode="nli_sp", verbose=False)
scores = scorer.score(contexts=[r["context"] for r in rows], claims=[r["fact"] for r in rows])
with open(sys.argv[2], "w") as f:
    for r, s in zip(rows, scores):
        f.write(json.dumps({**r, "alignscore": float(s)}) + "\n")
print(f"scored {len(rows)} pairs")
