"""Fig. 3: where the file channel's loss comes from, per model size (one interleaved run per size).

Claim at a glance: writing notes through a tool call drops facts and accuracy (4B, 8B, 32B; not 14B), while
the wording of the instruction changes nothing; reading from files costs more on top at 4B, 14B and 32B.
Form: (a) grouped bars per model size: share of supporting facts in the Researcher's output for broadcast,
the reply with B's wording, the tool-call write, and files; the tool-written arms share the files' teal;
(b) grouped bars per size of the three paired accuracy effects (wording, tool write, reading files) with
95% intervals drawn exactly; the tool-write effect is the dark bar.
Data: figs/data/fig3_split.json (agentipc.figdata from results/p10_write_*).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

ROWS = json.loads((Path(__file__).parent / "data" / "fig3_split.json").read_text())["rows"]
SIZES = [r["size"] for r in ROWS]

fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 104)
left, right = body.cols([1, 1.1], gap=18)

ax = fig.axes(left.take("bottom", 10, gap=2)[0], cats=SIZES, y=(0, 0.6), yticks=[0, 0.2, 0.4, 0.6],
              yfmt=lambda v: f"{v * 100:.0f}%", ylabel="Facts in notes")
ax.bars({"Broadcast": [r["notes_A1"] for r in ROWS],
         "Reply, files' wording": [r["notes_A1r"] for r in ROWS],
         "Tool-call write": [r["notes_A1w"] for r in ROWS],
         "Files (B)": [r["notes_B"] for r in ROWS]},
        ["navy4", "navy2", "teal5", "teal2"])
fig.caption(left.cx, left.b - 9, "(a) The tool-call write drops facts", size=7.5, weight=600)

EFFECTS = [("wording", "Wording", "gray2"), ("tool_write", "Tool-call write", "teal4"),
           ("read_files", "Reading files", "gold3")]
bx = fig.axes(right.take("bottom", 10, gap=2)[0], cats=SIZES, y=(-0.3, 0.1), yticks=[-0.3, -0.2, -0.1, 0, 0.1],
              yfmt=lambda v: f"{v * 100:+.0f}" if v else "0", ylabel="Accuracy effect (points)", grid=True)
bx.bars({name: [r[key] for r in ROWS] for key, name, _ in EFFECTS}, [c for _, _, c in EFFECTS], base=0)
# Exact asymmetric 95% intervals at each bar's center (bars() records each series' offset and width).
for key, name, _ in EFFECTS:
    off, bw = bx._bar_geom[name]
    for i, r in enumerate(ROWS):
        x = bx.X(i) + off + bw / 2
        ya, yb = bx.Y(r[f"{key}_hi"]), bx.Y(r[f"{key}_lo"])
        fig.line((x, ya), (x, yb), sw=0.5)
        fig.line((x - bw * 0.25, ya), (x + bw * 0.25, ya), sw=0.5)
        fig.line((x - bw * 0.25, yb), (x + bw * 0.25, yb), sw=0.5)
fig.caption(right.cx, right.b - 9, "(b) Accuracy cost of each step vs the step before", size=7.5, weight=600)

fig.legend(ax.legend_items, left.cx, strip.y)
fig.legend(bx.legend_items, right.cx, strip.y)
# Hue encodes how the notes were written (navy: reply, teal: tool call); bars keep a fixed order within
# each group, so the grayscale pairs are still told apart by position and legend order.
fig.ignore.add("grayscale")
fig.save(str(Path(__file__).parent / "out" / "fig_split"))
