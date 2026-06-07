"""Convert the built static TTF into an OTF (CFF, cubic outlines).

Draws every glyf glyph through a quadratic->cubic pen into T2 charstrings,
swaps the outline tables (glyf/loca -> CFF), and rebrands the container as
OTTO. cmap, GSUB (the cipher ligatures), and metrics are untouched, so the
OTF decodes the cipher stream identically to the TTF.

The variable font stays TTF-only: its REVL axis lives in gvar (glyf
variations), and a CFF2 conversion of variation data is not supported by
fontTools. TTF is also the better-supported container for variable fonts.

    python -m fontbuild.build_keyboard   # build dist/SoulsOnly.ttf first
    python tools/make_otf.py             # -> dist/SoulsOnly.otf
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fontTools.fontBuilder import FontBuilder  # noqa: E402
from fontTools.pens.qu2cuPen import Qu2CuPen  # noqa: E402
from fontTools.pens.t2CharStringPen import T2CharStringPen  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

SRC = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
DST = os.path.join(ROOT, "dist", "SoulsOnly.otf")

# TrueType-only tables that have no place in a CFF font.
TT_TABLES = ("glyf", "loca", "cvt ", "fpgm", "prep", "gasp")


def ttf_to_otf(src: str, dst: str) -> None:
    font = TTFont(src)
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]

    charstrings = {}
    for name in font.getGlyphOrder():
        pen = T2CharStringPen(hmtx[name][0], glyph_set)
        glyph_set[name].draw(Qu2CuPen(pen, max_err=1.0, all_cubic=True))
        charstrings[name] = pen.getCharString()

    # drop the TrueType outline tables BEFORE wrapping in FontBuilder
    # (it decides TTF-vs-CFF by the presence of glyf)
    for tag in TT_TABLES:
        if tag in font:
            del font[tag]
    font.sfntVersion = "OTTO"
    fb = FontBuilder(font=font)
    ps_name = font["name"].getDebugName(6) or "SoulsOnly-Regular"
    full_name = font["name"].getDebugName(4) or ps_name
    fb.setupCFF(ps_name, {"FullName": full_name}, charstrings, {})
    font["maxp"].tableVersion = 0x00005000  # CFF fonts use maxp 0.5
    font.save(dst)
    print(f"wrote {dst}")


def main() -> int:
    ttf_to_otf(SRC, DST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
