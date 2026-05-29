"""Keyboard-typeable ASCII encoding for Souls Only (Phase 5).

This is a refactor on top of the existing cipher, NOT a second implementation:
it reuses the fragment routing from cipher.carriers (ALPHABET,
FRAGMENT_CLASSES, fragment_class_of) and the slicing engine in
fontbuild.fragments. The only new idea here is the carrier *encoding*: every
half-glyph is addressed by a pool of short ASCII codes a USB keyboard can type,
instead of a single PUA codepoint.

Model:
  * Every letter renders as two half-glyphs: a left (shared across a fragment
    class, else the letter's own) and a right (always the letter's own). This is
    exactly the fragment routing from carriers.py, extended to all letters.
  * Each half-glyph owns a pool of CODE_LEN-char ASCII codes (homophones). A
    letter is typed as (random left code) + (random right code) = 2 * CODE_LEN
    characters, so it looks different in the byte stream every time.
  * The font collapses each code into its half-glyph via a GSUB ligature; the
    halves tile into the letter. Glyph names are opaque, so a table dump never
    reveals a code-to-letter mapping.
"""

from __future__ import annotations

import random

from cipher.carriers import ALPHABET, fragment_class_of

CODE_ALPHABET = "!#$%&*+=?@23456789"  # symbols + digits: typeable, noisy
CODE_LEN = 2
HOMOPHONES = 4  # interchangeable codes per half-glyph


def left_slot(letter: str) -> str:
    """Left half-glyph identity: shared per fragment class, else the letter's own."""
    cls = fragment_class_of(letter)
    return f"cls_{cls}" if cls else f"L_{letter}"


def right_slot(letter: str) -> str:
    return f"R_{letter}"


def half_slots() -> list[str]:
    """All distinct half-glyph slots, stable order: left slots then right slots."""
    lefts: list[str] = []
    seen: set[str] = set()
    for ch in ALPHABET:
        s = left_slot(ch)
        if s not in seen:
            seen.add(s)
            lefts.append(s)
    return lefts + [right_slot(ch) for ch in ALPHABET]


def half_glyph_name(slot: str) -> str:
    """Opaque glyph name for a half-glyph slot (no letter leaked)."""
    return f"kf_{half_slots().index(slot)}"


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


def code_to_letter() -> dict[str, str]:
    """Decoder map: a RIGHT code identifies the letter (right half is unique)."""
    return {code: letter for letter in ALPHABET for code in right_codes(letter)}


def carrier_glyph_name(ch: str) -> str:
    """Glyph name for one code-alphabet character carrier."""
    return f"kc_{ord(ch):04X}"


def encode(text: str, rng: random.Random | None = None) -> str:
    """Plaintext -> ASCII code stream. Each letter -> random left+right codes."""
    if rng is None:
        rng = random.Random()
    out: list[str] = []
    for ch in text:
        if ch in ALPHABET:
            out.append(rng.choice(left_codes(ch)))
            out.append(rng.choice(right_codes(ch)))
        else:
            out.append(ch)
    return "".join(out)


def decode(encoded: str) -> str:
    """ASCII code stream -> plaintext, using the cipher tables (the font carries
    no code-to-letter mapping, by design)."""
    to_letter = code_to_letter()
    codeset = set(CODE_ALPHABET)
    out: list[str] = []
    i, n = 0, len(encoded)
    while i < n:
        # A letter is a left code then a right code, each CODE_LEN chars.
        if encoded[i] in codeset and i + 2 * CODE_LEN <= n:
            right_code = encoded[i + CODE_LEN:i + 2 * CODE_LEN]
            letter = to_letter.get(right_code)
            if letter is not None and all(c in codeset for c in encoded[i:i + 2 * CODE_LEN]):
                out.append(letter)
                i += 2 * CODE_LEN
                continue
        out.append(encoded[i])
        i += 1
    return "".join(out)
