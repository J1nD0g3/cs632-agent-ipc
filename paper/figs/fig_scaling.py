"""Fig. 4: how the channels' costs and accuracy move as the payload grows (k questions per task).

Claim at a glance: the cache savings belong to small payloads. Once the agents' prompts no longer fit
the KV cache together, zero-copy broadcast computes as much as broadcast and the file channels compute
more than it (a); the file channels lose accuracy at every k, and B drops sharply only at k=16, where the
payload grows and the work fans out to three parallel Researchers at once, so the figure cannot separate the two (b).
Form: two line panels over k on a categorical axis (1, 3, 5, 8 with one Researcher; 16 with three
parallel Researchers, set apart by a dashed separator, with no line across it); broadcast is the dashed
reference at 1 / 0. Whiskers in (b) are paired 95% intervals against A1, with series dodged slightly.
Data: figs/data/fig4_scaling.json (agentipc.figdata from the main, k=8 and k=16 runs).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

DATA = json.loads((Path(__file__).parent / "data" / "fig4_scaling.json").read_text())["rows"]
KS = sorted({r["k"] for r in DATA})
CATS = [str(k) if k != 16 else "16 (fan-out)" for k in KS]
STYLE = {"A1zc": ("#F2B53A", "*", "A1-zc zero-copy"), "A2": ("gray4", "o", "A2 pipe"),
         "B": ("teal2", "s", "B files"), "C": ("teal5", "s", "C files+index")}


def series(ch, key):
    by = {r["k"]: r for r in DATA if r["channel"] == ch}
    return [by[k][key] if k in by else None for k in KS]


fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 112)
left, right = body.cols(2, gap=18)
xs = list(range(len(KS)))
seps = [CATS[-1]] if 16 in KS else ()

pa, ca = left.take("bottom", 10, gap=2)
ax = fig.axes(pa, cats=CATS, y=(0, 2.2), yticks=[0, 0.5, 1, 1.5, 2], yfmt=lambda v: f"{v:g}×",
              ylabel="Tokens computed vs A1", xlabel="Questions per task (k)", seps=seps)
ax.hline(1, label="A1 = 1", label_at="left")
DODGE = {ch: (i - (len(STYLE) - 1) / 2) * 0.07 for i, ch in enumerate(STYLE)}


def broken(axes, ch, ys, dx=0.0, **kw):
    """One line over k <= 8 and a lone marker at the fan-out point, so no segment crosses the separator."""
    pts = [(x + dx, y) for x, y, k in zip(xs, ys, KS) if y is not None and k != 16]
    axes.line([p[0] for p in pts], [p[1] for p in pts], **kw)
    if 16 in KS and ys[KS.index(16)] is not None:
        axes.line([xs[KS.index(16)] + dx], [ys[KS.index(16)]], **{k: v for k, v in kw.items() if k != "label"})


for ch, (col, mk, name) in STYLE.items():
    broken(ax, ch, series(ch, "comp_rel"), color=col, marker=mk, label=name)
fig.caption(left.cx, ca.t + 1, "(a) Prefill: savings fade as payloads grow", size=7.3, weight=600)

pb, cb = right.take("bottom", 10, gap=2)
bx = fig.axes(pb, cats=CATS, y=(-0.4, 0.06), yticks=[-0.4, -0.3, -0.2, -0.1, 0], yfmt=lambda v: f"{v * 100:+.0f}" if v else "0",
              ylabel="Accuracy vs A1 (points)", xlabel="Questions per task (k)", seps=seps)
bx.hline(0, label="A1", label_at="left")
for ch, (col, mk, name) in STYLE.items():
    dx = DODGE[ch]
    for x, lo, hi in zip(xs, series(ch, "acc_diff_lo"), series(ch, "acc_diff_hi")):
        if lo is not None:
            (px, ya), (_, yb) = bx.px(x + dx, hi), bx.px(x + dx, lo)
            fig.line((px, ya), (px, yb), sw=0.5, color="gray5")
    broken(bx, ch, series(ch, "acc_diff"), dx, color=col, marker=mk, label=name)
fig.caption(right.cx - 1.5, cb.t + 1, "(b) Accuracy: B drops at k=16, as payload and Researchers change", size=7.3, weight=600)

fig.legend(ax.legend_items + [("line", "gray5", "Paired 95% CI")], fig.width / 2, strip.y)
fig.save(str(Path(__file__).parent / "out" / "fig_scaling"))
