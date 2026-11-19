"""Channel mechanisms: how the Researcher's and Writer's results reach the next agent in each channel.

Claim at a glance: message channels copy content into the next prompt (broadcast all of it, zero-copy
the same but served from the cache, the pipe only the last output); file channels leave results in a
shared workspace that later agents must find and read (plus an index in C).
Plan: a 3 x 2 grid of panels with one identical layout: three robots (Researcher, Writer, Reviewer) in
a row. Message panels show, under each hop, what the receiver's prompt holds as a strip of colored
segments; file panels show the shared folder with its files and the write/read arrows. Same colors for
the same content everywhere (question, documents, notes, draft); hatched = served from the prefix cache.
"""
from archfig import Figure, Rect
from archfig.palette import color

ROLE_FILL = {"Researcher": "#D9E2F3", "Writer": "#DCEBEC", "Reviewer": "#E6EEDC"}
SEG = {"Q": "white", "Docs": "teal3", "Notes": "navy3", "Draft": "gold2", "Instr": "white"}

fig = Figure("text")
W = fig.area.w


def robot(cx, top, role, s=12.5):
    """Robot head in the user's reference style; returns the label's bottom y and the face rect."""
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
PANEL_H = 59
rows = [Rect(fig.area.x, fig.area.y + 14, W, PANEL_H), Rect(fig.area.x, fig.area.y + 14 + PANEL_H + 5, W, PANEL_H)]
PANELS = [("A1", "Broadcast", ""), ("A1zc", "Zero-copy broadcast", ""), ("A2", "Pipe", ""),
          ("B", "Shared files", ""), ("C", "Files + index", "")]
LABEL = {"A1": "A1", "A1zc": "A1-zc", "A2": "A2", "B": "B", "C": "C", "D": "D"}

fig.legend([("box", "white", "Questions"), ("box", "teal3", "Documents"), ("box", "navy3", "Notes"),
            ("box", "gold2", "Draft"), ("hatch", "gray4/white", "Reused from cache")],
           fig.area.cx, fig.area.y, anchor="n")

for i, (ch, name, sub) in enumerate(PANELS):
    c = cols[i] if i < 3 else cols2[i - 3]
    pr = Rect(c.x, rows[i // 3].y, c.w, PANEL_H)
    fig.panel(pr, f"{LABEL[ch]}  {name}", fill="gray1")
    body = pr.inset(5, t=11, b=3)
    xs = [body.x + body.w * f for f in (1 / 6, 3 / 6, 5 / 6)]
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
        files = [("notes", "navy3"), ("d01..d30", "teal3"), ("draft", "gold2")]
        if ch == "C":
            files = [("index", "navy5")] + files
        slots = folder.inset(4, y=2).cols(len(files), gap=4)
        boxes = {}
        for (name, fill), sl in zip(files, slots):
            fw, _ = fig.fit(name, size=6, shape="doc")
            r = sl.sized(min(sl.w, fw + 3), sl.h - 2.4, anchor="s")
            boxes[name] = fig.box(r, name, fill=fill, shape="doc", size=6, sw=0.6, stack=1 if name.startswith("d0") else 0)
        y0 = bottom + 0.5
        mid = (y0 + folder.y) / 2
        fig.arrow((xs[0], y0), (xs[0], folder.y), sw=0.8)
        fig.text(xs[0] + 3, mid, "write", size=6, anchor="start")
        fig.arrow((xs[1] - 3, folder.y), (xs[1] - 3, y0), sw=0.8)
        fig.arrow((xs[1] + 3, y0), (xs[1] + 3, folder.y), sw=0.8)
        fig.text(xs[1] + 6, mid - 0.8, "read, write", size=6, anchor="start")
        fig.arrow((xs[2], folder.y), (xs[2], y0), sw=0.8)
        fig.text(xs[2] + 3, mid, "read", size=6, anchor="start")
        if ch == "D":
            for j in (0, 1):
                a, b = faces[j], faces[j + 1]
                fig.arrow((a.r + 4, a.cy), (b.l - 4, b.cy), sw=1.0, color="navy5", label="handoff", label_size=6)

fig.save(str(__import__("pathlib").Path(__file__).parent / "out" / "fig_mechanism"))
