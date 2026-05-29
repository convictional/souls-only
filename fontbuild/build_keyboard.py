"""Build the keyboard-typeable Souls Only font (Phase 5).

A refactor that reuses the existing engine:
  * fontbuild.fragments  -> the half-glyph slicing (left_half_glyph /
    right_half_glyph / own_join / _join_for_class), one half per letter side.
  * cipher.keyboard      -> the ASCII code allocation and slot routing (which
    itself reuses cipher.carriers FRAGMENT_CLASSES / fragment_class_of).
  * fontbuild.features.compile_features -> FEA compilation.
  * fontbuild.reveal.build_reveal -> the REVL variable axis, applied on top.

Every letter becomes two half-glyphs addressed by 2-char ASCII codes; a GSUB
ligature collapses each code into its half-glyph; the halves tile into the
letter. Output: dist/SoulsKeys.ttf (static) and, via reveal, SoulsKeys-VF.ttf.
"""

from __future__ import annotations

import os

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

from cipher import keyboard as kb
from cipher.carriers import ALPHABET, fragment_class_of, FRAGMENT_CLASSES
from fontbuild.features import compile_features
from fontbuild.fragments import (
    CANONICAL,
    _install,
    _join_for_class,
    left_half_glyph,
    own_join,
    right_half_glyph,
)
from fontbuild.reveal import build_reveal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_FONT = os.path.join(ROOT, "base", "Jost-Regular.ttf")
OUT_FONT = os.path.join(ROOT, "dist", "SoulsKeys.ttf")
OUT_VF = os.path.join(ROOT, "dist", "SoulsKeys-VF.ttf")
OUT_FEA = os.path.join(ROOT, "dist", "fea", "keyboard.fea")

FONT_FAMILY = "Souls Keys"


def _letter_join(font: TTFont, letter: str) -> int:
    """The join coordinate for a letter: its class join, or its own."""
    cls = fragment_class_of(letter)
    if cls is not None:
        return _join_for_class(font["hmtx"], font.getBestCmap(),
                               FRAGMENT_CLASSES[cls])
    return own_join(font, letter)


def _add_blank(font: TTFont, name: str) -> None:
    glyf = font["glyf"]
    if name in glyf:
        return
    g = Glyph()
    g.numberOfContours = 0
    glyf[name] = g
    font["hmtx"][name] = (0, 0)


def _add_half_glyphs(font: TTFont) -> None:
    """Install one glyph per half-slot, reusing the fragment slicing helpers."""
    glyf = font["glyf"]
    for slot in kb.half_slots():
        name = kb.half_glyph_name(slot)
        if slot.startswith("cls_"):
            cls = slot[len("cls_"):]
            join = _join_for_class(font["hmtx"], font.getBestCmap(),
                                   FRAGMENT_CLASSES[cls])
            glyph, adv = left_half_glyph(font, CANONICAL[cls], join)
        elif slot.startswith("L_"):
            letter = slot[len("L_"):]
            glyph, adv = left_half_glyph(font, letter, own_join(font, letter))
        else:  # "R_<letter>"
            letter = slot[len("R_"):]
            glyph, adv = right_half_glyph(font, letter, _letter_join(font, letter))
        _install(font, name, glyph, adv)  # sets lsb = xMin (avoids half-gap)


def _add_carriers_and_cmap(font: TTFont) -> None:
    for ch in kb.CODE_ALPHABET:
        _add_blank(font, kb.carrier_glyph_name(ch))
    font.setGlyphOrder(list(font["glyf"].glyphOrder))
    for sub in [t for t in font["cmap"].tables if t.isUnicode()]:
        for ch in kb.CODE_ALPHABET:
            sub.cmap[ord(ch)] = kb.carrier_glyph_name(ch)


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
    name.setName("SoulsKeys-Regular", 6, 3, 1, 0x409)
    name.setName(FONT_FAMILY, 16, 3, 1, 0x409)


def build() -> None:
    font = TTFont(BASE_FONT)
    _add_half_glyphs(font)
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
    print(f"  {len(kb.half_slots())} half-glyphs, {n_codes} ASCII codes, "
          f"{len(ALPHABET)} letters")


def build_with_reveal() -> None:
    build()
    build_reveal(aligned_path=OUT_FONT, out_vf=OUT_VF)  # reused REVL builder


if __name__ == "__main__":
    build_with_reveal()
