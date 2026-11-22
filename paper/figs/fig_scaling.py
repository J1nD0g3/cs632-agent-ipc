"""Fig. 4: what breaks as tasks grow (section 5.1 and 5.2).

Claim at a glance: zero-copy's prefill saving needs the shared history to fit in the KV cache: 0.39x of
broadcast's prefill at k=3, 0.83x at k=8, 1.00x at k=16, and back to 0.36x on the same k=8 tasks with a 100k-token
cache (a); three Researchers sharing one folder lose about 20 points, which separate folders win back, and at
k=16 a write guard or the heading rule recovers about half of the loss (b).
Form: (a) prefill relative to A1 over k on a categorical axis, zero-copy the one bold gold line with its values
printed, the other channels pale; the k=8 cache-size control (one RTX PRO 6000, cross-run) as hollow gold stars
just right of k=8 with a green arrow from the 35k to the 100k cache. (b) accuracy minus A1 per task within each
run (paired 95% intervals) for one or three Researchers at k=8 and three at k=16; red = the shared folder, teal =
the file-channel fixes; a red arrow carries the k=8 loss (difference in differences against one Researcher) and
green arrows the gains over the shared folder.
Data: figs/data/fig4_scaling.json (agentipc.figdata.fig4) and figs/data/fig4_limits.json
(agentipc.figdata.fig4_limits, from results/p01_cache_*, p15_k8_*, p12_k16_clobber via paper_numbers).
"""
import json
from pathlib import Path

from archfig import Figure, Rect
from archfig.chart import marker_extent, marker_svg
from archfig.figure import Item
from archfig.palette import color as C

HERE = Path(__file__).parent
DATA = json.loads((HERE / "data" / "fig4_scaling.json").read_text())["rows"]
LIM = json.loads((HERE / "data" / "fig4_limits.json").read_text())
KS = sorted({r["k"] for r in DATA})
CATS = [str(k) if k != 16 else "16 (3 Res.)" for k in KS]
GOLD = "#F2B53A"
STYLE = {  # color, marker, legend name, line width, marker size
    "A2": ("gray3", "o", "A2 pipe", 0.8, 3.0),
    "B": ("teal2", "s", "B files", 0.8, 3.0),
    "C": ("teal3", "s", "C files+index", 0.8, 3.0),
    "A1zc": (GOLD, "*", "A1-zc zero-copy", 1.6, 5.0),
}
num = lambda v: f"{v:+.1f}".replace("-", "−")


def series(ch, key):
    by = {r["k"]: r for r in DATA if r["channel"] == ch}
    return [by[k][key] if k in by else None for k in KS]


def hollow(x, y, shape, d, color, sw=0.9):
    fig._emit(marker_svg(shape, x, y, d, "#ffffff", stroke=C(color), sw=sw))
    e = marker_extent(shape, x, y, d)
    fig.items.append(Item("mark", e, fill="white", sw=sw, label="marker"))
    return e


fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 111.5)
left, right = body.cols(2, gap=18)

pa, ca = left.take("bottom", 10, gap=2)
# k on a categorical scale, with one extra slot right of k=8 for the cache-size control.
POS = {1: 0, 3: 1, 5: 2, 8: 3, 16: 5.12}
SEP = 4.62
TICK = {POS[k]: c for k, c in zip(KS, CATS)}
ax = fig.axes(pa, x=(-0.45, 5.6), xticks=list(TICK), xfmt=TICK.get, y=(0, 2.2), yticks=[0, 0.5, 1, 1.5, 2],
              yfmt=lambda v: f"{v:g}×", ylabel="Tokens computed vs A1", xlabel="Questions per task (k)", grid=True)
fig.line((ax.X(SEP), ax.plot.t), (ax.X(SEP), ax.plot.b), color="#7F7F7F", sw=0.5, dash="dash", decor=True)
ax.hline(1)
fig.text(ax.X(1.75), ax.Y(1) - 2, "A1 = 1", size=6.5, valign="bottom")
for ch, (col, mk, name, sw, ms) in STYLE.items():
    ys = series(ch, "comp_rel")
    pts = [(POS[k], y) for y, k in zip(ys, KS) if k != 16]
    ax.line([p[0] for p in pts], [p[1] for p in pts], color=col, marker=mk, label=name, sw=sw, ms=ms)
    ax.line([POS[16]], [ys[-1]], color=col, marker=mk, sw=sw, ms=ms)  # k=16 stands alone past the separator
zc = dict(zip(KS, series("A1zc", "comp_rel")))
for k, dx, dy, anchor, valign in ((3, 0, -4.5, "middle", "bottom"), (8, -4, 4, "start", "top"),
                                  (16, 0, -4.5, "middle", "bottom")):
    px, py = ax.px(POS[k], zc[k])
    fig.text(px + dx, py + dy, f"{zc[k]:.2f}×", size=6.5, weight=700, color="gold5", anchor=anchor, valign=valign)
# Cache-size control at k=8: the same tasks on one RTX PRO 6000 with a 35k or a 100k-token cache.
cc = {r["series"]: r for r in LIM["cache_ctrl"]}
cx = POS[8] + 0.5
(sx, s35), (_, s100) = ax.px(cx, cc["35k"]["y"]), ax.px(cx, cc["100k"]["y"])
hollow(sx, s35, "*", 5.0, "gold5")
hollow(sx, s100, "*", 5.0, "gold5")
fig.arrow((sx, s35 + 4.0), (sx, s100 - 4.2), color="good", sw=1.1)
fig.text(sx + 4, s35, "35k cache", size=6, color="gold5", anchor="start")
fig.text(sx + 4, s100, "100k cache", size=6, color="good", weight=700, anchor="start")
fig.text(sx, s100 + 4, f"{cc['100k']['y']:.2f}×", size=6.5, color="good", weight=700, valign="top")
fig.caption(left.cx, ca.t + 1, "(a) Prefill vs A1: zero-copy's saving needs cache room", size=7.5, weight=600)

pb, cb = right.take("bottom", 10, gap=2)
W = {(r["group"], r["series"]): r for r in LIM["writers"]}
ORDER = [("k8", "one", "1 Res.", "gray2"), ("k8", "shared", "3 Res.", "red3"), ("k8", "folders", "own folders", "teal3"),
         ("k16", "shared", "3 Res.", "red3"), ("k16", "guard", "+ guard", "teal3"), ("k16", "heading", "+ heading", "teal3")]
bx = fig.axes(pb, groups=[("k = 8", [o[2] for o in ORDER[:3]]), ("k = 16", [o[2] for o in ORDER[3:]])],
              y=(-40, 6), yticks=[-40, -30, -20, -10, 0], yfmt=lambda v: f"{v:.0f}".replace("-", "−"),
              ylabel="Accuracy vs A1 (points)", seps=[3], group_seps=None)
bx.hline(0)
BW = 0.5
for i, (g, s, _, col) in enumerate(ORDER):
    vals = [None] * len(ORDER)
    vals[i] = W[(g, s)]["y"]
    bx.bars({f"{g}-{s}": vals}, [col], width=BW, legend=False)
    r = W[(g, s)]
    (px, ya), (_, yb) = bx.px(i, r["hi"]), bx.px(i, r["lo"])
    fig.line((px, ya), (px, yb), sw=0.6, color="ink")
fig.text(bx.plot.l + 2.5, bx.Y(0) - 1.8, "A1", size=6.5, anchor="start", valign="bottom")
half = bx._slot() * BW / 2


def step(i_from, i_to, v_from, v_to, label, color):
    """Dashed guide level with bar i_from's end, and an arrow from that level to bar i_to's end: beside bar i_to
    on its left when the bars overlap in height (a drop), else under bar i_to, right of its whisker (a gain)."""
    drop = v_to < v_from
    x = bx.X(i_to) - half - 3.0 if drop else bx.X(i_to) + 4.0
    y0, y1 = bx.Y(v_from), bx.Y(v_to)
    xf = bx.X(i_from) + half
    fig.line((xf, y0), (x + 1.5, y0), color=color, sw=0.7, dash="dash", decor=True)
    fig.arrow((x, y0), (x, y1 + (0.5 if drop else -0.5) * 0), color=color, sw=1.1)
    fig.text(x - 2.2, (y0 + y1) / 2, label, size=6.5, weight=700, color=color, anchor="end")


g = LIM["gains"]
step(0, 1, W[("k8", "one")]["y"], W[("k8", "shared")]["y"], num(g["fan_did_b"][0]), "bad")
step(1, 2, W[("k8", "shared")]["y"], W[("k8", "folders")]["y"], num(g["folders_over_b"][0]), "good")
step(3, 4, W[("k16", "shared")]["y"], W[("k16", "guard")]["y"], num(g["guard_over_b"][0]), "good")
step(3, 5, W[("k16", "shared")]["y"], W[("k16", "heading")]["y"], num(g["heading_over_b"][0]), "good")
fig.text(bx.X(1), bx.Y(W[("k8", "shared")]["lo"]) + 1.5, f"same path: {g['clash_b']:.0f}%", size=6, color="gray5",
         valign="top")
fig.text(bx.X(3), bx.Y(W[("k16", "shared")]["lo"]) + 1.5, num(W[("k16", "shared")]["y"]), size=6.5, weight=700,
         color="bad", valign="top")
fig.caption(right.cx, cb.t + 1, "(b) Parallel Researchers: one shared folder loses", size=7.5, weight=600)

fig.legend(ax.legend_items[-1:] + ax.legend_items[:-1], left.cx, strip.y)
fig.save(str(HERE / "out" / "fig_scaling"))
