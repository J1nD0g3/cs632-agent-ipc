"""Accuracy per channel and model size (the size runs), written as docs/accuracy_by_size.md and .csv.

python analysis/accuracy_table.py

Uses only the committed per-task rows (agentipc.load) and the computation of Table tab:app-size
(agentipc.appendix_tables.by and gap), then checks every value against paper/appendix_tables.tex (\\appTabSize)
and paper/numbers.tex, and exits non-zero on any mismatch.
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np

from agentipc import appendix_tables as T
from agentipc.load import load_rows, run_dir

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SIZES = (("4b", "4B", "Four"), ("8b", "8B", "Eight"), ("14b", "14B", "Fourteen"), ("32b", "32B", "ThirtyTwo"))
LABEL = {"A1": "A1 broadcast", "A1zc": "A1-zc zero-copy", "A2": "A2 pipe", "B": "B shared files",
         "C": "C files + index", "D": "D handoffs"}
NAME = {"A1": "AOne", "A1zc": "AZc", "A2": "ATwo", "B": "B", "C": "C", "D": "D"}
MAIN = ("A1", "A1zc", "A2", "B", "C")
RERUN = ("B", "C", "D")


def records(exp: str) -> list[dict]:
    return load_rows(exp).to_dict("records")


def plain(x: float) -> str:
    """Percent with one decimal; -0.0 prints as 0.0 (as in the paper's tables)."""
    s = f"{x * 100:.1f}"
    return s[1:] if s.startswith("-") and float(s) == 0 else s


def compute() -> list[dict]:
    out = []
    size = {s: records(f"p02_size_{s}") for s, _, _ in SIZES}
    for s, lab, tag in SIZES:
        a1 = T.by(size[s], "A1")
        for ch in T.CHS:
            d = T.by(size[s], ch)
            pre = np.mean([r["prefill_tokens"] for r in d.values()]) / np.mean([r["prefill_tokens"] for r in a1.values()])
            g = None if ch == "A1" else T.gap(d, a1)
            out.append(dict(model=f"Qwen3-{lab}", tag=tag, exp=f"p02_size_{s}", run=run_dir(f"p02_size_{s}").name,
                            channel=ch, acc=np.mean([r["acc"] for r in d.values()]), gap=g, n=len(d), prefill=pre,
                            cross_run=False, shown=not (s == "32b" and ch in RERUN)))
    rerun = records("p08_norm_32b")
    a1 = T.by(size["32b"], "A1")
    for ch in RERUN:
        d = T.by(rerun, ch)
        out.append(dict(model="Qwen3-32B", tag="ThirtyTwo", exp="p08_norm_32b", run=run_dir("p08_norm_32b").name,
                        channel=ch, acc=np.mean([r["acc"] for r in d.values()]), gap=T.gap(d, a1), n=len(d),
                        prefill=None, cross_run=True, shown=True))
    main = load_rows("t07_main")
    k3 = main[main["k"] == 3]
    for ch in T.CHS:
        d = k3[k3["channel"] == ch]
        out.append(dict(model="Qwen3-8B", tag="main", exp="t07_main", run=run_dir("t07_main").name, channel=ch,
                        acc=d["acc"].mean(), gap=None, n=len(d), prefill=None, cross_run=False, shown=True))
    return out


def tex_plain(s: str) -> str:
    return re.sub(r"\\mbox\{\$(.)\$(.*?)\}", r"\1\2", s).strip()


def paper_macros() -> dict[str, str]:
    text = (ROOT / "paper" / "numbers.tex").read_text()
    return {n: tex_plain(v) for n, v in re.findall(r"\\newcommand\{\\n(\w+)\}\{(.*)\\xspace\}", text)}


def check(rows: list[dict], macros: dict[str, str]) -> int:
    text = (ROOT / "paper" / "appendix_tables.tex").read_text()
    body = re.search(r"\\newcommand\{\\appTabSize\}\{%\n(.*?)\n\}", text, re.S).group(1)
    table = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.rstrip("\\ ").split(" & ")]
        table[cells[0]] = cells[1:]
    want, got = [], []

    def expect(where: str, ours: str, paper: str | None) -> None:
        want.append((where, ours, paper))

    order = [lab for _, lab, _ in SIZES]
    for r in rows:
        ch, tag = r["channel"], r["tag"]
        if r["exp"].startswith("p02_size_"):
            j = order.index(r["model"].split("-")[1]) * 3
            cells = table[T.SHOW[ch]]
            expect(f"appTabSize {T.SHOW[ch]} {r['model']} acc", T.pt(r["acc"]), cells[j])
            expect(f"appTabSize {T.SHOW[ch]} {r['model']} diff", T.cell(r["gap"]) if r["gap"] else "--", cells[j + 1])
            expect(f"appTabSize {T.SHOW[ch]} {r['model']} prefill", f"{r['prefill']:.2f}", cells[j + 2])
            pre = f"PSize{tag}"
            expect(f"\\n{pre}Acc{NAME[ch]}", plain(r["acc"]), macros.get(f"{pre}Acc{NAME[ch]}"))
            if ch == "A1":
                expect(f"\\n{pre}N", str(r["n"]), macros.get(f"{pre}N"))
        elif r["exp"] == "p08_norm_32b":
            cells = table[f"{ch}, path rerun$^\\ast$"]
            expect(f"appTabSize {ch} rerun acc", T.pt(r["acc"]), cells[1])
            expect(f"appTabSize {ch} rerun diff", T.cell(r["gap"]), cells[2])
            pre = f"RFourNorm{ch}"
            expect(f"\\n{pre}Acc", plain(r["acc"]), macros.get(f"{pre}Acc"))
            expect(f"\\n{pre}GapN", str(r["n"]), macros.get(f"{pre}GapN"))
        else:
            expect(f"\\nAcc{NAME[ch]}", plain(r["acc"]), macros.get(f"Acc{NAME[ch]}"))
            continue
        if r["gap"]:
            m, lo, hi, _ = r["gap"]
            base = f"PSize{tag}Gap{NAME[ch]}" if r["exp"].startswith("p02") else f"RFourNorm{ch}Gap"
            for suffix, v in (("", -m), ("Lo", -hi), ("Hi", -lo)):
                expect(f"\\n{base}{suffix}", plain(v), macros.get(base + suffix))
    bad = [w for w in want if w[1] != w[2]]
    for where, ours, paper in bad:
        print(f"MISMATCH {where}: recomputed {ours!r}, paper {paper!r}")
    print(f"checked {len(want)} values against paper/appendix_tables.tex and paper/numbers.tex: {len(bad)} mismatches")
    return len(bad)


def md_cell(r: dict, best: str | None) -> str:
    acc = plain(r["acc"])
    s = f"**{acc}**" if acc == best else acc
    if r["gap"]:
        m, lo, hi, _ = r["gap"]
        s += f" ({plain(m)}; {plain(lo)} to {plain(hi)})"
    return s + ("\\*" if r["cross_run"] else "")


def markdown(rows: list[dict], macros: dict[str, str]) -> str:
    shown = [r for r in rows if r["exp"] != "t07_main" and r["shown"]]
    cell = {(r["model"], r["channel"]): r for r in shown}
    models = [f"Qwen3-{lab}" for _, lab, _ in SIZES]
    best = {m: max((plain(cell[m, ch]["acc"]) for ch in MAIN), key=float) for m in models}
    n = {r["n"] for r in shown if r["channel"] == "A1"}
    assert len(n) == 1, n
    n = n.pop()
    orig = {r["channel"]: r for r in rows if r["exp"] == "p02_size_32b" and r["channel"] in RERUN}
    main = {r["channel"]: r for r in rows if r["exp"] == "t07_main"}
    main_best = max((plain(main[ch]["acc"]) for ch in MAIN), key=float)
    lines = [
        "# Accuracy by channel and model size",
        "",
        "Generated by `python analysis/accuracy_table.py` from the committed per-task rows; the same values as the "
        "paper's Table 10 (size runs).",
        "",
        f"Size runs: Qwen3-4B to 32B, one RTX PRO 6000 per run, {macros['KvPro']}-token KV cache, k = 3 questions per task, {n} tasks "
        f"per size ({n // 2} HotpotQA and {n // 2} 2Wiki), the same tasks in every channel. Each cell is accuracy "
        "(% of questions answered correctly) and, in parentheses, the paired difference to A1 broadcast "
        "(channel minus A1, in points, over the same tasks; negative means less accurate) and its 95% bootstrap "
        "interval, resampling tasks. An interval that excludes 0 is a significant difference. Bold: the most "
        "accurate of A1 to C per model size.",
        "",
        "| Channel | " + " | ".join(models) + " |",
        "| --- | " + " | ".join("---" for _ in models) + " |",
    ]
    for ch in T.CHS:
        lab = LABEL[ch] + (" (excluded from the main comparison)&dagger;" if ch == "D" else "")
        lines.append(f"| {lab} | " + " | ".join(md_cell(cell[m, ch], best[m] if ch in MAIN else None)
                                                for m in models) + " |")
    lines += [
        "",
        "\\* Qwen3-32B B, C, and D come from the path rerun (`p08_norm_32b`), in which the harness strips the "
        "`workspace/` prefix that Qwen3-32B sometimes put on file paths; they are paired with the size run's A1 "
        "(cross-run, so drift between the runs adds to the difference). The size run's own values were "
        + ", ".join(f"{ch} {md_cell(orig[ch], None)}" for ch in RERUN) + ".",
        "",
        "&dagger; D is excluded from the main comparison because its Researcher and Writer pass a message of at most "
        f"{macros['HandoffWords']} words plus file paths, instead of only copied messages or only files.",
        "",
        "For reference, the main run (a different run on a different server, not paired with the size runs): "
        f"Qwen3-8B on RTX 3090s, {macros['BigKv']}-token KV cache, k = 3, HotpotQA and 2Wiki pooled ({main['A1']['n']} tasks; "
        "`t07_main`). Accuracy (%):",
        "",
        "| Run | " + " | ".join(T.SHOW[ch] for ch in T.CHS) + " |",
        "| --- | " + " | ".join("---" for _ in T.CHS) + " |",
        "| Qwen3-8B, main run | " + " | ".join(md_cell(main[ch], main_best if ch in MAIN else None)
                                             for ch in T.CHS) + " |",
        "",
    ]
    return "\n".join(lines)


def write_csv(rows: list[dict]) -> None:
    with open(DOCS / "accuracy_by_size.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "exp", "run_id", "channel", "tasks", "acc_pct", "diff_vs_a1_pts", "ci_lo_pts",
                    "ci_hi_pts", "prefill_vs_a1", "cross_run", "in_table"])
        for r in rows:
            g = [plain(x) for x in r["gap"][:3]] if r["gap"] else ["", "", ""]
            w.writerow([r["model"], r["exp"], r["run"], T.SHOW[r["channel"]], r["n"], plain(r["acc"]), *g,
                        f"{r['prefill']:.2f}" if r["prefill"] is not None else "", int(r["cross_run"]),
                        int(r["shown"])])


def main() -> int:
    rows = compute()
    macros = paper_macros()
    bad = check(rows, macros)
    if bad:
        return 1
    DOCS.mkdir(exist_ok=True)
    (DOCS / "accuracy_by_size.md").write_text(markdown(rows, macros))
    write_csv(rows)
    print(f"wrote {DOCS / 'accuracy_by_size.md'} and {DOCS / 'accuracy_by_size.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
