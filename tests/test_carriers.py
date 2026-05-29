from cipher import carriers


def test_homophone_counts_by_tier():
    pairs = carriers.homophone_pairs()
    assert set(pairs) == set("abcdefghijklmnopqrstuvwxyz")
    for ch in "etaoins":
        assert len(pairs[ch]) == 6
    for ch in "rhldcu":
        assert len(pairs[ch]) == 4
    for ch in "mfpgwyb":
        assert len(pairs[ch]) == 2
    for ch in "vkxjqz":
        assert len(pairs[ch]) == 1


def test_total_pair_count():
    pairs = carriers.homophone_pairs()
    total = sum(len(v) for v in pairs.values())
    assert total == 6 * 7 + 4 * 6 + 2 * 7 + 1 * 6  # 86


def test_all_pair_carriers_unique_and_in_pua():
    pairs = carriers.homophone_pairs()
    seen = []
    for plist in pairs.values():
        for first, second in plist:
            seen.extend([first, second])
    assert len(seen) == len(set(seen))  # no carrier reused
    assert all(0xE000 <= cp <= 0xF8FF for cp in seen)


def test_noise_pool_disjoint_from_carriers():
    pairs = carriers.homophone_pairs()
    carrier_cps = {cp for plist in pairs.values() for pr in plist for cp in pr}
    noise = set(carriers.noise_codepoints())
    assert len(noise) == 64
    assert all(0xE000 <= cp <= 0xF8FF for cp in noise)
    assert carrier_cps.isdisjoint(noise)


def test_all_carrier_codepoints_matches_pairs():
    pairs = carriers.homophone_pairs()
    expected = {cp for plist in pairs.values() for pr in plist for cp in pr}
    assert set(carriers.all_carrier_codepoints()) == expected
    assert carriers.all_carrier_codepoints() == sorted(expected)


def test_glyph_name_schemes():
    assert carriers.carrier_glyph_name(0xE000) == "car_E000"
    assert carriers.noise_glyph_name(0xE800) == "noise_E800"
