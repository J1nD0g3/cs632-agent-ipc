"""Accuracy per channel and model size (the size runs), plus cost and run time per channel, written as
docs/accuracy_by_size.md and .csv.

python analysis/accuracy_table.py

Uses only the committed per-task rows and run_time.json files (agentipc.load) and the paper's own computations
(agentipc.appendix_tables for Tables tab:app-size and tab:app-timing, agentipc.paper_numbers for the main-run and
timing macros), then checks every value the paper reports against paper/appendix_tables.tex (\\appTabSize,
\\appTabTiming) and paper/numbers.tex, and exits non-zero on any mismatch.
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

from agentipc import appendix_tables as T
from agentipc.load import config, experiments, load_rows, run_dir
from agentipc.stats import ci

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


def cost() -> dict[str, dict]:
    """Main run (t07_main), k=3, both datasets pooled: per-task means as in paper_numbers.main_run, with 95% intervals."""
    main = load_rows("t07_main")
    k3 = main[main["k"] == 3]
    out = {}
    for ch in T.CHS:
        d = k3[k3["channel"] == ch]
        out[ch] = {m: ci(d[m]) for m in ("acc", "total_tokens", "prefill_tokens", "llm_calls", "file_io")}
        out[ch]["n"] = len(d)
    return out


def median_wall(exp: str) -> float:
    return float(np.median(load_rows(exp)["wall_s"]))


def run_time(exp: str) -> dict:
    return json.loads((run_dir(exp) / "run_time.json").read_text())


def timing() -> dict[str, dict]:
    """Timing runs as in appendix_tables.timing_table (six at a time, three runs per channel) and the 32-at-a-time runs
    of paper_numbers.round6 (two runs, A1, A1-zc, and B), with median task time relative to A1 paired by run."""
    out = {}
    for ch in T.CHS:
        exps = [f"p06_alone_{ch}", f"p11_alone_{ch}_r2", f"p11_alone_{ch}_r3"]
        rt = [run_time(e) for e in exps]
        vm = [d["vllm_metrics"] for d in rt if d.get("vllm_metrics")]
        out[ch] = dict(
            exps=exps, wall=[d["elapsed_s"] for d in rt],
            gen=np.mean([load_rows(e)["completion_tokens"].mean() for e in exps]),
            pre=np.mean([v["vllm:request_prefill_time_seconds_sum"] for v in vm]),
            dec=np.mean([v["vllm:request_decode_time_seconds_sum"] for v in vm]),
            tok=np.mean([v["vllm:request_decode_time_seconds_sum"] / v["vllm:generation_tokens_total"] * 1000
                         for v in vm]),
            med=[median_wall(e) for e in exps], n=len(load_rows(exps[-1])),
            conc={config(e)["concurrency"] for e in exps})
        hi = [f"p11_c32_{ch}_r{i}" for i in (1, 2)]
        if set(hi) <= set(experiments()):
            rt = [run_time(e) for e in hi]
            out[ch].update(hi_exps=hi, hi_wall=[d["elapsed_s"] for d in rt],
                           hi_pre=np.mean([d["vllm_metrics"]["vllm:request_prefill_time_seconds_sum"] for d in rt]),
                           hi_med=[median_wall(e) for e in hi], hi_n=len(load_rows(hi[-1])),
                           hi_conc={config(e)["concurrency"] for e in hi})
    a1 = out["A1"]
    for ch, t in out.items():
        ratios = [x / np.mean(a1["wall"]) for x in t["wall"]]
        t.update(time=np.mean(ratios), time_min=min(ratios), time_max=max(ratios), gen_rel=t["gen"] / a1["gen"],
                 pre_rel=t["pre"] / a1["pre"], dec_rel=t["dec"] / a1["dec"],
                 med_runs=[x / y for x, y in zip(t["med"], a1["med"])])
        t["med_rel"] = np.mean(t["med_runs"])
        if "hi_wall" in t:
            t.update(hi_time=np.mean(t["hi_wall"]) / np.mean(a1["hi_wall"]), hi_pre_rel=t["hi_pre"] / a1["hi_pre"],
                     hi_med_runs=[x / y for x, y in zip(t["hi_med"], a1["hi_med"])])
            t["hi_med_rel"] = np.mean(t["hi_med_runs"])
    return out


def tex_plain(s: str) -> str:
    return re.sub(r"\\mbox\{\$(.)\$(.*?)\}", r"\1\2", s).strip()


def paper_macros() -> dict[str, str]:
    text = (ROOT / "paper" / "numbers.tex").read_text()
    return {n: tex_plain(v) for n, v in re.findall(r"\\newcommand\{\\n(\w+)\}\{(.*)\\xspace\}", text)}


def tex_table(name: str) -> dict[str, list[str]]:
    """The rows of \\appTab<name> in paper/appendix_tables.tex, keyed by their first cell."""
    text = (ROOT / "paper" / "appendix_tables.tex").read_text()
    body = re.search(r"\\newcommand\{\\appTab" + name + r"\}\{%\n(.*?)\n\}", text, re.S).group(1)
    table = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.rstrip("\\ ").split(" & ")]
        table[cells[0]] = cells[1:]
    return table


def expect_cost_time(c: dict, t: dict, macros: dict[str, str], expect) -> None:
    """Main-run cost (paper_numbers.main_run), Table tab:app-timing, and the timing macros (round6, round10_text,
    round12, round13)."""
    for ch in T.CHS:
        n = NAME[ch]
        expect(f"\\nAcc{n}", plain(c[ch]["acc"][0]), macros.get(f"Acc{n}"))
        expect(f"\\nSent{n}", f"{c[ch]['total_tokens'][0] / 1000:.1f}k", macros.get(f"Sent{n}"))
        expect(f"\\nComp{n}", f"{c[ch]['prefill_tokens'][0] / 1000:.1f}k", macros.get(f"Comp{n}"))
        expect(f"\\nCalls{n}", f"{c[ch]['llm_calls'][0]:.1f}", macros.get(f"Calls{n}"))
    rel = lambda ch, m: c[ch][m][0] / c["A1"][m][0]
    for ch in ("A2", "B", "C", "D"):
        expect(f"\\nSentRatio{NAME[ch]}", f"{rel(ch, 'total_tokens'):.1f}", macros.get(f"SentRatio{NAME[ch]}"))
        expect(f"\\nCompRatio{NAME[ch]}", f"{rel(ch, 'prefill_tokens'):.2f}", macros.get(f"CompRatio{NAME[ch]}"))
    expect("\\nZcCut", f"{(1 - rel('A1zc', 'prefill_tokens')) * 100:.0f}", macros.get("ZcCut"))
    table = tex_table("Timing")
    for ch in T.CHS:
        x, n = t[ch], NAME[ch]
        ours = [f"{w:.0f}" for w in x["wall"]] + [f"{x[k]:.2f}" for k in ("time", "gen_rel", "pre_rel", "dec_rel")]
        ours.append(f"{x['tok']:.1f}")
        expect(f"appTabTiming {T.SHOW[ch]}", " & ".join(ours), " & ".join(table[T.SHOW[ch]]))
        if ch in ("A1zc", "A2", "B", "C"):
            for suffix, k in (("", "time"), ("Min", "time_min"), ("Max", "time_max")):
                expect(f"\\nRSixTime{n}{suffix}", f"{x[k]:.2f}", macros.get(f"RSixTime{n}{suffix}"))
            expect(f"\\nRSixPrefillTime{n}", f"{x['pre_rel']:.2f}", macros.get(f"RSixPrefillTime{n}"))
            expect(f"\\nRSixGen{n}", f"{x['gen_rel']:.1f}", macros.get(f"RSixGen{n}"))
        if ch in ("A1zc", "B"):
            expect(f"\\nRSixHiTime{n}", f"{x['hi_time']:.2f}", macros.get(f"RSixHiTime{n}"))
            expect(f"\\nRSixHiPrefillTime{n}", f"{x['hi_pre_rel']:.2f}", macros.get(f"RSixHiPrefillTime{n}"))
    a1, zc = t["A1"], t["A1zc"]
    expect("\\nRSixAloneN", str(a1["n"]), macros.get("RSixAloneN"))
    expect("\\nRSixHiN", str(a1["hi_n"]), macros.get("RSixHiN"))
    expect("\\nRSixTimeAOneMin", f"{min(a1['wall']):.0f}", macros.get("RSixTimeAOneMin"))
    expect("\\nRSixTimeAOneMax", f"{max(a1['wall']):.0f}", macros.get("RSixTimeAOneMax"))
    expect("\\nRSixDecodeShareAOne", f"{a1['dec'] / (a1['dec'] + a1['pre']) * 100:.0f}",
           macros.get("RSixDecodeShareAOne"))
    for suffix, v in (("", zc["med_rel"]), ("Min", min(zc["med_runs"])), ("Max", max(zc["med_runs"]))):
        expect(f"\\nRTwelveSixMedAZc{suffix}", f"{v:.2f}", macros.get(f"RTwelveSixMedAZc{suffix}"))
    expect("\\nRTenHiMedAZc", f"{zc['hi_med_rel']:.2f}", macros.get("RTenHiMedAZc"))
    expect("\\nRThirteenHiMedAZcMin", f"{min(zc['hi_med_runs']):.2f}", macros.get("RThirteenHiMedAZcMin"))
    expect("\\nRThirteenHiMedAZcMax", f"{max(zc['hi_med_runs']):.2f}", macros.get("RThirteenHiMedAZcMax"))
    for ch, x in t.items():
        expect(f"concurrency {T.SHOW[ch]}", macros.get("Conc"), "/".join(map(str, sorted(x["conc"]))))
        if "hi_conc" in x:
            expect(f"concurrency {T.SHOW[ch]} high", macros.get("ConcHi"), "/".join(map(str, sorted(x["hi_conc"]))))


def check(rows: list[dict], c: dict, t: dict, macros: dict[str, str]) -> int:
    table = tex_table("Size")
    want = []

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
    expect_cost_time(c, t, macros, expect)
    bad = [w for w in want if w[1] != w[2]]
    for where, ours, paper in bad:
        print(f"MISMATCH {where}: recomputed {ours!r}, paper {paper!r}")
    print(f"checked {len(want)} values against paper/appendix_tables.tex and paper/numbers.tex: {len(bad)} mismatches")
    return len(bad)


def mark(r: dict) -> str:
    """Down (up) arrow when the paired 95% interval to A1 lies entirely below (above) 0."""
    if not r["gap"]:
        return ""
    _, lo, hi, _ = r["gap"]
    return "↓" if hi < 0 else "↑" if lo > 0 else ""


def md_cell(r: dict, best: str | None, detail: bool) -> str:
    acc = plain(r["acc"])
    s = f"**{acc}**" if acc == best else acc
    if detail and r["gap"]:
        m, lo, hi, _ = r["gap"]
        s += f" ({plain(m)}; {plain(lo)} to {plain(hi)})"
    elif not detail:
        s += mark(r)
    return s + ("\\*" if r["cross_run"] else "")


def size_table(cell: dict, models: list[str], best: dict, detail: bool) -> list[str]:
    lines = ["| Channel | " + " | ".join(models) + " |", "| --- | " + " | ".join("---" for _ in models) + " |"]
    for ch in T.CHS:
        lab = LABEL[ch] + ("&dagger;" if ch == "D" else "")
        lines.append(f"| {lab} | " + " | ".join(md_cell(cell[m, ch], best[m] if ch in MAIN else None, detail)
                                                for m in models) + " |")
    return lines


def label(ch: str) -> str:
    return LABEL[ch] + ("&dagger;" if ch == "D" else "")


def x(v: float) -> str:
    return f"{v:.2f}×"


def span(vals) -> str:
    lo, hi = f"{min(vals):.2f}", f"{max(vals):.2f}"
    return f"{lo}×" if lo == hi else f"{lo}-{hi}×"


def cost_section(c: dict, macros: dict[str, str], detail: bool) -> list[str]:
    """Table 1: main-run cost per channel at k=3."""
    n = {v["n"] for v in c.values()}
    assert len(n) == 1, n
    rel = lambda ch, m: c[ch][m][0] / c["A1"][m][0]
    io = lambda v: "0" if v == 0 else f"{v:.1f}"
    fmt = {"total_tokens": lambda v: f"{v / 1000:.1f}", "prefill_tokens": lambda v: f"{v / 1000:.1f}",
           "llm_calls": lambda v: f"{v:.1f}", "file_io": io, "acc": plain}
    cols = ("total_tokens", "prefill_tokens", "llm_calls", "file_io", "acc")
    lines = [] if detail else [
        f"Main run: Qwen3-8B on RTX 3090s, {macros['BigKv']}-token KV cache, k = 3 questions per task, "
        f"{n.pop()} tasks (HotpotQA and 2Wiki pooled; `t07_main`). Each cell is a mean per task; file operations "
        "count `list_files`, `read_file`, and `write_file` calls.",
        "",
    ]
    lines += [
        "| Channel | Tokens sent (k) | Prefill computed (k) | Model calls | File operations | Accuracy (%) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for ch in T.CHS:
        cells = []
        for m in cols:
            mean, lo, hi = c[ch][m]
            s = fmt[m](mean)
            if detail and hi > lo:
                s += f" ({fmt[m](lo)} to {fmt[m](hi)})"
            cells.append(s)
        lines.append(f"| {label(ch)} | " + " | ".join(cells) + " |")
    if detail:
        return lines + ["", "In parentheses: 95% bootstrap intervals of each mean, resampling tasks."]
    pb, pc = x(rel("B", "prefill_tokens")), x(rel("C", "prefill_tokens"))
    pre = f"{pb} each" if pb == pc else f"{pb} and {pc}"
    return lines + [
        "",
        f"B and C send {rel('B', 'total_tokens'):.1f}× and {rel('C', 'total_tokens'):.1f}× broadcast's tokens "
        f"({c['B']['llm_calls'][0]:.1f} and {c['C']['llm_calls'][0]:.1f} model calls per task against "
        f"{c['A1']['llm_calls'][0]:.1f}) but compute less prefill ({pre}), because the prefix cache absorbs the "
        f"resent conversation; zero-copy sends about as many tokens as broadcast and computes "
        f"{(1 - rel('A1zc', 'prefill_tokens')) * 100:.0f}% less prefill.",
    ]


def prefill_section(rows: list[dict], macros: dict[str, str]) -> list[str]:
    """Table 2: prefill relative to A1 per channel and model size (Table 10's prefill column)."""
    size = [r for r in rows if r["exp"].startswith("p02_size_")]
    cell = {(r["model"], r["channel"]): r for r in size}
    models = [f"Qwen3-{lab}" for _, lab, _ in SIZES]
    lines = [
        "Size runs (as above): mean prefill tokens computed per task, relative to A1 broadcast at the same size "
        "and on the same tasks.",
        "",
        "| Channel | " + " | ".join(models) + " |",
        "| --- | " + " | ".join("---" for _ in models) + " |",
    ]
    for ch in T.CHS:
        lines.append(f"| {label(ch)} | " + " | ".join(
            x(cell[m, ch]["prefill"]) + ("&Dagger;" if not cell[m, ch]["shown"] else "") for m in models) + " |")
    pick = lambda chs: [r["prefill"] for r in size if r["channel"] in chs]
    lines += [
        "",
        f"Zero-copy and the pipe compute {span(pick(('A1zc', 'A2')))} broadcast's prefill at every size, and the "
        f"file channels {span(pick(('B', 'C')))}: at k = 3 with a "
        f"{macros['KvPro']}-token cache, files cost less prefill than broadcast, not more.",
        "",
        "&Dagger; Qwen3-32B B, C, and D: the size run's own values. Table 10 gives no prefill ratio for the path "
        "rerun (whose accuracy the accuracy table shows).",
    ]
    return lines


def timing_section(t: dict, macros: dict[str, str], detail: bool) -> list[str]:
    """Table 3: run time relative to A1 in the timing runs (Table 13) and the 32-at-a-time runs."""
    lo, hi = macros["Conc"], macros["ConcHi"]
    a1, zc = t["A1"], t["A1zc"]
    hi_chs = [T.SHOW[ch] for ch in T.CHS if "hi_wall" in t[ch]]
    dash = "–"
    lines = [
        f"Timing runs, separate from the main and size runs: each channel served alone on one RTX PRO 6000 (Qwen3-8B, "
        f"{macros['KvPro']}-token KV cache, {a1['n']} tasks at k = 3), three runs per channel with {lo} tasks at a "
        f"time and two runs of {', '.join(hi_chs[:-1])}, and {hi_chs[-1]} with {hi} at a time. Each cell is relative "
        "to A1 broadcast: the run's wall time (mean over runs), the median task's wall time (per run, then "
        "averaged), and vLLM's summed prefill and decode time.",
        "",
        f"| Channel | Run time ({lo}) | Median task ({lo}) | Prefill time ({lo}) | Decode time ({lo}) | "
        f"Run time ({hi}) | Median task ({hi}) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ch in T.CHS:
        v = t[ch]
        cells = [x(v["time"]), x(v["med_rel"]), x(v["pre_rel"]), x(v["dec_rel"])]
        cells += [x(v["hi_time"]), x(v["hi_med_rel"])] if "hi_wall" in v else [dash, dash]
        lines.append(f"| {label(ch)} | " + " | ".join(cells) + " |")
    share = a1["dec"] / (a1["dec"] + a1["pre"]) * 100
    lines += [
        "",
        f"Zero-copy cuts prefill time to {x(zc['pre_rel'])} but its runs take {x(zc['time'])} broadcast's: decoding "
        f"is {share:.0f}% of broadcast's prefill-plus-decode time, and zero-copy generates {zc['gen_rel']:.1f}× the "
        f"output tokens. With {hi} tasks at a time its median task takes {x(zc['hi_med_rel'])} but the run "
        f"{x(zc['hi_time'])}.",
        "",
        f"Cross-run: every ratio compares separate runs, so drift between runs adds to it. A1's runs took "
        f"{min(a1['wall']):.0f}-{max(a1['wall']):.0f} s with {lo} at a time and "
        f"{min(a1['hi_wall']):.0f}-{max(a1['hi_wall']):.0f} s with {hi}. vLLM's counters come from the second and "
        f"third {lo}-at-a-time runs. {dash}: not run with {hi} at a time. The run-time, prefill-time, and "
        "decode-time ratios with "
        f"{lo} at a time are the paper's Table 13 (Appendix G).",
    ]
    if detail:
        lines += [
            "",
            f"Per run, as in Table 13 ({lo} at a time): wall time of each run (s), run time relative to A1 (mean, and "
            "min to max over runs), generated tokens relative to A1, decode time per generated token (ms), and the "
            "median task's time relative to A1 in each run (runs paired by order).",
            "",
            "| Channel | Run 1 (s) | Run 2 (s) | Run 3 (s) | Run time | Min to max | Generated tokens | ms per token "
            "| Median task per run |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for ch in T.CHS:
            v = t[ch]
            lines.append(f"| {label(ch)} | " + " | ".join(f"{w:.0f}" for w in v["wall"]) + f" | {x(v['time'])} | "
                         f"{x(v['time_min'])} to {x(v['time_max'])} | {x(v['gen_rel'])} | {v['tok']:.1f} | "
                         + ", ".join(x(m) for m in v["med_runs"]) + " |")
        lines += [
            "",
            f"With {hi} at a time: wall time of each run (s), run time and summed prefill time relative to A1, and the "
            "median task's time relative to A1 in each run.",
            "",
            "| Channel | Run 1 (s) | Run 2 (s) | Run time | Prefill time | Median task per run |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for ch in T.CHS:
            v = t[ch]
            if "hi_wall" in v:
                lines.append(f"| {label(ch)} | " + " | ".join(f"{w:.0f}" for w in v["hi_wall"]) +
                             f" | {x(v['hi_time'])} | {x(v['hi_pre_rel'])} | "
                             + ", ".join(x(m) for m in v["hi_med_runs"]) + " |")
    return lines


def markdown(rows: list[dict], c: dict, t: dict, macros: dict[str, str]) -> str:
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
    marks = {mark(r) for r in rows} - {""}
    legend = []
    if "↓" in marks:
        legend.append("↓ significantly below A1 broadcast, paired 95% interval.")
    if "↑" in marks:
        legend.append("↑ significantly above A1 broadcast, paired 95% interval.")
    setup = (f"Size runs: Qwen3-4B to 32B, one RTX PRO 6000 per run, {macros['KvPro']}-token KV cache, k = 3 "
             f"questions per task, {n} tasks per size ({n // 2} HotpotQA and {n // 2} 2Wiki), the same tasks in "
             "every channel.")
    rerun_note = ("\\* Qwen3-32B B, C, and D: path rerun (`p08_norm_32b`, which strips a `workspace/` prefix "
                  "from file paths), paired with the size run's A1.")
    d_note = (f"&dagger; D is excluded from the main comparison: agents pass a message of at most "
              f"{macros['HandoffWords']} words plus file paths.")
    lines = [
        "# Accuracy, cost, and run time by channel",
        "",
        "Generated by `python analysis/accuracy_table.py` from the committed per-task rows and run times; the same "
        "values as the paper's Table 10 (size runs), Table 13 (timing runs), and its main-run and timing numbers.",
        "",
        "## Accuracy by channel and model size",
        "",
        setup + " Each cell is accuracy (% of questions answered correctly). Bold: the most accurate of A1 to C "
        "per model size.",
        "",
        *size_table(cell, models, best, detail=False),
        "",
        "  \n".join(legend),
        "",
        rerun_note + " The size run's own values: " + ", ".join(f"{ch} {md_cell(orig[ch], None, False)}"
                                                               for ch in RERUN) + ".",
        "",
        d_note,
        "",
        "For reference, the main run (a different run on a different server, not paired with the size runs): "
        f"Qwen3-8B on RTX 3090s, {macros['BigKv']}-token KV cache, k = 3, HotpotQA and 2Wiki pooled ({main['A1']['n']} tasks; "
        "`t07_main`). Accuracy (%):",
        "",
        "| Run | " + " | ".join(T.SHOW[ch] for ch in T.CHS) + " |",
        "| --- | " + " | ".join("---" for _ in T.CHS) + " |",
        "| Qwen3-8B, main run | " + " | ".join(md_cell(main[ch], main_best if ch in MAIN else None, False)
                                             for ch in T.CHS) + " |",
        "",
        "### With paired differences",
        "",
        "Each cell is accuracy (%) and, in parentheses, the paired difference to A1 broadcast (channel minus A1, in "
        "points, over the same tasks; negative means less accurate) and its 95% bootstrap interval, resampling "
        "tasks. An interval that excludes 0 is a significant difference. Bold: the most accurate of A1 to C per "
        "model size.",
        "",
        *size_table(cell, models, best, detail=True),
        "",
        rerun_note + " Cross-run, so drift between the runs adds to the difference. The size run's own values: "
        + ", ".join(f"{ch} {md_cell(orig[ch], None, True)}" for ch in RERUN) + ".",
        "",
        "## Cost by channel (main run)",
        "",
        *cost_section(c, macros, detail=False),
        "",
        d_note,
        "",
        "### With 95% intervals",
        "",
        *cost_section(c, macros, detail=True),
        "",
        "## Prefill relative to broadcast, by model size",
        "",
        *prefill_section(rows, macros),
        "",
        "## Run time relative to broadcast",
        "",
        *timing_section(t, macros, detail=True),
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
    rows, c, t = compute(), cost(), timing()
    macros = paper_macros()
    bad = check(rows, c, t, macros)
    if bad:
        return 1
    DOCS.mkdir(exist_ok=True)
    (DOCS / "accuracy_by_size.md").write_text(markdown(rows, c, t, macros))
    write_csv(rows)
    print(f"wrote {DOCS / 'accuracy_by_size.md'} and {DOCS / 'accuracy_by_size.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
