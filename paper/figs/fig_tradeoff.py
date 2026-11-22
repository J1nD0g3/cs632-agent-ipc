"""Fig. 2: what copying costs (k = 3, HotpotQA and 2Wiki pooled, 300 tasks per channel), with accuracy.

Claim at a glance: the three costs rank the channels differently. Files send the most tokens (a), broadcast
computes the most prefill (b), and zero-copy cuts broadcast's prefill by 61% at broadcast's accuracy but its
runs are not shorter (c).
Form: (a) and (b) are scatter panels with a shared accuracy axis; message channels are circles (navy, the
pipe gray), file channels squares (teal), zero-copy the one gold star; vertical bars are 95% intervals of each
channel's mean. In (a) each trailing channel carries its paired accuracy gap to A1; in (b) a green arrow
carries the prefill cut and the paired accuracy difference, and each label gives the share of prompt tokens
served from the prefix cache. (c) gives zero-copy's serving time over broadcast's in the timing runs (six and
32 tasks at a time) as bars from A1 = 1, with min-max whiskers over runs.
Data: figs/data/fig2_tradeoff.json (agentipc.figdata: channels, gap_vs_a1, zc_time).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

DATA = json.loads((Path(__file__).parent / "data" / "fig2_tradeoff.json").read_text())
GAP = DATA["gap_vs_a1"]  # accuracy minus A1's, paired by task in the same main run
ZC = GAP["A1zc"]
TIME = {r["row"]: r for r in DATA["zc_time"]}
CH = {c["channel"]: c for c in DATA["channels"]}
STYLE = {  # marker, fill, name
    "A1": ("o", "navy4", "A1 broadcast"),
    "A1zc": ("*", "#F2B53A", "A1-zc zero-copy"),
    "A2": ("o", "gray3", "A2 pipe"),
    "B": ("s", "teal2", "B files"),
    "C": ("s", "teal4", "C files+index"),
}
# Label offsets (dx, dy, anchor) per panel, placed by hand so names never touch markers or each other.
LABEL = {
    "sent": {"A1": (5, -5, "start"), "A1zc": (5, 5, "start"), "A2": (5, 0, "start"),
             "B": (-5, 4, "end"), "C": (-5, -4, "end"), "D": (5, 0, "start")},
    "comp": {"A1": (-5, -13, "end"), "A1zc": (-6, 0, "end"), "A2": (5, 5, "start"),
             "B": (5, 4, "start"), "C": (5, -4, "start"), "D": (-5, -12, "end")},
}

pts = lambda v: f"{v * 100:+.1f}".replace("-", "−")

fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 118)
left, right, third = body.cols([0.92, 1.1, 0.66], gap=12)
panels = [(left, "total_tokens", "sent", (0, 42000), "(a) Tokens sent per task"),
          (right, "prefill_tokens", "comp", (0, 14000), "(b) Tokens computed (prefill) per task")]
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
        if key == "sent" and ch in ("A2", "B", "C"):
            fig.text(px + dx, py + dy + 6.8, f"{pts(GAP[ch]['acc_diff'])} vs A1", size=6, anchor=anchor,
                     color="gray5")
        if key == "comp":  # share of the sent tokens the engine served from its prefix cache
            reused = 1 - c["prefill_tokens"] / c["prompt_tokens"]  # prompt tokens served from the cache
            fig.text(px + dx, py + dy + 6.8, f"{reused * 100:.0f}% cached", size=6, anchor=anchor,
                     color="gray5")
    if key == "comp":
        (ax_, ay), (bx, by) = ax.px(CH["A1"][metric], CH["A1"]["acc"]), ax.px(CH["A1zc"][metric], CH["A1zc"]["acc"])
        cut = 1 - CH["A1zc"][metric] / CH["A1"][metric]
        fig.arrow((ax_ - 5, by + 2), (bx + 6, by + 2), color="good", sw=1.0)
        # Under the arrow, between zero-copy's whisker and the file channels' whiskers.
        for j, (txt, wt) in enumerate(((f"−{cut * 100:.0f}% prefill", 700), (f"accuracy {pts(ZC['acc_diff'])}", 500),
                                       (f"({pts(ZC['acc_diff_lo'])} to {pts(ZC['acc_diff_hi'])})", 500))):
            fig.text(bx + 8, by + 8.5 + 7 * j, txt, size=6.5, anchor="start", color="good", weight=wt)
    fig.caption(rect.cx, cap.t + 1, title, size=7.5, weight=600)

# (c) Zero-copy's serving time over broadcast's: bars grow from A1 = 1, whiskers are min-max over runs.
ROWS = [("**6 at a time**", None), ("run time", "six_run_time"), ("median task", "six_median_task"),
        ("**32 at a time**", None), ("run time ", "thirty_two_run_time"), ("median task ", "thirty_two_median_task")]
FILL = {"six_run_time": "#F2B53A", "thirty_two_median_task": "good"}
chart, cap = third.take("bottom", 10, gap=2)
ax = fig.axes(chart, x=(0.6, 1.3), xticks=[0.6, 0.8, 1.0, 1.2], xfmt=lambda v: f"{v:.1f}×",
              ycats=[r[0] for r in ROWS], grid=False)
row_h = ax.plot.h / len(ROWS)
for i, (_, key) in enumerate(ROWS):
    if key is None:
        continue
    t = TIME[key]
    cy = ax.plot.t + (i + 0.5) * row_h
    x1, xv = ax.X(1.0), ax.X(t["value"])
    bh = row_h * 0.62
    if abs(xv - x1) > 0.3:
        fig.box(Rect(min(x1, xv), cy - bh / 2, abs(xv - x1), bh), None, fill=FILL.get(key, "gray2"), sw=0.5, r=0)
    fig.line((ax.X(t["lo"]), cy), (ax.X(t["hi"]), cy), sw=0.6, color="ink")
    for v in (t["lo"], t["hi"]):
        fig.line((ax.X(v), cy - 1.6), (ax.X(v), cy + 1.6), sw=0.6, color="ink")
    right = t["value"] >= 1.0
    fig.text(ax.X(t["hi"] if right else t["lo"]) + (2.5 if right else -2.5), cy, f"{t['value']:.2f}×", size=6.5,
             anchor="start" if right else "end", weight=700 if key in FILL else 500,
             color="good" if key == "thirty_two_median_task" else "ink")
ax.vline(1.0, color="gray5")
fig.text(ax.X(1.0) + 1.5, ax.plot.t + 1.5, "A1 = 1", size=6, anchor="start", valign="top", color="gray5")
fig.caption(third.cx, cap.t + 1, "(c) Zero-copy time vs A1", size=7.5, weight=600)

fig.legend([("marker", "o:navy4", "Message channels"), ("marker", "s:teal3", "File channels"),
            ("marker", "*:#F2B53A", "Zero-copy broadcast"), ("line", "gray5", "95% CI")],
           fig.width / 2, strip.y)

fig.save(str(Path(__file__).parent / "out" / "fig_tradeoff"))
