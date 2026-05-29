import random

from cipher import carriers
from cipher.encode import encode


def test_each_letter_encodes_to_one_of_its_homophone_pairs():
    pairs = carriers.homophone_pairs()
    # No noise, deterministic rng: every 'e' maps to one of e's 6 pairs.
    rng = random.Random(0)
    out = encode("e", rng=rng, noise_density=0.0)
    cp1, cp2 = ord(out[0]), ord(out[1])
    assert (cp1, cp2) in pairs["e"]


def test_no_noise_means_two_carriers_per_letter():
    out = encode("hello", rng=random.Random(1), noise_density=0.0)
    assert len(out) == 10  # 5 letters x 2 carriers, no noise


def test_homophones_vary_across_occurrences():
    # 'e' has 6 homophones; over many encodes we should see more than one pair.
    rng = random.Random(2)
    seen = set()
    for _ in range(50):
        out = encode("e", rng=rng, noise_density=0.0)
        seen.add((ord(out[0]), ord(out[1])))
    assert len(seen) > 1  # not always the same homophone


def test_noise_codepoints_are_inserted():
    noise = set(carriers.noise_codepoints())
    out = encode("hello world", rng=random.Random(3), noise_density=1.0)
    assert any(ord(c) in noise for c in out)


def test_no_letter_leaks_into_stream():
    out = encode("the quick brown fox", rng=random.Random(4), noise_density=0.5)
    assert not any(c.isalpha() for c in out)
