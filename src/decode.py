"""Private decoder / verification utility.

This reverses the cipher using ONLY the font's own tables (cmap + GSUB
ligatures), not cipher.py. That is the point: if the font can independently
turn an encoded stream back into the original plaintext, then the font's rules
and the encoder's tables genuinely agree, i.e. "the same secret expressed
twice" really is in sync.

The brief notes a real adversary could do exactly this in ~20 lines of Python;
this file is that adversary, kept on hand as a test oracle.

    python src/decode.py < encoded.txt
"""

from __future__ import annotations

import sys

from fontTools.ttLib import TTFont


def load_pair_to_letter(font_path: str) -> dict[tuple[int, int], str]:
    """Reconstruct {(cp1, cp2): letter} from the font alone.

    1. Read cmap to learn which glyph each PUA codepoint maps to.
    2. Read GSUB type-4 (ligature) lookups to learn which glyph pairs collapse
       into which output glyph.
    3. Read cmap again (reversed) to learn which letter the output glyph draws.
    """
    font = TTFont(font_path)
    cmap = font.getBestCmap()  # codepoint -> glyph name
    glyph_to_codepoint = {g: cp for cp, g in cmap.items()}

    pair_to_letter: dict[tuple[int, int], str] = {}
    gsub = font.get("GSUB")
    if gsub is None:
        raise RuntimeError("font has no GSUB table")

    for lookup in gsub.table.LookupList.Lookup:
        for sub in lookup.SubTable:
            # LookupType 4 == ligature substitution.
            ligatures = getattr(sub, "ligatures", None)
            if not ligatures:
                continue
            for first_glyph, lig_list in ligatures.items():
                for lig in lig_list:
                    # Full input sequence = first glyph + the component glyphs.
                    input_glyphs = [first_glyph] + list(lig.Component)
                    if len(input_glyphs) != 2:
                        continue  # milestone 1 only uses 2-glyph pairs
                    out_glyph = lig.LigGlyph
                    g1, g2 = input_glyphs
                    cp1 = glyph_to_codepoint.get(g1)
                    cp2 = glyph_to_codepoint.get(g2)
                    if cp1 is None or cp2 is None:
                        continue
                    # The output glyph's letter = whatever codepoint maps to it.
                    out_cp = glyph_to_codepoint.get(out_glyph)
                    if out_cp is None:
                        continue
                    pair_to_letter[(cp1, cp2)] = chr(out_cp)
    return pair_to_letter


def decode(encoded: str, font_path: str) -> str:
    """Turn an encoded PUA stream back into plaintext using the font."""
    table = load_pair_to_letter(font_path)
    out: list[str] = []
    i = 0
    n = len(encoded)
    while i < n:
        ch = encoded[i]
        cp = ord(ch)
        # Try to consume a PUA pair.
        if 0xE000 <= cp <= 0xF8FF and i + 1 < n:
            pair = (cp, ord(encoded[i + 1]))
            letter = table.get(pair)
            if letter is not None:
                out.append(letter)
                i += 2
                continue
        # Not part of a known pair: pass through (space, punctuation, etc.).
        out.append(ch)
        i += 1
    return "".join(out)


def main(argv: list[str]) -> int:
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    default_font = os.path.join(os.path.dirname(here), "build", "SoulsOnly.ttf")
    font_path = argv[1] if len(argv) > 1 else default_font
    encoded = sys.stdin.read().rstrip("\n")
    sys.stdout.write(decode(encoded, font_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
