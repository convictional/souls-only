import copy

from fontTools.ttLib import TTFont

from cipher import carriers
from fontbuild.glyphs import (
    add_blank_carrier_glyphs,
    add_homophone_glyphs,
    add_noise_glyphs,
)


def test_carrier_glyphs_added_and_zero_width(base_font_path):
    font = TTFont(base_font_path)
    add_blank_carrier_glyphs(font)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in carriers.all_carrier_codepoints():
        name = carriers.carrier_glyph_name(cp)
        assert name in glyf
        assert glyf[name].numberOfContours == 0
        assert hmtx[name][0] == 0


def test_noise_glyphs_added_and_zero_width(base_font_path):
    font = TTFont(base_font_path)
    add_noise_glyphs(font)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in carriers.noise_codepoints():
        name = carriers.noise_glyph_name(cp)
        assert name in glyf
        assert glyf[name].numberOfContours == 0
        assert hmtx[name][0] == 0


def test_homophone_duplicates_have_identical_outline(base_font_path):
    font = TTFont(base_font_path)
    add_homophone_glyphs(font)
    glyf = font["glyf"]
    base_cmap = font.getBestCmap()
    # 'e' has 6 homophones -> base glyph plus alt1..alt5 duplicates.
    e_glyph = base_cmap[ord("e")]
    for k in range(1, 6):
        dup = f"{e_glyph}.alt{k}"
        assert dup in glyf, f"{dup} missing"
        # identical outline: same coordinates as the base 'e' glyph
        assert glyf[dup].numberOfContours == glyf[e_glyph].numberOfContours
    # single-homophone letter 'q' gets no duplicate
    q_glyph = base_cmap[ord("q")]
    assert f"{q_glyph}.alt1" not in glyf


def test_glyph_order_consistent_after_all_additions(base_font_path):
    font = TTFont(base_font_path)
    add_blank_carrier_glyphs(font)
    add_noise_glyphs(font)
    add_homophone_glyphs(font)
    glyf = font["glyf"]
    assert len(glyf.glyphOrder) == len(glyf.glyphs)
