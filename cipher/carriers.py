"""Carrier allocation: the single source of truth for the cipher mapping.

Phase 2 scope: each letter owns a frequency-tiered LIST of carrier pairs
(homophones), so the most common letters have several interchangeable encodings
that flatten carrier frequency. Plus a pool of zero-width noise codepoints the
encoder sprinkles between letters. Phase 3 adds fragment carriers; phase 4 adds
the reveal axis. The encoder, font builder, and decoder all read from here.
"""

from __future__ import annotations

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Two parallel PUA blocks for ligature pairs: a pair is (first-block, second).
LIGA_FIRST_BASE = 0xE000
LIGA_SECOND_BASE = 0xE100

# Zero-width noise pool: a separate PUA block, disjoint from the pair blocks.
NOISE_BASE = 0xE800
NOISE_COUNT = 64

# How many homophones each letter gets, by English frequency. More homophones
# for common letters flattens the carrier-frequency distribution.
_TIERS = {
    "etaoins": 6,
    "rhldcu": 4,
    "mfpgwyb": 2,
    "vkxjqz": 1,
}


def homophone_count(letter: str) -> int:
    """How many carrier pairs a letter is allocated."""
    for letters, count in _TIERS.items():
        if letter in letters:
            return count
    raise KeyError(f"no homophone tier for {letter!r}")


def homophone_pairs() -> dict[str, list[tuple[int, int]]]:
    """Each lowercase letter -> its list of (first, second) carrier pairs.

    Carriers are assigned sequentially across the parallel PUA blocks in
    alphabet order, so allocation is deterministic and collision-free.
    """
    result: dict[str, list[tuple[int, int]]] = {}
    idx = 0
    for ch in ALPHABET:
        pairs: list[tuple[int, int]] = []
        for _ in range(homophone_count(ch)):
            pairs.append((LIGA_FIRST_BASE + idx, LIGA_SECOND_BASE + idx))
            idx += 1
        result[ch] = pairs
    return result


def noise_codepoints() -> list[int]:
    """The pool of zero-width noise carrier codepoints."""
    return [NOISE_BASE + i for i in range(NOISE_COUNT)]


def all_carrier_codepoints() -> list[int]:
    """Every distinct ligature-pair carrier codepoint (excludes noise)."""
    cps: set[int] = set()
    for plist in homophone_pairs().values():
        for first, second in plist:
            cps.add(first)
            cps.add(second)
    return sorted(cps)


def carrier_glyph_name(codepoint: int) -> str:
    """Glyph name for a ligature-pair carrier, e.g. 0xE000 -> 'car_E000'."""
    return f"car_{codepoint:04X}"


def noise_glyph_name(codepoint: int) -> str:
    """Glyph name for a noise carrier, e.g. 0xE800 -> 'noise_E800'."""
    return f"noise_{codepoint:04X}"
