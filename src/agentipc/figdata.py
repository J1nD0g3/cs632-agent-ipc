"""Write the data files the paper figures plot, from results/ only.

python -m agentipc.figdata   ->  paper/figs/data/fig1_mechanism.json, fig2_tradeoff.json, ... (and a csv beside each)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from .analyze import load_rows
from .stats import ci

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "figs" / "data"
CHANNELS = ("A1", "A1zc", "A2", "B", "C", "D")


def latest(exp: str) -> Path | None:
    runs = sorted(p.parent for p in (ROOT / "results" / exp).glob("2*/summary.json"))
    return runs[-1] if runs else None


def pooled(rows: list[dict], ch: str, k: int, metric: str) -> tuple[float, float, float]:
    vals = [r[metric] for r in rows if r["channel"] == ch and r["k"] == k and metric in r]
    return ci(vals)


def write(name: str, data: dict, table: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=1))
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)


def fig1(src: Path, k: int = 3) -> None:
    """Share of file-channel tasks whose Writer never opens a Researcher-written file (paper_numbers.main_run)."""
    from .paper_numbers import raw_records, writer_opened_notes
    skipped, n = {"B": 0, "C": 0}, {"B": 0, "C": 0}
    for rec in raw_records(src):
        if "error" in rec or rec["k"] != k or rec["channel"] not in n:
            continue
        skipped[rec["channel"]] += not writer_opened_notes(rec)
        n[rec["channel"]] += 1
    table = [{"channel": ch, "k": k, "n": n[ch], "writer_skipped_notes": round(skipped[ch] / n[ch], 4)} for ch in n]
    write("fig1_mechanism", {"source": str(src.relative_to(ROOT)), "k": k, "channels": table}, table)


def fig2(rows: list[dict], src: Path, k: int = 3) -> None:
    table = []
    for ch in CHANNELS:
        row = {"channel": ch, "k": k}
        for m in ("acc", "total_tokens", "prefill_tokens", "prompt_tokens"):
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    a1 = {r["task_id"]: r["acc"] for r in rows if r["channel"] == "A1" and r["k"] == k}
    gaps = {}
    for ch in CHANNELS[1:]:
        mean, lo, hi = ci([r["acc"] - a1[r["task_id"]] for r in rows
                           if r["channel"] == ch and r["k"] == k and r["task_id"] in a1])
        gaps[ch] = {"acc_diff": round(mean, 4), "acc_diff_lo": round(lo, 4), "acc_diff_hi": round(hi, 4)}
    write("fig2_tradeoff", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                            "channels": table, "gap_vs_a1": gaps, "zc_time": zc_time()}, table)


def zc_time() -> list[dict]:
    """Zero-copy's serving time over broadcast's in the timing runs, as paper_numbers.round6/10/12/13 compute it."""
    def elapsed(run: Path) -> float:
        return json.loads((run / "run_time.json").read_text())["elapsed_s"]

    def med(run: Path) -> float:
        return float(np.median([r["wall_s"] for r in load_rows(run)]))

    six = {ch: [latest(f"p06_alone_{ch}"), latest(f"p11_alone_{ch}_r2"), latest(f"p11_alone_{ch}_r3")]
           for ch in ("A1", "A1zc")}
    hi = {ch: [latest(f"p11_c32_{ch}_r{i}") for i in (1, 2)] for ch in ("A1", "A1zc")}
    out = []
    for label, runs in (("six", six), ("thirty_two", hi)):
        base = np.mean([elapsed(x) for x in runs["A1"]])
        t = [elapsed(x) / base for x in runs["A1zc"]]
        m = [med(z) / med(a) for z, a in zip(runs["A1zc"], runs["A1"])]
        for metric, vals in (("run_time", t), ("median_task", m)):
            out.append({"row": f"{label}_{metric}", "value": round(float(np.mean(vals)), 4),
                        "lo": round(min(vals), 4), "hi": round(max(vals), 4), "per_run": [round(v, 4) for v in vals],
                        "runs": [str(x.relative_to(ROOT)) for x in runs["A1zc"] + runs["A1"]]})
    return out


FAIL = ("aq_research_miss", "aq_delivery_miss", "aq_writer_wrong", "aq_reviewer_broke", "aq_no_answer")


def fig3(rows: list[dict], src: Path, k: int = 3) -> None:
    table = []
    for ch in CHANNELS:
        row = {"channel": ch, "k": k}
        for m in ("as_recall_notes", "as_kept_writer_input", "acc") + FAIL:
            mean, lo, hi = pooled(rows, ch, k, m)
            row.update({m: round(mean, 4), f"{m}_lo": round(lo, 4), f"{m}_hi": round(hi, 4)})
        table.append(row)
    write("fig3_loss", {"source": str(src.relative_to(ROOT)), "k": k, "pooled": "hotpotqa+2wiki",
                        "channels": table}, table)


def fig3_split() -> None:
    """2x2 per model size in one run (p16): notes written as a reply or through a tool call, then copied forward
    or delivered through files. Facts in the Researcher's notes and accuracy per arm, with 95% intervals."""
    table = []
    for size in ("4b", "8b", "14b", "32b"):
        run = latest(f"p16_store_{size}")
        rows = load_rows(run)
        row = {"size": size.upper(), "source": str(run.relative_to(ROOT))}
        for ch in ("A1r", "A1w", "Bs", "B"):
            rs = [r for r in rows if r["channel"] == ch and not r.get("error")]
            notes = [r["as_recall_notes"] for r in rs if "as_recall_notes" in r]
            row[f"notes_{ch}"] = round(float(np.mean(notes)), 4) if notes else None
            if notes:
                _, nlo, nhi = ci(notes)
                row.update({f"notes_{ch}_lo": round(nlo, 4), f"notes_{ch}_hi": round(nhi, 4)})
            mean, lo, hi = ci([r["acc"] for r in rs])
            row.update({f"acc_{ch}": round(mean, 4), f"acc_{ch}_lo": round(lo, 4), f"acc_{ch}_hi": round(hi, 4)})
        table.append(row)
    write("fig3_split", {"rows": table}, table)


def fig4(rows_by_k: dict[int, list[dict]], sources: dict[int, str]) -> None:
    """Per k: computed and sent tokens relative to A1, and accuracy relative to A1, both datasets pooled."""
    table = []
    for k, rows in sorted(rows_by_k.items()):
        base = {m: np.mean([r[m] for r in rows if r["channel"] == "A1" and r["k"] == k]) for m in
                ("total_tokens", "prefill_tokens", "acc")}
        a1 = {(r["task_id"]): r for r in rows if r["channel"] == "A1" and r["k"] == k}
        for ch in sorted({r["channel"] for r in rows}):
            rs = [r for r in rows if r["channel"] == ch and r["k"] == k]
            if not rs:
                continue
            diffs = [r["acc"] - a1[r["task_id"]]["acc"] for r in rs if r["task_id"] in a1]
            mean, lo, hi = ci(diffs) if ch != "A1" else (0.0, 0.0, 0.0)
            table.append({"k": k, "channel": ch, "n": len(rs), "source": sources[k],
                          "sent_rel": round(np.mean([r["total_tokens"] for r in rs]) / base["total_tokens"], 4),
                          "comp_rel": round(np.mean([r["prefill_tokens"] for r in rs]) / base["prefill_tokens"], 4),
                          "acc": round(np.mean([r["acc"] for r in rs]), 4),
                          "acc_diff": round(mean, 4), "acc_diff_lo": round(lo, 4), "acc_diff_hi": round(hi, 4)})
    write("fig4_scaling", {"rows": table}, table)


def _numbers(*sections) -> dict[str, str]:
    """Macros of the given paper_numbers sections, computed afresh from results/ (name -> TeX text)."""
    from .paper_numbers import Macros
    m = Macros()
    for fn in sections:
        fn(m)
    return {line[len("\\newcommand{\\n"):].split("}{", 1)[0]: line.split("}{", 1)[1][:-len("\\xspace}")]
            for line in m.lines}


def _num(text: str) -> float:
    return float(text.replace("\\mbox{$-$", "-").replace("\\mbox{$+$", "").rstrip("}").replace(",", ""))


def fig3_cause() -> None:
    """Fig. 3: (a) paired effects per size in the crossed runs (p16), with the Holm flags of Table 1 (round10_text);
    (b) Writer open rate and accuracy per arm in the told runs (p17), with the paired told-over-untold change."""
    from .paper_numbers import round10, round10_text, round12_told
    n = _numbers(round10, round10_text, round12_told)
    sizes = {"Four": "4B", "Eight": "8B", "Fourteen": "14B", "ThirtyTwo": "32B"}
    blank = {"panel": "", "size": "", "series": "", "x": None, "y": None, "lo": None, "hi": None, "n": None,
             "holm": None, "source": ""}
    effects, told, arrows = [], [], []
    for tag, size in sizes.items():
        src = str(latest(f"p16_store_{size.lower()}").relative_to(ROOT))
        for eff in ("FileTool", "FileReply", "WriteCopy"):
            effects.append({**blank, "panel": "a", "size": size, "series": eff, "y": _num(n[f"RTen{tag}{eff}"]),
                            "lo": _num(n[f"RTen{tag}{eff}Lo"]), "hi": _num(n[f"RTen{tag}{eff}Hi"]),
                            "n": int(_num(n[f"RTen{tag}{eff}N"])), "holm": n[f"RTenMark{eff}{tag}"] != "",
                            "source": src})
    for tag, size in (("Fourteen", "14B"), ("ThirtyTwo", "32B")):
        src = str(latest(f"p17_told_{size.lower()}").relative_to(ROOT))
        for arm in ("Tool", "Untold", "Told"):
            told.append({**blank, "panel": "b", "size": size, "series": arm, "x": _num(n[f"RTold{tag}Open{arm}"]),
                         "y": _num(n[f"RTold{tag}Acc{arm}"]), "source": src})
        name = f"RTold{tag}ToldOverUntold"
        arrows.append({**blank, "panel": "b", "size": size, "series": "ToldOverUntold", "y": _num(n[name]),
                       "lo": _num(n[f"{name}Lo"]), "hi": _num(n[f"{name}Hi"]), "n": int(_num(n[f"{name}N"])),
                       "source": src})
    write("fig3_cause", {"effects": effects, "told": told, "told_arrows": arrows,
                         "rescue_tool_file": {s: _num(n[f"RTen{t}RescueToolFile"]) for t, s in sizes.items()},
                         "n_crossed": int(_num(n["RTenN"]))}, effects + told + arrows)


def fig4_limits() -> None:
    """Fig. 4: zero-copy's prefill against A1 under a 35k/100k/400k cache at k=8 (p01, as paper_numbers.pro6000), and
    accuracy minus A1 per task with parallel Researchers at k=8 (p15) and k=16 (p12, as paper_numbers.round6)."""
    from .analyze import paired
    from .paper_numbers import round6, round8, round12
    n = _numbers(round6, round8, round12)
    blank = {"panel": "", "group": "", "series": "", "y": None, "lo": None, "hi": None, "n": None, "source": ""}
    cache = []
    for tag, exp in (("35k", "p01_cache_35k"), ("100k", "p01_cache_100k"), ("400k", "p01_cache_400k")):
        run = latest(exp)
        rows = load_rows(run)
        a1 = [r["prefill_tokens"] for r in rows if r["channel"] == "A1"]
        zc = [r["prefill_tokens"] for r in rows if r["channel"] == "A1zc"]
        cache.append({**blank, "panel": "a", "group": "k8", "series": tag, "y": round(np.mean(zc) / np.mean(a1), 4),
                      "n": len(a1), "source": str(run.relative_to(ROOT))})

    def by(rs, ch):
        return {r["task_id"]: r for r in rs if r["channel"] == ch and not r.get("error")}

    writers = []
    for exp, series in (("p15_k8_one", (("B", "one"),)), ("p15_k8_three", (("B", "shared"), ("Bf", "folders")))):
        run = latest(exp)
        rs = load_rows(run)
        a1 = by(rs, "A1")
        for ch, name in series:
            x = by(rs, ch)
            ids = sorted(set(x) & set(a1))
            mean, lo, hi = paired(np.array([x[i]["acc"] for i in ids], float), np.array([a1[i]["acc"] for i in ids], float))
            writers.append({**blank, "panel": "b", "group": "k8", "series": name, "y": round(mean * 100, 1),
                            "lo": round(lo * 100, 1), "hi": round(hi * 100, 1), "n": len(ids),
                            "source": str(run.relative_to(ROOT))})
    src = str(latest("p12_k16_clobber").relative_to(ROOT))
    for lab, name in (("B", "shared"), ("Guard", "guard"), ("Heading", "heading")):
        g = f"RSixKSixteen{lab}Gap"  # A1 minus the arm; negated here to read as the arm minus A1
        writers.append({**blank, "panel": "b", "group": "k16", "series": name, "y": -_num(n[g]), "lo": -_num(n[f"{g}Hi"]),
                        "hi": -_num(n[f"{g}Lo"]), "n": int(_num(n[f"{g}N"])), "source": src})
    gains = {"folders_over_b": [_num(n[f"REightFoldersOverB{s}"]) for s in ("", "Lo", "Hi")],
             "guard_over_b": [_num(n[f"RSixKSixteenGuardOverB{s}"]) for s in ("", "Lo", "Hi")],
             "heading_over_b": [_num(n[f"RSixKSixteenHeadingOverB{s}"]) for s in ("", "Lo", "Hi")],
             "share_guard": _num(n["RTwelveShareGuard"]), "share_heading": _num(n["RTwelveShareHeading"]),
             "clash_b": _num(n["REightClashB"]),
             "fan_did_b": [_num(n[f"REightFanDiD{s}"]) for s in ("", "Lo", "Hi")]}
    write("fig4_limits", {"cache_ctrl": cache, "writers": writers, "gains": gains}, cache + writers)


def main() -> int:
    src = latest("t07_main")
    rows = load_rows(src)
    fig1(src)
    fig2(rows, src)
    fig3(rows, src)
    by_k = {k: [r for r in rows if r["k"] == k] for k in (1, 3, 5)}
    sources = {k: str(src.relative_to(ROOT)) for k in by_k}
    for exp, k in (("t08_k8", 8), ("t08_large", 16)):
        run = latest(exp) if (ROOT / "results" / exp).exists() else None
        if run is not None:
            by_k[k] = load_rows(run)
            sources[k] = str(run.relative_to(ROOT))
    fig4(by_k, sources)
    fig3_split()
    fig3_cause()
    fig4_limits()
    print(f"wrote {OUT}/fig2_tradeoff.json, fig3_loss.json from {src.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
