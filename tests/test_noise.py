import random

from cipher import carriers
from cipher.decode import decode
from cipher.encode import encode


def test_noise_is_dropped_on_decode(built_font_path):
    text = "hello"
    encoded = encode(text, rng=random.Random(11), noise_density=3.0)
    noise = set(carriers.noise_codepoints())
    assert any(ord(c) in noise for c in encoded)  # noise really present
    assert decode(encoded, built_font_path) == text  # and dropped on decode


def test_carrier_frequency_is_flatter_than_letters(built_font_path):
    # 't' is ligature-routed; encoding many 't's spreads across its 6 homophones.
    rng = random.Random(12)
    firsts = set()
    for _ in range(200):
        out = encode("t", rng=rng, noise_density=0.0)
        firsts.add(ord(out[0]))
    assert len(firsts) == 6  # all 6 homophones of 't' get used
