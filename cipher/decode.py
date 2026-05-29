"""Decoder / oracle: reconstruct plaintext from the font's own tables.

Reverses the cipher using only cmap + GSUB ligatures, so a passing round-trip
proves the font's rules and the encoder's allocation agree. This is the
canonical equality oracle for tests (the encoder becomes non-deterministic once
phase-2 homophones land).
"""

from __future__ import annotations

import sys

from fontTools.ttLib import TTFont


def _load_pair_to_letter(font_path: str) -> dict[tuple[int, int], str]:
    font = TTFont(font_path)
    cmap = font.getBestCmap()  # codepoint -> glyph name
    glyph_to_codepoint = {g: cp for cp, g in cmap.items()}

    pair_to_letter: dict[tuple[int, int], str] = {}
    gsub = font.get("GSUB")
    if gsub is None:
        raise RuntimeError("font has no GSUB table")

    for lookup in gsub.table.LookupList.Lookup:
        for sub in lookup.SubTable:
            ligatures = getattr(sub, "ligatures", None)
            if not ligatures:
                continue
            for first_glyph, lig_list in ligatures.items():
                for lig in lig_list:
                    input_glyphs = [first_glyph] + list(lig.Component)
                    if len(input_glyphs) != 2:
                        continue
                    g1, g2 = input_glyphs
                    cp1 = glyph_to_codepoint.get(g1)
                    cp2 = glyph_to_codepoint.get(g2)
                    out_cp = glyph_to_codepoint.get(lig.LigGlyph)
                    if cp1 is None or cp2 is None or out_cp is None:
                        continue
                    pair_to_letter[(cp1, cp2)] = chr(out_cp)
    return pair_to_letter


def decode(encoded: str, font_path: str) -> str:
    table = _load_pair_to_letter(font_path)
    out: list[str] = []
    i, n = 0, len(encoded)
    while i < n:
        cp = ord(encoded[i])
        if 0xE000 <= cp <= 0xF8FF and i + 1 < n:
            pair = (cp, ord(encoded[i + 1]))
            letter = table.get(pair)
            if letter is not None:
                out.append(letter)
                i += 2
                continue
        out.append(encoded[i])
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
