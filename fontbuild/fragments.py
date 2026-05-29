"""Phase 3: generate shared-ambiguous fragment glyphs via skia-pathops.

For each fragment class, ONE canonical left fragment image (clipped from a
representative letter) is shared by every class member. Each member also gets
its own right fragment. Left advance = J, right advance = W_L - J, so the two
halves tile back into the letter's full advance width. Composition is cmap-only
(see features.py): there is no GSUB rule, so the font tables never link a
fragment glyph to a letter.

skia-pathops boolean ops emit cubic curves; TrueType `glyf` stores quadratics,
so results are routed back through Cu2QuPen on the way into a TTGlyphPen.
"""

from __future__ import annotations

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from cipher.carriers import (
    FRAGMENT_CLASSES,
    left_fragment_glyph_name,
    right_fragment_glyph_name,
)

# Representative letter whose left half becomes the class's shared left fragment.
#
# The "bowl" class shares cleanly: geometric letters genuinely share a near
# circular left, so clipping 'o' yields a left bowl that reads correctly under
# a c d e g o q.
#
# TODO (deferred hand-tuning): the "stem" class does NOT share cleanly. Clipping
# any real letter's stem (here 'n') drags in whatever attaches to that stem
# (n's arch shoulder), so the shared image is not a pure vertical bar and leaves
# a faint hairline seam on m n r u. Seam-overlap tuning cannot fix this (it just
# doubles strokes). The real fix is to hand-draw a SYNTHETIC pure-stem glyph for
# the stem class instead of clipping a letter. Until then, stems render with a
# minor cosmetic seam.
CANONICAL = {"bowl": "o", "stem": "n"}

# Generous vertical clip bounds (covers ascenders and descenders).
_YMIN, _YMAX = -400, 1000

# Fraction of the narrowest class member's advance used as the join coordinate.
_JOIN_FRACTION = 0.45

# The two halves overlap by this many units at the join so sub-pixel rounding
# cannot open a hairline gap. Advances are unaffected (still J and W - J), so the
# tiling width is preserved; only the filled outlines overlap across the seam.
_SEAM_OVERLAP = 8


class _ShiftPen:
    """Segment pen that translates every point by dx before forwarding."""

    def __init__(self, pen, dx):
        self.pen = pen
        self.dx = dx

    def moveTo(self, pt):
        self.pen.moveTo((pt[0] + self.dx, pt[1]))

    def lineTo(self, pt):
        self.pen.lineTo((pt[0] + self.dx, pt[1]))

    def curveTo(self, *pts):
        self.pen.curveTo(*[(x + self.dx, y) for x, y in pts])

    def qCurveTo(self, *pts):
        self.pen.qCurveTo(*[(x + self.dx, y) for x, y in pts])

    def closePath(self):
        self.pen.closePath()

    def endPath(self):
        try:
            self.pen.endPath()
        except AttributeError:
            pass


def _glyph_path(glyphset, name: str) -> pathops.Path:
    path = pathops.Path()
    glyphset[name].draw(path.getPen())
    return path


def _rect(xmin: float, xmax: float) -> pathops.Path:
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo((xmin, _YMIN))
    pen.lineTo((xmax, _YMIN))
    pen.lineTo((xmax, _YMAX))
    pen.lineTo((xmin, _YMAX))
    pen.closePath()
    return path


def _clip(path: pathops.Path, xmin: float, xmax: float) -> pathops.Path:
    return pathops.op(path, _rect(xmin, xmax), pathops.PathOp.INTERSECTION)


def _path_to_ttglyph(path: pathops.Path, dx: float = 0):
    ttpen = TTGlyphPen(None)
    cu2qu = Cu2QuPen(ttpen, max_err=1.0, reverse_direction=False)
    path.draw(_ShiftPen(cu2qu, dx) if dx else cu2qu)
    return ttpen.glyph()


def _join_for_class(hmtx, base_cmap, members: str) -> int:
    advances = [hmtx[base_cmap[ord(l)]][0] for l in members]
    return int(min(advances) * _JOIN_FRACTION)


def own_join(font: TTFont, letter: str) -> int:
    """Join coordinate for slicing a single letter into its own two halves."""
    hmtx = font["hmtx"]
    width = hmtx[font.getBestCmap()[ord(letter)]][0]
    return int(width * _JOIN_FRACTION)


def left_half_glyph(font: TTFont, letter: str, join: int,
                    overlap: int = _SEAM_OVERLAP):
    """Left half of `letter` clipped to [0, join + overlap]. Returns (glyph, adv).

    Reused for both the shared class left (pass the canonical letter) and a
    letter's own left half.
    """
    glyphset = font.getGlyphSet()
    g = font.getBestCmap()[ord(letter)]
    path = _clip(_glyph_path(glyphset, g), 0, join + overlap)
    return _path_to_ttglyph(path), join


def right_half_glyph(font: TTFont, letter: str, join: int,
                     overlap: int = _SEAM_OVERLAP):
    """Right half of `letter` clipped to [join - overlap, W], shifted left by
    join. Returns (glyph, advance = W - join)."""
    glyphset = font.getGlyphSet()
    hmtx = font["hmtx"]
    g = font.getBestCmap()[ord(letter)]
    width = hmtx[g][0]
    path = _clip(_glyph_path(glyphset, g), join - overlap, width)
    return _path_to_ttglyph(path, dx=-join), width - join


def _install(font: TTFont, name: str, glyph, advance: int) -> None:
    font["glyf"][name] = glyph
    font["hmtx"][name] = (advance, 0)


def add_fragment_glyphs(font: TTFont) -> dict[str, int]:
    """Add the shared left + per-letter right fragment glyphs. Returns joins.

    Used by the PUA cipher font (class letters only). The keyboard font reuses
    the same left_half_glyph / right_half_glyph helpers for all letters.
    """
    base_cmap = font.getBestCmap()
    joins: dict[str, int] = {}
    for cls, members in FRAGMENT_CLASSES.items():
        join = _join_for_class(font["hmtx"], base_cmap, members)
        joins[cls] = join
        # Shared left fragment: the canonical letter's left half.
        glyph, adv = left_half_glyph(font, CANONICAL[cls], join)
        _install(font, left_fragment_glyph_name(cls), glyph, adv)
        # Per-letter right fragments.
        for letter in members:
            glyph, adv = right_half_glyph(font, letter, join)
            _install(font, right_fragment_glyph_name(letter), glyph, adv)

    font.setGlyphOrder(list(font["glyf"].glyphOrder))
    return joins
