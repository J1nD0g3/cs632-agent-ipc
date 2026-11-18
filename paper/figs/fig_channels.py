"""Fig. 1: what the Writer's prompt holds, call by call, under each channel (one pilot task, to scale).

Claim at a glance: message passing sends one big prompt that is all computed; file channels resend a
growing conversation on every tool call, so they send more tokens, yet almost all of it is reused from
the prefix cache and little is computed.
Plan: one lane per channel on a shared token axis; each LLM call of the Writer is a bar whose segments
are colored by content. Newly computed tokens are drawn in full tone, tokens reused from the prefix
cache pale and hatched, so the eye sees "dark = work". The right panel repeats the totals as a pair of
bars per channel on one scale: sent (what an API bills) and computed (prompt minus cached).
Data: figs/data/fig1_writer_calls.json (agentipc.fig1_data on the pilot run).
"""
import json
from pathlib import Path

from archfig import Figure, Rect
from archfig.timeline import Timeline

DATA = json.loads((Path(__file__).parent / "data" / "fig1_writer_calls.json").read_text())
ORDER = [("A1", "A1 broadcast", "copy the history"), ("A2", "A2 pipe", "previous output"),
         ("B", "B files", "read via tools"), ("C", "C files + index", "workspace index"),
         ("D", "D handles", "pushed pointers")]
FILL = {"task": "gray3", "own": "gray1", "docs": "teal4", "notes": "navy4", "list": "gold3"}
PALE = {"task": "gray1", "own": "white", "docs": "teal1", "notes": "navy1", "list": "gold1"}
SENT, COMP = "white", "red4"
VMAX = 9000
T1 = 5600


def label_of(call, reads):
    tools = call["label"].split(",")
    t = tools[0]
    if t == "list_files":
        return "list files"
    if t == "read_file":
        path = reads.pop(0) if reads else ""
        name = Path(path).name
        if "notes" in name:
            return "read notes" if not path.startswith("docs/") else "read (no such file)"
        return "read " + name.split("_")[0]
    if t == "write_file":
        return "write draft" + (" (forced)" if call["forced"] else "")
    return "reply"


def merged(segs):
    out = []
    for k, n in segs:
        if out and out[-1][0] == k:
            out[-1][1] += n
        else:
            out.append([k, n])
    return out


fig = Figure("text")
legend_strip, body = fig.area.take("top", 12, gap=4)
plot, values = body.take("right", 92, gap=8)
n_rows = [len(DATA["channels"][c]["calls"]) for c, _, _ in ORDER]
row_h = 7.4
lane_h = [max(n, 2) * row_h for n in n_rows]
gaps = 3.5
tl_h = sum(lane_h) + gaps * (len(lane_h) - 1)
tl_rect = plot.sized(plot.w, tl_h, anchor="n")
tl = fig.timeline(tl_rect, t=(0, T1), lanes=[f"**{n}**\n{{small|{d}}}" for _, n, d in ORDER],
                  label_w=66, lane_h=lane_h, gap=gaps, track=None, label_size=7)

names = [c for c, _, _ in ORDER]
for (ch, _, _), n in zip(ORDER, n_rows):
    info = DATA["channels"][ch]
    reads = list(info["reads"])
    lane = tl.lane(names.index(ch))
    top = lane.cy - n * row_h / 2  # center the calls in the lane
    for i, call in enumerate(info["calls"]):
        y, x = top + i * row_h, 0
        for kind, tok in merged(call["segments"]):
            # Split at the cached prefix: reused tokens hatched, newly computed ones plain.
            for a, b, cached in ((x, min(x + tok, call["cached"]), True), (max(x, call["cached"]), x + tok, False)):
                if b > a:
                    fig.box(Rect(tl.x(a), y, tl.x(b) - tl.x(a), row_h), fill=PALE[kind] if cached else FILL[kind],
                            hatch="gray3" if cached else None, sw=0.5, r=0)
            x += tok
        fig.text(tl.x(call["prompt"]) + 2.5, y + row_h / 2, label_of(call, reads), size=6, anchor="start",
                 color="gray5")

axis_y = tl.axis(ticks=[0, 1000, 2000, 3000, 4000, 5000], fmt=lambda v: f"{v / 1000:g}k",
                 title="Writer prompt per LLM call (tokens)")

# Totals per channel as bars on one scale: tokens sent over all calls vs tokens actually computed.
bar_x0 = values.l
scale = lambda v: (values.w - 22) * v / VMAX
fig.text(values.l, tl.bottom + 14, "Writer total over all calls", size=7.5, anchor="start")
for idx, (ch, _, _) in enumerate(ORDER):
    calls = DATA["channels"][ch]["calls"]
    sent = sum(c["prompt"] for c in calls)
    comp = sum(c["prompt"] - c["cached"] for c in calls)
    lane = tl.lane(idx)
    h = 5.2
    for k, (v, fill) in enumerate(((sent, SENT), (comp, COMP))):
        r = Rect(bar_x0, lane.cy - h - 0.6 if k == 0 else lane.cy + 0.6, scale(v), h)
        fig.box(r, fill=fill, sw=0.5, r=0)
        fig.text(r.r + 2, r.cy, f"{v / 1000:.1f}k", size=6, anchor="start",
                 weight=700 if k else 400, color="ink" if k else "gray5")
fig.line((bar_x0, tl_rect.t - 2), (bar_x0, tl_rect.b + 2), sw=0.5)

fig.legend([("box", FILL["task"], "Task"), ("box", FILL["docs"], "Documents"),
            ("box", FILL["notes"], "Researcher notes"), ("box", FILL["list"], "File list"),
            ("box", FILL["own"], "Own turns"), ("hatch", "gray3/white", "Reused from cache (pale)"),
            ("box", SENT, "Sent"), ("box", COMP, "Computed")],
           fig.width / 2, legend_strip.y, ncols=8)
# Segment widths are token counts, so neighbouring bars differ by fractions of a point on purpose.
fig.ignore.add("align")
# The figure is read in color (gold file list vs teal documents); the cache hatch carries the main contrast.
fig.ignore.add("grayscale")
# Five channels need five lanes; the file channels need one row per call to show the round trips.
fig.ignore.add("aspect")
fig.save(str(Path(__file__).parent / "out" / "fig_channels"))
