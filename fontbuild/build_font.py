"""Orchestrate the Phase 1 pipeline: Jost base -> dist/SoulsOnly.ttf."""

from __future__ import annotations

import os

from fontTools.ttLib import TTFont

from cipher.carriers import all_carrier_codepoints, homophone_pairs
from fontbuild.features import compile_features, generate_fea, populate_cmap
from fontbuild.glyphs import add_blank_carrier_glyphs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_FONT = os.path.join(ROOT, "base", "Jost-Regular.ttf")
OUT_FONT = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
OUT_FEA = os.path.join(ROOT, "dist", "fea", "cipher.fea")

FONT_FAMILY = "Souls Only"
FONT_PS_NAME = "SoulsOnly-Regular"


def set_font_names(font: TTFont) -> None:
    name = font["name"]
    name.setName(FONT_FAMILY, 1, 3, 1, 0x409)
    name.setName("Regular", 2, 3, 1, 0x409)
    name.setName(FONT_FAMILY, 4, 3, 1, 0x409)
    name.setName(FONT_PS_NAME, 6, 3, 1, 0x409)
    name.setName(FONT_FAMILY, 16, 3, 1, 0x409)


def build() -> None:
    font = TTFont(BASE_FONT)

    add_blank_carrier_glyphs(font)
    populate_cmap(font)

    fea = generate_fea(font)
    os.makedirs(os.path.dirname(OUT_FEA), exist_ok=True)
    with open(OUT_FEA, "w") as fh:
        fh.write(fea)

    compile_features(font, OUT_FEA)
    set_font_names(font)

    os.makedirs(os.path.dirname(OUT_FONT), exist_ok=True)
    font.save(OUT_FONT)
    print(f"wrote {OUT_FONT}")
    n_pairs = sum(len(v) for v in homophone_pairs().values())
    print(f"  {len(all_carrier_codepoints())} carrier glyphs, "
          f"{n_pairs} ligature rules")


if __name__ == "__main__":
    build()
