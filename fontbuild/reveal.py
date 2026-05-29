"""Build the in-font scatter-to-align reveal as a variable font.

The reveal lives entirely inside the font on a custom `REVL` axis, with three
masters:
  * at REVL = 0 (the default, so the safe state is illegible) every glyph's
    outline is scattered: shrunk and randomly displaced, so the line reads as
    noise.
  * at REVL = _ALIGNED_AT (the middle of the axis) the outlines interpolate back
    to the true cipher glyphs and the text assembles.
  * at REVL = 1000 the outlines scatter again into a different distortion, so
    pushing the control all the way up does not reveal the text either.

This is the outline-variation (gvar) path from the spec: masters that differ
only in glyph coordinates, interpolated by fontTools.varLib. A page binds one
control to the axis; no reveal logic lives in page code.

Per-glyph scatter is deterministic (seeded) so a rebuild is reproducible, and is
keyed by glyph index so repeated glyphs (homophone duplicates) scatter
differently from one another.
"""

from __future__ import annotations

import os
import random

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIGNED = os.path.join(ROOT, "dist", "SoulsKeys.ttf")
OUT_VF = os.path.join(ROOT, "dist", "SoulsKeys-VF.ttf")

_AXIS_TAG = "REVL"
_AXIS_MAX = 1000
# The text is fully readable at the MIDDLE of the axis, not the top: outlines
# are the true glyphs at REVL = _ALIGNED_AT, and distort in BOTH directions
# (scattered toward 0, a different distortion toward 1000). So a reader finds a
# precise sweet spot rather than just cranking to the max.
_ALIGNED_AT = 650
# Scattered-end intensity. The glyph is warped by a random non-uniform 2x2
# matrix (anisotropic squash, shear, and possible flip, not just rotation),
# each control point is then jittered independently so the outline itself is
# destroyed, and the whole thing is flung across the line. At REVL=1000 every
# point interpolates back to its true position.
_SCATTER_DX = 620   # max horizontal displacement (font units)
_SCATTER_DY = 720   # max vertical displacement (font units)
_BASE_SCALE = 1.35  # scattered glyphs stay large (bigger than the true glyph)
_DIAG = (0.7, 1.3)  # per-axis stretch factor magnitude (random sign -> flips)
_SHEAR = 0.8        # max shear each way
_JITTER = 190       # per-control-point random displacement (font units)
_SEED = 20260529    # scatter at REVL = 0
_SEED2 = 71727374   # a DIFFERENT distortion at REVL = max (overshoot)


def _scatter_simple(glyph, glyf, rng, dx, dy):
    """Warp the glyph out of recognition (kept large), then displace."""
    coords = glyph.coordinates
    n = len(coords)
    if n == 0:
        return
    cx = sum(p[0] for p in coords) / n
    cy = sum(p[1] for p in coords) / n
    # Large, anisotropic, sheared, possibly flipped 2x2 warp.
    a = _BASE_SCALE * rng.uniform(*_DIAG) * rng.choice((-1, 1))
    d = _BASE_SCALE * rng.uniform(*_DIAG) * rng.choice((-1, 1))
    b = _BASE_SCALE * rng.uniform(-_SHEAR, _SHEAR)
    c = _BASE_SCALE * rng.uniform(-_SHEAR, _SHEAR)
    coords.translate((-cx, -cy))
    coords.transform(((a, b), (c, d)))
    coords.translate((cx + dx, cy + dy))
    for i in range(n):  # per-point jitter destroys the outline
        px, py = coords[i]
        coords[i] = (px + rng.uniform(-_JITTER, _JITTER),
                     py + rng.uniform(-_JITTER, _JITTER))
    glyph.recalcBounds(glyf)


def _make_scattered(aligned_path: str, seed: int) -> TTFont:
    """Return a copy of the aligned font with every inked glyph scattered.

    `seed` selects the random distortion, so two different seeds give two
    different distorted masters (one for each end of the axis)."""
    scattered = TTFont(aligned_path)  # reload a clean copy from disk
    glyf = scattered["glyf"]
    rng = random.Random(seed)
    for name in scattered.getGlyphOrder():
        glyph = glyf[name]
        dx = rng.uniform(-_SCATTER_DX, _SCATTER_DX)
        dy = rng.uniform(-_SCATTER_DY, _SCATTER_DY)
        if getattr(glyph, "numberOfContours", 0) > 0:
            _scatter_simple(glyph, glyf, rng, dx, dy)
        elif getattr(glyph, "numberOfContours", 0) == -1:
            # Composite: displace component offsets (no point coordinates).
            for comp in glyph.components:
                comp.x += dx
                comp.y += dy
    return scattered


def build_reveal(aligned_path: str = ALIGNED, out_vf: str = OUT_VF) -> None:
    """Wrap any static cipher font in the REVL axis: scattered at 0, the true
    glyphs at _ALIGNED_AT (the readable sweet spot), a different distortion at
    the max. Three masters; the default (0) stays illegible."""
    aligned = TTFont(aligned_path)
    scattered = _make_scattered(aligned_path, _SEED)
    distorted = _make_scattered(aligned_path, _SEED2)

    scatter_path = os.path.join(ROOT, "dist", "_master_scatter.ttf")
    aligned_master_path = os.path.join(ROOT, "dist", "_master_aligned.ttf")
    distort_path = os.path.join(ROOT, "dist", "_master_distort.ttf")
    scattered.save(scatter_path)
    aligned.save(aligned_master_path)
    distorted.save(distort_path)

    doc = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.tag = _AXIS_TAG
    axis.name = "Reveal"
    axis.minimum = 0
    axis.maximum = _AXIS_MAX
    axis.default = 0  # default to the illegible end
    doc.addAxis(axis)

    for path, loc in (
        (scatter_path, 0),
        (aligned_master_path, _ALIGNED_AT),
        (distort_path, _AXIS_MAX),
    ):
        src = SourceDescriptor()
        src.path = path
        src.location = {"Reveal": loc}
        doc.addSource(src)

    vf, _, _ = varlib_build(doc)
    vf.save(out_vf)
    for p in (scatter_path, aligned_master_path, distort_path):
        os.remove(p)
    print(f"wrote {out_vf}")
    print(f"  axis {_AXIS_TAG} 0..{_AXIS_MAX}, default 0; readable at {_ALIGNED_AT}")


if __name__ == "__main__":
    build_reveal()
