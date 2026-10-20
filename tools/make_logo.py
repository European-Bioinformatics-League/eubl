#!/usr/bin/env python3
"""Generate the EUBL sequence-logo mark as SVG.

The mark is drawn as a protein sequence logo whose most informative residue
at each of four positions spells E-U-B-L (all valid IUPAC amino-acid codes:
Glu, selenocysteine, Asx, Leu). Residues are coloured with the WebLogo
"chemistry" scheme. Glyph outlines are taken from Atkinson Hyperlegible Next
(OFL) at weight 800 and converted to paths, so the SVG needs no font.

Usage:  python3 tools/make_logo.py        (requires: pip install fonttools brotli)
Writes: layouts/_partials/logo-hero.html   (with axes, for the home page)
        layouts/_partials/logo-mark.html   (letters only, for the header)
        static/favicon.svg
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "static/fonts/atkinson-hyperlegible-next-latin-wght-normal.woff2"

# Stacks are listed top (most frequent) to bottom, heights in bits.
STACKS = [
    [("E", 2.95), ("D", 0.40), ("N", 0.22)],
    [("U", 2.45), ("C", 0.42), ("S", 0.22)],
    [("B", 2.75), ("D", 0.36), ("N", 0.24)],
    [("L", 3.25), ("I", 0.36), ("V", 0.24)],
]
CHEMISTRY = {  # WebLogo chemistry classes
    "acidic": "DE", "polar": "CGSTYU", "neutral": "NQB", "basic": "KRH",
    "hydrophobic": "AVLIPWFM",
}
FIXED = {  # colours used where CSS custom properties are not available
    "acidic": "#C8323C", "polar": "#1E8A55", "neutral": "#7A3FA8",
    "basic": "#2B5FC7", "hydrophobic": "#1A1F2B",
}

COL_W, GAP, BIT = 100, 10, 52      # column width, gap, pixels per bit
MAX_BITS = 4.32                     # log2(20)
H = MAX_BITS * BIT


def chem(ch):
    return next(k for k, v in CHEMISTRY.items() if ch in v)


def glyph_path(font, ch, x, y_top, w, h):
    """Return an SVG path for `ch` stretched to fill the box exactly."""
    gs = font.getGlyphSet()
    glyph = gs[font.getBestCmap()[ord(ch)]]
    bp = BoundsPen(gs)
    glyph.draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    sx, sy = w / (xmax - xmin), h / (ymax - ymin)
    # font units are y-up; SVG is y-down
    t = (sx, 0, 0, -sy, x - xmin * sx, y_top + ymax * sy)
    sp = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    glyph.draw(TransformPen(sp, t))
    return sp.getCommands()


def letters(font, x0=0, y_base=H, use_classes=True):
    out = []
    for i, stack in enumerate(STACKS):
        x = x0 + i * (COL_W + GAP)
        y = y_base - sum(b for _, b in stack) * BIT
        for ch, bits in stack:
            h = bits * BIT
            pad = 1.5 if h > 30 else 0.8          # thin white gap between stacked letters
            d = glyph_path(font, ch, x, y + pad, COL_W, h - 2 * pad)
            c = chem(ch)
            fill = f'class="aa-{c}"' if use_classes else f'fill="{FIXED[c]}"'
            out.append(f'<path {fill} d="{d}"/>')
            y += h
    return "\n".join(out)


def main():
    font = TTFont(FONT)
    font = instantiateVariableFont(font, {"wght": 800})
    width = 4 * COL_W + 3 * GAP

    # Header mark: letters only, styled by CSS classes.
    mark = (f'<svg class="logo-mark" viewBox="0 0 {width} {H:.0f}" role="img" '
            f'aria-labelledby="mark-title" xmlns="http://www.w3.org/2000/svg">'
            f'<title id="mark-title">EUBL</title>\n{letters(font)}\n</svg>\n')
    (ROOT / "layouts/_partials/logo-mark.html").write_text(mark)

    # Hero: letters plus a bits axis and position numbers.
    ax = 46  # room for the y axis on the left
    ticks = "\n".join(
        f'<line x1="{ax-8}" x2="{ax-2}" y1="{H - b*BIT:.1f}" y2="{H - b*BIT:.1f}"/>'
        f'<text x="{ax-12}" y="{H - b*BIT + 5:.1f}" text-anchor="end">{b}</text>'
        for b in range(0, 5))
    pos = "\n".join(
        f'<text x="{ax + 6 + i*(COL_W+GAP) + COL_W/2:.0f}" y="{H + 26:.0f}" '
        f'text-anchor="middle">{i+1}</text>' for i in range(4))
    hero = (
        f'<svg class="logo-hero" viewBox="0 0 {ax + 6 + width} {H + 36:.0f}" role="img" '
        f'aria-labelledby="hero-title hero-desc" xmlns="http://www.w3.org/2000/svg">'
        f'<title id="hero-title">EUBL</title>'
        f'<desc id="hero-desc">A protein sequence logo of four positions whose most '
        f'conserved residues read E, U, B, L.</desc>\n'
        f'<g class="logo-axis"><line x1="{ax-2}" x2="{ax-2}" y1="0" y2="{H:.1f}"/>\n{ticks}\n'
        f'<text class="logo-axis-label" transform="translate(10 {H/2:.0f}) rotate(-90)" '
        f'text-anchor="middle">bits</text>\n{pos}</g>\n'
        f'<g transform="translate({ax + 6} 0)">\n{letters(font)}\n</g>\n</svg>\n')
    (ROOT / "layouts/_partials/logo-hero.html").write_text(hero)

    fav = (f'<svg viewBox="-10 -10 {width + 20} {H + 20:.0f}" '
           f'xmlns="http://www.w3.org/2000/svg">\n{letters(font, use_classes=False)}\n</svg>\n')
    (ROOT / "static/favicon.svg").write_text(fav)


if __name__ == "__main__":
    main()
