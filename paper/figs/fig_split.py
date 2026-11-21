"""Fig. 3: how the Researcher writes its notes and how later agents get their inputs, per model size (one
interleaved run per size).

Claim at a glance: on tool-written notes, the file channel lowers accuracy at 4B, 14B, and 32B (b); tool-written
notes cover fewer facts than replies except at 14B (a); a reply the harness stores as notes.md does no better than
tool-written notes in the file channel (much worse at 14B, 32B).
Form: two panels with the same layout, one group of four bars per model size, in a fixed order: reply copied,
tool write copied, reply in the file channel (stored as notes.md), tool write in the file channel. Navy = copying
(broadcast: inputs in the prompt, answers by reply), teal = the file channel (B: inputs and outputs through tool
calls); dark = tool-call write, light = reply. (a) share of supporting facts in the Researcher's notes and
(b) accuracy, both with 95% intervals.
Data: figs/data/fig3_split.json (agentipc.figdata from results/p16_store_*).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

ROWS = json.loads((Path(__file__).parent / "data" / "fig3_split.json").read_text())["rows"]
SIZES = [r["size"] for r in ROWS]
ARMS = [("A1r", "Reply, copied", "navy2"), ("A1w", "Tool-written, copied", "navy4"),
        ("Bs", "Reply, file channel", "teal2"), ("B", "Tool-written, file channel", "teal4")]

fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 104)
left, right = body.cols([1, 1], gap=18)

ax = fig.axes(left.take("bottom", 10, gap=2)[0], cats=SIZES, y=(0, 0.6), yticks=[0, 0.2, 0.4, 0.6],
              yfmt=lambda v: f"{v * 100:.0f}%", ylabel="Facts in notes")
ax.bars({name: [r[f"notes_{ch}"] for r in ROWS] for ch, name, _ in ARMS}, [c for _, _, c in ARMS])
for ch, name, _ in ARMS:
    off, bw = ax._bar_geom[name]
    for i, r in enumerate(ROWS):
        x = ax.X(i) + off + bw / 2
        ya, yb = ax.Y(r[f"notes_{ch}_hi"]), ax.Y(r[f"notes_{ch}_lo"])
        fig.line((x, ya), (x, yb), sw=0.5)
        fig.line((x - bw * 0.25, ya), (x + bw * 0.25, ya), sw=0.5)
        fig.line((x - bw * 0.25, yb), (x + bw * 0.25, yb), sw=0.5)
fig.caption(left.cx, left.b - 9, "(a) Facts in the Researcher's notes (95% intervals)", size=7.5, weight=600)

bx = fig.axes(right.take("bottom", 10, gap=2)[0], cats=SIZES, y=(0.2, 0.85), yticks=[0.2, 0.4, 0.6, 0.8],
              yfmt=lambda v: f"{v * 100:.0f}%", ylabel="Accuracy", grid=True)
bx.bars({name: [r[f"acc_{ch}"] for r in ROWS] for ch, name, _ in ARMS}, [c for _, _, c in ARMS], legend=False)
for ch, name, _ in ARMS:
    off, bw = bx._bar_geom[name]
    for i, r in enumerate(ROWS):
        x = bx.X(i) + off + bw / 2
        ya, yb = bx.Y(r[f"acc_{ch}_hi"]), bx.Y(r[f"acc_{ch}_lo"])
        fig.line((x, ya), (x, yb), sw=0.5)
        fig.line((x - bw * 0.25, ya), (x + bw * 0.25, ya), sw=0.5)
        fig.line((x - bw * 0.25, yb), (x + bw * 0.25, yb), sw=0.5)
fig.caption(right.cx, right.b - 9, "(b) Accuracy (95% intervals)", size=7.5, weight=600)

fig.legend(ax.legend_items, fig.area.cx, strip.y, ncols=4)
# Hue encodes delivery (navy copied, teal files) and tone encodes writing (dark tool call, light reply); bars keep
# a fixed order in every group, so the grayscale-near pairs are still told apart by position and legend order.
fig.ignore.add("grayscale")
fig.save(str(Path(__file__).parent / "out" / "fig_split"))
