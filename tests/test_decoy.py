"""Tests for cipher.decoy: per-focal-point substitution mappings.

At each decoy focal point on the REVL axis every glyph impersonates a real
character (so OCR reads confident characters), but the WRONG one. A mapping
must respect the shared-left-half classes: all members of a fragment class
must map into a single target class, so the one shared left glyph composes
correctly with every member's right half.
"""

from cipher import charset
from cipher import decoy


def test_mapping_is_deterministic():
    assert decoy.focal_mapping(0) == decoy.focal_mapping(0)
    assert decoy.focal_mapping(2, seed=99) == decoy.focal_mapping(2, seed=99)


def test_mappings_differ_across_focals():
    maps = [decoy.focal_mapping(k) for k in range(4)]
    for i in range(len(maps)):
        for j in range(i + 1, len(maps)):
            assert maps[i] != maps[j]


def test_mapping_covers_charset_and_stays_inside_it():
    m = decoy.focal_mapping(0)
    assert set(m) == set(charset.CHARSET)
    assert all(v in charset.CHARSET for v in m.values())


def test_shared_classes_map_into_the_lowercase_bowl_class():
    # The shared left half-glyph renders ONE image at a focal point, so every
    # member of a fragment class must map into a single target class. We route
    # ALL shared classes into the lowercase bowl (acdegoq): it slices cleanly
    # and keeps decoys lowercase (a normal-looking message).
    for k in range(5):
        m = decoy.focal_mapping(k)
        for cls, members in charset.FRAGMENT_CLASSES.items():
            target_classes = {charset.class_of(m[ch]) for ch in members}
            assert target_classes == {"lbowl"}, (k, cls, target_classes)


def test_shared_class_members_get_distinct_targets():
    # No reuse within a class: each member maps to a different decoy letter.
    for k in range(5):
        m = decoy.focal_mapping(k)
        for cls, members in charset.FRAGMENT_CLASSES.items():
            targets = [m[ch] for ch in members]
            assert len(set(targets)) == len(targets), (k, cls, targets)


def test_letters_map_to_lowercase_letters():
    # Decoys should read like a normal (mostly lowercase) message, not SHOUT.
    for k in range(5):
        m = decoy.focal_mapping(k)
        for src, tgt in m.items():
            if src.isalpha():
                assert tgt.isalpha() and tgt.islower(), (k, src, tgt)
        assert not any(v.isupper() for v in m.values()), k


def test_digits_and_symbols_keep_their_category():
    # A normal message keeps numbers as numbers and punctuation as punctuation.
    for k in range(5):
        m = decoy.focal_mapping(k)
        for src, tgt in m.items():
            if src.isdigit():
                assert tgt.isdigit(), (k, src, tgt)
            elif not src.isalnum():
                assert not tgt.isalnum(), (k, src, tgt)


def test_decoys_use_many_distinct_letters():
    # Variety: letter targets should span most of the lowercase alphabet, not
    # collapse onto a handful of repeated shapes.
    for k in range(5):
        m = decoy.focal_mapping(k)
        letter_targets = {t for s, t in m.items() if s.isalpha()}
        assert len(letter_targets) >= 18, (k, len(letter_targets))


def test_no_character_targets_the_degenerate_stem_class():
    # No character (shared OR unshared) may map to a lowercase stem letter:
    # the stem's left half is a degenerate sliver that never tiles into a
    # coherent glyph at a decoy focal point.
    stem = set(charset.FRAGMENT_CLASSES["lstem"])
    for k in range(5):
        m = decoy.focal_mapping(k)
        assert not (set(m.values()) & stem), (k, set(m.values()) & stem)


def test_mapping_is_mostly_non_identity():
    for k in range(4):
        m = decoy.focal_mapping(k)
        moved = sum(1 for ch, v in m.items() if ch != " " and v != ch)
        assert moved >= 0.9 * (len(m) - 1), k
