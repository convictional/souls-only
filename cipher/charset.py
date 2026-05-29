"""Shared charset and half-glyph slot model for the cipher fonts.

Font-agnostic: defines WHICH characters are encoded and how each splits into a
left/right half-glyph slot. The keyboard and (later) PUA fonts each map these
slots to their own carrier encoding. Glyph names are opaque so a table dump
never reveals a slot-to-character mapping.
"""

from __future__ import annotations

LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"  # 32 ASCII symbols
PRINTABLE = LOWER + UPPER + DIGITS + SYMBOLS    # 94
SPACE = " "
CHARSET = PRINTABLE + SPACE                      # 95 (space is encoded)

# A reserved zero-width pad character (used only to pad a newline to 4 slots).
# It is deliberately excluded from the code carrier alphabet so it never forms
# a ligature; it renders as a zero-advance blank and is stripped on decode.
PAD = "\\"

# Characters allowed as code carriers (informational here; the keyboard module
# defines the actual carrier alphabet). PAD and '"' are excluded.
PRINTABLE_CODES_OK = "".join(c for c in PRINTABLE if c not in ('\\', '"'))

# Shared left-half classes: members share one left half-glyph image.
FRAGMENT_CLASSES = {
    "lbowl": "acdegoq",  # lowercase bowl, canonical o
    "lstem": "mnru",     # lowercase stem, canonical n
    "ubowl": "OCGQ",     # uppercase bowl, canonical O
}
CANONICAL = {"lbowl": "o", "lstem": "n", "ubowl": "O"}


def class_of(ch: str) -> str | None:
    for cls, members in FRAGMENT_CLASSES.items():
        if ch in members:
            return cls
    return None


def left_slot(ch: str) -> str:
    if ch == SPACE:
        return "SP_L"
    cls = class_of(ch)
    return f"cls_{cls}" if cls else f"L_{ch}"


def right_slot(ch: str) -> str:
    if ch == SPACE:
        return "SP_R"
    return f"R_{ch}"


def half_slots() -> list[str]:
    """All distinct half-glyph slots, stable order: left slots then right slots."""
    lefts: list[str] = []
    seen: set[str] = set()
    for ch in CHARSET:
        s = left_slot(ch)
        if s not in seen:
            seen.add(s)
            lefts.append(s)
    rights: list[str] = []
    seen_r: set[str] = set()
    for ch in CHARSET:
        s = right_slot(ch)
        if s not in seen_r:
            seen_r.add(s)
            rights.append(s)
    return lefts + rights


def half_glyph_name(slot: str) -> str:
    """Opaque glyph name for a slot (no character leaked)."""
    return f"h_{half_slots().index(slot)}"
