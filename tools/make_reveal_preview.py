"""Generate dist/reveal.html: the scatter-to-align reveal with a slider.

The cipher text is set in the variable font at REVL = 0 (scattered, illegible).
Drag the slider to ramp REVL toward 1000 and the text assembles. The slider just
forwards a number into font-variation-settings; no reveal logic is in the page.

    python -m fontbuild.build_font && python -m fontbuild.reveal
    python tools/make_reveal_preview.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cipher.encode import encode  # noqa: E402

SAMPLE = (
    "a font where the rendered glyphs spell readable words while the stored "
    "bytes are noise. the font itself is the decoder, applied only when the "
    "glyphs are drawn, never to the text that is copied or scraped.\n\n"
    "drag the control and the scattered shapes gather into language. nothing "
    "in the page knows what it says. the words exist only as a shape the axis "
    "resolves, so the reader has to draw the message together to read it.\n\n"
    "this is a statement piece, not a fortress. anyone can read the font and "
    "reverse it. the point is that a human, and only a human at rest, can sit "
    "and watch the noise become a sentence."
)
OUT = os.path.join(ROOT, "dist", "reveal.html")
VF = os.path.join(ROOT, "dist", "SoulsOnly-VF.ttf")

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Souls Only - scatter reveal</title>
<style>
  @font-face {{
    font-family:"Souls Only VF";
    src:url("SoulsOnly-VF.ttf?v={cachebust}") format("truetype");
  }}
  body {{ font-family:-apple-system,system-ui,sans-serif; max-width:60rem;
         margin:0 auto; padding:0 1rem 6rem; color:#222; }}
  .controls {{ position:sticky; top:0; background:#fff; padding:1rem 0 .6rem;
               border-bottom:1px solid #eee; z-index:2; }}
  input[type=range] {{ width:100%; }}
  .val {{ font-family:ui-monospace,Menlo,monospace; color:#666; }}
  .label {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.05em;
            color:#888; margin:1.4rem 0 .4rem; }}
  .cipher {{ font-family:"Souls Only VF"; font-size:1.7rem; line-height:1.7;
             white-space:pre-wrap; font-feature-settings:"liga" 1;
             font-variation-settings:"REVL" 0; min-height:60vh; }}
  .note {{ font-size:.85rem; color:#666; margin-top:1.5rem; }}
</style></head><body>
  <div class="controls">
    <input type="range" id="r" min="0" max="1000" value="0">
    <div>REVL = <span class="val" id="v">0</span> &nbsp; (drag right to reveal)</div>
  </div>
  <div class="label">Cipher text on the REVL axis (default: scatter)</div>
  <div class="cipher" id="c">{encoded}</div>
  <p class="note">Plaintext is several paragraphs of lowercase prose. The reveal
  is the font's own REVL variation axis; the slider only forwards a number into
  font-variation-settings. No glyph geometry or positions are computed in page
  code.</p>
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
    encoded = encode(SAMPLE)
    cachebust = int(os.path.getmtime(VF)) if os.path.exists(VF) else 0
    with open(OUT, "w") as fh:
        fh.write(TEMPLATE.format(plaintext=SAMPLE, encoded=encoded,
                                 cachebust=cachebust))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
