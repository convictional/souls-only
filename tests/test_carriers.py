from cipher import carriers


def test_every_letter_has_one_pair():
    pairs = carriers.ligature_pairs()
    assert set(pairs) == set("abcdefghijklmnopqrstuvwxyz")
    for first, second in pairs.values():
        assert 0xE000 <= first <= 0xF8FF
        assert 0xE000 <= second <= 0xF8FF


def test_pairs_are_unique_across_letters():
    pairs = carriers.ligature_pairs()
    seen = []
    for first, second in pairs.values():
        seen.append(first)
        seen.append(second)
    assert len(seen) == len(set(seen))  # no carrier reused


def test_all_carrier_codepoints_matches_pairs():
    pairs = carriers.ligature_pairs()
    expected = set()
    for first, second in pairs.values():
        expected.add(first)
        expected.add(second)
    assert set(carriers.all_carrier_codepoints()) == expected
    assert carriers.all_carrier_codepoints() == sorted(expected)


def test_glyph_name_scheme():
    assert carriers.carrier_glyph_name(0xE000) == "car_E000"
    assert carriers.carrier_glyph_name(0xE10A) == "car_E10A"
