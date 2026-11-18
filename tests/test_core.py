import asyncio
import json

import pytest

from agentipc.data import load_2wiki, make_tasks, task_stats
from agentipc.llm import MockClient
from agentipc.metrics import correct, f1, fact_present, parse_answers, score_run
from agentipc.pipeline import run_task, system_prompt
from agentipc.workspace import Workspace


def _row(i):
    return {"_id": f"q{i}", "type": "compositional", "question": f"Who directed film {i}?",
            "answer": f"Director {i}",
            "context": [[f"Film {i}", [f"Film {i} is a 1990 drama.", f"It was directed by Director {i}."]],
                        [f"Director {i}", [f"Director {i} was born in Paris."]],
                        [f"Other {i}", ["Unrelated text."]]],
            "supporting_facts": [[f"Film {i}", 1], [f"Director {i}", 0]],
            "evidences": [[f"Film {i}", "director", f"Director {i}"]]}


@pytest.fixture
def questions(tmp_path):
    p = tmp_path / "dev.json"
    p.write_text(json.dumps([_row(i) for i in range(10)]))
    return load_2wiki(p)


def test_loader_and_tasks_are_deterministic(questions):
    assert questions[0].facts[0].text == "It was directed by Director 0."
    assert questions[0].evidences == [("Film 0", "director", "Director 0")]
    a = make_tasks(questions, 2, 3, seed=1)
    b = make_tasks(questions, 2, 3, seed=1)
    assert [q.qid for t in a for q in t.questions] == [q.qid for t in b for q in t.questions]
    assert len(a[0].docs) == 9
    assert task_stats(a)["questions"] == 6


def test_workspace_counts_and_sandbox(tmp_path):
    ws = Workspace(tmp_path / "ws")
    ws.write_file("researcher", "notes/q1.md", "line1\nline2\nline3")
    assert ws.read_file("writer", "notes/q1.md", 2, 3) == "line2\nline3"
    assert ws.read_file("writer", "../etc/passwd").startswith("ERROR")
    assert ws.stats["writer"].reads == 1 and ws.stats["writer"].errors == 1
    assert ws.written_by("researcher") == "line1\nline2\nline3"


def test_answer_matching():
    assert parse_answers("Q1: Paris\nEvidence: x\n**Q2:** the Beatles", 3) == ["Paris", "the Beatles", ""]
    assert correct("The Beatles", "Beatles") and not correct("", "x")
    assert correct("Director 3 (French)", "Director 3")
    assert f1("New York City", "New York") > 0.7


def test_fact_presence(questions):
    q = questions[0]
    assert fact_present(q.facts[0], q, "Film 0 was directed by Director 0 [Film 0].")
    assert not fact_present(q.facts[1], q, "Film 0 was directed by Director 0.")


def _final(n):
    return "\n".join(f"Q{i + 1}: Director {i}\nEvidence: see docs." for i in range(n))


def test_channel_a_copies_history(questions, tmp_path):
    task = make_tasks(questions, 1, 2, seed=0)[0]
    client = MockClient(["NOTES: directed by Director", "DRAFT", _final(2)])
    rec = asyncio.run(run_task(task, "A1", client, tmp_path))
    assert len(client.calls) == 3 and client.calls[0]["tools"] is None
    reviewer_prompt = " ".join(m["content"] for m in client.calls[2]["messages"])
    assert "NOTES" in reviewer_prompt and "DRAFT" in reviewer_prompt and "Documents:" in reviewer_prompt
    assert rec["stage"]["notes"].startswith("NOTES")


def test_channel_b_uses_files(questions, tmp_path):
    task = make_tasks(questions, 1, 1, seed=0)[0]
    q = task.questions[0]
    final = f"Q1: {q.answer}\nEvidence: It was directed by {q.answer}."
    client = MockClient([
        [("write_file", {"path": "notes.md", "content": f"{q.facts[0].text} {q.facts[1].text}"})], "DONE",
        [("list_files", {})], [("read_file", {"path": "notes.md"})],
        [("write_file", {"path": "draft.md", "content": final})], "DONE",
        [("read_file", {"path": "draft.md"})], [("write_file", {"path": "final.md", "content": final})], "DONE",
    ])
    rec = asyncio.run(run_task(task, "B", client, tmp_path))
    writer_prompt = " ".join(str(m.get("content")) for m in client.calls[2]["messages"])
    assert "Documents:" not in writer_prompt
    s = score_run(rec, task.questions)
    assert s["acc"] == 1.0 and s["file_reads"] == 2 and s["file_writes"] == 3
    assert s["fact_recall_notes"] == 1.0 and s["fact_kept_writer_input"] == 1.0


def test_channel_c_prompts_mention_index():
    assert "index.md" in system_prompt("writer", "C") and "index.md" not in system_prompt("writer", "B")


def test_pipe_passes_only_previous_output(questions, tmp_path):
    task = make_tasks(questions, 1, 1, seed=0)[0]
    client = MockClient(["NOTES", "DRAFT", _final(1)])
    asyncio.run(run_task(task, "A2", client, tmp_path))
    reviewer_prompt = " ".join(m["content"] for m in client.calls[2]["messages"])
    assert "DRAFT" in reviewer_prompt and "NOTES" not in reviewer_prompt and "Documents:" not in reviewer_prompt


def test_zero_copy_shares_prefix(questions, tmp_path):
    task = make_tasks(questions, 1, 1, seed=0)[0]
    client = MockClient(["NOTES", "DRAFT", _final(1)])
    asyncio.run(run_task(task, "A1zc", client, tmp_path))
    r, w, v = (c["messages"] for c in client.calls)
    assert r[:2] == w[:2] == v[:2] and w[2] == v[2]
    a1 = MockClient(["NOTES", "DRAFT", _final(1)])
    asyncio.run(run_task(task, "A1", a1, tmp_path))
    words = lambda msgs: sorted(" ".join(m["content"] for m in msgs).split())
    assert words(v) == words(a1.calls[2]["messages"])


def test_handles_push_short_message(questions, tmp_path):
    task = make_tasks(questions, 1, 1, seed=0)[0]
    client = MockClient([
        [("write_file", {"path": "notes.md", "content": "facts"})], "HANDOFF: Q1 see notes.md",
        [("write_file", {"path": "draft.md", "content": _final(1)})], "HANDOFF2: draft.md",
        [("write_file", {"path": "final.md", "content": _final(1)})], "DONE",
    ])
    rec = asyncio.run(run_task(task, "D", client, tmp_path))
    reviewer_prompt = " ".join(str(m.get("content")) for m in client.calls[4]["messages"])
    assert "HANDOFF: Q1" in reviewer_prompt and "HANDOFF2" in reviewer_prompt and "Documents:" not in reviewer_prompt
    assert rec["stage"]["writer_input"].startswith("HANDOFF")


def test_five_agent_chain(questions, tmp_path):
    task = make_tasks(questions, 1, 1, seed=0)[0]
    chain = ("researcher", "writer", "checker", "reviewer")
    client = MockClient(["NOTES", "DRAFT", "CHECKED", _final(1)])
    rec = asyncio.run(run_task(task, "A1", client, tmp_path, chain=chain))
    assert rec["stage"]["checker"] == "CHECKED" and "Fact-checker" in client.calls[0]["messages"][0]["content"]


def test_index_tracks_agent_files(tmp_path, questions):
    from agentipc.pipeline import seed_workspace
    task = make_tasks(questions, 1, 1, seed=0)[0]
    ws = Workspace(tmp_path / "c")
    seed_workspace(ws, task, "C")
    ws.write_file("researcher", "notes.md", "# Notes for Q1\nfact")
    idx = (ws.root / "index.md").read_text()
    assert "notes.md | by researcher | 2 lines | Notes for Q1" in idx
    assert idx.index("notes.md") < idx.index("docs/")
