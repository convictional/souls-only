"""Generate test/preview.html embedding an encoded sample in the cipher font.

The rendered paragraph (with the font applied) should read as plaintext to a
human. The same bytes, shown in a fallback font and as a copy-paste box, are
PUA garbage. Open the file in a browser to see the decoupling.

    python test/make_preview.py && open test/preview.html
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from encode import encode  # noqa: E402

SAMPLE = "the quick brown fox jumps over the lazy dog"
OUT = os.path.join(HERE, "preview.html")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Souls Only - glyph-layer cipher preview</title>
<style>
  @font-face {{
    font-family: "Souls Only";
    src: url("../build/SoulsOnly.ttf") format("truetype");
  }}
  body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 50rem;
         margin: 3rem auto; padding: 0 1rem; color: #222; line-height: 1.5; }}
  h1 {{ font-size: 1.3rem; }}
  .label {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .05em;
            color: #888; margin: 1.5rem 0 .3rem; }}
  .cipher {{ font-family: "Souls Only"; font-size: 2rem; line-height: 1.3;
             /* standard + contextual ligatures must be on (they are by default) */
             font-feature-settings: "liga" 1, "calt" 1; }}
  .raw {{ font-family: ui-monospace, Menlo, monospace; font-size: 1rem;
          background: #f4f4f4; padding: .75rem; border-radius: 6px;
          word-break: break-all; white-space: pre-wrap; }}
  .note {{ font-size: .85rem; color: #666; }}
</style>
</head>
<body>
  <h1>Human-readable, AI-illegible: glyph-layer cipher</h1>
  <p class="note">Plaintext below: <code>{plaintext}</code></p>

  <div class="label">Rendered with the cipher font (what a human sees)</div>
  <p class="cipher">{encoded}</p>

  <div class="label">The same bytes in a normal font (what a scraper/LLM/copy-paste sees)</div>
  <div class="raw">{encoded}</div>

  <div class="label">The same bytes as explicit codepoints</div>
  <div class="raw">{codepoints}</div>

  <p class="note">If the font loaded, the first block reads as the plaintext
  while the lower blocks are Private Use Area noise. Try selecting and copying
  the first block: you get the noise, not the words.</p>
</body>
</html>
"""


def main() -> int:
    encoded = encode(SAMPLE)
    codepoints = " ".join(f"U+{ord(c):04X}" for c in encoded)
    html = TEMPLATE.format(
        plaintext=SAMPLE,
        encoded=encoded,
        codepoints=codepoints,
    )
    with open(OUT, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
