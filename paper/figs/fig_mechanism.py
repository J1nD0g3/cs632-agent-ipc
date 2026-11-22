"""Channel mechanisms: how the Researcher's and Writer's results reach the next agent in each channel.

Claim at a glance: message channels copy content into the next prompt (broadcast all of it, zero-copy
the same but served from the cache, the pipe only the last output); file channels leave results in a
shared workspace that later agents must find and read (plus an index in C), and B's Writer never opens
the notes in 42% of tasks (C's in 8%).
Plan: a 3 x 2 grid of panels with one identical layout: three robots (Researcher, Writer, Reviewer) in
a row. Message panels show, under each hop, what the receiver's prompt holds as a strip of colored
segments; file panels show the shared folder with its files and the write/read arrows. The Writer's read of
the notes enters it from the left, where a message would, and carries the measured skip rate (red dashed
in B, muted in C). Data: figs/data/fig1_mechanism.json (agentipc.figdata, main run). Same colors for
the same content everywhere (question, documents, notes, draft); hatched = served from the prefix cache.
"""
import json
from pathlib import Path

from archfig import Figure, Rect
from archfig.palette import color

DATA = json.loads((Path(__file__).parent / "data" / "fig1_mechanism.json").read_text())
SKIP = {c["channel"]: c["writer_skipped_notes"] for c in DATA["channels"]}  # Writer never opens the notes (k=3)
ROLE_FILL = {"Researcher": "#D9E2F3", "Writer": "#DCEBEC", "Reviewer": "#E6EEDC"}
SEG = {"Q": "white", "Docs": "teal3", "Notes": "navy3", "Draft": "gold2", "Instr": "white"}

fig = Figure("text")
W = fig.area.w


def robot(cx, top, role, s=12.5):
    """Robot-head icon; returns the label's bottom y and the face rect."""
    ink, fill = color("ink"), ROLE_FILL[role]
    fw, fh = s, s * 0.78
    fx, fy = cx - fw / 2, top + s * 0.30
    ear_w, ear_h = s * 0.13, s * 0.36
    sw = 0.9
    svg = [
        f'<line x1="{cx}" y1="{top + s * 0.10}" x2="{cx}" y2="{fy}" stroke="{ink}" stroke-width="{sw}"/>',
        f'<circle cx="{cx}" cy="{top + s * 0.07}" r="{s * 0.07}" fill="{fill}" stroke="{ink}" stroke-width="{sw}"/>',
        f'<rect x="{fx - ear_w}" y="{fy + (fh - ear_h) / 2}" width="{ear_w}" height="{ear_h}" rx="0.8" '
        f'fill="{fill}" stroke="{ink}" stroke-width="{sw}"/>',
        f'<rect x="{fx + fw}" y="{fy + (fh - ear_h) / 2}" width="{ear_w}" height="{ear_h}" rx="0.8" '
        f'fill="{fill}" stroke="{ink}" stroke-width="{sw}"/>',
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="{s * 0.2}" fill="{fill}" stroke="{ink}" '
        f'stroke-width="{sw * 1.2}"/>',
        f'<circle cx="{cx - s * 0.2}" cy="{fy + fh * 0.38}" r="{s * 0.065}" fill="none" stroke="{ink}" stroke-width="{sw}"/>',
        f'<circle cx="{cx + s * 0.2}" cy="{fy + fh * 0.38}" r="{s * 0.065}" fill="none" stroke="{ink}" stroke-width="{sw}"/>',
        f'<path d="M {cx - s * 0.17} {fy + fh * 0.62} Q {cx} {fy + fh * 0.82} {cx + s * 0.17} {fy + fh * 0.62}" '
        f'fill="none" stroke="{ink}" stroke-width="{sw}" stroke-linecap="round"/>',
    ]
    face = Rect(fx - ear_w, top, fw + 2 * ear_w, fy + fh - top)
    fig.raw("".join(svg), extent=face)
    fig.text(cx, fy + fh + 1.5, f"**{role}**", size=6.5, valign="top")
    return Rect(fx, fy, fw, fh), fy + fh + 8.5


def strip(x, y, w, parts, cached=()):
    """A prompt as segments [(kind, weight)]; kinds in `cached` are hatched (served from the cache)."""
    total = sum(p[1] for p in parts)
    cx = x
    for kind, wt in parts:
        sw = w * wt / total
        fig.box(Rect(cx, y, sw, 6.2), None, fill=SEG[kind], sw=0.5, r=0,
                hatch="gray4/white" if kind in cached else None)
        cx += sw
    return Rect(x, y, w, 6.2)


cols = fig.area.cols(3, gap=5)
cols2 = fig.area.cols(2, gap=5)  # the file channels take the bottom row in two wider panels
ROW_H = (51, 59)  # message panels have slack under their strips; file panels need the folder's height
rows = [Rect(fig.area.x, fig.area.y + 13, W, ROW_H[0]), Rect(fig.area.x, fig.area.y + 13 + ROW_H[0] + 5, W, ROW_H[1])]
PANELS = [("A1", "Broadcast", ""), ("A1zc", "Zero-copy broadcast", ""), ("A2", "Pipe", ""),
          ("B", "Shared files", ""), ("C", "Files + index", "")]
LABEL = {"A1": "A1", "A1zc": "A1-zc", "A2": "A2", "B": "B", "C": "C", "D": "D"}

fig.legend([("box", "white", "Questions"), ("box", "teal3", "Documents"), ("box", "navy3", "Notes"),
            ("box", "gold2", "Draft"), ("hatch", "gray4/white", "Reused from cache")],
           fig.area.cx, fig.area.y, anchor="n")

for i, (ch, name, sub) in enumerate(PANELS):
    c = cols[i] if i < 3 else cols2[i - 3]
    pr = Rect(c.x, rows[i // 3].y, c.w, rows[i // 3].h)
    fig.panel(pr, f"{LABEL[ch]}  {name}", fill="gray1")
    body = pr.inset(5, t=11, b=3)
    # File panels move the Writer right so the skip-rate label fits between its read and the Writer's name.
    xs = [body.x + body.w * f for f in ((1 / 6, 3 / 6, 5 / 6) if ch.startswith("A") else (1 / 6, 0.54, 5 / 6))]
    faces = []
    for x, role in zip(xs, ("Researcher", "Writer", "Reviewer")):
        face, bottom = robot(x, body.y, role)
        faces.append(face)
    low = Rect(body.x, bottom + 3, body.w, body.b - bottom - 3)
    if ch in ("A1", "A1zc", "A2"):
        for j in (0, 1):
            a, b = faces[j], faces[j + 1]
            fig.arrow((a.r + 4, a.cy), (b.l - 4, b.cy), sw=1.0)
        hop = [Rect(xs[0] + 6, low.y, xs[1] - xs[0], low.h), Rect(xs[1] + 6, low.y, xs[2] - xs[1], low.h)]
        if ch == "A2":
            payload = [[("Q", 1), ("Notes", 2)], [("Q", 1), ("Draft", 2)]]
        else:
            payload = [[("Q", 1), ("Docs", 5), ("Notes", 2)], [("Q", 1), ("Docs", 5), ("Notes", 2), ("Draft", 2)]]
        cached = ("Q", "Docs", "Notes") if ch == "A1zc" else ()
        for j, (h, parts) in enumerate(zip(hop, payload)):
            w = h.w * (0.5 if ch == "A2" else 0.82) * (1 if j else 0.8)
            c = (("Q", "Docs") if j == 0 else ("Q", "Docs", "Notes")) if ch == "A1zc" else ()
            fig.text(h.cx - 6, h.y, "to Writer" if j == 0 else "to Reviewer", size=6, valign="top",
                     color="gray5")
            strip(h.cx - 6 - w / 2, h.y + 7.5, w, parts, cached=c)
    else:
        folder = Rect(low.x + 4, low.y + 6, low.w - 8, low.h - 6)
        fig.box(folder, None, fill="white", sw=0.6, r=1.5, dash="dash")
        # Each doc sits where its arrows can land on it vertically without passing a robot's name.
        files = [("notes", "navy3", xs[0] + 22), ("d01..d30", "teal3", xs[1]), ("draft", "gold2", xs[2] - 18)]
        if ch == "C":
            files = [("index", "navy5", xs[0] - 14)] + files
        boxes = {}
        for name, fill, cx in files:
            fw, _ = fig.fit(name, size=6, shape="doc")
            r = Rect(cx - (fw + 3) / 2, folder.y + 4.4, fw + 3, folder.h - 6.4)
            boxes[name] = fig.box(r, name, fill=fill, shape="doc", size=6, sw=0.6, stack=1 if name.startswith("d0") else 0)
        y0 = bottom + 0.5
        mid = (y0 + folder.y) / 2
        top_of = lambda n: boxes[n].rect.t
        fig.arrow((xs[0] + 14, y0), (xs[0] + 14, top_of("notes")), sw=0.8)
        fig.text(xs[0] + 11, mid, "write", size=6, anchor="end")
        # The Writer's read of the notes, the one the skip rate measures, enters it from the left like a message.
        skip = SKIP[ch]
        tone = "bad" if ch == "B" else "navy4"
        fig.arrow((xs[0] + 26, top_of("notes")), (xs[0] + 26, faces[1].cy), (faces[1].l - 4, faces[1].cy),
                  sw=1.0, color=tone, dash="dash" if ch == "B" else None)
        label = f"unread in\n{skip * 100:.0f}% of tasks"
        fig.text(xs[0] + 28.5, faces[1].cy + 2, f"**{label}**" if ch == "B" else label, size=6.5, anchor="start",
                 valign="top", color=tone if ch == "B" else "gray5")
        fig.arrow((xs[1], top_of("d01..d30")), (xs[1], y0), sw=0.8)
        fig.text(xs[1] + 3, mid, "read", size=6, anchor="start")
        fig.arrow((faces[1].r + 4, faces[1].cy), (xs[2] - 25, faces[1].cy), (xs[2] - 25, top_of("draft")), sw=0.8)
        fig.text(xs[2] - 28, mid, "write", size=6, anchor="end")
        fig.arrow((xs[2] - 11, top_of("draft")), (xs[2] - 11, y0), sw=0.8)
        fig.text(xs[2] - 8, mid, "read", size=6, anchor="start")
        if ch == "D":
            for j in (0, 1):
                a, b = faces[j], faces[j + 1]
                fig.arrow((a.r + 4, a.cy), (b.l - 4, b.cy), sw=1.0, color="navy5", label="handoff", label_size=6)

fig.save(str(Path(__file__).parent / "out" / "fig_mechanism"))
