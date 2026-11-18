"""Multi-hop QA questions and the multi-question tasks the agents solve."""
from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Fact:
    title: str
    sent_id: int
    text: str


@dataclass
class Question:
    qid: str
    dataset: str
    question: str
    answer: str
    qtype: str
    paragraphs: list[tuple[str, list[str]]]
    facts: list[Fact] = field(default_factory=list)
    evidences: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass
class Doc:
    doc_id: str
    title: str
    text: str


@dataclass
class Task:
    task_id: str
    dataset: str
    questions: list[Question]
    docs: list[Doc]

    def to_json(self) -> dict:
        return asdict(self)


def _support(paragraphs, pairs) -> list[Fact]:
    sents = {t: s for t, s in paragraphs}
    return [Fact(title, int(sid), sents[title][sid].strip())
            for title, sid in pairs if title in sents and 0 <= sid < len(sents[title])]


def load_hotpot(path: str | Path) -> list[Question]:
    """HotpotQA distractor dev, from the original JSON or the Hugging Face parquet."""
    path = Path(path)
    if path.suffix == ".parquet":
        import pandas as pd
        rows = []
        for r in pd.read_parquet(path).to_dict("records"):
            ctx = r["context"]
            sf = r["supporting_facts"]
            rows.append({"_id": r["id"], "question": r["question"], "answer": r["answer"],
                         "type": r["type"],
                         "context": [[t, list(s)] for t, s in zip(ctx["title"], ctx["sentences"])],
                         "supporting_facts": [[t, int(i)] for t, i in zip(sf["title"], sf["sent_id"])]})
    else:
        rows = json.loads(path.read_text())
    out = []
    for r in rows:
        paras = [(t, list(s)) for t, s in r["context"]]
        out.append(Question(r["_id"], "hotpotqa", r["question"], r["answer"], r["type"], paras,
                            _support(paras, r["supporting_facts"])))
    return out


def load_2wiki(path: str | Path) -> list[Question]:
    out = []
    for r in json.loads(Path(path).read_text()):
        paras = [(t, list(s)) for t, s in r["context"]]
        out.append(Question(r["_id"], "2wiki", r["question"], r["answer"], r["type"], paras,
                            _support(paras, r["supporting_facts"]),
                            [tuple(e) for e in r.get("evidences", []) if len(e) == 3]))
    return out


LOADERS = {"hotpotqa": load_hotpot, "2wiki": load_2wiki}


def usable(q: Question) -> bool:
    """Keep questions whose supporting sentences are all present and whose answer is not yes/no."""
    return len(q.facts) >= 2 and q.answer.strip().lower() not in {"yes", "no"}


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60] or "doc"


def make_tasks(questions: list[Question], n_tasks: int, k: int, seed: int) -> list[Task]:
    """Draw n_tasks bundles of k distinct questions; documents are the union of their paragraphs."""
    pool = sorted((q for q in questions if usable(q)), key=lambda q: q.qid)
    rng = random.Random(seed)
    picked = rng.sample(pool, n_tasks * k)
    tasks = []
    for i in range(n_tasks):
        qs = picked[i * k:(i + 1) * k]
        docs, seen = [], {}
        for q in qs:
            for title, sents in q.paragraphs:
                if title in seen:
                    continue
                seen[title] = True
                docs.append(Doc(f"d{len(docs):03d}_{_slug(title)}", title, " ".join(s.strip() for s in sents)))
        rng.shuffle(docs)
        tasks.append(Task(f"{qs[0].dataset}-k{k}-s{seed}-{i:04d}", qs[0].dataset, qs, docs))
    return tasks


def task_stats(tasks: list[Task]) -> dict:
    n_docs = [len(t.docs) for t in tasks]
    chars = [sum(len(d.text) for d in t.docs) for t in tasks]
    facts = [sum(len(q.facts) for q in t.questions) for t in tasks]
    types: dict[str, int] = {}
    for t in tasks:
        for q in t.questions:
            types[q.qtype] = types.get(q.qtype, 0) + 1
    mean = lambda xs: round(sum(xs) / len(xs), 1) if xs else 0
    return {"tasks": len(tasks), "questions": sum(len(t.questions) for t in tasks),
            "docs_mean": mean(n_docs), "doc_chars_mean": mean(chars),
            "support_facts_mean": mean(facts), "types": types}
