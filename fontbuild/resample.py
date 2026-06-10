"""Uniform outline resampling so any glyph can gvar-morph into any other.

gvar stores per-point deltas, so every master of a glyph must carry the SAME
number of contours and points. Letter halves do not (an o-bowl is two rings,
an n-stem is one), so the decoy reveal rewrites every outline as a fixed
structure: C contours of exactly N on-curve points each, padding unused
contour slots with rings collapsed to a single point (zero area, invisible).

Resampling is deterministic: rings are sorted by descending area, each ring is
sampled uniformly by arc length, and the start point is normalized to the
topmost sample, so two resamples of the same outline are identical and two
different letters resample into point-for-point corresponding structures.
"""

from __future__ import annotations

import math

from array import array

from fontTools.pens.basePen import BasePen
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates

# Dense pre-sampling of curve segments before arc-length resampling.
_CURVE_STEPS = 16


class _FlattenPen(BasePen):
    """Records each contour as a dense polyline (curves sampled)."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.rings: list[list[tuple[float, float]]] = []
        self._cur: list[tuple[float, float]] = []

    def _moveTo(self, pt):
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _qCurveToOne(self, p1, p2):
        x0, y0 = self._cur[-1]
        for i in range(1, _CURVE_STEPS + 1):
            t = i / _CURVE_STEPS
            mt = 1 - t
            x = mt * mt * x0 + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * y0 + 2 * mt * t * p1[1] + t * t * p2[1]
            self._cur.append((x, y))

    def _curveToOne(self, p1, p2, p3):
        x0, y0 = self._cur[-1]
        for i in range(1, _CURVE_STEPS + 1):
            t = i / _CURVE_STEPS
            mt = 1 - t
            x = (mt ** 3 * x0 + 3 * mt * mt * t * p1[0]
                 + 3 * mt * t * t * p2[0] + t ** 3 * p3[0])
            y = (mt ** 3 * y0 + 3 * mt * mt * t * p1[1]
                 + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])
            self._cur.append((x, y))

    def _closePath(self):
        if len(self._cur) > 1 and self._cur[0] == self._cur[-1]:
            self._cur.pop()  # drop the duplicated closing point
        if self._cur:
            self.rings.append(self._cur)
        self._cur = []

    def _endPath(self):
        self._closePath()


def _signed_area(ring) -> float:
    s = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def _resample_ring(ring, n: int):
    """Uniform arc-length resampling of a closed polyline to n points."""
    pts = ring + [ring[0]]  # close the loop
    seg_len = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    total = sum(seg_len)
    if total == 0:
        return [ring[0]] * n
    out = []
    target = 0.0
    step = total / n
    seg = 0
    walked = 0.0
    for _ in range(n):
        while seg < len(seg_len) and walked + seg_len[seg] < target - 1e-9:
            walked += seg_len[seg]
            seg += 1
        if seg >= len(seg_len):
            out.append(pts[-1])
        else:
            t = 0.0 if seg_len[seg] == 0 else (target - walked) / seg_len[seg]
            (x0, y0), (x1, y1) = pts[seg], pts[seg + 1]
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        target += step
    return out


def _normalize_start(ring):
    """Rotate the ring so it starts at the topmost (then leftmost) sample."""
    start = max(range(len(ring)), key=lambda i: (ring[i][1], -ring[i][0]))
    return ring[start:] + ring[:start]


def _finish_rings(pen: _FlattenPen, points_per_contour: int):
    rings = [
        _normalize_start(_resample_ring(r, points_per_contour))
        for r in pen.rings
    ]
    rings.sort(key=lambda r: (-abs(_signed_area(r)), min(r)))
    return rings


def glyph_rings(glyphset, name: str, points_per_contour: int):
    """The glyph's outline as rings of exactly points_per_contour points each,
    sorted by descending area (outer ring first), start points normalized."""
    pen = _FlattenPen(glyphset)
    glyphset[name].draw(pen)
    return _finish_rings(pen, points_per_contour)


def ttglyph_rings(glyph, glyf, points_per_contour: int):
    """Rings for a standalone TrueType glyph (e.g. a freshly sliced half)."""
    pen = _FlattenPen(None)
    glyph.draw(pen, glyf)
    return _finish_rings(pen, points_per_contour)


def pad_rings(rings, n_contours: int, points_per_contour: int):
    """Pad to n_contours by appending rings collapsed to a single point."""
    if len(rings) > n_contours:
        raise ValueError(f"glyph has {len(rings)} rings, cap {n_contours}")
    if rings:
        first = rings[0]
        cx = sum(x for x, _ in first) / len(first)
        cy = sum(y for _, y in first) / len(first)
        pad_pt = (cx, cy)
    else:
        pad_pt = (0.0, 0.0)
    pad = [pad_pt] * points_per_contour
    return list(rings) + [list(pad) for _ in range(n_contours - len(rings))]


def rings_to_ttglyph(rings):
    """Rings -> a TrueType glyph of straight segments (every point on-curve).

    Built directly (not via TTGlyphPen) because the pen optimizes away
    "redundant" points -- and identical point counts across masters is the
    entire reason this module exists.
    """
    glyph = Glyph()
    coords: list[tuple[int, int]] = []
    end_pts: list[int] = []
    for ring in rings:
        coords.extend((round(x), round(y)) for x, y in ring)
        end_pts.append(len(coords) - 1)
    glyph.numberOfContours = len(rings)
    glyph.coordinates = GlyphCoordinates(coords)
    glyph.endPtsOfContours = end_pts
    glyph.flags = array("B", [1] * len(coords))  # all on-curve
    glyph.program = ttProgram.Program()
    return glyph
