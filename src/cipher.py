"""The cipher mapping: the single source of truth for both halves of the system.

The brief is explicit that the encoder's pair tables and the font's ligature
rules are "the same secret expressed twice" and must stay in sync. To guarantee
that, both the Python encoder (encode.py) and the font builder (build_font.py)
import the tables from this one module. Nothing else defines the mapping.

Milestone 1 scope (deliberately minimal, per the brief's first milestone):
  * lowercase a-z only
  * each letter maps to exactly ONE codepoint pair (deterministic, no
    homophonic randomness yet)
  * everything else (spaces, punctuation, digits, uppercase) passes through
    unchanged

The structure is already shaped for what comes next: each letter owns a *list*
of pairs, so layering in multiple homophones per letter (Scheme A) later means
appending to these lists, with no change to the font-build or decode logic.
"""

from __future__ import annotations

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Two disjoint blocks inside the Unicode Private Use Area (U+E000..U+F8FF).
# A plaintext letter is encoded as one "high" codepoint followed by one "low"
# codepoint. Using a pair (not a single codepoint) is the whole point: a GSUB
# ligature collapses the two-codepoint input into one visible glyph, so the
# stored codepoint count and the rendered glyph count deliberately diverge.
PUA_FIRST_BASE = 0xE000  # first codepoint of each pair lives here
PUA_SECOND_BASE = 0xE100  # second codepoint of each pair lives here


def letter_to_pairs() -> dict[str, list[tuple[int, int]]]:
    """Map each lowercase letter to its list of allowed codepoint pairs.

    Milestone 1: exactly one pair per letter. The list-of-pairs shape is what
    future homophonic encoding will grow into.
    """
    mapping: dict[str, list[tuple[int, int]]] = {}
    for i, ch in enumerate(ALPHABET):
        mapping[ch] = [(PUA_FIRST_BASE + i, PUA_SECOND_BASE + i)]
    return mapping


def all_pairs() -> list[tuple[int, int]]:
    """Every codepoint pair the cipher can emit, across all letters."""
    pairs: list[tuple[int, int]] = []
    for letter_pairs in letter_to_pairs().values():
        pairs.extend(letter_pairs)
    return pairs


def all_pua_codepoints() -> list[int]:
    """Every distinct PUA codepoint the font must define a glyph for."""
    seen: set[int] = set()
    for first, second in all_pairs():
        seen.add(first)
        seen.add(second)
    return sorted(seen)


def pair_to_letter() -> dict[tuple[int, int], str]:
    """Reverse map: a codepoint pair -> the plaintext letter it renders as.

    Used by the decoder/round-trip harness. With homophones this stays a clean
    many-pairs-to-one-letter map.
    """
    reverse: dict[tuple[int, int], str] = {}
    for letter, pairs in letter_to_pairs().items():
        for pair in pairs:
            reverse[pair] = letter
    return reverse


def pua_glyph_name(codepoint: int) -> str:
    """Stable glyph name for a PUA codepoint, e.g. 0xE000 -> 'pua_E000'.

    Both the font builder and the decoder derive glyph names this way so they
    never have to be listed twice.
    """
    return f"pua_{codepoint:04X}"
