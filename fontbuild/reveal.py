"""Phase 4: build the in-font scatter-to-align reveal as a variable font.

The reveal lives entirely inside the font on a custom `REVL` axis:
  * at REVL = 0 (the default, so the safe state is illegible) every glyph's
    outline is scattered: shrunk and randomly displaced, so the line reads as
    noise.
  * at REVL = 1000 the outlines interpolate back to the true cipher glyphs and
    the text assembles.

This is the outline-variation (gvar) path from the spec: two masters that differ
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
ALIGNED = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
OUT_VF = os.path.join(ROOT, "dist", "SoulsOnly-VF.ttf")

_AXIS_TAG = "REVL"
_AXIS_MAX = 1000
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
_SEED = 20260529


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


def _make_scattered(aligned_path: str) -> TTFont:
    """Return a copy of the aligned font with every inked glyph scattered."""
    scattered = TTFont(aligned_path)  # reload a clean copy from disk
    glyf = scattered["glyf"]
    rng = random.Random(_SEED)
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
    """Wrap any static cipher font in the REVL scatter-to-align variable axis."""
    aligned = TTFont(aligned_path)
    scattered = _make_scattered(aligned_path)

    scattered_path = os.path.join(ROOT, "dist", "_master_scattered.ttf")
    master_aligned_path = os.path.join(ROOT, "dist", "_master_aligned.ttf")
    scattered.save(scattered_path)
    aligned.save(master_aligned_path)

    doc = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.tag = _AXIS_TAG
    axis.name = "Reveal"
    axis.minimum = 0
    axis.maximum = _AXIS_MAX
    axis.default = 0  # default to the illegible end
    doc.addAxis(axis)

    src_scatter = SourceDescriptor()
    src_scatter.path = scattered_path
    src_scatter.location = {"Reveal": 0}
    doc.addSource(src_scatter)

    src_aligned = SourceDescriptor()
    src_aligned.path = master_aligned_path
    src_aligned.location = {"Reveal": _AXIS_MAX}
    doc.addSource(src_aligned)

    vf, _, _ = varlib_build(doc)
    vf.save(out_vf)
    os.remove(scattered_path)
    os.remove(master_aligned_path)
    print(f"wrote {out_vf}")
    print(f"  axis {_AXIS_TAG} 0..{_AXIS_MAX}, default 0 (scattered)")


if __name__ == "__main__":
    build_reveal()
