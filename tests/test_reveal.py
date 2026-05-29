from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


def _bounds(font, gname):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[gname].draw(pen)
    return pen.bounds


def _close(a, b, tol=2.0):
    return a is not None and b is not None and all(
        abs(x - y) <= tol for x, y in zip(a, b)
    )


def test_revl_axis_present_and_defaults_scattered(built_vf_path):
    f = TTFont(built_vf_path)
    axes = {a.axisTag: a for a in f["fvar"].axes}
    assert "REVL" in axes
    assert axes["REVL"].minValue == 0
    assert axes["REVL"].defaultValue == 0  # safe default is illegible
    assert axes["REVL"].maxValue == 1000


def test_no_named_instance_sits_at_the_legible_end(built_vf_path):
    # Named-instance footgun: nothing should hand an attacker the reveal value.
    f = TTFont(built_vf_path)
    for inst in f["fvar"].instances:
        assert inst.coordinates.get("REVL", 0) < 1000


def test_aligned_end_restores_true_outlines(built_vf_path, built_font_path):
    aligned = TTFont(built_font_path)
    inst = instantiateVariableFont(TTFont(built_vf_path), {"REVL": 1000},
                                   inplace=False)
    # Real letter, fragment left, and fragment right should all restore exactly.
    for g in ("o", "a", "fragL_0", "fragR_0"):
        assert _close(_bounds(inst, g), _bounds(aligned, g)), g


def test_scattered_end_differs_from_true(built_vf_path, built_font_path):
    aligned = TTFont(built_font_path)
    inst0 = instantiateVariableFont(TTFont(built_vf_path), {"REVL": 0},
                                    inplace=False)
    assert not _close(_bounds(inst0, "o"), _bounds(aligned, "o"))


def test_reveal_preserves_cipher_tables(built_vf_path):
    # The reveal is purely additive: cmap and GSUB are unchanged, so the cipher
    # still works at any axis value.
    f = TTFont(built_vf_path)
    assert "cmap" in f and "GSUB" in f and "gvar" in f
    from cipher import carriers

    best = f.getBestCmap()
    for cp in carriers.all_carrier_codepoints():
        assert best.get(cp) == carriers.carrier_glyph_name(cp)
