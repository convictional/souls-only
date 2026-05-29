import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADER = os.path.join(ROOT, "demo", "qmk", "cipher_table.h")


def _generate():
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_qmk_table.py")],
                   check=True, cwd=ROOT)
    return open(HEADER).read()


def test_header_has_full_charset_pools_and_index():
    from cipher import charset, keyboard as kb
    h = _generate()
    assert f"#define KB_HOMOPHONES {kb.HOMOPHONES}" in h
    assert f"#define KB_NCHARS {len(charset.CHARSET)}" in h
    assert "static const char *const kb_left[KB_NCHARS][KB_HOMOPHONES]" in h
    assert "static const char *const kb_right[KB_NCHARS][KB_HOMOPHONES]" in h
    assert "kb_index(uint16_t keycode, bool shifted)" in h
    assert "case KC_A:" in h
    assert "case KC_SLSH:" in h
    assert "#define KB_PAD" in h


def test_pools_match_cipher_tables():
    from cipher import charset, keyboard as kb
    _generate()
    h = open(HEADER).read()
    a_left = kb.left_codes("a")
    row = "{ " + ", ".join(f'"{c}"' for c in a_left) + " }"
    assert row in h
