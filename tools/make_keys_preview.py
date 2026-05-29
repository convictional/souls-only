"""Generate dist/keys.html: the keyboard-typeable Souls Keys font on the REVL
slider, fed by the keyboard encoder (cipher.keyboard). This is what the physical
keyboard's output looks like when rendered by the Souls Keys font.

    python -m fontbuild.build_keyboard   # builds SoulsKeys.ttf + SoulsKeys-VF.ttf
    python tools/make_keys_preview.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cipher import keyboard as kb  # noqa: E402

SAMPLE = (
    "Souls Keys now renders the FULL charset: Uppercase, digits 0123456789, "
    "and symbols !@#$%&*()-+=/?;:'\",.<> all tile into readable glyphs.\n\n"
    "The Quick Brown Fox Jumps Over 13 Lazy Dogs! (cost: $4.50 @ 90% off?) "
    "Email a.b@example.com -- the bytes are noise; the font is the decoder."
)
OUT = os.path.join(ROOT, "dist", "keys.html")
VF = os.path.join(ROOT, "dist", "SoulsKeys-VF.ttf")

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Souls Keys - keyboard cipher + reveal</title>
<style>
  @font-face {{
    font-family:"Souls Keys VF";
    src:url("SoulsKeys-VF.ttf?v={cachebust}") format("truetype");
  }}
  body {{ font-family:-apple-system,system-ui,sans-serif; max-width:60rem;
         margin:0 auto; padding:0 1rem 6rem; color:#222; }}
  .controls {{ position:sticky; top:0; background:#fff; padding:1rem 0 .6rem;
               border-bottom:1px solid #eee; z-index:2; }}
  input[type=range] {{ width:100%; }}
  .val {{ font-family:ui-monospace,Menlo,monospace; color:#666; }}
  .label {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.05em;
            color:#888; margin:1.4rem 0 .4rem; }}
  .cipher {{ font-family:"Souls Keys VF"; font-size:1.7rem; line-height:1.7;
             white-space:pre-wrap; font-feature-settings:"liga" 1;
             font-variation-settings:"REVL" 0; min-height:55vh; }}
  .raw {{ font-family:ui-monospace,Menlo,monospace; font-size:.95rem;
          background:#f4f4f4; padding:.75rem; border-radius:6px;
          word-break:break-all; color:#555; }}
  .note {{ font-size:.85rem; color:#666; margin-top:1.5rem; }}
</style></head><body>
  <div class="controls">
    <input type="range" id="r" min="0" max="1000" value="0">
    <div>REVL = <span class="val" id="v">0</span> &nbsp; (drag right to reveal)</div>
  </div>
  <div class="label">Rendered with Souls Keys (what a human sees)</div>
  <div class="cipher" id="c">{encoded}</div>
  <div class="label">The raw bytes a keyboard types / a scraper sees</div>
  <div class="raw">{encoded}</div>
  <p class="note">Every letter is two random 2-char codes (4 ASCII symbols). The
  font ligates each code into a half-glyph and tiles the halves into the letter;
  the REVL axis scatters and reveals. The keyboard firmware emits exactly these
  bytes (see demo/qmk).</p>
  <script>
    const r = document.getElementById('r');
    const c = document.getElementById('c');
    const v = document.getElementById('v');
    r.addEventListener('input', () => {{
      c.style.fontVariationSettings = '"REVL" ' + r.value;
      v.textContent = r.value;
    }});
  </script>
</body></html>
"""


def main() -> int:
    encoded = kb.encode(SAMPLE)
    cachebust = int(os.path.getmtime(VF)) if os.path.exists(VF) else 0
    with open(OUT, "w") as fh:
        fh.write(TEMPLATE.format(encoded=encoded, cachebust=cachebust))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
