"""Carrier allocation: the single source of truth for the cipher mapping.

Phase 1 scope: lowercase a-z, exactly one ligature carrier pair per letter,
deterministic. Phase 2 grows the list-of-carriers shape for homophones; phase 3
adds fragment carriers. Keeping allocation here means the encoder, the font
builder, and the decoder never define the mapping independently.
"""

from __future__ import annotations

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Two parallel PUA blocks. A ligature pair is (first-block cp, second-block cp).
LIGA_FIRST_BASE = 0xE000
LIGA_SECOND_BASE = 0xE100


def ligature_pairs() -> dict[str, tuple[int, int]]:
    """Each lowercase letter -> its one (first, second) carrier pair."""
    return {
        ch: (LIGA_FIRST_BASE + i, LIGA_SECOND_BASE + i)
        for i, ch in enumerate(ALPHABET)
    }


def all_carrier_codepoints() -> list[int]:
    """Every distinct carrier codepoint the font must define a glyph for."""
    cps: set[int] = set()
    for first, second in ligature_pairs().values():
        cps.add(first)
        cps.add(second)
    return sorted(cps)


def carrier_glyph_name(codepoint: int) -> str:
    """Stable glyph name for a carrier codepoint, e.g. 0xE000 -> 'car_E000'."""
    return f"car_{codepoint:04X}"
