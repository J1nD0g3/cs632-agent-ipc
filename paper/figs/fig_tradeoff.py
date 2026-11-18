"""Fig. 2: accuracy against cost for every channel (k = 3, HotpotQA and 2Wiki pooled, 300 tasks each).

Claim at a glance: only zero-copy broadcast sits in the top-left corner of both panels. Billed by
tokens sent (a), broadcast costs a third of the file channels and keeps the best accuracy; counted by
tokens actually computed (b), zero-copy broadcast keeps broadcast's accuracy at the cost of a pipe.
Form: two scatter panels with a shared accuracy axis; message channels are circles (navy family, the
pipe gray), file channels squares (teal family), zero-copy broadcast the one gold star; vertical bars
are 95% bootstrap CIs; an arrow in (b) carries the zero-copy saving.
Data: figs/data/fig2_tradeoff.json (agentipc.figdata from the main run).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

DATA = json.loads((Path(__file__).parent / "data" / "fig2_tradeoff.json").read_text())
CH = {c["channel"]: c for c in DATA["channels"]}
STYLE = {  # marker, fill, name
    "A1": ("o", "navy4", "A1 broadcast"),
    "A1zc": ("*", "#F2B53A", "A1 zero-copy"),
    "A2": ("o", "gray3", "A2 pipe"),
    "B": ("s", "teal2", "B files"),
    "C": ("s", "teal4", "C files+index"),
    "D": ("s", "teal3", "D handles"),
}
# Label offsets (dx, dy, anchor) per panel, placed by hand so names never touch markers or each other.
LABEL = {
    "sent": {"A1": (5, -5, "start"), "A1zc": (5, 5, "start"), "A2": (5, 0, "start"),
             "B": (-5, 4, "end"), "C": (-5, -4, "end"), "D": (5, 0, "start")},
    "comp": {"A1": (-5, -6, "end"), "A1zc": (-6, 0, "end"), "A2": (5, 5, "start"),
             "B": (5, 4, "start"), "C": (5, -4, "start"), "D": (5, 0, "start")},
}

fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 118)
left, right = body.cols(2, gap=16)
panels = [(left, "total_tokens", "sent", (0, 42000), "(a) Tokens sent per task (API billing)"),
          (right, "prefill_tokens", "comp", (0, 14000), "(b) Tokens computed per task (self-hosted)")]
for rect, metric, key, xr, title in panels:
    chart, cap = rect.take("bottom", 10, gap=2)
    step = 10000 if xr[1] > 20000 else 2000
    ax = fig.axes(chart, x=xr, xticks=list(range(0, xr[1] + 1, step)), xfmt=lambda v: f"{v / 1000:g}k",
                  y=(0.56, 0.78), yticks=[0.6, 0.65, 0.7, 0.75], yfmt=lambda v: f"{v * 100:.0f}%",
                  ylabel="Accuracy" if key == "sent" else None, grid=True)
    for ch, (mk, fill, name) in STYLE.items():
        c = CH[ch]
        x, y = c[metric], c["acc"]
        (x0, ylo), (_, yhi) = ax.px(x, c["acc_lo"]), ax.px(x, c["acc_hi"])
        fig.line((x0, ylo), (x0, yhi), sw=0.6, color="gray5")
        ax.point(x, y, marker=mk, d=6.0 if mk == "*" else 4.2, fill=fill)
        dx, dy, anchor = LABEL[key][ch]
        px, py = ax.px(x, y)
        fig.text(px + dx, py + dy, name, size=6.5, anchor=anchor, weight=700 if ch == "A1zc" else 500)
    if key == "comp":
        (ax_, ay), (bx, by) = ax.px(CH["A1"][metric], CH["A1"]["acc"]), ax.px(CH["A1zc"][metric], CH["A1zc"]["acc"])
        cut = 1 - CH["A1zc"][metric] / CH["A1"][metric]
        fig.arrow((ax_ - 5, by + 2), (bx + 6, by + 2), color="good", sw=1.0,
                  label=f"−{cut * 100:.0f}% computed, same accuracy", label_side="above", label_color="good")
    fig.caption(rect.cx, cap.t + 1, title, size=7.5, weight=600)

fig.legend([("marker", "o:navy4", "Message channels"), ("marker", "s:teal3", "File channels"),
            ("marker", "*:#F2B53A", "Zero-copy broadcast"), ("line", "gray5", "95% CI")],
           fig.width / 2, strip.y)
# The saving label rides on its arrow, as a dimension label would.
fig.ignore.add(("text-near-line", "computed, same"))
fig.save(str(Path(__file__).parent / "out" / "fig_tradeoff"))
