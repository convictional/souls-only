from fontTools.ttLib import TTFont

from cipher import carriers
from fontbuild.features import generate_fea, populate_cmap


def test_generate_fea_has_a_rule_per_homophone(base_font_path):
    font = TTFont(base_font_path)
    fea = generate_fea(font)
    # one ligature rule per homophone pair (86 total)
    assert fea.count("    sub ") == 86
    assert fea.strip().startswith("feature liga {")
    assert fea.strip().endswith("} liga;")


def test_generate_fea_routes_first_homophone_to_base_glyph(base_font_path):
    font = TTFont(base_font_path)
    fea = generate_fea(font)
    pairs = carriers.homophone_pairs()
    h_glyph = font.getBestCmap()[ord("h")]
    first, second = pairs["h"][0]
    g1 = carriers.carrier_glyph_name(first)
    g2 = carriers.carrier_glyph_name(second)
    assert f"sub {g1} {g2} by {h_glyph};" in fea


def test_generate_fea_routes_later_homophones_to_alt_glyphs(base_font_path):
    font = TTFont(base_font_path)
    fea = generate_fea(font)
    pairs = carriers.homophone_pairs()
    e_glyph = font.getBestCmap()[ord("e")]
    first, second = pairs["e"][1]  # second homophone of 'e'
    g1 = carriers.carrier_glyph_name(first)
    g2 = carriers.carrier_glyph_name(second)
    assert f"sub {g1} {g2} by {e_glyph}.alt1;" in fea


def test_populate_cmap_maps_carriers_and_noise(base_font_path):
    font = TTFont(base_font_path)
    populate_cmap(font)
    best = font.getBestCmap()
    for cp in carriers.all_carrier_codepoints():
        assert best.get(cp) == carriers.carrier_glyph_name(cp)
    for cp in carriers.noise_codepoints():
        assert best.get(cp) == carriers.noise_glyph_name(cp)
