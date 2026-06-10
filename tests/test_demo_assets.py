import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, "demo", "cipher_table.js")


def _generate():
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_demo_assets.py")],
                   check=True, cwd=ROOT)
    return open(JS).read()


def test_js_has_full_charset_and_pad_and_encoder():
    from cipher import charset
    js = _generate()
    left = json.loads(re.search(r"const KB_LEFT = (\{.*?\});", js, re.S).group(1))
    right = json.loads(re.search(r"const KB_RIGHT = (\{.*?\});", js, re.S).group(1))
    for ch in charset.PRINTABLE:
        assert ch in left and ch in right
    # Space is not ciphered, so it carries no codes -- the page emits it as-is.
    assert " " not in left and " " not in right
    assert "function cipherEncodeChar" in js
    assert "const KB_PAD" in js


def test_js_pools_match_cipher():
    from cipher import keyboard as kb
    js = _generate()
    left = json.loads(re.search(r"const KB_LEFT = (\{.*?\});", js, re.S).group(1))
    assert left["A"] == kb.left_codes("A")
