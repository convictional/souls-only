import random
import re

from fontTools.ttLib import TTFont

from cipher import carriers
from cipher.decode import decode
from cipher.encode import encode


def test_fragment_geometry_tiles_back_to_full_width(base_font_path):
    # left advance (J) + right advance (W - J) must equal the rendered letter's
    # advance. A letter may borrow its right half from another glyph (e.g. 'a'
    # borrows 'd'), in which case W is the source glyph's advance.
    from fontbuild.fragments import _RIGHT_SOURCE, add_fragment_glyphs

    font = TTFont(base_font_path)
    joins = add_fragment_glyphs(font)
    hmtx = font["hmtx"]
    base_cmap = font.getBestCmap()
    for cls, members in carriers.FRAGMENT_CLASSES.items():
        j = joins[cls]
        lname = carriers.left_fragment_glyph_name(cls)
        assert hmtx[lname][0] == j
        for letter in members:
            source = _RIGHT_SOURCE.get(letter, (letter, None))[0]
            w = hmtx[base_cmap[ord(source)]][0]
            rname = carriers.right_fragment_glyph_name(letter)
            assert hmtx[rname][0] == w - j  # tiles back to full advance


def test_fragment_carriers_mapped_in_cmap(built_font_path):
    font = TTFont(built_font_path)
    best = font.getBestCmap()
    for cls in carriers.FRAGMENT_CLASSES:
        lname = carriers.left_fragment_glyph_name(cls)
        for cp in carriers.left_carriers(cls):
            assert best.get(cp) == lname  # every left homophone -> shared glyph
    for letter in carriers.fragment_letters():
        rname = carriers.right_fragment_glyph_name(letter)
        for cp in carriers.right_carriers(letter):
            assert best.get(cp) == rname


def test_shared_left_glyph_is_reused_across_class(built_font_path):
    # The ambiguity property: all members of a class point at ONE left glyph.
    font = TTFont(built_font_path)
    best = font.getBestCmap()
    for cls, members in carriers.FRAGMENT_CLASSES.items():
        left_glyphs = {
            best[cp] for letter in members
            for cp in carriers.left_carriers(carriers.fragment_class_of(letter))
        }
        assert len(left_glyphs) == 1  # one shared left image for the whole class


def test_table_dump_reveals_no_fragment_to_letter_mapping(built_font_path):
    font = TTFont(built_font_path)
    # 1. Fragment glyph names are opaque (no source letter encoded in the name).
    glyph_names = font.getGlyphOrder()
    frag_names = [g for g in glyph_names if g.startswith(("fragL_", "fragR_"))]
    assert frag_names  # they exist
    for g in frag_names:
        assert re.fullmatch(r"frag[LR]_\d+", g), f"non-opaque fragment name {g!r}"
    # 2. No GSUB rule references any fragment glyph (no fragment->letter rule).
    gsub = font["GSUB"]
    frag_set = set(frag_names)
    for lookup in gsub.table.LookupList.Lookup:
        for sub in lookup.SubTable:
            ligatures = getattr(sub, "ligatures", None)
            if not ligatures:
                continue
            for first_glyph, lig_list in ligatures.items():
                assert first_glyph not in frag_set
                for lig in lig_list:
                    assert lig.LigGlyph not in frag_set
                    for comp in lig.Component:
                        assert comp not in frag_set


def test_fragment_letters_roundtrip_with_noise(built_font_path):
    # Text rich in fragment letters (a c d e g o q m n r u) plus ligature ones.
    text = "ocean dragon group memo announce queue"
    for seed in range(6):
        encoded = encode(text, rng=random.Random(seed), noise_density=1.5)
        assert decode(encoded, built_font_path) == text


def test_fragment_letters_emit_fragment_carriers():
    # A fragment letter's stream uses the fragment carrier blocks, not ligature.
    out = encode("o", rng=random.Random(0), noise_density=0.0)
    left, right = ord(out[0]), ord(out[1])
    assert left in carriers.left_carrier_to_class()
    assert right in carriers.right_carrier_to_letter()
    assert carriers.right_carrier_to_letter()[right] == "o"


def test_space_half_glyphs_are_blank_and_tile_to_space_width(base_font_path):
    from fontbuild.fragments import space_half_glyphs
    font = TTFont(base_font_path)
    space_w = font["hmtx"][font.getBestCmap()[ord(" ")]][0]
    (lg, ladv), (rg, radv) = space_half_glyphs(font)
    assert lg.numberOfContours == 0 and rg.numberOfContours == 0
    assert ladv + radv == space_w


def test_pad_glyph_is_zero_advance_blank(base_font_path):
    from fontbuild.fragments import pad_glyph
    g, adv = pad_glyph()
    assert g.numberOfContours == 0
    assert adv == 0
