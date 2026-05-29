import random
import re

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from cipher import keyboard as kb

SAMPLES = [
    "the quick brown fox jumps over the lazy dog",
    "souls only",
    "ocean morning",
    "abcdefghijklmnopqrstuvwxyz",
]


def _shape(font_path, text):
    data = open(font_path, "rb").read()
    font = hb.Font(hb.Face(data))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"liga": True})
    go = TTFont(font_path).getGlyphOrder()
    return [go[i.codepoint] for i in buf.glyph_infos]


def test_codes_are_two_chars_from_the_alphabet():
    for pool in kb.slot_codes().values():
        for code in pool:
            assert len(code) == kb.CODE_LEN
            assert all(c in kb.CODE_ALPHABET for c in code)


def test_roundtrip_pure_cipher():
    for s in SAMPLES:
        enc = kb.encode(s, rng=random.Random(1))
        assert kb.decode(enc) == s


def test_homophones_vary_across_occurrences():
    rng = random.Random(2)
    seen = set()
    for _ in range(60):
        seen.add(kb.encode("e", rng=rng))
    assert len(seen) > 1  # repeated letter looks different in the stream


def test_no_letter_leaks_into_stream():
    enc = kb.encode("the quick brown fox", rng=random.Random(3))
    assert not any(c.isalpha() for c in enc)


def test_shaping_has_no_notdef_and_two_halves_per_letter(built_keys_path):
    text = "the quick brown fox"
    enc = kb.encode(text, rng=random.Random(4))
    shaped = _shape(built_keys_path, enc)
    assert ".notdef" not in shaped
    halves = [g for g in shaped if g.startswith("kf_")]
    n_letters = sum(c.isalpha() for c in text)
    assert len(halves) == 2 * n_letters


def test_table_dump_reveals_no_code_to_letter_mapping(built_keys_path):
    font = TTFont(built_keys_path)
    # GSUB only ligates code carriers into opaque half-glyphs (kf_*), never a
    # real letter glyph. Glyph names are opaque.
    gsub = font["GSUB"]
    real_letters = set("abcdefghijklmnopqrstuvwxyz")
    for lookup in gsub.table.LookupList.Lookup:
        for sub in lookup.SubTable:
            ligs = getattr(sub, "ligatures", None)
            if not ligs:
                continue
            for _, lig_list in ligs.items():
                for lig in lig_list:
                    assert lig.LigGlyph not in real_letters
    for slot in kb.half_slots():
        assert re.fullmatch(r"kf_\d+", kb.half_glyph_name(slot))


def test_half_glyph_lsb_matches_xmin(built_keys_path):
    # The left side bearing must equal the glyph's xMin; otherwise renderers
    # reposition the half and open a gap, so a letter reads as two strokes.
    font = TTFont(built_keys_path)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for slot in kb.half_slots():
        name = kb.half_glyph_name(slot)
        g = glyf[name]
        if getattr(g, "numberOfContours", 0) <= 0:
            continue
        g.recalcBounds(glyf)
        assert hmtx[name][1] == g.xMin, f"{name}: lsb {hmtx[name][1]} != xMin {g.xMin}"


def test_keyboard_reveal_axis(built_keys_vf_path):
    f = TTFont(built_keys_vf_path)
    axes = {a.axisTag: a for a in f["fvar"].axes}
    assert "REVL" in axes
    assert axes["REVL"].defaultValue == 0


def test_keyboard_reveal_aligned_restores(built_keys_vf_path, built_keys_path):
    aligned = TTFont(built_keys_path)
    inst = instantiateVariableFont(TTFont(built_keys_vf_path), {"REVL": 1000},
                                   inplace=False)

    def bounds(font, g):
        pen = BoundsPen(font.getGlyphSet())
        font.getGlyphSet()[g].draw(pen)
        return pen.bounds

    # a shared left half and a right half should restore to their aligned shape
    sample_glyph = kb.half_glyph_name(kb.half_slots()[0])
    a = bounds(aligned, sample_glyph)
    b = bounds(inst, sample_glyph)
    assert a and b and all(abs(x - y) <= 2 for x, y in zip(a, b))
