"""Per-focal-point decoy substitution mappings for the REVL axis.

Each decoy focal point k renders every character as a DIFFERENT real
character, so a scrubber (or an OCR pass) reads confident glyphs at every
focal point and cannot tell which one carries the message. A mapping must
respect the shared-left-half model from cipher.charset: all members of a
fragment class share ONE left glyph, so the whole class maps into a single
target class (whose canonical left half that glyph wears at that focal).

Font-agnostic and deterministic: the same (k, seed) always yields the same
mapping, so font rebuilds are reproducible.
"""

from __future__ import annotations

import random

from cipher import charset

DECOY_SEED = 20260609

# Where shared-class members land. The lowercase bowl (a c d e g o q) slices
# cleanly AND is lowercase, so routing every shared class here keeps decoys
# looking like a normal lowercase message. (The lowercase stem m n r u does
# NOT slice cleanly -- its shared left is a degenerate sliver -- so it is never
# a target; as a SOURCE it maps into the bowl like the others.)
_BOWL = charset.FRAGMENT_CLASSES["lbowl"]          # "acdegoq"
_STEM = frozenset(charset.FRAGMENT_CLASSES["lstem"])

# Per-category target pools so a decoy reads like real text: letters become
# lowercase letters, digits stay digits, symbols stay symbols. Stems are
# excluded from letter targets (degenerate left); the two carrier-reserved
# symbols (" and \) are excluded from symbol targets.
_LOWER_TARGETS = [c for c in charset.LOWER if c not in _STEM]   # 22 letters
_DIGIT_TARGETS = list(charset.DIGITS)
_SYMBOL_TARGETS = [c for c in charset.SYMBOLS if c not in ('"', "\\")]


def _pick_distinct(rng: random.Random, members: str, pool: list[str]) -> list[str]:
    """A distinct target per member (no reuse), none equal to its own member."""
    for _ in range(200):
        picks = rng.sample(pool, len(members))
        if all(p != m for p, m in zip(members, picks)):
            return picks
    return rng.sample(pool, len(members))  # fallback (vanishingly unlikely)


def focal_mapping(k: int, seed: int = DECOY_SEED) -> dict[str, str]:
    """Substitution mapping for decoy focal k: char -> impersonated char.

    Designed so a decoy reads like an ordinary lowercase message:
      * Every shared class maps into the lowercase bowl, each member to a
        DISTINCT bowl letter (the one shared left half is the correct left for
        all of them, so each tiles into a real lowercase letter).
      * Unshared letters map to distinct lowercase letters; digits to digits;
        symbols to symbols -- keeping word shapes, numbers, and punctuation.
    Every target tiles cleanly (no degenerate stem ever reaches the screen),
    and nothing maps to itself, so the decoy never leaks the true character.
    """
    rng = random.Random(seed * 1000003 + k)
    mapping: dict[str, str] = {}  # space is never ciphered, so never mapped

    for members in charset.FRAGMENT_CLASSES.values():
        for ch, tgt in zip(members, _pick_distinct(rng, members, _BOWL)):
            mapping[ch] = tgt

    # Unshared characters: map within their own category, distinct per category
    # where the pool allows, never to themselves.
    used: dict[int, set[str]] = {}
    for ch in charset.CHARSET:
        if ch in mapping:
            continue
        if ch.isalpha():
            pool = _LOWER_TARGETS
        elif ch.isdigit():
            pool = _DIGIT_TARGETS
        else:
            pool = _SYMBOL_TARGETS
        seen = used.setdefault(id(pool), set())
        choices = [c for c in pool if c != ch and c not in seen] or \
                  [c for c in pool if c != ch]
        tgt = rng.choice(choices)
        seen.add(tgt)
        mapping[ch] = tgt
    return mapping
