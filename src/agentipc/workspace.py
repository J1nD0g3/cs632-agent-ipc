"""Shared file workspace with per-agent I/O accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


class WorkspaceError(Exception):
    pass


@dataclass
class IOStats:
    lists: int = 0
    reads: int = 0
    writes: int = 0
    read_chars: int = 0
    write_chars: int = 0
    errors: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class Workspace:
    root: Path
    stats: dict[str, IOStats] = field(default_factory=dict)
    ops: list[dict] = field(default_factory=list)
    reads_by: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self):
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, path: str) -> Path:
        p = PurePosixPath(str(path).strip().lstrip("./") or ".")
        if p.is_absolute() or ".." in p.parts or str(p) == ".":
            raise WorkspaceError(f"invalid path: {path!r}")
        return self.root / p

    def _st(self, agent: str) -> IOStats:
        return self.stats.setdefault(agent, IOStats())

    def seed(self, path: str, content: str) -> None:
        """Place a file without counting it as agent I/O (source documents)."""
        f = self._path(path)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)

    def files(self) -> list[str]:
        return sorted(str(f.relative_to(self.root)) for f in self.root.rglob("*") if f.is_file())

    def list_files(self, agent: str) -> str:
        st = self._st(agent)
        st.lists += 1
        lines = []
        for rel in self.files():
            text = (self.root / rel).read_text()
            lines.append(f"{rel} ({text.count(chr(10)) + (0 if text.endswith(chr(10)) or not text else 1)} lines, {len(text)} chars)")
        out = "\n".join(lines) or "(empty)"
        self.ops.append({"agent": agent, "op": "list", "n": len(lines)})
        return out

    def read_file(self, agent: str, path: str, start_line: int | None = None, end_line: int | None = None) -> str:
        st = self._st(agent)
        try:
            f = self._path(path)
            if not f.is_file():
                raise WorkspaceError(f"no such file: {path}")
        except WorkspaceError as e:
            st.errors += 1
            self.ops.append({"agent": agent, "op": "read", "path": str(path), "error": str(e)})
            return f"ERROR: {e}"
        lines = f.read_text().splitlines()
        lo = max(1, int(start_line or 1))
        hi = min(len(lines), int(end_line or len(lines)))
        chunk = "\n".join(lines[lo - 1:hi])
        st.reads += 1
        st.read_chars += len(chunk)
        self.reads_by.setdefault(agent, []).append(chunk)
        self.ops.append({"agent": agent, "op": "read", "path": str(path), "lines": [lo, hi], "chars": len(chunk)})
        return chunk

    def write_file(self, agent: str, path: str, content: str, append: bool = False) -> str:
        st = self._st(agent)
        try:
            f = self._path(path)
        except WorkspaceError as e:
            st.errors += 1
            self.ops.append({"agent": agent, "op": "write", "path": str(path), "error": str(e)})
            return f"ERROR: {e}"
        f.parent.mkdir(parents=True, exist_ok=True)
        content = str(content)
        if append and f.exists():
            prev = f.read_text()
            f.write_text(prev + ("" if prev.endswith("\n") or not prev else "\n") + content)
        else:
            f.write_text(content)
        st.writes += 1
        st.write_chars += len(content)
        self.ops.append({"agent": agent, "op": "write", "path": str(path), "append": bool(append), "chars": len(content)})
        return f"OK: wrote {len(content)} chars to {path}"

    def written_by(self, agent: str) -> str:
        """Current text of every file this agent wrote."""
        paths = []
        for op in self.ops:
            if op["agent"] == agent and op["op"] == "write" and "error" not in op and op["path"] not in paths:
                paths.append(op["path"])
        out = []
        for p in paths:
            f = self._path(p)
            if f.is_file():
                out.append(f.read_text())
        return "\n".join(out)

    def total(self) -> IOStats:
        t = IOStats()
        for st in self.stats.values():
            for k, v in st.__dict__.items():
                setattr(t, k, getattr(t, k) + v)
        return t
