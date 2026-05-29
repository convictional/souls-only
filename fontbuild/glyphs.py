"""Glyph generation for the cipher font.

Three jobs, all writing into the (aligned) master:
  * blank zero-advance glyphs for every ligature-pair carrier codepoint
  * blank zero-advance glyphs for every noise codepoint (invisible padding)
  * duplicate letter glyphs for homophones (index 1..n-1), each a deep copy of
    the base letter outline so the rendered image is identical while the glyph
    ID is distinct (distinct IDs let phase 4 scatter each occurrence on its own)
"""

from __future__ import annotations

import copy

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

from cipher.carriers import (
    all_carrier_codepoints,
    carrier_glyph_name,
    homophone_pairs,
    noise_codepoints,
    noise_glyph_name,
)


def _add_blank(glyf, hmtx, name: str) -> None:
    if name in glyf:
        return
    blank = Glyph()
    blank.numberOfContours = 0
    glyf[name] = blank  # also appends to glyf's own glyph order
    hmtx[name] = (0, 0)


def add_blank_carrier_glyphs(font: TTFont) -> None:
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in all_carrier_codepoints():
        _add_blank(glyf, hmtx, carrier_glyph_name(cp))
    font.setGlyphOrder(list(glyf.glyphOrder))


def add_noise_glyphs(font: TTFont) -> None:
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in noise_codepoints():
        _add_blank(glyf, hmtx, noise_glyph_name(cp))
    font.setGlyphOrder(list(glyf.glyphOrder))


def add_homophone_glyphs(font: TTFont) -> None:
    """Duplicate each letter glyph once per extra homophone (index 1..n-1)."""
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    base_cmap = font.getBestCmap()
    for letter, plist in homophone_pairs().items():
        base_glyph = base_cmap.get(ord(letter))
        if base_glyph is None:
            raise RuntimeError(f"base font has no glyph for {letter!r}")
        for k in range(1, len(plist)):
            dup = f"{base_glyph}.alt{k}"
            if dup in glyf:
                continue
            glyf[dup] = copy.deepcopy(glyf[base_glyph])
            hmtx[dup] = hmtx[base_glyph]
    font.setGlyphOrder(list(glyf.glyphOrder))
