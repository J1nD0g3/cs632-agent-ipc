"""Print a run's summary as a table: python -m agentipc.report results/<exp>/<run_id> [metric ...]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT = ("acc", "total_tokens", "prefill_tokens", "llm_calls", "file_io", "fact_recall_notes",
           "fact_kept_writer_input", "info_loss", "wall_s", "turn_limit", "overflow")


def main() -> int:
    run = Path(sys.argv[1])
    metrics = sys.argv[2:] or DEFAULT
    summ = json.loads((run / "summary.json").read_text())
    head = f"{'group':<22}{'n':>4}{'err':>4}" + "".join(f"{m[:12]:>13}" for m in metrics)
    print(head)
    for key, g in summ.items():
        cells = []
        for m in metrics:
            v = g.get(m, {}).get("mean")
            cells.append(f"{'-' if v is None else (f'{v:.0f}' if abs(v) >= 100 else f'{v:.3f}'):>13}")
        print(f"{key:<22}{g['n']:>4}{g['errors']:>4}" + "".join(cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
