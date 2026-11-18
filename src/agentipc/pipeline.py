"""Researcher -> Writer -> Reviewer over one of three channels (A message passing, B files, C files + index)."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .data import Task
from .llm import ContextOverflow
from .workspace import Workspace

CHANNELS = ("A", "B", "C")
ROLES = ("researcher", "writer", "reviewer")

TEAM = ("You are one of three agents (Researcher, Writer, Reviewer) that answer a set of questions "
        "together, in that order.")

FORMAT = ("Use exactly this format for every question, in order:\n"
          "Q1: <short answer, a few words>\n"
          "Evidence: <one to three sentences that support the answer and cite document titles>\n"
          "Q2: ...")

ROLE_TEXT = {
    "researcher": ("You are the Researcher. Read the documents and collect every fact needed to answer each "
                   "question. For each question, list the relevant facts, quoting or closely paraphrasing the "
                   "documents and naming the document title of each fact. Multi-hop questions need several "
                   "linked facts; include the intermediate ones. Do not decide the final answers."),
    "writer": ("You are the Writer. Using the Researcher's facts, write a draft answer for each question: a "
               "short answer and one to three sentences of evidence that cite document titles."),
    "reviewer": ("You are the Reviewer. Check the Writer's draft against the facts, fix answers that are wrong "
                 "or unsupported, and produce the final answers."),
}

OUTPUT_A = {
    "researcher": "Reply with your notes. Your whole reply is passed to the next agents.",
    "writer": "Reply with the draft. " + FORMAT,
    "reviewer": "Reply with the final answers. " + FORMAT,
}

OUTPUT_FILES = {
    "researcher": ("The other agents cannot see your reply; they see only the shared workspace. Save your "
                   "notes there with write_file (choose the file names and how to split them). The source "
                   "documents are also in the workspace under docs/. When your notes are saved, reply DONE."),
    "writer": ("The Researcher's notes and the source documents are in the shared workspace. Find what you "
               "need with list_files and read_file; read only what you need. Save the draft to draft.md with "
               "write_file, then reply DONE. " + FORMAT),
    "reviewer": ("The draft (draft.md), the Researcher's notes and the source documents are in the shared "
                 "workspace. Read what you need with read_file. Save the final answers to final.md with "
                 "write_file, then reply DONE. " + FORMAT),
}

INDEX_RULE = {
    "researcher": ("The workspace has an index file, index.md, that the other agents read first. For every "
                   "file you write, append one line to index.md (write_file with append=true): "
                   "`<path> | <which questions> | <what facts it holds>`."),
    "writer": ("Read index.md first and use it to pick what to read. After saving draft.md, append one line "
               "for it to index.md (append=true)."),
    "reviewer": "Read index.md first and use it to pick what to read.",
}

TOOLS = [
    {"type": "function", "function": {
        "name": "list_files", "description": "List every file in the shared workspace with its size.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a workspace file, or only lines start_line..end_line (1-based).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"},
            "start_line": {"type": "integer"},
            "end_line": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write a workspace file; append=true adds to the end.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "append": {"type": "boolean"}}, "required": ["path", "content"]}}},
]

STAGE_FILE = {"writer": "draft.md", "reviewer": "final.md"}


def questions_block(task: Task) -> str:
    return "Questions:\n" + "\n".join(f"Q{i + 1}: {q.question}" for i, q in enumerate(task.questions))


def documents_block(task: Task) -> str:
    return "Documents:\n\n" + "\n\n".join(f"[{d.title}]\n{d.text}" for d in task.docs)


def system_prompt(role: str, channel: str) -> str:
    parts = [TEAM, ROLE_TEXT[role], OUTPUT_A[role] if channel == "A" else OUTPUT_FILES[role]]
    if channel == "C":
        parts.append(INDEX_RULE[role])
    return "\n\n".join(parts)


@dataclass
class AgentRun:
    role: str
    reply: str = ""
    calls: list[dict] = field(default_factory=list)
    hit_turn_limit: bool = False
    overflow: bool = False


async def run_agent(client, ws: Workspace | None, role: str, messages: list[dict], max_turns: int) -> AgentRun:
    run = AgentRun(role)
    tools = TOOLS if ws is not None else None
    for turn in range(max_turns):
        try:
            r = await client.chat(messages, tools)
        except ContextOverflow as e:
            run.overflow = True
            run.calls.append({"turn": turn, "error": "context_overflow", "detail": str(e)[:200]})
            return run
        call = {"turn": turn, "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
                "cached_tokens": r.cached_tokens, "latency_ms": round(r.latency_ms, 1),
                "finish_reason": r.finish_reason, "tools": []}
        run.calls.append(call)
        if not r.tool_calls or ws is None:
            run.reply = r.content
            return run
        messages.append({"role": "assistant", "content": r.content or None, "tool_calls": r.tool_calls})
        for tc in r.tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = None
            if not isinstance(args, dict):
                out = "ERROR: arguments must be a JSON object"
            elif name == "list_files":
                out = ws.list_files(role)
            elif name == "read_file":
                out = ws.read_file(role, args.get("path", ""), args.get("start_line"), args.get("end_line"))
            elif name == "write_file":
                out = ws.write_file(role, args.get("path", ""), args.get("content", ""), bool(args.get("append")))
            else:
                out = f"ERROR: unknown tool {name}"
            call["tools"].append(name)
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": out})
    run.hit_turn_limit = True
    return run


def seed_workspace(ws: Workspace, task: Task, channel: str) -> None:
    for d in task.docs:
        ws.seed(f"docs/{d.doc_id}.txt", f"{d.title}\n{d.text}\n")
    if channel == "C":
        ws.seed("index.md", "# Index: <path> | <questions> | <contents>\n" +
                "".join(f"docs/{d.doc_id}.txt | - | source document: {d.title}\n" for d in task.docs))


async def run_task(task: Task, channel: str, client, workdir: Path, max_turns: int = 12) -> dict:
    assert channel in CHANNELS
    t0 = time.perf_counter()
    qs, docs = questions_block(task), documents_block(task)
    ws = None if channel == "A" else Workspace(Path(workdir) / f"{task.task_id}_{channel}")
    if ws is not None:
        seed_workspace(ws, task, channel)

    runs: dict[str, AgentRun] = {}
    stage: dict[str, str] = {}
    # Researcher input is the same in every channel: the questions and the documents.
    msgs = [{"role": "system", "content": system_prompt("researcher", channel)},
            {"role": "user", "content": f"{qs}\n\n{docs}"}]
    runs["researcher"] = await run_agent(client, ws, "researcher", msgs, 1 if ws is None else max_turns)
    stage["notes"] = runs["researcher"].reply if ws is None else ws.written_by("researcher")

    for role, prev in (("writer", "researcher"), ("reviewer", "writer")):
        if channel == "A":
            # Message passing: every earlier message is copied into this agent's prompt.
            msgs = [{"role": "system", "content": system_prompt(role, channel)},
                    {"role": "user", "content": f"{qs}\n\n{docs}"},
                    {"role": "user", "content": f"[Researcher]\n{runs['researcher'].reply}"}]
            if role == "reviewer":
                msgs.append({"role": "user", "content": f"[Writer]\n{runs['writer'].reply}"})
        else:
            msgs = [{"role": "system", "content": system_prompt(role, channel)},
                    {"role": "user", "content": qs}]
        runs[role] = await run_agent(client, ws, role, msgs, 1 if ws is None else max_turns)
        if ws is None:
            stage["draft" if role == "writer" else "final"] = runs[role].reply
            if role == "writer":
                stage["writer_input"] = runs["researcher"].reply
        else:
            f = ws.root / STAGE_FILE[role]
            text = f.read_text() if f.is_file() else ""
            stage["draft" if role == "writer" else "final"] = text
            if role == "writer":
                stage["writer_input"] = "\n".join(ws.reads_by.get("writer", []))
    if ws is not None and not stage["final"]:
        stage["final"] = runs["reviewer"].reply
        stage["final_from_reply"] = "1"

    return {
        "task_id": task.task_id, "channel": channel, "dataset": task.dataset, "k": len(task.questions),
        "wall_s": round(time.perf_counter() - t0, 2),
        "agents": {r: {"calls": a.calls, "hit_turn_limit": a.hit_turn_limit, "overflow": a.overflow,
                       "reply": a.reply} for r, a in runs.items()},
        "io": {r: s.as_dict() for r, s in ws.stats.items()} if ws else {},
        "io_ops": ws.ops if ws else [],
        "stage": stage,
    }
