"""Fig. 3: where each channel loses information (k = 3, both datasets pooled, 300 tasks per channel).

Claim at a glance: the channels fail at different stages. Writing to files makes the Researcher keep
fewer facts, and without an index or with handles the Writer then reads only part of them; the pipe
delivers everything but its Reviewer, left without the facts, breaks answers that were right.
Form: (a) grouped bars per channel: share of supporting facts in the Researcher's output and share
of those that reached the Writer (AlignScore); (b) stacked bars: share of questions answered wrong,
split by the first stage that explains the error; the pipe's "Reviewer broke it" segment is the one
red. Data: figs/data/fig3_loss.json (agentipc.figdata from the main run).
"""
import json
from pathlib import Path

from archfig import Figure, Rect

DATA = json.loads((Path(__file__).parent / "data" / "fig3_loss.json").read_text())
ORDER = ["A1", "A1zc", "A2", "B", "C"]
NAMES = ["A1", "A1-zc", "A2", "B", "C"]
CH = {c["channel"]: c for c in DATA["channels"]}

fig = Figure("text")
strip, body = fig.area.take("top", 12, gap=4)
body = Rect(body.x, body.y, body.w, 108)
left, right = body.cols([1, 1], gap=18)

ax = fig.axes(left.take("bottom", 10, gap=2)[0], cats=NAMES, y=(0, 1.0), yticks=[0, 0.25, 0.5, 0.75, 1.0],
              yfmt=lambda v: f"{v * 100:.0f}%", ylabel="Supporting facts")
ax.bars({"In Researcher output": [CH[c]["as_recall_notes"] for c in ORDER],
         "Reached Writer": [CH[c]["as_recall_notes"] * CH[c]["as_kept_writer_input"] for c in ORDER]},
        ["navy2", "navy4"], labels=lambda v: f"{v * 100:.0f}")
fig.caption(left.cx, left.b - 9, "(a) Facts kept before the Writer", size=7.5, weight=600)
legend_a = ax.legend_items

STACK = [("aq_research_miss", "Researcher missed", "teal4"),
         ("aq_delivery_miss", "Not delivered", "gold2"),
         ("aq_writer_wrong", "Writer wrong", "gray2"),
         ("aq_reviewer_broke", "Reviewer broke it", "red4")]
bx = fig.axes(right.take("bottom", 10, gap=2)[0], cats=NAMES, y=(0, 0.45), yticks=[0, 0.1, 0.2, 0.3, 0.4],
              yfmt=lambda v: f"{v * 100:.0f}%", ylabel="Wrong answers")
bx.bars({name: [CH[c][key] for c in ORDER] for key, name, _ in STACK}, [col for _, _, col in STACK],
        stacked=True)
fig.caption(right.cx, right.b - 9, "(b) Why answers were wrong (stage at fault)", size=7.5, weight=600)

fig.legend(legend_a, left.cx, strip.y)
fig.legend(bx.legend_items, right.cx, strip.y)
# Colors encode stage and are read in color; the two navy tones in (a) differ in lightness.
fig.ignore.add("grayscale")
fig.save(str(Path(__file__).parent / "out" / "fig_loss"))
