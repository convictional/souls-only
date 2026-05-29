from fontTools.ttLib import TTFont


def test_space_half_glyphs_are_blank_and_tile_to_space_width(base_font_path):
    from fontbuild.fragments import space_half_glyphs
    font = TTFont(base_font_path)
    space_w = font["hmtx"][font.getBestCmap()[ord(" ")]][0]
    (lg, ladv), (rg, radv) = space_half_glyphs(font)
    assert lg.numberOfContours == 0 and rg.numberOfContours == 0
    assert ladv + radv == space_w


def test_pad_glyph_is_zero_advance_blank(base_font_path):
    from fontbuild.fragments import pad_glyph
    g, adv = pad_glyph()
    assert g.numberOfContours == 0
    assert adv == 0
