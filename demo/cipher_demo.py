"""Single source of truth for the Monday-demo cipher.

This is intentionally separate from src/cipher.py so the demo does not touch the
in-flight PUA font work on the phase-1-rebase-jost branch. It is a throwaway,
self-contained mapping for the live demo only.

Demo cipher (deliberately the simplest scheme that survives a live demo):
  * Each lowercase letter maps to a fixed 3-character ASCII "code" drawn from a
    small alphabet of uncommon letters. Deterministic, no randomness.
  * The keyboard (QMK) emits the code; the demo font's GSUB `liga` rule collapses
    the 3-glyph code back into the one real letter glyph.
  * Because every code is exactly 3 glyphs and the keyboard always emits whole
    codes, the shaper tiles the stream into clean triples with no ambiguity.

Why ASCII (not PUA): a USB HID keyboard can only send positional keycodes, so it
cannot type PUA without host-side Unicode setup. ASCII codes type on any machine
with zero setup, and a homophonic/contextual/noisy version is still illegible to
an LLM. The demo uses the minimal deterministic core of that idea.
"""

from __future__ import annotations

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Uncommon letters so the raw stream looks like obvious garbage. 7 symbols give
# 7**3 = 343 codes, far more than the 26 we need.
CODE_ALPHABET = "kqxzjvw"
CODE_LEN = 3


def demo_map() -> dict[str, str]:
    """Map each lowercase letter to its fixed 3-character code.

    Index i is written as a 3-digit base-7 number over CODE_ALPHABET, so every
    letter gets a distinct code of exactly CODE_LEN characters.
    """
    n = len(CODE_ALPHABET)
    mapping: dict[str, str] = {}
    for i, letter in enumerate(ALPHABET):
        d0 = (i // (n * n)) % n
        d1 = (i // n) % n
        d2 = i % n
        mapping[letter] = CODE_ALPHABET[d0] + CODE_ALPHABET[d1] + CODE_ALPHABET[d2]
    return mapping


def _self_check() -> None:
    m = demo_map()
    assert len(m) == 26, "expected 26 letters"
    assert len(set(m.values())) == 26, "codes must be unique"
    assert all(len(c) == CODE_LEN for c in m.values()), "all codes same length"
    assert all(ch in CODE_ALPHABET for c in m.values() for ch in c), "code alphabet"


_self_check()


if __name__ == "__main__":
    for letter, code in demo_map().items():
        print(f"{letter} -> {code}")
