"""Add blank, zero-advance carrier glyphs to a base font.

The raw carrier stream, with ligatures not applied, must render as nothing
meaningful, so each carrier maps (in features.py) to one of these blank glyphs.
"""

from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

from cipher.carriers import all_carrier_codepoints, carrier_glyph_name


def add_blank_carrier_glyphs(font: TTFont) -> None:
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in all_carrier_codepoints():
        name = carrier_glyph_name(cp)
        if name in glyf:
            continue
        blank = Glyph()
        blank.numberOfContours = 0  # no outline -> renders nothing
        # Assigning to glyf[] appends the name to glyf's own glyph order; we
        # sync the font-level order from it so maxp recalc does not assert.
        glyf[name] = blank
        hmtx[name] = (0, 0)  # zero advance width, zero left side bearing
    font.setGlyphOrder(list(glyf.glyphOrder))
