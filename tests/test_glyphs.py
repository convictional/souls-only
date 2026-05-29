from fontTools.ttLib import TTFont

from cipher import carriers
from fontbuild.glyphs import add_blank_carrier_glyphs


def test_carrier_glyphs_added_and_zero_width(base_font_path):
    font = TTFont(base_font_path)
    add_blank_carrier_glyphs(font)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for cp in carriers.all_carrier_codepoints():
        name = carriers.carrier_glyph_name(cp)
        assert name in glyf, f"{name} missing from glyf"
        assert glyf[name].numberOfContours == 0  # blank, no outline
        assert hmtx[name][0] == 0  # zero advance width


def test_glyph_order_stays_consistent(base_font_path):
    font = TTFont(base_font_path)
    add_blank_carrier_glyphs(font)
    glyf = font["glyf"]
    # maxp recalc asserts len(glyphOrder) == len(glyphs); exercise it.
    assert len(glyf.glyphOrder) == len(glyf.glyphs)
