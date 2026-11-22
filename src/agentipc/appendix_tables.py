"""Appendix tables and verbatim excerpts for the paper.

python -m agentipc.appendix_tables      (also run at the end of python -m agentipc.paper_numbers)
Writes paper/appendix_tables.tex (each table body as a macro \\appTab<Name>) and paper/appendix/*.txt
(verbatim text from the code and the run records, typeset with \\VerbatimInput). Every number comes from
results/ and results_raw/; nothing is typed by hand.
"""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import numpy as np
import yaml

from . import pipeline as P
from .analyze import analyze, load_rows, paired
from .data import load_2wiki, load_hotpot
from .factpairs import tasks_of
from .judge_all import PROMPT as JUDGE_PROMPT
from .metrics import correct, parse_answers
from .paper_numbers import _norm_path, kv_tokens, latest, raw_records, writer_opened_notes
from .stats import ci
from .workspace import Workspace

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
OUT = PAPER / "appendix"
STORE_FACTS = (ROOT / "data").resolve().parent / "factcheck"
CHS = ("A1", "A1zc", "A2", "B", "C", "D")
SHOW = {"A1": "A1", "A1zc": "A1-zc", "A2": "A2", "B": "B", "C": "C", "D": "D"}
SIZES = (("4b", "4B"), ("8b", "8B"), ("14b", "14B"), ("32b", "32B"))
# The worked example: a k=3 main-run task chosen by rule (see example_candidates).
EXAMPLE = "2wiki-k3-s2-0117"


def num(x: float, d: int = 1) -> str:
    """A number with a typeset minus sign; -0.0 prints as 0.0."""
    s = f"{x:.{d}f}"
    if s.startswith("-") and float(s) == 0:
        s = s[1:]
    return "\\mbox{$-$" + s[1:] + "}" if s.startswith("-") else s


def pt(x: float) -> str:
    return num(x * 100)


def ival(lo: float, hi: float) -> str:
    return f"{pt(lo)}, {pt(hi)}"


def by(rows, ch):
    return {r["task_id"]: r for r in rows if r["channel"] == ch and not r.get("error")}


def gap(x: dict, y: dict, metric: str = "acc"):
    """Paired mean of x - y over shared tasks, with the 95% bootstrap interval, and the task count."""
    ids = sorted(set(x) & set(y))
    mean, lo, hi = paired(np.array([x[i][metric] for i in ids], float), np.array([y[i][metric] for i in ids], float))
    return mean, lo, hi, len(ids)


def cell(g) -> str:
    return f"{pt(g[0])} \\scriptsize({ival(g[1], g[2])})"


def cfg_of(run: Path) -> dict:
    return yaml.safe_load((run / "config.yaml").read_text())


# ---------------------------------------------------------------- A. tasks

def tasks_table() -> str:
    """Per dataset and k: task counts, documents, supporting sentences, and the Researcher's prompt size."""
    lines = []
    for exp, ks in (("t07_main", (1, 3, 5)), ("t08_k8", (8,)), ("t08_large", (16,))):
        run = latest(exp)
        stats = json.loads((run / "task_stats.json").read_text())
        prompt = {}
        for rec in raw_records(run):
            if rec["channel"] != "A1" or "error" in rec:
                continue
            for role, a in rec["agents"].items():
                if role.startswith("researcher") and a["calls"]:
                    prompt.setdefault((rec["dataset"], rec["k"]), []).append(a["calls"][0]["prompt_tokens"])
        for ds, name in (("hotpotqa", "HotpotQA"), ("2wiki", "2Wiki")):
            for k in ks:
                key = next(x for x in stats if x.startswith(f"{ds}_k{k}_"))
                s = stats[key]
                seed = key.rsplit("_s", 1)[1]
                types = s["types"]
                if ds == "hotpotqa":
                    ty = f"{types.get('bridge', 0)}/{types.get('comparison', 0)}"
                else:
                    ty = "/".join(str(types.get(t, 0)) for t in ("compositional", "comparison", "inference", "bridge_comparison"))
                pr = prompt[(ds, k)]
                lines.append(f"{name} & {k} & {seed} & {s['tasks']} & {s['questions']} & {s['docs_mean']:.1f} & "
                             f"{s['doc_chars_mean'] / 1000:.1f} & {s['support_facts_mean']:.1f} & "
                             f"{np.mean(pr) / 1000:.1f} ({max(pr) / 1000:.1f}) & {ty} \\\\")
    return "\n".join(lines)


def task_listings(tasks) -> None:
    """How the worked example's three questions become one task."""
    t = tasks[EXAMPLE]
    # The Researcher's user message for the task (questions, then the shuffled documents).
    docs = P.documents_block(t).split("\n\n")
    head = docs[0]
    shown = []
    for d in docs[1:3]:
        title, text = d.split("\n", 1)
        shown.append(title + "\n" + (text[:150].rstrip() + " [...]" if len(text) > 150 else text))
    msg = P.questions_block(t) + "\n\n" + head + "\n\n" + "\n\n".join(shown) + "\n\n[...]\n"
    (OUT / "task_message.txt").write_text(msg)
    # What B's Writer saw from list_files in this task: the seeded documents and the Researcher's notes file.
    rec = next(r for r in raw_records(latest("t07_main")) if r["task_id"] == EXAMPLE and r["channel"] == "B")
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(Path(tmp))
        P.seed_workspace(ws, t, "B")
        for o in rec["io_ops"]:
            if o["agent"] == "researcher" and o["op"] == "write" and "error" not in o:
                ws.seed(_norm_path(o["path"]), rec["stage"]["notes"])
        listing = ws.list_files("writer").splitlines()
    (OUT / "task_listing.txt").write_text("\n".join(listing[:3] + ["[...]"] + listing[-2:]) + "\n")


# ---------------------------------------------------------------- B. prompts

def prompt_listings() -> None:
    chain = ("researcher", "writer", "reviewer")
    fmt = P.FORMAT
    short = lambda s: s.replace(fmt, "[...]")
    parts = [
        ("System prompt, first paragraph (every agent)", P.team_text(chain)),
        ("Role, Researcher", P.ROLE_TEXT["researcher"]),
        ("Role, Writer", P.ROLE_TEXT["writer"]),
        ("Role, Reviewer", P.ROLE_TEXT["reviewer"]),
        ("Role, Fact-checker (four-agent chain only, App. H)", P.ROLE_TEXT["checker"]),
        ("Answer format (FORMAT; shown once, [...] below)", fmt),
        ("Message channels (A1, A1-zc, A2), Researcher", P.OUTPUT_MSG["researcher"]),
        ("Message channels, Writer", short(P.OUTPUT_MSG["writer"])),
        ("Message channels, Reviewer", short(P.OUTPUT_MSG["reviewer"])),
        ("File channels (B, C, D), Researcher", P.OUTPUT_FILES["researcher"]),
        ("File channels, Writer", short(P.OUTPUT_FILES["writer"])),
        ("File channels, Reviewer", short(P.OUTPUT_FILES["reviewer"].format(prev_file="draft.md"))),
        ("File channels, after the file rule", P.DONE_RULE),
        ("C, Researcher (added)", P.INDEX_RULE["researcher"]),
        ("C, Writer and Reviewer (added)", P.INDEX_RULE["other"]),
        ("D, Researcher and Writer (replaces the DONE rule)", P.HANDOFF_RULE),
        ("D, Writer and Reviewer (added)", P.HANDOFF_READ),
        ("Reply-written notes, copied (A1r), Researcher (replaces the file rule)", P.OUTPUT_REPLY_MATCHED),
        ("Stored reply (Bs, and Bs0 with 00_notes.md), Researcher (replaces the file rule)", P.OUTPUT_REPLY_STORED),
        ("Told stored reply (Bt, and Bt0 with 00_notes.md), Writer and Reviewer (added)", P.NOTES_PATH_RULE),
        ("Reply-output (Br), Writer (replaces the file rule)", short(P.OUTPUT_READ_REPLY["writer"])),
        ("Reply-output (Br), Reviewer (replaces the file rule)", short(P.OUTPUT_READ_REPLY["reviewer"])),
        ("Heading rule without the index (Bh), Researcher (added)", P.HEADING_RULE),
        ("Batched reads (Bb), Writer and Reviewer (added)", P.BATCH_RULE),
    ]
    (OUT / "prompts.txt").write_text("\n".join(f">> {name}\n{text}\n" for name, text in parts))
    tools = []
    for t in P.TOOLS + [P.READ_MANY]:
        f = t["function"]
        props = f["parameters"].get("properties", {})
        req = set(f["parameters"].get("required", []))
        args = ", ".join(f"{a}: {v['type']}" + ("" if a in req else "?") for a, v in props.items())
        tools.append(f"{f['name']}({args})  \"{f['description']}\"")
    (OUT / "tools.txt").write_text("\n".join(tools) + "\n")
    (OUT / "judge_prompt.txt").write_text(JUDGE_PROMPT + "\n")


# ---------------------------------------------------------------- C. runs and serving

RUNS = [
    ("Main run", ["t07_main"], "reported"),
    ("$k{=}8$ run", ["t08_k8"], "reported"),
    ("$k{=}16$ run", ["t08_large"], "reported"),
    ("Documents control", ["t09_scope"], "reported"),
    ("Replay control", ["t09_replay"], "reported"),
    ("Rerun (noise)", ["t09_repeat"], "reported"),
    ("Cache runs", ["p01_cache_35k", "p01_cache_100k", "p01_cache_400k"], "reported"),
    ("Size runs", [f"p02_size_{s}" for s, _ in SIZES], "reported"),
    ("32B path rerun", ["p08_norm_32b"], "reported"),
    ("Zero-copy replay", ["p09_zcreplay_4b", "p09_zcreplay_8b"], "reported"),
    ("Wording runs", [f"p10_write_{s}" for s, _ in SIZES], "reported"),
    ("Crossed runs", [f"p16_store_{s}" for s, _ in SIZES], "reported"),
    ("Reply-output runs", [f"p14_read_{s}" for s, _ in SIZES], "reported"),
    ("Told runs", ["p17_told_14b", "p17_told_32b"], "reported"),
    ("First-listed run", ["p18_first_14b"], "reported"),
    ("Timing, 6 at a time", [f"p06_alone_{c}" for c in CHS] + [f"p11_alone_{c}_r{i}" for c in CHS for i in (2, 3)], "reported"),
    ("Timing, 32 at a time", [f"p11_c32_{c}_r{i}" for c in ("A1", "A1zc", "B") for i in (1, 2)], "reported"),
    ("$k{=}16$ budget runs", ["p07_k16_kv100k", "p07_k16_b24"], "reported"),
    ("$k{=}16$ guard run", ["p12_k16_clobber"], "reported"),
    ("$k{=}8$ folder runs", ["p15_k8_one", "p15_k8_three"], "reported"),
    ("Batched reads", ["t08_batch"], "App.~\\ref{app:cut}"),
    ("Fact-checker chain", ["t08_chain4"], "App.~\\ref{app:cut}"),
    ("$k{=}3$ fan-out", ["t08_fanout"], "App.~\\ref{app:cut}"),
    ("4B on RTX 3090", ["t08_qwen4b"], "App.~\\ref{app:cut}"),
    ("32B corner", ["p03_corner_32b_35k"], "App.~\\ref{app:cut}"),
]
ARM = {"A1": "A1", "A1zc": "A1-zc", "A2": "A2", "B": "B", "C": "C", "D": "D", "A1r": "A1r", "A1w": "A1w",
       "Bs": "Bs", "Bt": "Bt", "Bs0": "Bs0", "Bt0": "Bt0", "Br": "Br", "Bb": "Bb", "A2d": "A2d", "Bd": "Bd",
       "Bn": "Bn", "Bh": "Bh", "Bf": "Bf"}


def pro6000_kv() -> dict:
    """(exp, run_id) -> (kv tokens, GPU memory utilization), from the PRO 6000 ledgers (server logs)."""
    out = {}
    for f in sorted((ROOT / "results").glob("pro6000*_kv_used.txt")):
        for line in f.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            cols = line.split("\t")
            if len(cols) >= 7 and cols[5].replace(",", "").isdigit() and (ROOT / "results" / cols[0] / cols[1]).is_dir():
                out[(cols[0], cols[1])] = (int(cols[5].replace(",", "")), cols[6])
    return out


def run_info(exp: str, kv: dict) -> dict:
    run = latest(exp)
    cfg = cfg_of(run)
    env = json.loads((run / "env.json").read_text())
    rows = load_rows(run)
    gpu = "RTX PRO 6000" if "PRO 6000" in env["gpu"] else "RTX 3090" if "3090" in env["gpu"] else env["gpu"]
    servers = len(cfg["server"].get("base_urls") or [1])
    model = cfg["model"].split("Qwen3-")[1]
    if gpu == "RTX PRO 6000":
        tokens, util = kv[(exp, run.name)]
    else:
        tokens, util = kv_tokens(f"Qwen3-{model}"), "0.90"
    per_k = {}
    for r in rows:
        per_k.setdefault(r["k"], set()).add((r["dataset"], r["task_id"]))
    return {"exp": exp, "gpu": gpu, "servers": servers, "model": model, "kv": tokens, "util": util,
            "k": sorted(per_k), "tasks": max(len(v) for v in per_k.values()), "chans": cfg["channels"],
            "cap": cfg["max_tokens"], "turns": cfg["max_turns"], "conc": cfg["concurrency"],
            "researchers": cfg.get("researchers", 1), "date": run.name[:8], "vllm": env["vllm_version"]}


def runs_table() -> tuple[str, dict]:
    kv = pro6000_kv()
    lines, seen = [], {}
    join = lambda xs: "/".join(dict.fromkeys(str(x) for x in xs))
    for label, exps, use in RUNS:
        infos = [run_info(e, kv) for e in exps]
        for i in infos:
            seen[i["exp"]] = i
        gpu = infos[0]["gpu"]
        gpu = f"{infos[0]['servers']}$\\times$ {gpu}" if infos[0]["servers"] > 1 else gpu
        kvs = join(f"{i['kv']:,}" for i in infos)
        chans = []
        for i in infos:
            chans += [ARM[c] for c in i["chans"] if ARM[c] not in chans]
        dates = sorted({i["date"] for i in infos})
        date = dates[0][4:6] + "/" + dates[0][6:] + ("--" + dates[-1][6:] if len(dates) > 1 else "")
        res = join(i["researchers"] for i in infos)
        lines.append(f"{label} & {join(i['model'] for i in infos)} & {gpu} & {kvs} & {join(x for i in infos for x in i['k'])} & "
                     f"{join(i['tasks'] for i in infos)} & {res} & {', '.join(chans)} & {join(i['cap'] for i in infos)} & "
                     f"{join(i['turns'] for i in infos)} & {join(i['conc'] for i in infos)} & {date} & {use} \\\\")
    return "\n".join(lines), seen


# ---------------------------------------------------------------- D. worked example

def block(text: str, start: str, cut: int | None = None) -> str:
    """The lines of text from the first line containing `start` to the end, trailing blanks removed; with cut,
    longer lines end in [...] after that many characters."""
    lines = text.splitlines()
    i = next(j for j, l in enumerate(lines) if start in l)
    if cut is not None:
        lines = [l if len(l) <= cut else l[:cut].rsplit(" ", 1)[0] + " [...]" for l in lines]
    return "\n".join(lines[i:]).rstrip()


def trace(rec: dict, agent: str) -> list[str]:
    """The agent's file operations, written as the tool calls that made them."""
    out = []
    for o in rec["io_ops"]:
        if o["agent"] != agent:
            continue
        if o["op"] == "list":
            out.append("list_files()")
        elif o["op"] == "read":
            out.append(f"read_file(\"{o['path']}\")" + (f"  -> {o['error']}" if "error" in o else ""))
        else:
            out.append(f"write_file(\"{o['path']}\", <{o['chars']} chars>)")
    return out


def example_candidates() -> tuple[list[str], int]:
    """k=3 main-run tasks that ran in A1, A1zc, A2, B, and C where broadcast answers every question, the pipe's
    Reviewer turns a right draft answer wrong, and B's Writer never opens the notes."""
    recs = {}
    for rec in raw_records(latest("t07_main")):
        if rec["k"] == 3 and "error" not in rec:
            recs.setdefault(rec["task_id"], {})[rec["channel"]] = rec
    full = {t: d for t, d in recs.items() if all(c in d for c in ("A1", "A1zc", "A2", "B", "C"))}
    hits = [t for t, d in sorted(full.items()) if d["A1"]["score"]["acc"] == 1.0
            and d["A2"]["score"]["q_reviewer_broke"] > 0 and not writer_opened_notes(d["B"])]
    return hits, len(full)


def example(tasks) -> str:
    t = tasks[EXAMPLE]
    recs = {r["channel"]: r for r in raw_records(latest("t07_main")) if r["task_id"] == EXAMPLE}
    qs = t.questions
    (OUT / "ex_task.txt").write_text("\n".join(f"Q{i + 1}: {q.question}\n    gold: {q.answer}" for i, q in enumerate(qs)) + "\n")
    for ch in ("A1", "A1zc", "A2", "B", "C"):
        rec = recs[ch]
        st = rec["stage"]
        out = []
        if ch in ("B", "C"):
            notes_files = [o["path"] for o in rec["io_ops"] if o["agent"] == "researcher" and o["op"] == "write"]
            out.append(">> Researcher's tool calls")
            out += trace(rec, "researcher")
            if ch == "B":
                out.append(f">> {notes_files[0]}, Q3 part")
                out.append(block(st["notes"], "Q3"))
        elif ch == "A1":  # the other message channels' notes state the same Q3 facts; only their drafts are shown
            out.append(">> Researcher's reply (the notes), Q3 part")
            out.append(block(st["notes"], "Q3"))
        if ch in ("B", "C"):
            out.append(">> Writer's tool calls")
            out += trace(rec, "writer")
            out.append(">> draft.md, Q3")
        else:
            out.append(">> Writer's reply (the draft), Q3")
        # Drafts that copy the notes' facts correctly are cut; the pipe's and B's are shown whole.
        out.append(block(st["draft"], "Q3:", None if ch in ("A2", "B") else 90))
        if ch == "B":
            out.append(">> Reviewer's tool calls")
            out += trace(rec, "reviewer")
        same = block(st["final"], "Q3:").strip() == block(st["draft"], "Q3:").strip()
        name = "final.md" if ch in ("B", "C") else "Reviewer's reply (the final answers)"
        if same:
            out.append(f">> {name}, Q3: same text as the draft")
        else:
            out.append(f">> {name}, Q3")
            out.append(block(st["final"], "Q3:"))
        (OUT / f"ex_{ch}.txt").write_text("\n".join(out) + "\n")
    rows = []
    for ch in ("A1", "A1zc", "A2", "B", "C"):
        rec = recs[ch]
        final = parse_answers(rec["stage"]["final"], 3)
        draft = parse_answers(rec["stage"]["draft"], 3)
        mark = lambda a, q: "\\checkmark" if correct(a, q.answer) else "$\\times$"
        q3 = final[2]
        opened = ("yes" if writer_opened_notes(rec) else "no") if ch in ("B", "C") else "copied"
        rows.append(f"{SHOW[ch]} & {mark(final[0], qs[0])} & {mark(final[1], qs[1])} & {mark(draft[2], qs[2])} & "
                    f"{q3} {mark(q3, qs[2])} & {opened} & {rec['score']['total_tokens'] / 1000:.1f}k & "
                    f"{rec['score']['prefill_tokens'] / 1000:.1f}k \\\\")
    return "\n".join(rows)


# ---------------------------------------------------------------- E. fact measures

def facts_table() -> str:
    run = latest("t07_main")
    syn = json.loads((run / "judge_synthetic.json").read_text())
    av = json.loads((run / "alignscore_validation.json").read_text())
    jx = json.loads((run / "judge_cross.json").read_text())
    k = lambda x: f"{x:.2f}"
    rows = [("AlignScore ($\\ge$0.5)", av["synthetic"], f"{av['synthetic']['auc']:.3f}",
             "--", k(av["real"]["qwen3-8b"]["kappa"]), k(av["real"]["llama3-8b"]["kappa"]), k(av["real"]["lexical"]["kappa"])),
            ("Qwen3-8B judge", syn["qwen3-8b"], "--", k(av["real"]["qwen3-8b"]["kappa"]), "--",
             k(jx["qwen_vs_other"]["kappa"]), k(jx["qwen_vs_lexical"]["kappa"])),
            ("Llama-3-8B judge", syn["llama3-8b"], "--", k(av["real"]["llama3-8b"]["kappa"]),
             k(jx["qwen_vs_other"]["kappa"]), "--", k(jx["other_vs_lexical"]["kappa"])),
            ("Lexical anchors", syn["lexical"], "--", k(av["real"]["lexical"]["kappa"]),
             k(jx["qwen_vs_lexical"]["kappa"]), k(jx["other_vs_lexical"]["kappa"]), "--")]
    out = []
    for name, s, auc, *kap in rows:
        out.append(f"{name} & {s['present'] * 100:.0f} & {s['dropped'] * 100:.0f} & {s['swapped'] * 100:.0f} & {auc} & "
                   + " & ".join(kap) + " \\\\")
    return "\n".join(out)


def synthetic_listing() -> None:
    """One synthetic triple (present, dropped, swapped) with its AlignScore values, the first in file order."""
    rows = [json.loads(l) for l in open(STORE_FACTS / "synthetic_as.jsonl")]
    trip = rows[:3]
    assert [r["kind"] for r in trip] == ["present", "dropped", "swapped"] and len({r["fact"] for r in trip}) == 1
    fact = trip[0]["fact"]
    sents = lambda text: re.split(r"(?<=[.!?])\s+", text)
    swapped = next(s for s in sents(trip[2]["context"]) if s not in trip[0]["context"])
    out = [f"question: {trip[0]['question']}", f"fact F: {fact}",
           f"present: F is among the paragraphs' other sentences, shuffled   AlignScore {trip[0]['alignscore']:.3f}",
           f"dropped: F removed   AlignScore {trip[1]['alignscore']:.3f}",
           f"swapped: F replaced by \"{swapped}\"   AlignScore {trip[2]['alignscore']:.3f}"]
    (OUT / "synthetic.txt").write_text("\n".join(out) + "\n")


def stage_table() -> str:
    """Main run, k=3: fact coverage by three measures and the first stage that explains each wrong answer."""
    run = latest("t07_main")
    rows = [r for r in load_rows(run) if r["k"] == 3]
    ent = json.loads((run / "entities.json").read_text())["pooled"]
    out = []
    for ch in CHS:
        rs = [r for r in rows if r["channel"] == ch]
        m = lambda key: np.mean([r[key] for r in rs if key in r]) * 100
        e = ent[f"k3|{ch}"]
        wrong = 100 - np.mean([r["acc"] for r in rs]) * 100
        out.append(f"{SHOW[ch]} & {m('as_recall_notes'):.0f} & {m('as_kept_writer_input'):.0f} & "
                   f"{e['ent_recall_notes'] * 100:.0f} & {e['ent_kept_writer_input'] * 100:.0f} & "
                   f"{m('judge_recall_notes'):.0f} & {wrong:.1f} & {m('aq_research_miss'):.1f} & {m('aq_delivery_miss'):.1f} & "
                   f"{m('aq_writer_wrong'):.1f} & {m('aq_reviewer_broke'):.1f} & {m('aq_no_answer'):.1f} \\\\")
    return "\n".join(out)


# ---------------------------------------------------------------- G. full results

def main_table() -> str:
    """Accuracy, paired gap to A1, tokens sent, and prefill per channel, dataset, and k (RTX 3090 runs)."""
    out = []
    for exp, ks in (("t07_main", (1, 3, 5)), ("t08_k8", (8,)), ("t08_large", (16,))):
        rows = load_rows(latest(exp))
        res = analyze(rows, "A1")
        for k in ks:
            for j, ch in enumerate(CHS):
                cells = []
                for ds in ("hotpotqa", "2wiki"):
                    g = res.get(f"{ds}|k{k}|{ch}")
                    if g is None:
                        cells += ["--"] * 4
                        continue
                    d = g.get("acc_diff")
                    cells += [pt(g["acc"]), f"{pt(d[0])} \\scriptsize({ival(d[1], d[2])})" if d else "--",
                              f"{g['total_tokens'] / 1000:.1f}", f"{g['prefill_tokens'] / 1000:.1f}"]
                n = res[f"hotpotqa|k{k}|A1"]["n"]
                lead = f"\\multirow{{6}}{{*}}{{{k} ({n})}}" if j == 0 else ""
                out.append(f"{lead} & {SHOW[ch]} & " + " & ".join(cells) + " \\\\")
            out.append("\\midrule")
    return "\n".join(out[:-1])


def size_table() -> str:
    """Size runs (RTX PRO 6000, 100k-token cache, k=3): accuracy and paired gap to A1, and prefill / A1."""
    out = []
    data = {}
    for s, lab in SIZES:
        rows = load_rows(latest(f"p02_size_{s}"))
        data[s] = rows
    rerun = load_rows(latest("p08_norm_32b"))
    for ch in CHS:
        cells = []
        for s, _ in SIZES:
            rows = data[s]
            a1 = by(rows, "A1")
            pre = np.mean([r["prefill_tokens"] for r in by(rows, ch).values()]) / np.mean([r["prefill_tokens"] for r in a1.values()])
            acc = np.mean([r["acc"] for r in by(rows, ch).values()])
            if ch == "A1":
                cells += [pt(acc), "--", f"{pre:.2f}"]
            else:
                cells += [pt(acc), cell(gap(by(rows, ch), a1)), f"{pre:.2f}"]
        out.append(f"{SHOW[ch]} & " + " & ".join(cells) + " \\\\")
    a1 = by(data["32b"], "A1")
    for ch in ("B", "C", "D"):
        g = gap(by(rerun, ch), a1)
        acc = np.mean([r["acc"] for r in by(rerun, ch).values()])
        out.append(f"{ch}, path rerun$^\\ast$ & \\multicolumn{{9}}{{c}}{{}} & {pt(acc)} & {cell(g)} & -- \\\\")
    return "\n".join(out)


def cache_table() -> str:
    """Cache runs (Qwen3-8B, k=8) and the 32B corner cell: accuracy and prefill relative to A1."""
    exps = ["p01_cache_35k", "p01_cache_100k", "p01_cache_400k", "p03_corner_32b_35k"]
    data = {e: load_rows(latest(e)) for e in exps}
    out = []
    for ch in CHS:
        cells = []
        for e in exps:
            rows = data[e]
            a1 = np.mean([r["prefill_tokens"] for r in by(rows, "A1").values()])
            d = by(rows, ch)
            cells += [pt(np.mean([r["acc"] for r in d.values()])),
                      f"{np.mean([r['prefill_tokens'] for r in d.values()]) / a1:.2f}"]
        out.append(f"{SHOW[ch]} & " + " & ".join(cells) + " \\\\")
    return "\n".join(out)


def arms_table() -> str:
    """Accuracy of every arm of the PRO 6000 runs at k=3, with the Writer's notes-open rate for file arms."""
    groups = [("Wording", "p10_write", ("A1", "A1r", "A1w", "B")),
              ("Crossed", "p16_store", ("A1r", "A1w", "Bs", "B")),
              ("Reply-output", "p14_read", ("A1w", "B", "Br")),
              ("Told", "p17_told", ("Bs", "Bt", "B")),
              ("First-listed", "p18_first", ("B", "Bt", "Bs0", "Bt0"))]
    out = []
    for gname, prefix, arms in groups:
        runs = {}
        for s, _ in SIZES:
            r = latest(f"{prefix}_{s}")
            if r is not None:
                runs[s] = r
        recs = {s: [x for x in raw_records(r) if "error" not in x] for s, r in runs.items()}
        rows = {s: load_rows(r) for s, r in runs.items()}
        for j, arm in enumerate(arms):
            cells = []
            for s, _ in SIZES:
                if s not in runs:
                    cells.append("")
                    continue
                acc = np.mean([v["acc"] for v in by(rows[s], arm).values()])
                c = pt(acc)
                if arm in P.FILE_CHANNELS:
                    op = np.mean([writer_opened_notes(x) for x in recs[s] if x["channel"] == arm]) * 100
                    c += f" / {op:.0f}"
                cells.append(c)
            n = len({x["task_id"] for x in recs[next(iter(recs))] if x["channel"] == arms[0]})
            lead = f"\\multirow{{{len(arms)}}}{{*}}{{{gname} ({n})}}" if j == 0 else ""
            out.append(f"{lead} & {ARM[arm]} & " + " & ".join(cells) + " \\\\")
        out.append("\\midrule")
    return "\n".join(out[:-1])


def timing_table() -> str:
    """Serving time of each channel run alone on one RTX PRO 6000 (Qwen3-8B, 100k tokens, k=3)."""
    out = []
    t, gen, pre, dec, tok = {}, {}, {}, {}, {}
    for ch in CHS:
        runs = [latest(f"p06_alone_{ch}"), latest(f"p11_alone_{ch}_r2"), latest(f"p11_alone_{ch}_r3")]
        rt = [json.loads((x / "run_time.json").read_text()) for x in runs]
        t[ch] = [d["elapsed_s"] for d in rt]
        gen[ch] = np.mean([np.mean([r["completion_tokens"] for r in load_rows(x)]) for x in runs])
        vm = [d["vllm_metrics"] for d in rt if d.get("vllm_metrics")]
        pre[ch] = np.mean([v["vllm:request_prefill_time_seconds_sum"] for v in vm])
        dec[ch] = np.mean([v["vllm:request_decode_time_seconds_sum"] for v in vm])
        tok[ch] = np.mean([v["vllm:request_decode_time_seconds_sum"] / v["vllm:generation_tokens_total"] * 1000 for v in vm])
    base = np.mean(t["A1"])
    for ch in CHS:
        ratio = [x / base for x in t[ch]]
        out.append(f"{SHOW[ch]} & " + " & ".join(f"{x:.0f}" for x in t[ch]) + f" & {np.mean(ratio):.2f} & "
                   f"{gen[ch] / gen['A1']:.2f} & {pre[ch] / pre['A1']:.2f} & {dec[ch] / dec['A1']:.2f} & {tok[ch]:.1f} \\\\")
    return "\n".join(out)


# ---------------------------------------------------------------- H. cut results

def cut_table() -> str:
    """Each result cut from the body: comparison, estimate with 95% interval and task count, and its label."""
    main = load_rows(latest("t07_main"))
    k3 = [r for r in main if r["k"] == 3]
    mk = lambda rows, ch: {(r["dataset"], r["task_id"]): r for r in rows if r["channel"] == ch}
    rows = []

    def add(item, comp, g, label):
        rows.append(f"{item}: {comp} & {pt(g[0])} & {ival(g[1], g[2])} & {g[3]} & {label} \\\\")

    add("D", "D $-$ A1", gap(mk(k3, "D"), mk(k3, "A1")), "in-run")
    bb = load_rows(latest("t08_batch"))
    add("Batched reads", "Bb $-$ main-run B", gap(mk(bb, "Bb"), mk(k3, "B")), "cross-run")
    ch4 = load_rows(latest("t08_chain4"))
    for ch in ("A2", "B"):
        add("Fact-checker", f"{ch} with $-$ without", gap(mk(ch4, ch), mk(k3, ch)), "cross-run")
    fan = load_rows(latest("t08_fanout"))
    for ch in ("A1", "B"):
        add("$k{=}3$ fan-out", f"{SHOW[ch]}, three $-$ one Researcher", gap(mk(fan, ch), mk(k3, ch)), "cross-run")
    ids = sorted(set(mk(fan, "B")) & set(mk(fan, "A1")))
    did = [(mk(fan, "B")[i]["acc"] - mk(k3, "B")[i]["acc"]) - (mk(fan, "A1")[i]["acc"] - mk(k3, "A1")[i]["acc"]) for i in ids]
    add("$k{=}3$ fan-out", "B's change $-$ A1's", (*ci(did), len(ids)), "cross-run")
    for s, lab in SIZES:
        p14 = load_rows(latest(f"p14_read_{s}"))
        add(f"Br, {lab}", "Br $-$ A1w", gap(by(p14, "Br"), by(p14, "A1w")), "in-run")
    small = load_rows(latest("t08_qwen4b"))
    sk3 = [r for r in small if r["k"] == 3]
    for ch in ("A1zc", "B"):
        add("4B, RTX 3090", f"{SHOW[ch]} $-$ A1", gap(mk(sk3, ch), mk(sk3, "A1")), "in-run")
    return "\n".join(rows)


def write_tables(tables: dict[str, str]) -> None:
    body = ["% Generated by python -m agentipc.appendix_tables; do not edit."]
    for name, text in tables.items():
        body.append(f"\\newcommand{{\\appTab{name}}}{{%\n{text}\n}}")
    (PAPER / "appendix_tables.tex").write_text("\n".join(body) + "\n")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    _, tasks = tasks_of(latest("t07_main"))
    hits, _ = example_candidates()
    assert EXAMPLE in hits, (EXAMPLE, hits)
    task_listings(tasks)
    prompt_listings()
    synthetic_listing()
    runs, _ = runs_table()
    tables = {"Tasks": tasks_table(), "Runs": runs, "Example": example(tasks), "Facts": facts_table(),
              "Stage": stage_table(), "Main": main_table(), "Size": size_table(), "Cache": cache_table(),
              "Arms": arms_table(), "Timing": timing_table(), "Cut": cut_table()}
    write_tables(tables)
    print(f"wrote {len(tables)} appendix tables to {PAPER / 'appendix_tables.tex'} and listings to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
