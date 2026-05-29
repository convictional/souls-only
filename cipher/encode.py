"""Encoder: plaintext -> carrier codepoint stream.

Phase 1: lowercase a-z -> the single ligature pair for that letter; every other
character passes through unchanged. The encoder emits only carriers, never real
letters.
"""

from __future__ import annotations

import sys

from cipher.carriers import homophone_pairs


def encode(text: str) -> str:
    pairs = {k: v[0] for k, v in homophone_pairs().items()}
    out: list[str] = []
    for ch in text:
        pair = pairs.get(ch)
        if pair is None:
            out.append(ch)
            continue
        first, second = pair
        out.append(chr(first))
        out.append(chr(second))
    return "".join(out)


def main(argv: list[str]) -> int:
    text = " ".join(argv[1:]) if len(argv) > 1 else sys.stdin.read().rstrip("\n")
    sys.stdout.write(encode(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
