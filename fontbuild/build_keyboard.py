"""Build the keyboard-typeable Souls Only font (charset extension).

A refactor that reuses the existing engine:
  * fontbuild.fragments  -> the half-glyph slicing (left_half_glyph /
    right_half_glyph / own_join / _join_for_class / space_half_glyphs /
    pad_glyph), one half per slot across the full charset.
  * cipher.keyboard      -> the ASCII code allocation and slot routing over
    the full printable charset (letters, digits, symbols, space).
  * fontbuild.features.compile_features -> FEA compilation.
  * fontbuild.decoy_reveal.build_decoy_reveal -> the REVL variable axis with
    decoy focal points and the hidden true text, applied on top.

Every character becomes two half-glyphs addressed by 2-char ASCII codes; a
GSUB ligature collapses each code into its half-glyph; the halves tile into
the character. Output: dist/SoulsOnly.ttf (static) and, via reveal,
SoulsOnly-VF.ttf.
"""

from __future__ import annotations

import os

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

from cipher import charset
from cipher import keyboard as kb
from fontbuild.features import compile_features
from fontbuild.fragments import (
    _install,
    _join_for_class,
    left_half_glyph,
    own_join,
    pad_glyph,
    right_half_glyph,
)
from fontbuild.decoy_reveal import build_decoy_reveal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_FONT = os.path.join(ROOT, "base", "Jost-Regular.ttf")
OUT_FONT = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
OUT_VF = os.path.join(ROOT, "dist", "SoulsOnly-VF.ttf")
OUT_FEA = os.path.join(ROOT, "dist", "fea", "keyboard.fea")

FONT_FAMILY = "Souls Only"


def _char_join(font: TTFont, ch: str) -> int:
    """Join coordinate for a character: its class join, or its own."""
    cls = charset.class_of(ch)
    if cls is not None:
        return _join_for_class(font["hmtx"], font.getBestCmap(),
                               charset.FRAGMENT_CLASSES[cls])
    return own_join(font, ch)


def _add_blank(font: TTFont, name: str) -> None:
    glyf = font["glyf"]
    if name in glyf:
        return
    g = Glyph()
    g.numberOfContours = 0
    glyf[name] = g
    font["hmtx"][name] = (0, 0)


def _fragment_source(font: TTFont, ch: str) -> str:
    """Deterministic inked half-glyph to clone as carrier ink for `ch`."""
    half_names = [charset.half_glyph_name(s) for s in charset.half_slots()]
    glyf = font["glyf"]
    n = len(half_names)
    i = (ord(ch) * 31 + 7) % n  # spread across fragments
    while glyf[half_names[i]].numberOfContours <= 0:  # skip blanks (space)
        i = (i + 1) % n
    return half_names[i]


def _add_inked_carrier(font: TTFont, name: str, source: str) -> None:
    """Install a carrier glyph carrying a copy of `source`'s fragment ink, so
    stray (un-ligated) carrier characters render as cipher noise, not blanks."""
    glyf = font["glyf"]
    if name in glyf:
        return
    pen = TTGlyphPen(font.getGlyphSet())
    font.getGlyphSet()[source].draw(pen)
    _install(font, name, pen.glyph(), font["hmtx"][source][0])


def _add_half_glyphs(font: TTFont) -> None:
    """Install one glyph per half-slot over the charset, reusing the slicer.

    Shared classes (lowercase bowl/stem, uppercase bowl) install one left glyph
    from the canonical character; everything else uses its own halves. Space is
    not ciphered, so it has no half-glyphs -- it stays the font's own space.
    """
    done: set[str] = set()
    for ch in charset.CHARSET:
        ls = charset.left_slot(ch)
        if ls not in done:
            done.add(ls)
            if ls.startswith("cls_"):
                cls = ls[len("cls_"):]
                canon = charset.CANONICAL[cls]
                glyph, adv = left_half_glyph(font, canon, _char_join(font, canon))
            else:  # "L_<ch>"
                glyph, adv = left_half_glyph(font, ch, own_join(font, ch))
            _install(font, charset.half_glyph_name(ls), glyph, adv)
        rs = charset.right_slot(ch)
        if rs not in done:
            done.add(rs)
            glyph, adv = right_half_glyph(font, ch, _char_join(font, ch))
            _install(font, charset.half_glyph_name(rs), glyph, adv)


def _add_carriers_and_cmap(font: TTFont) -> None:
    for ch in kb.CODE_ALPHABET:
        _add_inked_carrier(font, kb.carrier_glyph_name(ch),
                           _fragment_source(font, ch))
    pg, padv = pad_glyph()
    _install(font, kb.carrier_glyph_name(charset.PAD), pg, padv)
    font.setGlyphOrder(list(font["glyf"].glyphOrder))
    for sub in [t for t in font["cmap"].tables if t.isUnicode()]:
        for ch in kb.CODE_ALPHABET:
            sub.cmap[ord(ch)] = kb.carrier_glyph_name(ch)
        sub.cmap[ord(charset.PAD)] = kb.carrier_glyph_name(charset.PAD)


def _generate_fea() -> str:
    """One GSUB ligature per code: the 2 code chars collapse to the half-glyph."""
    lines = ["feature liga {"]
    for slot, codes in kb.slot_codes().items():
        target = kb.half_glyph_name(slot)
        for code in codes:
            g0 = kb.carrier_glyph_name(code[0])
            g1 = kb.carrier_glyph_name(code[1])
            lines.append(f"    sub {g0} {g1} by {target};")
    lines.append("} liga;")
    lines.append("")
    return "\n".join(lines)


def _set_names(font: TTFont) -> None:
    name = font["name"]
    name.setName(FONT_FAMILY, 1, 3, 1, 0x409)
    name.setName("Regular", 2, 3, 1, 0x409)
    name.setName(FONT_FAMILY, 4, 3, 1, 0x409)
    name.setName("SoulsOnly-Regular", 6, 3, 1, 0x409)
    name.setName(FONT_FAMILY, 16, 3, 1, 0x409)


def build() -> None:
    font = TTFont(BASE_FONT)
    _add_half_glyphs(font)
    # Letters are carriers now, and carriers wear fragment ink, so plain typed
    # text renders as cipher noise; only the code stream ligates into words.
    _add_carriers_and_cmap(font)

    os.makedirs(os.path.dirname(OUT_FEA), exist_ok=True)
    with open(OUT_FEA, "w") as fh:
        fh.write(_generate_fea())
    compile_features(font, OUT_FEA)  # reused
    _set_names(font)

    os.makedirs(os.path.dirname(OUT_FONT), exist_ok=True)
    font.save(OUT_FONT)
    n_codes = sum(len(c) for c in kb.slot_codes().values())
    print(f"wrote {OUT_FONT}")
    print(f"  {len(charset.half_slots())} half-glyphs, {n_codes} ASCII codes, "
          f"{len(charset.CHARSET)} characters")


def build_with_reveal() -> None:
    build()
    build_decoy_reveal(aligned_path=OUT_FONT, out_vf=OUT_VF)


if __name__ == "__main__":
    build_with_reveal()
