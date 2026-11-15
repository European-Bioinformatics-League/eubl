#!/usr/bin/env python3
"""Prepare the EUBL logo for the website from the master SVG drawn in Inkscape.

Usage:
    python3 tools/prepare_logo.py [brand/EUBL_logo.svg]
    (requires: pip install fonttools)

The master SVG is expected to contain
  * stroked shapes (ellipses, circles, line paths): the two strands;
  * one large filled path: the letters E U B L;
  * optionally smaller filled paths: the subtitle "European Bioinformatics League".
Text must be converted to paths (Inkscape: Path > Object to Path).

It writes
  layouts/_partials/logo.html  inline SVG without subtitle (header), coloured by CSS
                               (so it follows light/dark mode) and with strokes
                               that keep a readable width at any size;
  layouts/_partials/logo-full.html  the same with the subtitle (home page);
  static/logo.svg              the full logo, with subtitle and fixed colours,
                               for downloads, posters and slides;
  static/favicon.svg           a square icon: the letters in two rows on a tile.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "brand/EUBL_logo.svg"
NS = "{http://www.w3.org/2000/svg}"


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def style_of(el):
    """Merge presentation attributes and the style attribute."""
    s = {k: el.get(k) for k in ("fill", "stroke", "stroke-width") if el.get(k)}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            s[k.strip()] = v.strip()
    return s


def path_bounds(d):
    pen = ControlBoundsPen(None)
    parse_path(d, pen)
    return pen.bounds


def read_master(path):
    tree = ET.parse(path)
    strands, fills = [], []
    for el in tree.iter():
        tag = el.tag.replace(NS, "")
        if tag not in ("ellipse", "circle", "path"):
            continue
        st = style_of(el)
        stroke = st.get("stroke", "none")
        fill = st.get("fill", "#000000")
        if tag in ("ellipse", "circle"):
            cx, cy = float(el.get("cx")), float(el.get("cy"))
            rx = float(el.get("rx") or el.get("r"))
            ry = float(el.get("ry") or el.get("r"))
            shape = {"tag": "ellipse", "cx": cx, "cy": cy, "rx": rx, "ry": ry,
                     "bounds": (cx - rx, cy - ry, cx + rx, cy + ry)}
        else:
            d = el.get("d")
            shape = {"tag": "path", "d": d, "bounds": path_bounds(d)}
        sw = float(re.sub(r"[^0-9.]", "", st.get("stroke-width", "0")) or 0)
        is_stroked = stroke not in ("none", "#000000") and sw > 0 and fill == "none"
        if is_stroked:
            shape.update(colour=stroke.lower(), width=sw)
            strands.append(shape)
        elif fill != "none":
            shape.update(colour=fill.lower())
            fills.append(shape)
    if not fills:
        sys.exit("No filled paths found: convert the text to paths first.")
    area = lambda s: (s["bounds"][2] - s["bounds"][0]) * (s["bounds"][3] - s["bounds"][1])
    letters = max(fills, key=area)
    subtitle = [f for f in fills if f is not letters]
    return strands, letters, subtitle


def union(shapes, pad):
    xs0, ys0, xs1, ys1 = zip(*(s["bounds"] for s in shapes))
    return min(xs0) - pad, min(ys0) - pad, max(xs1) + pad, max(ys1) + pad


def viewbox(b):
    return f"{num(b[0])} {num(b[1])} {num(b[2] - b[0])} {num(b[3] - b[1])}"


def shape_svg(s, attrs):
    if s["tag"] == "ellipse":
        return (f'<ellipse cx="{num(s["cx"])}" cy="{num(s["cy"])}" '
                f'rx="{num(s["rx"])}" ry="{num(s["ry"])}" {attrs}/>')
    return f'<path d="{s["d"]}" {attrs}/>'


def main():
    strands, letters, subtitle = read_master(SRC)
    colours = list(dict.fromkeys(s["colour"] for s in strands))  # in order of appearance
    stroke_w = max((s["width"] for s in strands), default=0)

    # 1. Inline partials for the site: CSS classes, non-scaling strokes.
    #    logo.html has no subtitle (for small sizes); logo-full.html keeps it.
    def inline(with_subtitle, label):
        b = union(strands + [letters] + (subtitle if with_subtitle else []), pad=stroke_w + 2)
        body = []
        for i, c in enumerate(colours, 1):
            items = "".join(shape_svg(s, 'vector-effect="non-scaling-stroke"')
                            for s in strands if s["colour"] == c)
            body.append(f'<g class="logo-strand logo-strand-{i}">{items}</g>')
        body.append(f'<path class="logo-letters" d="{letters["d"]}"/>')
        if with_subtitle:
            body += [f'<path class="logo-subtitle" d="{f["d"]}"/>' for f in subtitle]
        return (
            "{{/* Generated by tools/prepare_logo.py from brand/EUBL_logo.svg. Do not edit. */}}\n"
            f'<svg class="logo{{{{ with .class }}}} {{{{ . }}}}{{{{ end }}}}" viewBox="{viewbox(b)}" '
            f'role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg">'
            + "".join(body) + "</svg>\n")
    (ROOT / "layouts/_partials/logo.html").write_text(inline(False, "EUBL"))
    (ROOT / "layouts/_partials/logo-full.html").write_text(
        inline(True, "EUBL: European Bioinformatics League"))

    # 2. Full logo with subtitle and fixed colours.
    b = union(strands + [letters] + subtitle, pad=stroke_w + 2)
    items = [shape_svg(s, f'fill="none" stroke="{s["colour"]}" stroke-width="{num(s["width"])}"')
             for s in strands]
    items += [shape_svg(f, f'fill="{f["colour"]}"') for f in [letters] + subtitle]
    full = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox(b)}" '
            f'stroke-linecap="square">\n<title>European Bioinformatics League</title>\n'
            + "\n".join(items) + "\n</svg>\n")
    (ROOT / "static/logo.svg").write_text(full)

    # 3. Square favicon: letters split into E U / B L.
    rec = RecordingPen()
    parse_path(letters["d"], rec)
    contours, cur = [], []
    for op, args in rec.value:
        cur.append((op, args))
        if op in ("closePath", "endPath"):
            contours.append(cur)
            cur = []
    def cbounds(c):
        p = ControlBoundsPen(None)
        for op, args in c:
            getattr(p, op)(*args)
        return p.bounds
    # Group contours into letters: a contour inside another (a counter) joins it.
    glyphs = []
    for c in sorted(contours, key=lambda c: cbounds(c)[0]):
        cb = cbounds(c)
        host = next((g for g in glyphs if g["b"][0] <= cb[0] and cb[2] <= g["b"][2]), None)
        if host:
            host["c"].append(c)
        else:
            glyphs.append({"b": cb, "c": [c]})
    if len(glyphs) != 4:
        print(f"warning: found {len(glyphs)} letters, not 4; favicon not written")
        return
    # Tight 2 x 2 grid on a rounded tile in the letters' colour; the letters are
    # thickened with a stroke so that they survive at 16 px.
    gw = max(g["b"][2] - g["b"][0] for g in glyphs)
    gh = max(g["b"][3] - g["b"][1] for g in glyphs)
    gap_x, gap_y = 0.30 * gw, 0.16 * gh
    block_w, block_h = 2 * gw + gap_x, 2 * gh + gap_y
    size = 1.30 * max(block_w, block_h)
    ox, oy = (size - block_w) / 2, (size - block_h) / 2
    sp = SVGPathPen(None, ntos=num)
    for i, g in enumerate(glyphs):
        col, row = i % 2, i // 2
        x0 = ox + col * (gw + gap_x) + (gw - (g["b"][2] - g["b"][0])) / 2
        y0 = oy + row * (gh + gap_y) + (gh - (g["b"][3] - g["b"][1])) / 2
        tp = TransformPen(sp, (1, 0, 0, 1, x0 - g["b"][0], y0 - g["b"][1]))
        for c in g["c"]:
            for op, args in c:
                getattr(tp, op)(*args)
    fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(size)} {num(size)}">\n'
           f'<rect width="{num(size)}" height="{num(size)}" rx="{num(size * 0.18)}" '
           f'fill="{letters["colour"]}"/>\n'
           f'<path d="{sp.getCommands()}" fill="#ffffff" stroke="#ffffff" '
           f'stroke-width="{num(size * 0.025)}" stroke-linejoin="miter"/>\n</svg>\n')
    (ROOT / "static/favicon.svg").write_text(fav)

    print("letters:", letters["colour"], "| strands:", ", ".join(colours),
          "| subtitle paths:", len(subtitle))


if __name__ == "__main__":
    main()
