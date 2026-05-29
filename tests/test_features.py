from fontTools.ttLib import TTFont

from cipher import carriers
from fontbuild.features import generate_fea, populate_cmap


def test_generate_fea_has_a_rule_per_letter(base_font_path):
    font = TTFont(base_font_path)
    fea = generate_fea(font)
    assert fea.count("    sub ") == 26  # one ligature rule per letter
    assert fea.strip().startswith("feature liga {")
    assert fea.strip().endswith("} liga;")


def test_generate_fea_uses_carrier_glyph_names(base_font_path):
    font = TTFont(base_font_path)
    fea = generate_fea(font)
    first, second = carriers.ligature_pairs()["h"]
    g1 = carriers.carrier_glyph_name(first)
    g2 = carriers.carrier_glyph_name(second)
    h_glyph = font.getBestCmap()[ord("h")]
    assert f"sub {g1} {g2} by {h_glyph};" in fea


def test_populate_cmap_maps_every_carrier(base_font_path):
    font = TTFont(base_font_path)
    populate_cmap(font)
    best = font.getBestCmap()
    for cp in carriers.all_carrier_codepoints():
        assert best.get(cp) == carriers.carrier_glyph_name(cp)
