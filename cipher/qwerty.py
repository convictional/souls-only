"""US-QWERTY physical layout: QMK keycode -> (unshifted char, shifted char).

Pure data, shared by the QMK table generator and the browser demo generator so
the firmware and the demo agree on what each physical key types. Covers exactly
the 94 printable characters (space is handled separately via SPACE_KEYCODE).
"""

from __future__ import annotations

SPACE_KEYCODE = "KC_SPC"

LAYOUT: dict[str, tuple[str, str]] = {
    # letters
    **{f"KC_{c.upper()}": (c, c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"},
    # number row
    "KC_1": ("1", "!"), "KC_2": ("2", "@"), "KC_3": ("3", "#"),
    "KC_4": ("4", "$"), "KC_5": ("5", "%"), "KC_6": ("6", "^"),
    "KC_7": ("7", "&"), "KC_8": ("8", "*"), "KC_9": ("9", "("),
    "KC_0": ("0", ")"),
    # punctuation keys
    "KC_MINS": ("-", "_"), "KC_EQL": ("=", "+"),
    "KC_LBRC": ("[", "{"), "KC_RBRC": ("]", "}"), "KC_BSLS": ("\\", "|"),
    "KC_SCLN": (";", ":"), "KC_QUOT": ("'", '"'), "KC_GRV": ("`", "~"),
    "KC_COMM": (",", "<"), "KC_DOT": (".", ">"), "KC_SLSH": ("/", "?"),
}
