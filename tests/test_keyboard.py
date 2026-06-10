import random
import re

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from cipher import keyboard as kb

SAMPLES = [
    "the quick brown fox jumps over the lazy dog",
    "The Quick Brown Fox 123",
    "Hello, World! @ #5 & (you) = ok?",
    "souls only",
    "ALL CAPS AND 0123456789",
    "sym: !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
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


def test_carrier_alphabet_is_92_safe_chars():
    # Letters, digits, and symbols all carry code material now.
    from cipher import charset
    assert len(kb.CODE_ALPHABET) == 92
    assert '"' not in kb.CODE_ALPHABET
    assert "\\" not in kb.CODE_ALPHABET
    assert all(c in kb.CODE_ALPHABET for c in charset.LOWER)
    assert all(c in kb.CODE_ALPHABET for c in charset.UPPER)
    assert all(c in kb.CODE_ALPHABET for c in charset.DIGITS)


def test_code_space_covers_all_slots():
    from cipher import charset
    slots = charset.half_slots()
    pools = kb.slot_codes()
    assert set(pools) == set(slots)
    need = len(slots) * kb.HOMOPHONES
    assert need <= len(kb.CODE_ALPHABET) ** kb.CODE_LEN
    all_codes = [c for pool in pools.values() for c in pool]
    assert len(all_codes) == len(set(all_codes))


def test_roundtrip_pure_cipher():
    import random
    for s in SAMPLES:
        enc = kb.encode(s, rng=random.Random(1))
        assert kb.decode(enc) == s


def test_roundtrip_with_spaces_and_newlines():
    import random
    text = "Hello World\nLine two\\here\nThird 99! a\\b"
    enc = kb.encode(text, rng=random.Random(2))
    assert kb.decode(enc) == text


def test_space_stays_a_literal_space():
    # Space is NOT ciphered -- it passes through as a real space so the stream
    # keeps word boundaries and the font wraps/selects normally anywhere.
    import random
    assert kb.encode(" ", rng=random.Random(3)) == " "
    enc = kb.encode("a b", rng=random.Random(3))
    assert enc.count(" ") == 1
    assert kb.decode(enc) == "a b"


def test_newline_is_real_newline_plus_three_pads():
    import random
    from cipher import charset
    enc = kb.encode("\n", rng=random.Random(4))
    assert enc == "\n" + charset.PAD * 3
    assert kb.decode(enc) == "\n"


def test_homophones_vary_across_occurrences():
    rng = random.Random(2)
    seen = set()
    for _ in range(60):
        seen.add(kb.encode("e", rng=rng))
    assert len(seen) > 1  # repeated letter looks different in the stream


def test_stream_mixes_letters_digits_and_symbols():
    # The encoded stream draws on the whole carrier alphabet, so it contains
    # letters as well as digits and symbols (and reads as noise, not words).
    enc = kb.encode("the quick brown fox jumps over the lazy dog",
                    rng=random.Random(3))
    assert any(c.isalpha() for c in enc)
    assert any(c.isdigit() for c in enc)
    assert any(not c.isalnum() for c in enc)


def test_shaping_full_charset_no_notdef(built_keys_path):
    import random
    text = "The Quick Brown Fox 99! @#$ (a) = ok?"
    enc = kb.encode(text, rng=random.Random(7))
    shaped = _shape(built_keys_path, enc)
    assert ".notdef" not in shaped


def test_uppercase_bowl_is_shared(built_keys_path):
    from cipher import charset
    left_glyphs = {charset.half_glyph_name(charset.left_slot(ch)) for ch in "OCGQ"}
    assert len(left_glyphs) == 1  # O C G Q share one left half-glyph
    shared = next(iter(left_glyphs))
    font = TTFont(built_keys_path)
    assert shared in font["glyf"]  # and that shared glyph is in the built font


def test_table_dump_reveals_no_code_to_letter_mapping(built_keys_path):
    font = TTFont(built_keys_path)
    # GSUB only ligates code carriers into opaque half-glyphs (h_<n>), never a
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
        assert re.fullmatch(r"h_\d+", kb.half_glyph_name(slot))


def test_half_glyph_lsb_matches_xmin(built_keys_path):
    from cipher import charset
    font = TTFont(built_keys_path)
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for slot in charset.half_slots():
        name = charset.half_glyph_name(slot)
        g = glyf[name]
        if getattr(g, "numberOfContours", 0) <= 0:
            continue
        g.recalcBounds(glyf)
        assert hmtx[name][1] == g.xMin


def test_keyboard_reveal_axis(built_keys_vf_path):
    f = TTFont(built_keys_vf_path)
    axes = {a.axisTag: a for a in f["fvar"].axes}
    assert "REVL" in axes
    assert axes["REVL"].defaultValue == 0


def test_keyboard_reveal_aligned_restores(built_keys_vf_path, built_keys_path):
    # Readable at the secret interpolation point (REVL=650), not the top. The
    # restored shape is the RESAMPLED true outline (uniform point structure),
    # so compare against the builder's expectation, not the raw static glyph.
    from fontbuild import decoy_reveal as dr
    aligned = TTFont(built_keys_path)
    inst = instantiateVariableFont(TTFont(built_keys_vf_path),
                                   {"REVL": dr.SECRET_REVL}, inplace=False)

    def bounds(glyphset, g):
        pen = BoundsPen(glyphset)
        glyphset[g].draw(pen)
        return pen.bounds

    sample_glyph = kb.half_glyph_name(kb.half_slots()[0])
    expected = dr.expected_true_glyphs(aligned)[sample_glyph]
    got = bounds(inst.getGlyphSet(), sample_glyph)
    want = (expected.xMin, expected.yMin, expected.xMax, expected.yMax)
    assert got and all(abs(x - y) <= 2 for x, y in zip(want, got))


def test_plain_letters_render_as_inked_carriers(built_keys_path):
    # Normally-typed letters must NOT decode: A-Z / a-z map to their carrier
    # glyphs (kc_<hex>), which carry meaningless fragment ink, so stray text
    # renders as noise (not blank, not readable letters). Only the cipher
    # stream (carrier codes -> ligatures) reads as words.
    from cipher import charset
    font = TTFont(built_keys_path)
    glyf = font["glyf"]
    best = font.getBestCmap()
    for ch in charset.LOWER + charset.UPPER:
        g = best.get(ord(ch))
        assert g is not None, ch
        assert re.fullmatch(r"kc_[0-9A-F]{4}", g), \
            f"{ch!r} -> {g!r} (should be a carrier glyph)"
        assert glyf[g].numberOfContours > 0, f"{ch!r} carrier is blank"


def test_every_carrier_has_ink_except_pad(built_keys_path):
    from cipher import charset
    font = TTFont(built_keys_path)
    glyf = font["glyf"]
    for ch in kb.CODE_ALPHABET:
        assert glyf[kb.carrier_glyph_name(ch)].numberOfContours > 0, repr(ch)
    pad = kb.carrier_glyph_name(charset.PAD)
    assert glyf[pad].numberOfContours == 0  # pad stays an invisible blank


def test_encoded_stream_fully_ligates(built_keys_path):
    # Every 2-char code must collapse into exactly one half-glyph: each ciphered
    # character -> 2 half-glyphs, while a literal space stays one space glyph.
    # A stray carrier that fails to ligate would leak extra glyphs.
    text = "The Quick Brown Fox 99! @#$ (a) = ok?"
    enc = kb.encode(text, rng=random.Random(11))
    shaped = _shape(built_keys_path, enc)
    n_spaces = text.count(" ")
    n_ciphered = len(text) - n_spaces
    assert len(shaped) == 2 * n_ciphered + n_spaces
    space_glyph = TTFont(built_keys_path).getBestCmap()[ord(" ")]
    half_or_space = [g for g in shaped if re.fullmatch(r"h_\d+", g) or g == space_glyph]
    assert len(half_or_space) == len(shaped)
