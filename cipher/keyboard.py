"""Keyboard-typeable ASCII encoding for Souls Only (Phase 5).

Uses cipher.charset for the full printable charset (letters, digits, symbols,
space) with a grown ASCII carrier alphabet. The only new idea over the PUA
cipher is the carrier *encoding*: every half-glyph is addressed by a pool of
short ASCII codes a USB keyboard can type, instead of a single PUA codepoint.

Model:
  * Every character in the charset renders as two half-glyphs: a left (shared
    across a fragment class for certain letter groups, else the character's own)
    and a right (always the character's own).
  * Each half-glyph owns a pool of CODE_LEN-char ASCII codes (homophones). A
    character is typed as (random left code) + (random right code) = 2 *
    CODE_LEN characters, so it looks different in the byte stream every time.
  * The font collapses each code into its half-glyph via a GSUB ligature; the
    halves tile into the character. Glyph names are opaque, so a table dump
    never reveals a code-to-character mapping.
"""

from __future__ import annotations

import random

from cipher import charset

# Carrier alphabet: the 10 digits plus the ASCII symbols EXCEPT " and \ (those
# would need escaping in the generated C and JS; \ is reserved as the pad char).
# 40 characters -> 1600 two-char codes, covering ~178 slots x HOMOPHONES.
CODE_ALPHABET = charset.DIGITS + "".join(
    c for c in charset.SYMBOLS if c not in ('"', "\\")
)
CODE_LEN = 2
HOMOPHONES = 4  # interchangeable codes per half-glyph

left_slot = charset.left_slot
right_slot = charset.right_slot
half_slots = charset.half_slots
half_glyph_name = charset.half_glyph_name


def _all_codes() -> list[str]:
    if CODE_LEN != 2:
        raise NotImplementedError("code generation assumes CODE_LEN == 2")
    return [a + b for a in CODE_ALPHABET for b in CODE_ALPHABET]


def slot_codes() -> dict[str, list[str]]:
    """Each half-glyph slot -> its pool of HOMOPHONES distinct codes."""
    slots = half_slots()
    codes = _all_codes()
    need = len(slots) * HOMOPHONES
    if need > len(codes):
        raise RuntimeError(f"need {need} codes, only {len(codes)} available")
    return {s: codes[i * HOMOPHONES:(i + 1) * HOMOPHONES]
            for i, s in enumerate(slots)}


def left_codes(letter: str) -> list[str]:
    return slot_codes()[left_slot(letter)]


def right_codes(letter: str) -> list[str]:
    return slot_codes()[right_slot(letter)]


def code_to_char() -> dict[str, str]:
    """Decoder map: a RIGHT code identifies the character (right half is unique)."""
    return {code: ch for ch in charset.CHARSET for code in right_codes(ch)}


def carrier_glyph_name(ch: str) -> str:
    """Glyph name for one code-alphabet character carrier."""
    return f"kc_{ord(ch):04X}"


def encode(text: str, rng: random.Random | None = None) -> str:
    """Plaintext -> stream. Each printable char and space -> random left+right
    codes (4 carrier chars). Newline -> a real newline plus 3 pad chars. Other
    characters (tab, non-ASCII) pass through unchanged."""
    if rng is None:
        rng = random.Random()
    out: list[str] = []
    for ch in text:
        if ch == "\n":
            out.append("\n")
            out.append(charset.PAD * 3)
        elif ch in charset.CHARSET:
            out.append(rng.choice(left_codes(ch)))
            out.append(rng.choice(right_codes(ch)))
        else:
            out.append(ch)
    return "".join(out)


def decode(encoded: str) -> str:
    """Stream -> plaintext. Pads are stripped; real newlines pass through; a
    right code identifies its character via the cipher tables."""
    to_char = code_to_char()
    codeset = set(CODE_ALPHABET)
    cleaned = encoded.replace(charset.PAD, "")  # drop pad chars
    out: list[str] = []
    i, n = 0, len(cleaned)
    while i < n:
        ch = cleaned[i]
        if ch in codeset and i + 2 * CODE_LEN <= n \
                and all(c in codeset for c in cleaned[i:i + 2 * CODE_LEN]):
            right_code = cleaned[i + CODE_LEN:i + 2 * CODE_LEN]
            mapped = to_char.get(right_code)
            if mapped is not None:
                out.append(mapped)
                i += 2 * CODE_LEN
                continue
        out.append(ch)
        i += 1
    return "".join(out)
