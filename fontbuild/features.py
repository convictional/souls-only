"""GSUB `liga` compilation for the Souls Keys font.

build_keyboard.py writes a FEA file (one ligature rule per 2-char ASCII code,
collapsing the code's carrier pair into an opaque half-glyph) and calls
compile_features to replace the base font's OpenType layout with only that
feature.
"""

from __future__ import annotations

from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont


def compile_features(font: TTFont, fea_path: str) -> None:
    """Replace the base OT layout with only our cipher feature, from a FEA file."""
    # The base font's GPOS (kerning) is intentionally stripped here.
    for tag in ("GSUB", "GPOS"):
        if tag in font:
            del font[tag]
    addOpenTypeFeatures(font, fea_path)
