"""Tests for fontbuild.resample: uniform outline structure for gvar morphs.

gvar interpolation needs every master of a glyph to share an identical point
structure. The resampler rewrites any outline as exactly C contours of N
on-curve points each (collapsed padding contours for the unused slots), so any
letter half can morph into any other.
"""

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from fontbuild import resample


def _glyph_for(font, ch):
    return font.getBestCmap()[ord(ch)]


def _signed_area(ring):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def _bounds(font, name):
    gs = font.getGlyphSet()
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def test_resampled_structure_is_exact(base_font_path):
    font = TTFont(base_font_path)
    rings = resample.glyph_rings(font.getGlyphSet(), _glyph_for(font, "o"),
                                 points_per_contour=64)
    assert len(rings) == 2  # o: outer ring + counter
    assert all(len(r) == 64 for r in rings)


def test_resampling_is_deterministic(base_font_path):
    font = TTFont(base_font_path)
    gs = font.getGlyphSet()
    name = _glyph_for(font, "a")
    a = resample.glyph_rings(gs, name, points_per_contour=48)
    b = resample.glyph_rings(gs, name, points_per_contour=48)
    assert a == b


def test_resampled_outline_preserves_bbox(base_font_path):
    font = TTFont(base_font_path)
    name = _glyph_for(font, "n")
    orig = _bounds(font, name)
    rings = resample.glyph_rings(font.getGlyphSet(), name,
                                 points_per_contour=96)
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    new = (min(xs), min(ys), max(xs), max(ys))
    assert all(abs(o - n) <= 6 for o, n in zip(orig, new))


def test_resampling_preserves_winding(base_font_path):
    font = TTFont(base_font_path)
    gs = font.getGlyphSet()
    name = _glyph_for(font, "o")
    rings = resample.glyph_rings(gs, name, points_per_contour=64)
    outer, inner = sorted(rings, key=lambda r: -abs(_signed_area(r)))
    # The counter must wind opposite to the outer ring so the fill has a hole.
    assert _signed_area(outer) * _signed_area(inner) < 0


def test_padding_adds_collapsed_rings(base_font_path):
    font = TTFont(base_font_path)
    rings = resample.glyph_rings(font.getGlyphSet(), _glyph_for(font, "n"),
                                 points_per_contour=32)
    padded = resample.pad_rings(rings, n_contours=3, points_per_contour=32)
    assert len(padded) == 3
    assert padded[0] == rings[0]
    for ring in padded[1:]:
        assert len(ring) == 32
        assert len(set(ring)) == 1  # collapsed to a single point: invisible


def test_rings_to_ttglyph_roundtrip(base_font_path):
    font = TTFont(base_font_path)
    rings = resample.glyph_rings(font.getGlyphSet(), _glyph_for(font, "o"),
                                 points_per_contour=64)
    padded = resample.pad_rings(rings, n_contours=3, points_per_contour=64)
    glyph = resample.rings_to_ttglyph(padded)
    assert glyph.numberOfContours == 3
    assert len(glyph.coordinates) == 3 * 64
    assert all(f & 1 for f in glyph.flags)  # every point on-curve


def test_blank_glyph_yields_no_rings(base_font_path):
    font = TTFont(base_font_path)
    name = _glyph_for(font, " ")
    rings = resample.glyph_rings(font.getGlyphSet(), name,
                                 points_per_contour=32)
    assert rings == []
