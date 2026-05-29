"""Generate dist/preview.html embedding an encoded sample in the cipher font.

The rendered block should read as plaintext; the same bytes in a normal font are
PUA noise.

    ./.venv/bin/python tools/make_preview.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cipher.encode import encode  # noqa: E402

SAMPLE = "the quick brown fox jumps over the lazy dog"
OUT = os.path.join(ROOT, "dist", "preview.html")

TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Souls Only preview</title>
<style>
  @font-face {{ font-family:"Souls Only"; src:url("SoulsOnly.ttf") format("truetype"); }}
  body {{ font-family:-apple-system,system-ui,sans-serif; max-width:50rem; margin:3rem auto; padding:0 1rem; }}
  .label {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; color:#888; margin:1.5rem 0 .3rem; }}
  .cipher {{ font-family:"Souls Only"; font-size:2rem; font-feature-settings:"liga" 1; }}
  .raw {{ font-family:ui-monospace,Menlo,monospace; background:#f4f4f4; padding:.75rem; border-radius:6px; word-break:break-all; }}
</style></head><body>
  <p>Plaintext: <code>{plaintext}</code></p>
  <div class="label">Rendered with the cipher font (human sees)</div>
  <p class="cipher">{encoded}</p>
  <div class="label">Same bytes in a normal font (scraper sees)</div>
  <div class="raw">{encoded}</div>
</body></html>
"""


def main() -> int:
    encoded = encode(SAMPLE)
    with open(OUT, "w") as fh:
        fh.write(TEMPLATE.format(plaintext=SAMPLE, encoded=encoded))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
