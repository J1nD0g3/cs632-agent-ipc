"""Fig. 3: why files lose (section 4.3 a and c).

Claim at a glance: reading tool-written notes as files instead of copying them costs 8-22 points at 4B, 14B, and
32B but not significantly at 8B (a); later agents rarely open a stored notes.md unless told its path, and telling
the path helped only at 32B (b).
Form: (a) paired accuracy effects with 95% intervals per model size, three dodged series. The claim's series (files
instead of copying, tool-written notes) is the large dark teal circle with its value printed; filled markers are
Holm-significant in Table 1's 16-test family (the same RTenMark flags that bold Table 1's cells), hollow ones are
not. (b) the told runs, one per size: share of tasks whose Writer opened the notes (x) against accuracy (y);
model size is both shape and color (gray circle 14B, teal square 32B), every point is labeled with its arm, and the
told points carry the paired change from telling the path (arrow for 32B). Hollow is used only in (a). Exploratory.
Data: figs/data/fig3_cause.json (agentipc.figdata.fig3_cause, from results/p16_store_* and results/p17_told_* via
paper_numbers.round10, round10_text, and round12_told).
"""
import json
from pathlib import Path

from archfig import Figure, Rect
from archfig.chart import marker_extent, marker_svg
from archfig.figure import Item
from archfig.palette import color as C

DATA = json.loads((Path(__file__).parent / "data" / "fig3_cause.json").read_text())
SIZES = ["4B", "8B", "14B", "32B"]
EFF = {(r["size"], r["series"]): r for r in DATA["effects"]}
TOLD = {(r["size"], r["series"]): r for r in DATA["told"]}
ARROW = {r["size"]: r for r in DATA["told_arrows"]}
SERIES = [  # key, marker, diameter, color, legend label
    ("FileTool", "o", 5.0, "teal5", "**Files instead of copying, tool-written notes**"),
    ("FileReply", "s", 3.8, "teal2", "Files instead of copying, stored reply"),
    ("WriteCopy", "d", 3.6, "gray3", "Tool write instead of reply, copied"),
]
DARKER = {"teal2": "teal3", "gray3": "gray4"}  # a pale outline alone would vanish in print
DODGE = {"FileTool": -0.22, "FileReply": 0.0, "WriteCopy": 0.22}
num = lambda v: f"{v:+.1f}".replace("-", "−") if v else "0.0"


def hollow(x, y, shape, d, color, sw=1.0):
    """A white marker outlined in its series color: the effect is not Holm-significant."""
    fig._emit(marker_svg(shape, x, y, d, "#ffffff", stroke=C(color), sw=sw))
    e = marker_extent(shape, x, y, d)
    fig.items.append(Item("mark", e, fill="white", sw=sw, label="marker"))
    return e


fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 102)
left, right = body.cols([1.15, 1], gap=18)

pa, ca = left.take("bottom", 10, gap=2)
ticks = [s if s != "4B" else "4B\n{gray5|all rescued}" for s in SIZES]
ax = fig.axes(pa, cats=ticks, x=(-0.78, 3.5), y=(-40, 5), yticks=[-40, -30, -20, -10, 0], yfmt=lambda v: f"{v:.0f}".replace("-", "−"),
              ylabel="Change (points)", grid=True)
ax.hline(0)
fig.text(ax.plot.l + 2.5, ax.Y(0) + 2, "no change", size=6.5, anchor="start", valign="top")
for key, mk, d, col, _ in SERIES:
    for i, size in enumerate(SIZES):
        r = EFF[(size, key)]
        x = i + DODGE[key]
        (px, ylo), (_, yhi) = ax.px(x, r["lo"]), ax.px(x, r["hi"])
        fig.line((px, ylo), (px, yhi), sw=0.6, color="gray5")
        if r["holm"]:
            e = ax.point(x, r["y"], marker=mk, d=d, fill=col)
        else:
            px_, py_ = ax.px(x, r["y"])
            e = hollow(px_, py_, mk, d, DARKER.get(col, col), sw=1.0)
        if key == "FileTool":
            fig.text(e.l - 2.2, e.cy, num(r["y"]), size=6.5, weight=700, color="teal5", anchor="end")
fig.caption(left.cx, ca.t + 1, "(a) Accuracy change, per model size (paired, 95% CI)", size=7.5, weight=600)

pb, cb = right.take("bottom", 10, gap=2)
bx = fig.axes(pb, x=(0, 100), xticks=[0, 25, 50, 75, 100], xfmt=lambda v: f"{v:.0f}%", y=(38, 76),
              yticks=[40, 50, 60, 70], yfmt=lambda v: f"{v:.0f}%", ylabel="Accuracy",
              xlabel="Writer opened the notes (% of tasks)", grid=True)
SIZE = {"14B": ("o", "gray4", "gray5"), "32B": ("s", "teal4", "teal5")}  # marker, fill, label color
ARM = {"Tool": "tool-written", "Untold": "untold", "Told": "told"}
pos = {}
for size, (mk, fill, _) in SIZE.items():
    for arm in ARM:
        r = TOLD[(size, arm)]
        pos[(size, arm)] = bx.px(r["x"], r["y"])
        bx.point(r["x"], r["y"], marker=mk, d=4.6, fill=fill)
(x0, y0), (x1, y1) = pos[("32B", "Untold")], pos[("32B", "Told")]
fig.arrow((x0 + 3.5, y0 - 1.2), (x1 - 3.6, y1 + 1.3), color="good", sw=1.2)
a32, a14 = ARROW["32B"], ARROW["14B"]
# Each point carries its own label; the paired change from telling the path sits on the told point.
LAB = {("32B", "Told"): (3, -3.5, "end", "bottom", f"**32B told: {num(a32['y'])} pts** ({num(a32['lo'])} to {num(a32['hi'])})", "good"),
       ("14B", "Told"): (-2.5, -3.5, "start", "bottom", f"14B told: {num(a14['y'])} pts ({num(a14['lo'])} to {num(a14['hi'])})", None),
       ("14B", "Untold"): (4.5, 0.5, "start", "middle", "14B untold", None),
       ("32B", "Untold"): (-3.5, 0, "end", "middle", "32B untold", None),
       ("32B", "Tool"): (-3.5, 1.8, "end", "middle", "32B tool-written", None),
       ("14B", "Tool"): (0, 7, "end", "top", "14B tool-written", None)}
for (size, arm), (dx, dy, anchor, valign, text, col) in LAB.items():
    px, py = pos[(size, arm)]
    fig.text(px + dx, py + dy, text, size=6.5, anchor=anchor, valign=valign, color=col or SIZE[size][2])
fig.caption(right.cx, cb.t + 1, "(b) Finding the stored notes (told runs, exploratory)", size=7.5, weight=600)

fig.legend([("marker", f"{mk}:{col}", lab) for _, mk, _, col, lab in SERIES] +
           [("marker", "o:white", "hollow: not Holm-significant")], fig.area.cx, strip.y)
fig.save(str(Path(__file__).parent / "out" / "fig_split"))
