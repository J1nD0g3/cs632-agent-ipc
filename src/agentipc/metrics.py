"""Task success, token cost, file I/O and information loss for one pipeline run."""
from __future__ import annotations

import re
import string
from collections import Counter

from .data import Fact, Question

STOP = set("""a an the of in on at to for from by with and or but is are was were be been being as that this
these those it its he she they his her their them who whom whose which what when where why how did does do
has have had not no yes than then also into over under about after before between during while one two""".split())


def normalize(s: str) -> str:
    """Official HotpotQA answer normalization."""
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def f1(pred: str, gold: str) -> float:
    p, g = normalize(pred).split(), normalize(gold).split()
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if not p or not g or same == 0:
        return 0.0
    prec, rec = same / len(p), same / len(g)
    return 2 * prec * rec / (prec + rec)


def em(pred: str, gold: str) -> float:
    return float(normalize(pred) == normalize(gold))


def correct(pred: str, gold: str) -> bool:
    """Exact match, F1 >= 0.8, or the gold answer appearing whole in a short prediction."""
    np_, ng = normalize(pred), normalize(gold)
    if not np_:
        return False
    contained = bool(ng) and re.search(rf"\b{re.escape(ng)}\b", np_) is not None and len(np_.split()) <= len(ng.split()) + 4
    return em(pred, gold) == 1.0 or f1(pred, gold) >= 0.8 or contained


def parse_answers(text: str, n: int) -> list[str]:
    """Pull 'Qi: answer' lines; missing answers are empty strings."""
    out = [""] * n
    for m in re.finditer(r"(?im)^\s*[*#>\-\s]*\**Q(\d+)\**\s*[:.)\-]\s*\**(.*?)\**\s*$", text or ""):
        i = int(m.group(1)) - 1
        if 0 <= i < n and not out[i]:
            out[i] = m.group(2).strip()
    return out


def _tokens(s: str) -> list[str]:
    return normalize(s).split()


def anchors(fact: Fact, question: Question) -> set[str]:
    """Content tokens a text must carry to state the fact: numbers and words not already in the question."""
    q = set(_tokens(question.question))
    toks = [t for t in _tokens(fact.text) if t not in STOP and t not in q and len(t) > 1]
    return set(toks)


def fact_present(fact: Fact, question: Question, text: str, thresh: float = 0.5) -> bool:
    a = anchors(fact, question)
    if not a:
        return True
    have = set(_tokens(text))
    return len(a & have) / len(a) >= thresh


def triple_present(triple: tuple[str, str, str], text: str) -> bool:
    have = " " + normalize(text) + " "
    subj, _, obj = triple
    return all((" " + normalize(x) + " ") in have for x in (subj, obj) if normalize(x))


def score_run(rec: dict, task_questions: list[Question]) -> dict:
    n = len(task_questions)
    preds = parse_answers(rec["stage"].get("final", ""), n)
    ok = [correct(p, q.answer) for p, q in zip(preds, task_questions)]
    out = {
        "answered": sum(bool(p) for p in preds) / n,
        "em": sum(em(p, q.answer) for p, q in zip(preds, task_questions)) / n,
        "f1": sum(f1(p, q.answer) for p, q in zip(preds, task_questions)) / n,
        "acc": sum(ok) / n,
        "all_correct": float(all(ok)),
    }
    calls = [c for a in rec["agents"].values() for c in a["calls"] if "error" not in c]
    out["prompt_tokens"] = sum(c["prompt_tokens"] for c in calls)
    out["completion_tokens"] = sum(c["completion_tokens"] for c in calls)
    out["total_tokens"] = out["prompt_tokens"] + out["completion_tokens"]
    out["prefill_tokens"] = sum(c["prompt_tokens"] - c["cached_tokens"] for c in calls)
    out["llm_calls"] = len(calls)
    for role, a in rec["agents"].items():
        out[f"tokens_{role}"] = sum(c["prompt_tokens"] + c["completion_tokens"] for c in a["calls"] if "error" not in c)
    out["overflow"] = float(any(a["overflow"] for a in rec["agents"].values()))
    out["turn_limit"] = float(any(a["hit_turn_limit"] for a in rec["agents"].values()))
    io = rec.get("io") or {}
    out["file_reads"] = sum(s["reads"] for s in io.values())
    out["file_writes"] = sum(s["writes"] for s in io.values())
    out["file_lists"] = sum(s["lists"] for s in io.values())
    out["file_io"] = out["file_reads"] + out["file_writes"] + out["file_lists"]
    out["read_chars"] = sum(s["read_chars"] for s in io.values())
    out["write_chars"] = sum(s["write_chars"] for s in io.values())

    stages = ("notes", "writer_input", "draft", "final")
    facts = [(f, q) for q in task_questions for f in q.facts]
    present = {s: [fact_present(f, q, rec["stage"].get(s, "")) for f, q in facts] for s in stages}
    nf = len(facts) or 1
    out["fact_recall_notes"] = sum(present["notes"]) / nf
    found = [i for i, v in enumerate(present["notes"]) if v]
    for s in ("writer_input", "draft", "final"):
        out[f"fact_kept_{s}"] = (sum(present[s][i] for i in found) / len(found)) if found else 0.0
    out["info_loss"] = 1 - out["fact_kept_final"] if found else 1.0
    out["fact_recall_final"] = sum(present["final"]) / nf
    triples = [t for q in task_questions for t in q.evidences]
    if triples:
        out["triple_recall_notes"] = sum(triple_present(t, rec["stage"].get("notes", "")) for t in triples) / len(triples)
        out["triple_recall_final"] = sum(triple_present(t, rec["stage"].get("final", "")) for t in triples) / len(triples)
    out["preds"] = preds
    return out
