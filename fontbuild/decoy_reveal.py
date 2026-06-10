"""The multi-focal decoy reveal: REVL axis with substitution focal points and
a hidden true text.

Axis layout (REVL 0..1000, default 0):

  plateaus   one per decoy focal point, INCLUDING the extremes (0 and 1000):
             every half-glyph wears the half of a DIFFERENT real character
             (cipher.decoy substitution mapping), so a scrubber/OCR reads
             confident lowercase text that decodes to nothing. Each focal is a
             flat plateau (two identical masters) so it is easy to land on, and
             there is no obvious "noise" state hinting that anything is hidden.
  flanks     two garbage masters around the secret point storing true -+ a
             random swing. The TRUE glyph outlines are stored NOWHERE in the
             file: they materialize only at the secret interpolation point
             between the flanks (an uneven ratio, so no gvar peak marks it
             and averaging adjacent masters does not reconstruct it).

Between masters, gvar interpolates vertices linearly, so scrubbing morphs
every half-glyph fluidly from one letterform toward the next. All half-glyph
outlines are resampled to a uniform point structure (fontbuild.resample) so
any half can morph into any other; advances interpolate with them.

Everything lives in standard glyf/gvar/hmtx data -- a page only sets
font-variation-settings, and the .ttf alone carries the whole behavior.
"""

from __future__ import annotations

import io
import os
import random

from fontTools.designspaceLib import (
    AxisDescriptor,
    DesignSpaceDocument,
    SourceDescriptor,
)
from fontTools.ttLib import TTFont
from fontTools.varLib import build as varlib_build

from cipher import charset, decoy
from fontbuild import resample
from fontbuild.fragments import (
    _join_for_class,
    left_half_glyph,
    own_join,
    right_half_glyph,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIGNED = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
# Decoy targets are sliced from the BASE font: the built cipher font remaps
# letter codepoints to carrier glyphs, so its cmap no longer yields real
# letter outlines to clip.
BASE_FONT = os.path.join(ROOT, "base", "Jost-Regular.ttf")
OUT_VF = os.path.join(ROOT, "dist", "SoulsOnly-VF.ttf")

_AXIS_TAG = "REVL"
_AXIS_MAX = 1000

# Uniform structure: every varying half-glyph is C rings of N points.
N_POINTS = 64

# Focal sweet spots. EVERY focal -- decoys AND the real text -- is hidden the
# same way: it materializes only at its center, between two garbage flank
# masters storing shape -+ a random swing. So NOTHING (not even a decoy) is
# stored as a clean master, the distortion is symmetric across all focals, and
# the real point is indistinguishable from a decoy by inspecting the file.
SECRET_REVL = 650                                  # the real text's sweet spot
FOCAL_CENTERS = (70, 230, 390, 530, 650, 810, 940)

# Asymmetric flank offsets per focal (lo below the center, hi above). lo != hi
# so the sweet spot is never the midpoint of its two flanks -- you cannot find
# it by averaging the two odd masters. Chosen so all flank masters stay ordered
# and non-overlapping across the axis.
_OFFSETS = {70: (34, 46), 230: (44, 32), 390: (36, 48), 530: (48, 34),
            650: (38, 46), 810: (33, 49), 940: (47, 35)}

# Per-point random swing (font units) stored in each flank. Bigger -> the flanks
# are noisier and each sweet spot is sharper (narrower readable window).
SWING = 300

# The six decoy sweet spots (every focal that is not the real text).
DECOY_CENTERS = tuple(c for c in FOCAL_CENTERS if c != SECRET_REVL)
_N_DECOYS = len(DECOY_CENTERS)


def _char_join(base: TTFont, ch: str) -> int:
    cls = charset.class_of(ch)
    if cls is not None:
        return _join_for_class(base["hmtx"], base.getBestCmap(),
                               charset.FRAGMENT_CLASSES[cls])
    return own_join(base, ch)


def _target_half(base: TTFont, slot: str, mapping: dict[str, str]):
    """(rings, advance) of the half-glyph `slot` wears at a decoy focal, or
    None for the blank space halves. Sliced from the BASE font, whose cmap
    still maps letters to their real outlines."""
    if slot in ("SP_L", "SP_R"):
        return None
    if slot.startswith("cls_"):
        member = charset.FRAGMENT_CLASSES[slot[len("cls_"):]][0]
        target = mapping[member]  # whole class maps into one target class
    else:  # "L_<ch>" / "R_<ch>"
        target = mapping[slot[2:]]
    if slot.startswith("R_"):
        glyph, adv = right_half_glyph(base, target, _char_join(base, target))
    else:
        cls = charset.class_of(target)
        canon = charset.CANONICAL[cls] if cls else target
        glyph, adv = left_half_glyph(base, canon, _char_join(base, target))
    return resample.ttglyph_rings(glyph, base["glyf"], N_POINTS), adv


def _variants(font: TTFont, base: TTFont | None = None) -> dict[str, dict]:
    """Per varying half-glyph: true rings + advance, one decoy (rings,
    advance) per focal, and the unified contour count. Blank space halves are
    excluded (they stay blank at every REVL).

    True half-glyphs are read from the built cipher `font` (the installed
    h_<n> outlines); decoy targets are sliced from `base` (Jost), whose cmap
    still maps letters to real outlines."""
    if base is None:
        base = TTFont(BASE_FONT)
    mappings = [decoy.focal_mapping(k) for k in range(_N_DECOYS)]
    glyphset = font.getGlyphSet()
    out: dict[str, dict] = {}
    for slot in charset.half_slots():
        decoys = [_target_half(base, slot, m) for m in mappings]
        if all(d is None for d in decoys):
            continue  # SP_L / SP_R
        name = charset.half_glyph_name(slot)
        true_rings = resample.glyph_rings(glyphset, name, N_POINTS)
        true_adv = font["hmtx"][name][0]
        contours = max(len(true_rings), *(len(d[0]) for d in decoys))
        out[name] = {"true": (true_rings, true_adv), "decoys": decoys,
                     "contours": contours}
    return out


def _built(rings, contours: int):
    return resample.rings_to_ttglyph(
        resample.pad_rings(rings, contours, N_POINTS))


def _install(font: TTFont, name: str, glyph, advance: int) -> None:
    glyf = font["glyf"]
    glyf[name] = glyph
    glyph.recalcBounds(glyf)
    font["hmtx"][name] = (advance, getattr(glyph, "xMin", 0))


def expected_true_glyphs(font: TTFont) -> dict[str, object]:
    """{half-glyph name: the resampled TRUE glyph} (for tests/inspection)."""
    out = {}
    for name, v in _variants(font).items():
        g = _built(v["true"][0], v["contours"])
        g.recalcBounds(font["glyf"])
        out[name] = g
    return out


def expected_decoy_glyphs(font: TTFont, k: int) -> dict[str, object]:
    out = {}
    for name, v in _variants(font).items():
        g = _built(v["decoys"][k][0], v["contours"])
        g.recalcBounds(font["glyf"])
        out[name] = g
    return out


def expected_decoy_advances(font: TTFont, k: int) -> dict[str, int]:
    return {name: v["decoys"][k][1] for name, v in _variants(font).items()}


def build_decoy_reveal(aligned_path: str = ALIGNED,
                       out_vf: str = OUT_VF) -> str:
    """Wrap the static cipher font in the all-hidden decoy-focal REVL axis."""
    aligned = TTFont(aligned_path)
    variants = _variants(aligned)
    blob = open(aligned_path, "rb").read()

    def fresh(shapes: str) -> TTFont:
        """A new font whose half-glyphs carry a focal's clean shapes.
        shapes is "true" or "decoy:<k>"."""
        f = TTFont(io.BytesIO(blob))
        for name, v in variants.items():
            if shapes == "true":
                rings, adv = v["true"]
            else:
                rings, adv = v["decoys"][int(shapes.split(":")[1])]
            _install(f, name, _built(rings, v["contours"]), adv)
        return f

    def garble(shapes: str, seed: str, coeff: float, sign: float) -> TTFont:
        """A flank master: each varying point moved by sign*coeff*g, where g is
        a per-point random field keyed by `seed`. Using the SAME seed for a
        focal's two flanks (with the matching coeffs/signs) makes the swing
        cancel exactly at the focal's center, so the clean shape appears only
        there and nowhere is it stored."""
        f = fresh(shapes)
        glyf = f["glyf"]
        for name in variants:
            glyph = glyf[name]
            coords = glyph.coordinates
            rng = random.Random(f"{seed}:{name}")
            for i in range(len(coords)):
                gx = rng.uniform(-SWING, SWING)
                gy = rng.uniform(-SWING, SWING)
                x, y = coords[i]
                coords[i] = (round(x + sign * coeff * gx),
                             round(y + sign * coeff * gy))
            glyph.recalcBounds(glyf)
            f["hmtx"][name] = (f["hmtx"][name][0], glyph.xMin)
        return f

    masters: list[tuple[int, TTFont]] = []
    decoy_k = 0
    for center in FOCAL_CENTERS:
        lo, hi = _OFFSETS[center]
        shapes = "true" if center == SECRET_REVL else f"decoy:{decoy_k}"
        if center != SECRET_REVL:
            decoy_k += 1
        # weights at the center: w_lo on the low flank, w_hi on the high flank.
        w_lo = hi / (lo + hi)
        w_hi = lo / (lo + hi)
        seed = f"focal:{center}"
        # low flank = shape - w_hi*g ; high flank = shape + w_lo*g.
        masters.append((center - lo, garble(shapes, seed, w_hi, -1.0)))
        masters.append((center + hi, garble(shapes, seed, w_lo, +1.0)))

    # Bookend garbage masters at the axis ends: they give varLib its required
    # default master at 0 and define the (garbage) rendering past the outermost
    # focals. Their tents are zero at every focal center, so they never disturb
    # a sweet spot.
    masters.append((0, garble("true", "end:lo", 1.0, +1.0)))
    masters.append((_AXIS_MAX, garble("true", "end:hi", 1.0, -1.0)))

    doc = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.tag = _AXIS_TAG
    axis.name = "Reveal"
    axis.minimum = 0
    axis.maximum = _AXIS_MAX
    axis.default = 0  # default to a decoy (a plausible-but-wrong message)
    doc.addAxis(axis)

    tmp_paths = []
    for loc, f in sorted(masters, key=lambda lf: lf[0]):
        path = os.path.join(ROOT, "dist", f"_dm_{loc}.ttf")
        f.save(path)
        tmp_paths.append(path)
        src = SourceDescriptor()
        src.path = path
        src.location = {"Reveal": loc}
        doc.addSource(src)

    vf, _, _ = varlib_build(doc)
    _set_vf_names(vf, aligned)
    vf.save(out_vf)
    for p in tmp_paths:
        os.remove(p)
    print(f"wrote {out_vf}")
    print(f"  axis {_AXIS_TAG} 0..{_AXIS_MAX}, default 0; "
          f"{_N_DECOYS} decoy focals + 1 real, all hidden between garbage "
          f"flanks; nothing stored")
    return out_vf


def _set_vf_names(vf: TTFont, aligned: TTFont) -> None:
    """Distinct family ("<base> VF") so OS installs do not collide."""
    base_family = (aligned["name"].getDebugName(16)
                   or aligned["name"].getDebugName(1) or "Souls Only")
    vf_family = f"{base_family} VF"
    vf_ps = base_family.replace(" ", "") + "VF-Regular"
    name = vf["name"]
    for plat in ((3, 1, 0x409), (1, 0, 0)):
        name.setName(vf_family, 1, *plat)
        name.setName("Regular", 2, *plat)
        name.setName(vf_family, 4, *plat)
        name.setName(vf_ps, 6, *plat)
        name.setName(vf_family, 16, *plat)
        name.setName("Regular", 17, *plat)


if __name__ == "__main__":
    build_decoy_reveal()
