"""Round-trip test harness: plaintext -> encode -> decode -> plaintext.

Two independent checks per sample:
  1. decode-via-font: reverse the encoded stream using ONLY the built font's
     tables (decode.py). Proves the font's GSUB/cmap actually reconstruct the
     letters, i.e. the rendering layer is the decoder.
  2. stream-is-garbage: assert the encoded letters became PUA codepoints, so the
     stored stream genuinely differs from the plaintext.

Run:
    python test/roundtrip.py
Exit code 0 on success, 1 on any failure.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from decode import decode  # noqa: E402
from encode import encode  # noqa: E402

FONT = os.path.join(ROOT, "build", "SoulsOnly.ttf")

SAMPLES = [
    "hello",
    "hello world",
    "the quick brown fox jumps over the lazy dog",
    "a",
    "abcdefghijklmnopqrstuvwxyz",
    "this is a statement piece, not unbreakable.",  # punctuation passes through
]


def is_pua(ch: str) -> bool:
    return 0xE000 <= ord(ch) <= 0xF8FF


def run() -> int:
    failures = 0
    for sample in SAMPLES:
        encoded = encode(sample)
        decoded = decode(encoded, FONT)

        # Check 1: the font reconstructs the original plaintext.
        if decoded != sample:
            print(f"FAIL round-trip: {sample!r} -> {decoded!r}")
            failures += 1
            continue

        # Check 2: every plaintext letter is now stored as PUA garbage.
        letters = [c for c in sample if c.isalpha()]
        pua_in_stream = [c for c in encoded if is_pua(c)]
        if letters and len(pua_in_stream) != 2 * len(letters):
            print(f"FAIL garbage: {sample!r} has {len(letters)} letters but "
                  f"{len(pua_in_stream)} PUA codepoints (expected {2*len(letters)})")
            failures += 1
            continue

        # Check 3: no plaintext letter survives verbatim in the stream.
        leaked = [c for c in encoded if c.isalpha()]
        if leaked:
            print(f"FAIL leak: {sample!r} leaked letters {leaked!r} into stream")
            failures += 1
            continue

        print(f"ok  {sample!r}  ({len(sample)} chars -> {len(encoded)} codepoints)")

    if failures:
        print(f"\n{failures} failure(s)")
        return 1
    print(f"\nall {len(SAMPLES)} samples passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
