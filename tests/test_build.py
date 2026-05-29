from fontTools.ttLib import TTFont

from cipher import carriers


def test_build_produces_loadable_font(built_font_path):
    font = TTFont(built_font_path)
    assert "GSUB" in font


def test_built_font_maps_carriers_and_noise(built_font_path):
    font = TTFont(built_font_path)
    best = font.getBestCmap()
    for cp in carriers.all_carrier_codepoints():
        assert best.get(cp) == carriers.carrier_glyph_name(cp)
    for cp in carriers.noise_codepoints():
        assert best.get(cp) == carriers.noise_glyph_name(cp)


def test_built_font_has_homophone_duplicate_glyphs(built_font_path):
    font = TTFont(built_font_path)
    glyf = font["glyf"]
    e_glyph = font.getBestCmap()[ord("e")]
    assert f"{e_glyph}.alt5" in glyf  # 'e' has 6 homophones -> alt1..alt5


def test_built_font_has_ligature_lookup(built_font_path):
    font = TTFont(built_font_path)
    gsub = font["GSUB"]
    has_ligature = any(
        lookup.LookupType == 4 for lookup in gsub.table.LookupList.Lookup
    )
    assert has_ligature
