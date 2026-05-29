"""cmap population and GSUB `liga` compilation for the ligature path.

Phase 1 routes every letter through GSUB ligatures: each carrier pair collapses
into the real Jost letter glyph. Fragment-routed letters (phase 3) will get cmap
entries only, with no GSUB rule.
"""

from __future__ import annotations

from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont

from cipher.carriers import (
    all_carrier_codepoints,
    carrier_glyph_name,
    homophone_pairs,
)


def populate_cmap(font: TTFont) -> None:
    """Map each carrier codepoint to its glyph in every Unicode cmap subtable."""
    cmap = font["cmap"]
    unicode_subtables = [t for t in cmap.tables if t.isUnicode()]
    if not unicode_subtables:
        raise RuntimeError("base font has no Unicode cmap subtable")
    for sub in unicode_subtables:
        for cp in all_carrier_codepoints():
            sub.cmap[cp] = carrier_glyph_name(cp)


def generate_fea(font: TTFont) -> str:
    """Build the FEA `liga` feature: each carrier pair -> its real letter glyph."""
    base_cmap = font.getBestCmap()
    lines = ["feature liga {"]
    for letter, (first, second) in {k: v[0] for k, v in homophone_pairs().items()}.items():
        letter_glyph = base_cmap.get(ord(letter))
        if letter_glyph is None:
            raise RuntimeError(f"base font has no glyph for {letter!r}")
        g1 = carrier_glyph_name(first)
        g2 = carrier_glyph_name(second)
        lines.append(f"    sub {g1} {g2} by {letter_glyph};")
    lines.append("} liga;")
    lines.append("")
    return "\n".join(lines)


def compile_features(font: TTFont, fea_path: str) -> None:
    """Replace the base OT layout with only our cipher feature, from a FEA file."""
    # The base font's GPOS (kerning) is intentionally stripped here; phase 3
    # will rebuild GPOS for fragment seam math.
    for tag in ("GSUB", "GPOS"):
        if tag in font:
            del font[tag]
    addOpenTypeFeatures(font, fea_path)
