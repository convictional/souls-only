"""Tests for fontbuild.decoy_reveal: the multi-focal REVL variable font.

Axis layout: decoy plateaus across the whole axis INCLUDING the extremes (0
and 1000), each rendering a substitution-mapped alphabet of real lowercase
letter shapes, and the TRUE glyphs stored NOWHERE -- they materialize only at
the secret interpolation point between the two flanking garbage masters.
"""

import pytest
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from cipher import charset, decoy
from fontbuild import decoy_reveal as dr
from fontbuild import resample


@pytest.fixture(scope="session")
def decoy_vf_path(built_keys_path) -> str:
    import os
    out = dr.build_decoy_reveal(aligned_path=built_keys_path)
    assert os.path.exists(out)
    return out


def _instance(vf_path, revl):
    return instantiateVariableFont(TTFont(vf_path), {"REVL": revl},
                                   inplace=False)


def _coords(font, name):
    return list(font["glyf"][name].coordinates)


def _max_diff(a, b):
    assert len(a) == len(b)
    return max(max(abs(x0 - x1), abs(y0 - y1))
               for (x0, y0), (x1, y1) in zip(a, b))


def _rms(a, b):
    assert len(a) == len(b)
    n = len(a) or 1
    return (sum((x0 - x1) ** 2 + (y0 - y1) ** 2
                for (x0, y0), (x1, y1) in zip(a, b)) / n) ** 0.5


SAMPLE_SLOTS = [
    charset.left_slot("o"),    # shared lowercase bowl
    charset.right_slot("e"),   # a letter's own right half
    charset.right_slot("5"),   # a digit's right half
    charset.left_slot("k"),    # an unshared left half
]


def test_axis_is_revl_default_zero(decoy_vf_path):
    f = TTFont(decoy_vf_path)
    axes = {a.axisTag: a for a in f["fvar"].axes}
    assert set(axes) == {"REVL"}
    a = axes["REVL"]
    assert (a.minValue, a.defaultValue, a.maxValue) == (0, 0, 1000)


def test_no_gvar_peak_at_any_focal_center(decoy_vf_path):
    # NOTHING is stored at a focal center -- decoys and the real text alike
    # materialize only by interpolation between flanks. So no gvar tuple may
    # peak at any focal center (the real point is not special in the metadata).
    f = TTFont(decoy_vf_path)
    centers = [c / 1000.0 for c in dr.FOCAL_CENTERS]
    for name, tvs in f["gvar"].variations.items():
        for tv in tvs:
            _, peak, _ = tv.axes["REVL"]
            for c in centers:
                assert abs(peak - c) > 0.02, (name, peak, c)


def test_true_shapes_materialize_at_the_secret_point(decoy_vf_path,
                                                     built_keys_path):
    aligned = TTFont(built_keys_path)
    expected = dr.expected_true_glyphs(aligned)
    inst = _instance(decoy_vf_path, dr.SECRET_REVL)
    for slot in SAMPLE_SLOTS:
        name = charset.half_glyph_name(slot)
        assert _max_diff(_coords(inst, name),
                         list(expected[name].coordinates)) <= 2, slot


def test_between_focals_is_garbage(decoy_vf_path, built_keys_path):
    # Between two sweet spots every half-glyph is heavily distorted (the swing
    # has not cancelled), so the axis reads as noise away from the focals.
    aligned = TTFont(built_keys_path)
    expected = dr.expected_true_glyphs(aligned)
    mids = [(dr.FOCAL_CENTERS[i] + dr.FOCAL_CENTERS[i + 1]) // 2
            for i in range(len(dr.FOCAL_CENTERS) - 1)]
    for revl in mids:
        inst = _instance(decoy_vf_path, revl)
        for slot in SAMPLE_SLOTS:
            name = charset.half_glyph_name(slot)
            assert _rms(_coords(inst, name),
                        list(expected[name].coordinates)) > 40, (revl, slot)


def test_focal_is_a_sweet_spot_not_a_plateau(decoy_vf_path, built_keys_path):
    # No flat plateau: the clean shape appears only AT the center and degrades
    # as you move off it (nothing clean is stored, so there is no flat top).
    aligned = TTFont(built_keys_path)
    center = dr.DECOY_CENTERS[0]
    expected = dr.expected_decoy_glyphs(aligned, 0)
    at = _instance(decoy_vf_path, center)
    off = _instance(decoy_vf_path, center + 25)
    for slot in SAMPLE_SLOTS:
        name = charset.half_glyph_name(slot)
        exp = list(expected[name].coordinates)
        assert _max_diff(_coords(at, name), exp) <= 2, slot       # clean at center
        assert _rms(_coords(off, name), exp) > 20, slot           # degraded off it


def test_each_focal_renders_its_mapped_letters(decoy_vf_path, built_keys_path):
    aligned = TTFont(built_keys_path)
    for k, center in enumerate(dr.DECOY_CENTERS):
        inst = _instance(decoy_vf_path, center)
        expected = dr.expected_decoy_glyphs(aligned, k)
        for slot in SAMPLE_SLOTS:
            name = charset.half_glyph_name(slot)
            assert _max_diff(_coords(inst, name),
                             list(expected[name].coordinates)) <= 2, (k, slot)


def test_decoy_focal_differs_from_true(decoy_vf_path, built_keys_path):
    # Each character must render as a DIFFERENT character at a decoy. The RIGHT
    # half uniquely identifies the character (the shared lowercase-bowl LEFT can
    # legitimately stay the same shape -- bowl->bowl -- while the right half
    # changes the letter), so check the right halves moved.
    aligned = TTFont(built_keys_path)
    expected = dr.expected_true_glyphs(aligned)
    inst = _instance(decoy_vf_path, dr.DECOY_CENTERS[0])
    right_slots = [charset.right_slot(ch) for ch in "oe5k"]
    diffs = [
        _rms(_coords(inst, charset.half_glyph_name(s)),
             list(expected[charset.half_glyph_name(s)].coordinates))
        for s in right_slots
    ]
    assert all(d > 10 for d in diffs), diffs


def test_decoy_advances_track_the_mapped_letter(decoy_vf_path,
                                                built_keys_path):
    # Half-glyph advances interpolate too; at a focal center they equal the
    # mapped target's metrics.
    aligned = TTFont(built_keys_path)
    inst = _instance(decoy_vf_path, dr.DECOY_CENTERS[0])
    slot = charset.right_slot("e")
    name = charset.half_glyph_name(slot)
    expected_adv = dr.expected_decoy_advances(aligned, 0)[name]
    assert abs(inst["hmtx"][name][0] - expected_adv) <= 1, expected_adv


def test_decoy_halves_tile_into_coherent_glyphs(decoy_vf_path):
    # A character's left and right halves must JOIN into one coherent letter at
    # a focal point -- no floating sliver disconnected from the body. Checked at
    # both decoy centers and the real center.
    from fontTools.pens.boundsPen import BoundsPen
    chars = "the password is souls only abcdef"
    for center in (dr.DECOY_CENTERS[0], dr.DECOY_CENTERS[-1], dr.SECRET_REVL):
        inst = _instance(decoy_vf_path, center)
        gs = inst.getGlyphSet()
        hmtx = inst["hmtx"]

        def bounds(name):
            p = BoundsPen(gs)
            gs[name].draw(p)
            return p.bounds

        for ch in chars:
            if ch == " ":
                continue
            ls = charset.half_glyph_name(charset.left_slot(ch))
            rs = charset.half_glyph_name(charset.right_slot(ch))
            lb, rb = bounds(ls), bounds(rs)
            if not lb or not rb:
                continue
            ladv = hmtx[ls][0]
            seam_gap = (ladv + rb[0]) - lb[2]  # right placed xMin - left xMax
            assert seam_gap <= 40, (center, ch, "seam gap", seam_gap)
            # Neither half is a degenerate sliver/point.
            lh, rh = lb[3] - lb[1], rb[3] - rb[1]
            assert lh >= 80 and rh >= 80, (center, ch, "degenerate half", lh, rh)
            # The halves are not vertically disjoint (no stranded sliver).
            overlap = min(lb[3], rb[3]) - max(lb[1], rb[1])
            assert overlap > 0, (center, ch, "disjoint halves", overlap)


def test_literal_space_is_unaffected_by_revl(decoy_vf_path):
    # Space is a real space (U+0020), not a ciphered half-glyph: it must render
    # as a blank, fixed-width gap at EVERY REVL (never scattered or morphed),
    # so text wraps and selects normally wherever the font is used.
    for revl in (0, dr.DECOY_CENTERS[1], dr.SECRET_REVL, 1000):
        inst = _instance(decoy_vf_path, revl)
        space = inst.getBestCmap()[ord(" ")]
        g = inst["glyf"][space]
        assert g.numberOfContours == 0
        assert inst["hmtx"][space][0] > 0  # keeps a real advance width
