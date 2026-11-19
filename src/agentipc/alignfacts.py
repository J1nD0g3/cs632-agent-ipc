"""Turn AlignScore pair scores into per-run fact metrics and failure attribution.

python -m agentipc.alignfacts results/<exp>/<run_id> SCORED.jsonl [threshold]
Writes results_raw/.../alignscore_rows.jsonl.gz (one row per run, merged by analyze.load_rows) and
results/<exp>/<run_id>/alignscore.json (means per dataset, k and channel).
A fact counts as stated when AlignScore >= threshold (0.5 by default, the operating point checked on the
synthetic pairs).
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

from .factpairs import tasks_of
from .metrics import correct, parse_answers
from .stats import ci

ROOT = Path(__file__).resolve().parents[2]
KINDS = ("ok", "reviewer_fixed", "overflow", "no_answer", "research_miss", "delivery_miss", "writer_wrong",
         "reviewer_broke")


def main() -> int:
    run_dir, scored = Path(sys.argv[1]), Path(sys.argv[2])
    thr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    cfg, tasks = tasks_of(run_dir)
    raw = ROOT / "results_raw" / cfg["exp"] / run_dir.name
    have = defaultdict(dict)
    for line in open(scored):
        r = json.loads(line)
        have[(r["task_id"], r["channel"])][(r["stage"], r["q"], r["f"])] = r["alignscore"] >= thr
    rows = []
    for line in gzip.open(raw / "records.jsonl.gz", "rt"):
        rec = json.loads(line)
        key = (rec["task_id"], rec["channel"])
        if "error" in rec or key not in have:
            continue
        h, qs = have[key], tasks[rec["task_id"]].questions
        facts = [(qi, fi) for qi, q in enumerate(qs) for fi in range(len(q.facts))]
        notes = [h.get(("notes", qi, fi), False) for qi, fi in facts]
        got = [h.get(("writer_input", qi, fi), False) for qi, fi in facts]
        found = [i for i, v in enumerate(notes) if v]
        row = {"task_id": rec["task_id"], "channel": rec["channel"], "dataset": rec["dataset"], "k": rec["k"],
               "as_recall_notes": sum(notes) / len(facts)}
        if found:  # delivery is undefined when the Researcher's output states none of the facts
            row["as_kept_writer_input"] = sum(got[i] for i in found) / len(found)
        final = parse_answers(rec["stage"].get("final", ""), len(qs))
        draft = parse_answers(rec["stage"].get("draft", ""), len(qs))
        overflow = any(a["overflow"] for a in rec["agents"].values())
        counts = dict.fromkeys(KINDS, 0)
        right_but_missing = 0  # base rate: correct answers whose Researcher output misses a fact
        for qi, q in enumerate(qs):
            good, d_ok = correct(final[qi], q.answer), correct(draft[qi], q.answer)
            n_has = all(h.get(("notes", qi, fi), False) for fi in range(len(q.facts)))
            g_has = all(h.get(("writer_input", qi, fi), False) for fi in range(len(q.facts)))
            kind = ("ok" if d_ok else "reviewer_fixed") if good else "overflow" if overflow else \
                "no_answer" if not final[qi] else "reviewer_broke" if d_ok else \
                "research_miss" if not n_has else "delivery_miss" if not g_has else "writer_wrong"
            counts[kind] += 1
            right_but_missing += good and not n_has
        row.update({f"aq_{k}": v / len(qs) for k, v in counts.items()})
        row["aq_right_notes_miss"] = right_but_missing / len(qs)
        rows.append(row)
    with gzip.open(raw / "alignscore_rows.jsonl.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    out = {"threshold": thr, "scored": str(scored), "groups": {}}
    for key in sorted({(r["dataset"], r["k"], r["channel"]) for r in rows}):
        rs = [r for r in rows if (r["dataset"], r["k"], r["channel"]) == key]
        g = {"n": len(rs)}
        for m in sorted({c for r in rs for c in r if c.startswith(("as_", "aq_"))}):
            mean, lo, hi = ci([r[m] for r in rs if m in r])
            g[m] = {"mean": round(mean, 4), "lo": round(lo, 4), "hi": round(hi, 4)}
        out["groups"]["|".join(map(str, key))] = g
    (run_dir / "alignscore.json").write_text(json.dumps(out, indent=1))
    for ch in sorted({r["channel"] for r in rows}):
        rs = [r for r in rows if r["channel"] == ch]
        print(ch, len(rs), " ".join(f"{m}={np.mean([r[m] for r in rs if m in r]):.2f}" for m in
                                    ("as_recall_notes", "as_kept_writer_input", "aq_research_miss",
                                     "aq_delivery_miss", "aq_writer_wrong", "aq_reviewer_broke")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
