"""Encoder: plaintext -> obfuscated PUA codepoint stream.

This is the half of the cipher that produces the "garbage" stored bytes. The
font's GSUB rules (build_font.py) are the half that visually reconstructs the
truth. Both read their tables from cipher.py.

Usage:
    python src/encode.py "hello world"
    echo "hello world" | python src/encode.py
"""

from __future__ import annotations

import sys

from cipher import letter_to_pairs


def encode(text: str) -> str:
    """Encode plaintext into the PUA codepoint stream.

    Milestone 1 behaviour:
      * lowercase a-z -> the single codepoint pair for that letter
      * every other character passes through unchanged (spaces, punctuation,
        digits, and uppercase are not yet obfuscated)
    """
    mapping = letter_to_pairs()
    out: list[str] = []
    for ch in text:
        pairs = mapping.get(ch)
        if pairs is None:
            out.append(ch)
            continue
        # Milestone 1: deterministic, always the first (only) pair.
        first, second = pairs[0]
        out.append(chr(first))
        out.append(chr(second))
    return "".join(out)


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        text = " ".join(argv[1:])
    else:
        text = sys.stdin.read().rstrip("\n")
    sys.stdout.write(encode(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
