"""Encoder: plaintext -> carrier codepoint stream.

Phase 2: each lowercase letter is encoded as a RANDOMLY chosen homophone pair
(flattening carrier frequency), and zero-width noise codepoints are sprinkled
between letters (wrecking pair-adjacency and tokenization analysis). Noise is
never placed inside a pair, which would break the GSUB ligature adjacency. The
encoder emits only carriers and noise, never real letters.
"""

from __future__ import annotations

import random
import sys

from cipher.carriers import homophone_pairs, noise_codepoints


def _emit_noise(out: list[str], rng: random.Random, noise_density: float,
                noise_pool: list[int]) -> None:
    """Append zero or more noise codepoints based on density.

    noise_density is the expected number of noise codepoints to emit at this
    boundary: the integer part is always emitted, the fractional part is a
    probability for one more.
    """
    n = int(noise_density)
    if rng.random() < (noise_density - n):
        n += 1
    for _ in range(n):
        out.append(chr(rng.choice(noise_pool)))


def encode(text: str, rng: random.Random | None = None,
           noise_density: float = 0.5) -> str:
    """Encode plaintext into the carrier + noise stream.

    rng: optional Random for deterministic tests; defaults to a fresh Random.
    noise_density: expected noise codepoints emitted between adjacent letters.
    """
    if rng is None:
        rng = random.Random()
    pairs = homophone_pairs()
    noise_pool = noise_codepoints()

    out: list[str] = []
    prev_was_letter = False
    for ch in text:
        plist = pairs.get(ch)
        if plist is None:
            out.append(ch)
            prev_was_letter = False
            continue
        # Noise goes BETWEEN letters, never inside a pair.
        if prev_was_letter:
            _emit_noise(out, rng, noise_density, noise_pool)
        first, second = rng.choice(plist)
        out.append(chr(first))
        out.append(chr(second))
        prev_was_letter = True
    return "".join(out)


def main(argv: list[str]) -> int:
    text = " ".join(argv[1:]) if len(argv) > 1 else sys.stdin.read().rstrip("\n")
    sys.stdout.write(encode(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
