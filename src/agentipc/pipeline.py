"""An agent chain (Researcher -> ... -> Reviewer) over one inter-agent channel.

Channels: A1 broadcast (whole history copied), A1zc (A1 ordered so the prefix cache is reused),
A2 pipe (previous output only), B files, C files + index, D handles (short pushed message + files).
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from .data import Task
from .llm import ContextOverflow, SaltedClient
from .workspace import Workspace

CHANNELS = ("A1", "A1zc", "A2", "B", "Bb", "C", "D")
MESSAGE_CHANNELS = ("A1", "A1zc", "A2")
FILE_CHANNELS = ("B", "Bb", "C", "D")

TEAM = ("You are one agent in a team that answers a set of questions together. The agents work in this "
        "order: {chain}.")

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
    "checker": ("You are the Fact-checker. Check every answer in the current draft against the Researcher's "
                "facts and the documents, correct answers that are wrong or unsupported, and produce a "
                "checked draft."),
    "reviewer": ("You are the Reviewer. Check the latest draft, fix answers that are wrong or unsupported, "
                 "and produce the final answers."),
}
NAME = {"researcher": "Researcher", "writer": "Writer", "checker": "Fact-checker", "reviewer": "Reviewer",
        "researchers": "Researchers (several, in parallel)"}


def base_role(role: str) -> str:
    return "researcher" if role.startswith("researcher") else role


def display(role: str) -> str:
    return f"Researcher {role[10:]}" if role.startswith("researcher") and role[10:].isdigit() else NAME[role]

OUTPUT_MSG = {
    "researcher": "Reply with your notes. Your reply is passed on to the next agents.",
    "writer": "Reply with the draft. " + FORMAT,
    "checker": "Reply with the checked draft. " + FORMAT,
    "reviewer": "Reply with the final answers. " + FORMAT,
}

# File each role must leave for the next one in the file channels.
OUT_FILE = {"writer": "draft.md", "checker": "checked.md", "reviewer": "final.md"}

OUTPUT_FILES = {
    "researcher": ("The documents are in this message, so you do not need to read any file. The other agents "
                   "cannot see your reply; they see only the shared workspace, where the source documents also "
                   "are (under docs/). Save your notes there with write_file, in one or a few calls (choose the "
                   "file names and how to split them)."),
    "writer": ("The Researcher's notes and the source documents are in the shared workspace. Find the notes "
               "with list_files and read them with read_file; read a source document only to check a doubtful "
               "fact. Save the draft to draft.md with write_file. " + FORMAT),
    "checker": ("The draft (draft.md), the Researcher's notes and the source documents are in the shared "
                "workspace. Read what you need with read_file. Save the checked draft to checked.md with "
                "write_file. " + FORMAT),
    "reviewer": ("The latest draft ({prev_file}), the Researcher's notes and the source documents are in the "
                 "shared workspace. Read what you need with read_file. Save the final answers to final.md with "
                 "write_file. " + FORMAT),
}
DONE_RULE = "When your file is saved, reply DONE."

INDEX_RULE = {
    "researcher": ("The workspace keeps an index file, index.md, listing every file with its author and first "
                   "line; the other agents read it first. Start each notes file with a heading that says which "
                   "questions it covers."),
    "other": "Read index.md first (it lists every file with its author and first line) and use it to pick what to read.",
}

HANDOFF_RULE = ("When your file is saved, reply with a handoff message for the next agents of at most 120 "
                "words: for each question, the key finding in one line and the workspace path (and line "
                "numbers, if useful) where the details are. The next agents see this message but not your files "
                "unless they read them.")
HANDOFF_READ = ("Handoff messages from earlier agents are below. They say where the details are; read files only "
                "for details the handoff does not give.")

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


def questions_block(task: Task) -> str:
    return "Questions:\n" + "\n".join(f"Q{i + 1}: {q.question}" for i, q in enumerate(task.questions))


def documents_block(task: Task) -> str:
    return "Documents:\n\n" + "\n\n".join(f"[{d.title}]\n{d.text}" for d in task.docs)


def team_text(chain: tuple[str, ...]) -> str:
    return TEAM.format(chain=" -> ".join(NAME[r] for r in chain))


def instruction(role: str, channel: str, chain: tuple[str, ...]) -> str:
    """Role and channel instructions (everything an agent is told besides its inputs)."""
    role = base_role(role)
    parts = [ROLE_TEXT[role]]
    if channel in MESSAGE_CHANNELS:
        parts.append(OUTPUT_MSG[role])
    else:
        i = chain.index(role) if role in chain else 0
        prev_file = OUT_FILE.get(chain[i - 1], "draft.md") if i > 0 else ""
        parts.append(OUTPUT_FILES[role].format(prev_file=prev_file))
        parts.append(HANDOFF_RULE if channel == "D" and role != "reviewer" else DONE_RULE)
        if channel == "Bb" and role != "researcher":
            parts.append(BATCH_RULE)
        if channel == "C":
            parts.append(INDEX_RULE["researcher" if role == "researcher" else "other"])
        if channel == "D" and role != "researcher":
            parts.append(HANDOFF_READ)
    return "\n\n".join(parts)


def system_prompt(role: str, channel: str, chain: tuple[str, ...] = ("researcher", "writer", "reviewer")) -> str:
    return team_text(chain) + "\n\n" + instruction(role, channel, chain)


@dataclass
class AgentRun:
    role: str
    reply: str = ""
    calls: list[dict] = field(default_factory=list)
    hit_turn_limit: bool = False
    overflow: bool = False


WRITE_ONLY = [t for t in TOOLS if t["function"]["name"] == "write_file"]
# Bb: B plus a batched read, the agent analogue of readv(): several files in one round trip.
READ_MANY = {"type": "function", "function": {
    "name": "read_files", "description": "Read several workspace files in one call.",
    "parameters": {"type": "object", "properties": {
        "paths": {"type": "array", "items": {"type": "string"}}}, "required": ["paths"]}}}
TOOLS_BATCH = TOOLS + [READ_MANY]
BATCH_RULE = ("To read several files, use read_files with all their paths in one call; every tool call is a "
              "separate round trip.")
FORCE_WRITE = {"type": "function", "function": {"name": "write_file"}}


def _missing_output(ws: Workspace, role: str, out_file: str | None) -> bool:
    return not (ws.root / out_file).is_file() if out_file else not ws.written_by(role)


def _do_tool(ws: Workspace, role: str, name: str, raw_args: str | None) -> str:
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        args = None
    if not isinstance(args, dict):
        return "ERROR: arguments must be a JSON object"
    if name == "list_files":
        return ws.list_files(role)
    if name == "read_file":
        return ws.read_file(role, args.get("path", ""), args.get("start_line"), args.get("end_line"))
    if name == "read_files" and isinstance(args.get("paths"), list):
        return "\n\n".join(f"=== {p} ===\n" + ws.read_file(role, str(p)) for p in args["paths"][:20])
    if name == "write_file":
        return ws.write_file(role, args.get("path", ""), args.get("content", ""), bool(args.get("append")))
    return f"ERROR: unknown tool {name}"


async def _chat(client, run: AgentRun, messages, tools, turn: int, forced: bool):
    try:
        r = await client.chat(messages, tools, FORCE_WRITE if forced else None)
    except ContextOverflow as e:
        run.overflow = True
        run.calls.append({"turn": turn, "error": "context_overflow", "detail": str(e)[:200]})
        return None, None
    call = {"turn": turn, "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
            "cached_tokens": r.cached_tokens, "latency_ms": round(r.latency_ms, 1),
            "finish_reason": r.finish_reason, "tools": []}
    if forced:
        call["forced_write"] = True
    run.calls.append(call)
    return r, call


async def run_agent(client, ws: Workspace | None, role: str, messages: list[dict], max_turns: int,
                    out_file: str | None = None, full_tools: list[dict] = TOOLS) -> AgentRun:
    """Tool loop. An agent that stops without leaving its output gets one forced write_file turn."""
    run = AgentRun(role)
    tools = None if ws is None else (WRITE_ONLY if base_role(role) == "researcher" else full_tools)
    prev_sig, plain_reply = None, False
    for turn in range(max_turns if ws is not None else 1):
        r, call = await _chat(client, run, messages, tools, turn, False)
        if r is None:
            return run
        sig = [(tc["function"]["name"], tc["function"].get("arguments")) for tc in r.tool_calls]
        if ws is None or not r.tool_calls or sig == prev_sig:
            if r.tool_calls:
                call["repeat_stop"] = True  # the model repeats its last call verbatim
            run.reply, plain_reply = r.content, True
            break
        prev_sig = sig
        messages.append({"role": "assistant", "content": r.content or None, "tool_calls": r.tool_calls})
        for tc in r.tool_calls:
            name = tc["function"]["name"]
            out = _do_tool(ws, role, name, tc["function"].get("arguments"))
            call["tools"].append(name)
            left = max_turns - turn - 1
            if name == "write_file" and out.startswith("OK"):
                out += ". If you are finished, reply without calling a tool."
            if left <= 3:
                out += f"\n[{left} tool turns left]"
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": out})
    else:
        run.hit_turn_limit = ws is not None
    if ws is not None and _missing_output(ws, role, out_file):
        if plain_reply:
            messages.append({"role": "assistant", "content": run.reply or ""})
        messages.append({"role": "user", "content": f"Save your output to {out_file} now." if out_file
                         else "Save your notes now."})
        r, call = await _chat(client, run, messages, tools, max_turns, True)
        for tc in (r.tool_calls if r is not None else []):
            _do_tool(ws, role, tc["function"]["name"], tc["function"].get("arguments"))
            call["tools"].append(tc["function"]["name"])
    return run


def seed_workspace(ws: Workspace, task: Task, channel: str) -> None:
    for d in task.docs:
        ws.seed(f"docs/{d.doc_id}.txt", f"{d.title}\n{d.text}\n")
    if channel == "C":
        ws.auto_index = True
        ws.refresh_index()


def build_messages(role: str, channel: str, chain: tuple[str, ...], task: Task, replies: dict[str, str],
                   flat: list[str] | None = None, rtask: Task | None = None) -> list[dict]:
    """Messages for one agent. flat lists every agent in order (parallel Researchers expanded); rtask is the
    part of the task a parallel Researcher covers."""
    flat = flat or list(chain)
    qs, docs = questions_block(task), documents_block(task)
    before = flat[:flat.index(role)]
    if base_role(role) == "researcher":
        # A Researcher's input is the same in every channel: its questions and their documents.
        if rtask is not None:
            qs, docs = rtask_block(rtask), documents_block(rtask)
        if channel == "A1zc":
            return [{"role": "system", "content": team_text(chain)},
                    {"role": "user", "content": f"{qs}\n\n{docs}"},
                    {"role": "user", "content": instruction(role, channel, chain)}]
        return [{"role": "system", "content": system_prompt(role, channel, chain)},
                {"role": "user", "content": f"{qs}\n\n{docs}"}]
    if channel in ("A1", "A1zc"):
        # A1 copies everything said so far: the task (all questions and documents) and every earlier output.
        history = [{"role": "user", "content": f"{qs}\n\n{docs}"}]
        history += [{"role": "user", "content": f"[{display(r)}]\n{replies[r]}"} for r in before]
        if channel == "A1":
            return [{"role": "system", "content": system_prompt(role, channel, chain)}] + history
        # A1zc: same content, shared history first and the role instruction last, so consecutive agents
        # share a prompt prefix that the serving engine can reuse.
        return ([{"role": "system", "content": team_text(chain)}] + history +
                [{"role": "user", "content": instruction(role, channel, chain)}])
    if channel == "A2":
        # A pipe carries only the previous stage's output (all parallel Researchers, if that stage had several).
        prev = [r for r in before if base_role(r) == base_role(before[-1])] if base_role(before[-1]) == "researcher" \
            else [before[-1]]
        body = "\n\n".join(f"[{display(r)}]\n{replies[r]}" for r in prev)
        return [{"role": "system", "content": system_prompt(role, channel, chain)},
                {"role": "user", "content": f"{qs}\n\n{body}"}]
    msgs = [{"role": "system", "content": system_prompt(role, channel, chain)},
            {"role": "user", "content": qs}]
    if channel == "D":
        msgs.append({"role": "user", "content": "\n\n".join(f"[{display(r)} handoff]\n{replies[r]}" for r in before)})
    return msgs


def rtask_block(rtask: Task) -> str:
    """Questions of a parallel Researcher, keeping their numbers in the whole task."""
    return ("Your questions (other Researchers cover the rest):\n" +
            "\n".join(f"Q{n}: {q.question}" for n, q in zip(rtask.numbers, rtask.questions)))


def split_task(task: Task, n: int) -> list[Task]:
    """Split a task's questions into n contiguous groups, each with the documents of its questions."""
    size = -(-len(task.questions) // n)
    by_title = {d.title: d for d in task.docs}
    parts = []
    for g in range(n):
        idx = list(range(g * size, min(len(task.questions), (g + 1) * size)))
        if not idx:
            continue
        qs = [task.questions[i] for i in idx]
        titles = {t for q in qs for t, _ in q.paragraphs}
        sub = Task(f"{task.task_id}.r{g + 1}", task.dataset, qs, [d for d in task.docs if d.title in titles])
        sub.numbers = [i + 1 for i in idx]
        parts.append(sub)
    return parts


async def run_task(task: Task, channel: str, client, workdir: Path, max_turns: int = 12,
                   chain: tuple[str, ...] = ("researcher", "writer", "reviewer"), researchers: int = 1) -> dict:
    assert channel in CHANNELS and chain[0] == "researcher" and chain[-1] == "reviewer"
    t0 = time.perf_counter()
    client = SaltedClient(client, f"{task.task_id}.{channel}.{len(chain)}.{researchers}.{time.time_ns()}"
                          if researchers > 1 else f"{task.task_id}.{channel}.{len(chain)}.{time.time_ns()}")
    files = channel in FILE_CHANNELS
    tag = f"{len(chain)}" if researchers == 1 else f"{len(chain)}r{researchers}"
    ws = Workspace(Path(workdir) / f"{task.task_id}_{channel}_{tag}") if files else None
    if ws is not None:
        seed_workspace(ws, task, channel)
    tools = TOOLS_BATCH if channel == "Bb" else TOOLS
    turns = max_turns if files else 1

    if researchers > 1:
        parts = split_task(task, researchers)
        rroles = [f"researcher{i + 1}" for i in range(len(parts))]
        shown = ("researchers",) + tuple(chain[1:])
    else:
        parts, rroles, shown = [None], ["researcher"], chain
    flat = rroles + list(chain[1:])

    runs: dict[str, AgentRun] = {}
    replies: dict[str, str] = {}
    stage: dict[str, str] = {}
    # Parallel Researchers run concurrently, as in an orchestrator-worker fan-out.
    res = await asyncio.gather(*(run_agent(client, ws, r, build_messages(r, channel, shown, task, replies, flat, sub),
                                           turns, None, tools) for r, sub in zip(rroles, parts)))
    for r, run in zip(rroles, res):
        runs[r], replies[r] = run, run.reply
    if files:
        stage["notes"] = "\n".join(ws.written_by(r) for r in rroles)
        if channel == "D":
            stage["notes"] += "\n" + "\n".join(replies[r] for r in rroles)
    else:
        stage["notes"] = "\n".join(replies[r] for r in rroles)

    for role in chain[1:]:
        msgs = build_messages(role, channel, shown, task, replies, flat)
        runs[role] = await run_agent(client, ws, role, msgs, turns, OUT_FILE.get(role), tools)
        replies[role] = runs[role].reply
        out = replies[role]
        if files:
            f = ws.root / OUT_FILE[role]
            out = f.read_text() if f.is_file() else ""
        stage[{"writer": "draft", "reviewer": "final"}.get(role, role)] = out
        if role == "writer":
            # What actually reached the Writer from the Researchers.
            pushed = "\n".join(replies[r] for r in rroles)
            if channel in MESSAGE_CHANNELS:
                stage["writer_input"] = pushed
            else:
                stage["writer_input"] = "\n".join([pushed if channel == "D" else ""] + ws.reads_by.get("writer", []))
    if files and not stage.get("final"):
        stage["final"] = replies.get("reviewer", "")
        stage["final_from_reply"] = "1"

    return {
        "task_id": task.task_id, "channel": channel, "dataset": task.dataset, "k": len(task.questions),
        "chain": list(chain), "researchers": researchers, "wall_s": round(time.perf_counter() - t0, 2),
        "agents": {r: {"calls": a.calls, "hit_turn_limit": a.hit_turn_limit, "overflow": a.overflow,
                       "reply": a.reply} for r, a in runs.items()},
        "io": {r: s.as_dict() for r, s in ws.stats.items()} if ws else {},
        "io_ops": ws.ops if ws else [],
        "stage": stage,
    }
