"""OpenAI-compatible chat client for a vLLM server, plus a scripted mock for tests."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import httpx


class ContextOverflow(Exception):
    pass


@dataclass
class Reply:
    content: str
    tool_calls: list[dict]
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    latency_ms: float
    finish_reason: str


class ChatClient:
    def __init__(self, base_url: str, model: str, max_tokens: int = 1024, seed: int = 0,
                 temperature: float = 0.0, timeout: float = 600.0, enable_thinking: bool = False):
        self.url = base_url.rstrip("/") + "/v1/chat/completions"
        self.model, self.max_tokens, self.seed, self.temperature = model, max_tokens, seed, temperature
        self.enable_thinking = enable_thinking
        self.http = httpx.AsyncClient(timeout=timeout)

    async def chat(self, messages: list[dict], tools: list[dict] | None = None, tool_choice=None) -> Reply:
        body = {"model": self.model, "messages": messages, "max_tokens": self.max_tokens,
                "temperature": self.temperature, "seed": self.seed,
                "chat_template_kwargs": {"enable_thinking": self.enable_thinking}}
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice or "auto"
        t0 = time.perf_counter()
        for attempt in range(3):
            r = await self.http.post(self.url, json=body)
            if r.status_code == 400 and ("context length" in r.text or "maximum" in r.text):
                raise ContextOverflow(r.text[:300])
            if r.status_code >= 500 and attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            break
        d = r.json()
        ch = d["choices"][0]
        msg = ch["message"]
        u = d.get("usage") or {}
        cached = ((u.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0
        return Reply(msg.get("content") or "", msg.get("tool_calls") or [], u.get("prompt_tokens", 0),
                     u.get("completion_tokens", 0), cached, (time.perf_counter() - t0) * 1000,
                     ch.get("finish_reason") or "")

    async def aclose(self):
        await self.http.aclose()


class MockClient:
    """Returns scripted replies in order; each item is a str or a list of (name, args) tool calls."""

    def __init__(self, script):
        self.script = list(script)
        self.calls: list[dict] = []

    async def chat(self, messages, tools=None, tool_choice=None) -> Reply:
        self.calls.append({"messages": [dict(m) for m in messages], "tools": tools, "tool_choice": tool_choice})
        item = self.script.pop(0) if self.script else "done"
        n_prompt = sum(len(str(m.get("content") or "")) for m in messages) // 4
        if isinstance(item, str):
            return Reply(item, [], n_prompt, len(item) // 4, 0, 1.0, "stop")
        import json
        calls = [{"id": f"call_{len(self.calls)}_{i}", "type": "function",
                  "function": {"name": n, "arguments": json.dumps(a)}} for i, (n, a) in enumerate(item)]
        return Reply("", calls, n_prompt, 10, 0, 1.0, "tool_calls")

    async def aclose(self):
        pass
