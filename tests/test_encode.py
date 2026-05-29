from cipher import carriers
from cipher.encode import encode


def test_letters_become_their_pair():
    pairs = carriers.ligature_pairs()
    first, second = pairs["h"]
    assert encode("h") == chr(first) + chr(second)


def test_two_codepoints_per_letter():
    assert len(encode("hello")) == 10  # 5 letters x 2 carriers


def test_non_letters_pass_through():
    out = encode("a b")
    # middle char is the original space, untouched
    assert " " in out
    assert len(out) == 2 + 1 + 2  # a(2) + space(1) + b(2)


def test_no_letter_leaks_into_stream():
    out = encode("the quick brown fox")
    assert not any(c.isalpha() for c in out)


def test_uppercase_digits_punctuation_pass_through():
    out = encode("Hi 9!")
    # 'H', ' ', '9', '!' pass through unchanged; only lowercase 'i' is encoded.
    assert "H" in out and "9" in out and "!" in out and " " in out
    # exactly one lowercase letter ('i') -> 2 PUA carriers, rest pass through
    pua = [c for c in out if 0xE000 <= ord(c) <= 0xF8FF]
    assert len(pua) == 2
