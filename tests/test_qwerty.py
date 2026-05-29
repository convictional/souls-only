from cipher import qwerty
from cipher import charset


def test_layout_covers_every_printable_char_once():
    produced = set()
    for kc, (unshifted, shifted) in qwerty.LAYOUT.items():
        produced.add(unshifted)
        produced.add(shifted)
    assert produced == set(charset.PRINTABLE)


def test_space_key_present():
    assert qwerty.SPACE_KEYCODE == "KC_SPC"


def test_known_mappings():
    assert qwerty.LAYOUT["KC_A"] == ("a", "A")
    assert qwerty.LAYOUT["KC_1"] == ("1", "!")
    assert qwerty.LAYOUT["KC_SLSH"] == ("/", "?")
    assert qwerty.LAYOUT["KC_GRV"] == ("`", "~")
    assert qwerty.LAYOUT["KC_BSLS"] == ("\\", "|")
