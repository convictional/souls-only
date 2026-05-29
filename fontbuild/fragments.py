"""Half-glyph slicing for the Souls Keys font, via skia-pathops.

Every character is sliced into a left and a right half. Shared classes (the
lowercase bowl a c d e g o q, the lowercase stem m n r u, the uppercase bowl
O C G Q) reuse ONE canonical left half across the whole class so the left image
is ambiguous; each character keeps its own right half. Left advance = J, right
advance = W_L - J, so the two halves tile back into the character's full advance
width. build_keyboard.py addresses each half by an opaque glyph name and binds
the 2-char ASCII carrier codes to it with a GSUB ligature.

skia-pathops boolean ops emit cubic curves; TrueType `glyf` stores quadratics,
so results are routed back through Cu2QuPen on the way into a TTGlyphPen.
"""

from __future__ import annotations

import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph

# TODO (deferred hand-tuning): the lowercase "stem" class (m n r u) does NOT
# share cleanly. Clipping any real letter's stem (the canonical 'n', see
# charset.CANONICAL) drags in whatever attaches to that stem (n's arch
# shoulder), so the shared image is not a pure vertical bar and leaves a faint
# hairline seam on m n r u. Seam-overlap tuning cannot fix this (it just doubles
# strokes). The real fix is to hand-draw a SYNTHETIC pure-stem glyph for the
# stem class instead of clipping a letter. Until then, stems render with a minor
# cosmetic seam. (The "bowl" classes share cleanly: clipping 'o' / 'O' yields a
# left bowl that reads correctly across the class.)

# Generous vertical clip bounds (covers ascenders and descenders).
_YMIN, _YMAX = -400, 1000

# Fraction of the narrowest class member's advance used as the join coordinate.
_JOIN_FRACTION = 0.45

# The two halves overlap by this many units at the join so sub-pixel rounding
# cannot open a hairline gap. Advances are unaffected (still J and W - J), so the
# tiling width is preserved; only the filled outlines overlap across the seam.
_SEAM_OVERLAP = 8

# Per-letter right-half source overrides: {letter: (source_letter, y_ceiling)}.
# Jost's single-story 'a' has a much smaller bowl than the shared 'o', so a's own
# right half mismatches the shared bowl and leaves a stub at the seam. 'd' has an
# o-sized bowl plus a right stem; clipping d's right half to the x-height drops
# the ascender and yields exactly the right side of a single-story 'a' that tiles
# cleanly with the shared o-bowl. y_ceiling = a touch above the x-height top.
_RIGHT_SOURCE = {"a": ("d", 478)}


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


def _clip_box(path: pathops.Path, xmin: float, xmax: float,
              ymin: float, ymax: float) -> pathops.Path:
    box = pathops.Path()
    pen = box.getPen()
    pen.moveTo((xmin, ymin))
    pen.lineTo((xmax, ymin))
    pen.lineTo((xmax, ymax))
    pen.lineTo((xmin, ymax))
    pen.closePath()
    return pathops.op(path, box, pathops.PathOp.INTERSECTION)


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
    join. Returns (glyph, advance = W - join).

    A letter may borrow its right half from another glyph (see _RIGHT_SOURCE),
    e.g. 'a' borrows 'd' clipped to the x-height so its right side matches the
    shared o-bowl. The advance comes from the source so the halves still tile.
    """
    glyphset = font.getGlyphSet()
    hmtx = font["hmtx"]
    source, ceiling = _RIGHT_SOURCE.get(letter, (letter, None))
    g = font.getBestCmap()[ord(source)]
    width = hmtx[g][0]
    if ceiling is None:
        path = _clip(_glyph_path(glyphset, g), join - overlap, width)
    else:
        path = _clip_box(_glyph_path(glyphset, g), join - overlap, width,
                         _YMIN, ceiling)
    return _path_to_ttglyph(path, dx=-join), width - join


def _blank_glyph():
    g = Glyph()
    g.numberOfContours = 0
    return g


def space_half_glyphs(font: TTFont):
    """Two blank half-glyphs whose advances sum to the space advance, so an
    encoded space tiles into a space-width gap. Returns ((lg, ladv), (rg, radv))."""
    width = font["hmtx"][font.getBestCmap()[ord(" ")]][0]
    ladv = width // 2
    return (_blank_glyph(), ladv), (_blank_glyph(), width - ladv)


def pad_glyph():
    """A zero-advance blank glyph for the newline pad character. Returns (g, adv)."""
    return _blank_glyph(), 0


def _install(font: TTFont, name: str, glyph, advance: int) -> None:
    glyf = font["glyf"]
    glyf[name] = glyph
    # The left side bearing MUST equal the glyph's xMin. Half-glyphs have ink at
    # nonzero xMin (left halves start at the letter's stem, right halves a touch
    # before 0), so a hardcoded lsb=0 makes renderers reposition the glyph and
    # open a gap between the two halves. Recalc bounds and set lsb = xMin.
    glyph.recalcBounds(glyf)
    lsb = getattr(glyph, "xMin", 0)
    font["hmtx"][name] = (advance, lsb)
