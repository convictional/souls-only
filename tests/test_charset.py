from cipher import charset


def test_charset_is_full_printable_plus_space():
    assert charset.LOWER == "abcdefghijklmnopqrstuvwxyz"
    assert charset.UPPER == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert charset.DIGITS == "0123456789"
    assert len(charset.SYMBOLS) == 32
    assert len(charset.PRINTABLE) == 94
    assert charset.SPACE == " "
    assert charset.SPACE in charset.CHARSET and len(charset.CHARSET) == 95


def test_fragment_classes_include_uppercase_bowl():
    assert charset.FRAGMENT_CLASSES["lbowl"] == "acdegoq"
    assert charset.FRAGMENT_CLASSES["lstem"] == "mnru"
    assert charset.FRAGMENT_CLASSES["ubowl"] == "OCGQ"
    assert charset.CANONICAL == {"lbowl": "o", "lstem": "n", "ubowl": "O"}


def test_class_of():
    assert charset.class_of("a") == "lbowl"
    assert charset.class_of("n") == "lstem"
    assert charset.class_of("O") == "ubowl"
    assert charset.class_of("b") is None
    assert charset.class_of("5") is None


def test_left_slot_shares_within_class_only():
    assert charset.left_slot("a") == charset.left_slot("c") == "cls_lbowl"
    assert charset.left_slot("O") == charset.left_slot("Q") == "cls_ubowl"
    assert charset.left_slot("b") == "L_b"
    assert charset.left_slot("5") == "L_5"
    assert charset.left_slot(" ") == "SP_L"


def test_right_slot_is_per_char():
    assert charset.right_slot("a") == "R_a"
    assert charset.right_slot("O") == "R_O"
    assert charset.right_slot(" ") == "SP_R"


def test_half_slots_unique_and_cover_charset():
    slots = charset.half_slots()
    assert len(slots) == len(set(slots))
    for ch in charset.CHARSET:
        assert charset.left_slot(ch) in slots
        assert charset.right_slot(ch) in slots
    assert charset.half_glyph_name(slots[0]) == "h_0"


def test_pad_char_is_outside_normal_text():
    assert charset.PAD == "\\"
    assert charset.PAD not in charset.PRINTABLE_CODES_OK
    assert '"' not in charset.PRINTABLE_CODES_OK
