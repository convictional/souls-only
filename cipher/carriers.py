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


# --- Phase 3: shared-ambiguous fragment scheme ---
#
# Letters in a fragment class render as two tiling half-glyphs composed purely
# through cmap (no GSUB rule), so the font tables never document the
# fragment->letter mapping. All members of a class share ONE canonical left
# fragment image (the unit of ambiguity); each member has its own right
# fragment. Glyph names are deliberately opaque (no letter), so a table dump
# reveals only meaningless half-shapes. The fragment->letter knowledge lives
# only here, in the cipher tables.
FRAGMENT_CLASSES = {
    "bowl": "acdegoq",  # shared round left bowl
    "stem": "mnru",     # shared x-height left stem
}

# Fragment carriers come in homophone pools too, so frequency stays flat even
# for the common letters that route through fragments. Every left carrier in a
# class maps (in cmap) to the same shared left glyph; every right carrier for a
# letter maps to that letter's one right glyph. The image is unchanged; only the
# stored codepoint varies.
FRAG_LEFT_BASE = 0xE900    # left-fragment carriers (homophone pool per class)
FRAG_RIGHT_BASE = 0xEA00   # right-fragment carriers (homophone pool per letter)
FRAG_LEFT_HOMOPHONES = 6   # interchangeable left carriers per class
FRAG_RIGHT_HOMOPHONES = 4  # interchangeable right carriers per fragment letter


def fragment_letters() -> str:
    """All letters routed through the fragment path, sorted, deduplicated."""
    return "".join(sorted(set("".join(FRAGMENT_CLASSES.values()))))


def fragment_class_of(letter: str) -> str | None:
    """The class a letter belongs to, or None if it is ligature-routed."""
    for cls, members in FRAGMENT_CLASSES.items():
        if letter in members:
            return cls
    return None


def _class_index(cls: str) -> int:
    return list(FRAGMENT_CLASSES).index(cls)


def left_carriers(cls: str) -> list[int]:
    """The shared left-fragment carrier pool (homophones) for a class."""
    base = FRAG_LEFT_BASE + _class_index(cls) * FRAG_LEFT_HOMOPHONES
    return [base + k for k in range(FRAG_LEFT_HOMOPHONES)]


def right_carriers(letter: str) -> list[int]:
    """The right-fragment carrier pool (homophones) for a fragment letter."""
    base = FRAG_RIGHT_BASE + fragment_letters().index(letter) * FRAG_RIGHT_HOMOPHONES
    return [base + k for k in range(FRAG_RIGHT_HOMOPHONES)]


def fragment_carrier_codepoints() -> list[int]:
    """Every fragment carrier codepoint (left pools per class, right pools per letter)."""
    cps: list[int] = []
    for cls in FRAGMENT_CLASSES:
        cps += left_carriers(cls)
    for letter in fragment_letters():
        cps += right_carriers(letter)
    return sorted(cps)


def left_fragment_glyph_name(cls: str) -> str:
    """Opaque glyph name for a class's shared left fragment (no letter leaked)."""
    return f"fragL_{_class_index(cls)}"


def right_fragment_glyph_name(letter: str) -> str:
    """Opaque glyph name for a letter's right fragment (no letter leaked)."""
    return f"fragR_{fragment_letters().index(letter)}"


def left_carrier_to_class() -> dict[int, str]:
    """Reverse map: any left carrier -> its class."""
    return {cp: cls for cls in FRAGMENT_CLASSES for cp in left_carriers(cls)}


def right_carrier_to_letter() -> dict[int, str]:
    """Reverse map used by the decoder: any right carrier -> its letter."""
    return {cp: letter for letter in fragment_letters() for cp in right_carriers(letter)}
