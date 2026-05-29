import random

import pytest

from cipher.decode import decode
from cipher.encode import encode

SAMPLES = [
    "hello",
    "hello world",
    "the quick brown fox jumps over the lazy dog",
    "a",
    "abcdefghijklmnopqrstuvwxyz",
    "ee ee ee",  # repeated high-homophone letter
]


@pytest.mark.parametrize("sample", SAMPLES)
def test_roundtrip_no_noise(sample, built_font_path):
    encoded = encode(sample, rng=random.Random(7), noise_density=0.0)
    assert decode(encoded, built_font_path) == sample


@pytest.mark.parametrize("sample", SAMPLES)
def test_roundtrip_with_noise(sample, built_font_path):
    encoded = encode(sample, rng=random.Random(8), noise_density=2.0)
    assert decode(encoded, built_font_path) == sample


@pytest.mark.parametrize("seed", range(10))
def test_roundtrip_many_random_streams(seed, built_font_path):
    text = "the quick brown fox"
    encoded = encode(text, rng=random.Random(seed), noise_density=1.5)
    assert decode(encoded, built_font_path) == text
