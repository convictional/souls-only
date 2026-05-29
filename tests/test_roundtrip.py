import pytest

from cipher.decode import decode
from cipher.encode import encode

SAMPLES = [
    "hello",
    "hello world",
    "the quick brown fox jumps over the lazy dog",
    "a",
    "abcdefghijklmnopqrstuvwxyz",
]


@pytest.mark.parametrize("sample", SAMPLES)
def test_roundtrip_through_font_tables(sample, built_font_path):
    encoded = encode(sample)
    assert decode(encoded, built_font_path) == sample


@pytest.mark.parametrize("sample", SAMPLES)
def test_stream_is_pua_garbage(sample, built_font_path):
    encoded = encode(sample)
    letters = [c for c in sample if c.isalpha()]
    pua = [c for c in encoded if 0xE000 <= ord(c) <= 0xF8FF]
    assert len(pua) == 2 * len(letters)
    assert not any(c.isalpha() for c in encoded)
