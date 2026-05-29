"""cmap population and GSUB `liga` compilation.

Phase 2 maps both ligature-pair carriers and noise codepoints in cmap, and emits
one GSUB ligature rule per homophone pair: homophone 0 collapses to the base
letter glyph, homophones 1..n-1 collapse to that letter's `.altK` duplicate.
Noise codepoints map to invisible glyphs and intentionally participate in NO
ligature rule, so they render as nothing and the decoder can recognise them as
noise (a PUA glyph that is never a ligature input).
"""

from __future__ import annotations

from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont

from cipher.carriers import (
    FRAGMENT_CLASSES,
    all_carrier_codepoints,
    carrier_glyph_name,
    fragment_letters,
    homophone_pairs,
    left_carriers,
    left_fragment_glyph_name,
    noise_codepoints,
    noise_glyph_name,
    right_carriers,
    right_fragment_glyph_name,
)


def populate_cmap(font: TTFont) -> None:
    """Map every carrier and noise codepoint to its glyph in all Unicode cmaps."""
    cmap = font["cmap"]
    unicode_subtables = [t for t in cmap.tables if t.isUnicode()]
    if not unicode_subtables:
        raise RuntimeError("base font has no Unicode cmap subtable")
    for sub in unicode_subtables:
        for cp in all_carrier_codepoints():
            sub.cmap[cp] = carrier_glyph_name(cp)
        for cp in noise_codepoints():
            sub.cmap[cp] = noise_glyph_name(cp)
        # Fragment carriers map straight to fragment glyphs. There is NO GSUB
        # rule for these: the tiling happens purely by adjacency in layout, so
        # the tables never document the fragment-to-letter mapping.
        for cls in FRAGMENT_CLASSES:
            lname = left_fragment_glyph_name(cls)
            for cp in left_carriers(cls):
                sub.cmap[cp] = lname
        for letter in fragment_letters():
            rname = right_fragment_glyph_name(letter)
            for cp in right_carriers(letter):
                sub.cmap[cp] = rname


def generate_fea(font: TTFont) -> str:
    """Build the FEA `liga` feature: one rule per homophone pair."""
    base_cmap = font.getBestCmap()
    lines = ["feature liga {"]
    for letter, plist in homophone_pairs().items():
        letter_glyph = base_cmap.get(ord(letter))
        if letter_glyph is None:
            raise RuntimeError(f"base font has no glyph for {letter!r}")
        for k, (first, second) in enumerate(plist):
            target = letter_glyph if k == 0 else f"{letter_glyph}.alt{k}"
            g1 = carrier_glyph_name(first)
            g2 = carrier_glyph_name(second)
            lines.append(f"    sub {g1} {g2} by {target};")
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
