"""Decoder / oracle: reconstruct plaintext from the font's own tables.

Reverses the cipher using only cmap + GSUB ligatures, so a passing round-trip
proves the font's rules and the encoder's allocation agree. This is the
canonical equality oracle for tests (the encoder is non-deterministic: random
homophones plus random noise).

Phase 2 reversal handles two new things, both from the font alone:
  * homophone duplicate glyphs: a ligature may output `e.alt3`, which is not in
    cmap. We map it back to its letter by stripping the `.altN` suffix and
    resolving the base glyph through cmap. (An attacker would instead note the
    duplicate has the same outline as the cmap'd letter; the name suffix is the
    cheap equivalent for our own oracle.)
  * noise: a PUA codepoint whose glyph is never a ligature INPUT is padding and
    is dropped before pairing.
"""

from __future__ import annotations

import re
import sys

from fontTools.ttLib import TTFont

_ALT_SUFFIX = re.compile(r"^(.*)\.alt\d+$")


def _glyph_to_letter(glyph: str, glyph_to_codepoint: dict[str, int]):
    cp = glyph_to_codepoint.get(glyph)
    if cp is not None:
        return chr(cp)
    m = _ALT_SUFFIX.match(glyph)  # e.g. 'e.alt3' -> 'e'
    if m:
        base_cp = glyph_to_codepoint.get(m.group(1))
        if base_cp is not None:
            return chr(base_cp)
    return None


def _analyze_font(font_path: str):
    font = TTFont(font_path)
    cmap = font.getBestCmap()  # codepoint -> glyph name
    glyph_to_codepoint = {g: cp for cp, g in cmap.items()}

    gsub = font.get("GSUB")
    if gsub is None:
        raise RuntimeError("font has no GSUB table")

    pair_to_letter: dict[tuple[int, int], str] = {}
    ligature_input_glyphs: set[str] = set()

    for lookup in gsub.table.LookupList.Lookup:
        for sub in lookup.SubTable:
            ligatures = getattr(sub, "ligatures", None)
            if not ligatures:
                continue
            for first_glyph, lig_list in ligatures.items():
                for lig in lig_list:
                    input_glyphs = [first_glyph] + list(lig.Component)
                    ligature_input_glyphs.update(input_glyphs)
                    if len(input_glyphs) != 2:
                        continue
                    g1, g2 = input_glyphs
                    cp1 = glyph_to_codepoint.get(g1)
                    cp2 = glyph_to_codepoint.get(g2)
                    if cp1 is None or cp2 is None:
                        continue
                    letter = _glyph_to_letter(lig.LigGlyph, glyph_to_codepoint)
                    if letter is not None:
                        pair_to_letter[(cp1, cp2)] = letter

    # A PUA codepoint whose glyph is never a ligature input is noise.
    noise_codepoints = {
        cp for cp, g in cmap.items()
        if 0xE000 <= cp <= 0xF8FF and g not in ligature_input_glyphs
    }
    return pair_to_letter, noise_codepoints


def decode(encoded: str, font_path: str) -> str:
    pair_to_letter, noise_codepoints = _analyze_font(font_path)
    # Drop noise first; it is only ever placed between letters, never inside a
    # pair, so removing it leaves the carrier pairs contiguous.
    cleaned = [c for c in encoded if ord(c) not in noise_codepoints]

    out: list[str] = []
    i, n = 0, len(cleaned)
    while i < n:
        cp = ord(cleaned[i])
        if 0xE000 <= cp <= 0xF8FF and i + 1 < n:
            pair = (cp, ord(cleaned[i + 1]))
            letter = pair_to_letter.get(pair)
            if letter is not None:
                out.append(letter)
                i += 2
                continue
        out.append(cleaned[i])
        i += 1
    return "".join(out)


def main(argv: list[str]) -> int:
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    default_font = os.path.join(os.path.dirname(here), "dist", "SoulsOnly.ttf")
    font_path = argv[1] if len(argv) > 1 else default_font
    sys.stdout.write(decode(sys.stdin.read().rstrip("\n"), font_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
