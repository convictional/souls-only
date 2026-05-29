# Souls Only: a human-readable, AI-illegible typeface

A font whose **rendered glyphs** spell readable text while the **stored
codepoint stream** (what copy-paste, HTML/PDF extraction, and scrapers see) is
Private Use Area noise. The font is the decoder, applied only at the rendering
layer. A paired Python encoder turns plaintext into the obfuscated stream.

This is a craft and statement project, not a claim of unbreakable security. See
Limitations in `font-cipher-brief.md`.

## How it works

A font has two streams people usually conflate: the **codepoint stream** (stored
bytes) and the **glyph stream** (what is drawn after `cmap` and GSUB run). This
project decouples them:

- The encoder maps each letter to a pair of PUA codepoints (semantically empty
  to an LLM, and not the real letters).
- The font maps each PUA codepoint to a blank, zero-width glyph in `cmap`, so
  the raw stream renders as nothing meaningful.
- A GSUB `liga` rule collapses each PUA pair into the one real letter glyph
  borrowed from the base font. So a human reading the rendered text sees the
  true words, while the bytes stay garbage.

Because two codepoints collapse into one glyph, the stored codepoint count and
the rendered glyph count deliberately diverge.

## Current status: Phase 4 complete (all phases built)

Decoupling, homophones, zero-width noise, shared-ambiguous fragments, and the
in-font scatter-to-align reveal are all working and verified:

- lowercase a-z, with frequency-tiered homophones (6 carriers for the most
  common letters down to 1 for the rarest), realized as distinct glyph IDs with
  identical outlines so the image is unchanged while carrier frequency flattens
- the encoder picks a random homophone per letter and sprinkles zero-width noise
  codepoints between letters (never inside a pair)
- two letter classes render as shared-ambiguous half-glyphs composed purely
  through cmap, with no GSUB rule: the bowl class `a c d e g o q` shares one
  canonical left bowl, the stem class `m n r u` shares one left stem. Glyph
  names are opaque, so a font-table dump reveals only meaningless half-shapes
  and never a fragment-to-letter mapping
- fragment carriers also come in homophone pools, so the common fragment letters
  stay frequency-flat
- the decoder reverses ligature letters from the font and fragment letters from
  the cipher tables (the font intentionally documents no fragment mapping), and
  round-trips arbitrary random streams (homophones + noise + fragments) back to
  plaintext

Known limit (by design): the shared left fragment is a single compromise image
reused across a class. The bowl class `a c d e g o q` shares cleanly. The stem
class `m n r u` does not: a stem clipped from a real letter is not a pure bar,
so those letters carry a faint hairline seam. The deferred fix is a hand-drawn
synthetic shared-stem glyph (see the TODO in `fontbuild/fragments.py`).

The reveal (Phase 4) is a variable font built from two masters on a custom
`REVL` axis: at `REVL` = 0 (the default, so the safe state is illegible) every
glyph is warped out of recognition by a random non-uniform transform plus
per-control-point jitter; at `REVL` = 1000 every point interpolates back to its
true position and the text assembles. The entire decode and reveal mechanism
lives in the font (`cmap`, `GSUB`, fragment composition, and `fvar`/`gvar`); a
page contributes only the single `REVL` axis value via one control. The axis is
unnamed and there is no legible named instance, so the reveal value is not
handed to an automated reader for free.

Honest limit (restated from the spec): the `REVL` value is one bounded number,
so an automated attacker can sweep axis values and OCR the legible frame. This
layer is the most portable and self-contained reveal, and the weakest against
automated vision. It is a statement device, scoped as such.

Not yet implemented: full case/digit/punctuation coverage, and the GPOS
position-variation refinement of the reveal (this build uses outline variation).
See the integrated design spec under `docs/superpowers/specs/`.

## Keyboard-typeable variant (Souls Keys)

The PUA font above is not typeable on a hardware keyboard (USB HID cannot send
Private Use Area codepoints). `Souls Keys` is a refactor of the same engine for a
physical cipher keyboard: every letter renders as two half-glyphs, each
addressed by a pool of 2-character ASCII codes, so a letter is typed as two
random codes (four ASCII symbols, homophones). A GSUB ligature collapses each
code into its half-glyph and the halves tile into the letter; the same `REVL`
reveal applies. `cipher/keyboard.py` is the single source of truth that drives
the font GSUB, the QMK firmware table, and the browser demo. See `demo/` for the
keyboard build, the QMK keymap, and the live demo page.

## Layout

```
docs/superpowers/      design spec and implementation plans
cipher/carriers.py     carrier allocation: the one shared source of truth
cipher/encode.py       plaintext -> carrier codepoint stream
cipher/decode.py       font tables -> plaintext (round-trip oracle)
fontbuild/glyphs.py    add blank zero-width carrier glyphs to the base
fontbuild/features.py  cmap population + GSUB liga compilation
fontbuild/build_font.py  orchestrate the pipeline -> dist/SoulsOnly.ttf
fontbuild/fragments.py  shared-ambiguous half-glyph slicing (skia-pathops), reused
fontbuild/reveal.py    build the REVL variable reveal font from two masters
cipher/keyboard.py     keyboard track: ASCII code layer (reuses carriers routing)
fontbuild/build_keyboard.py  build dist/SoulsKeys.ttf (+ REVL) from the engine
tools/make_qmk_table.py      generate the QMK firmware table from cipher/keyboard
tools/make_demo_assets.py    generate the browser demo table + copy the VF
demo/                  the physical cipher keyboard demo (QMK keymap, runbook, page)
tools/make_preview.py  generate dist/preview.html (static cipher preview)
tools/make_reveal_preview.py  generate dist/reveal.html (the REVL slider)
tests/                 pytest suite (run via python -m pytest)
base/Jost-Regular.ttf  instanced OFL base font (glyph outlines)
dist/SoulsOnly.ttf     the built cipher font (static)
dist/SoulsOnly-VF.ttf  the variable reveal font (REVL axis)
```

## Setup and run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
bash scripts/fetch_base_font.sh        # if base/Jost-Regular.ttf is missing

./.venv/bin/python -m fontbuild.build_font    # build the static cipher font
./.venv/bin/python -m fontbuild.reveal        # build the REVL variable font
./.venv/bin/python -m pytest                  # run the suite
./.venv/bin/python tools/make_preview.py         # static cipher preview
./.venv/bin/python tools/make_reveal_preview.py  # the REVL scatter-reveal slider
# then: python -m http.server 8753  and open dist/reveal.html

# keyboard-typeable variant (Souls Keys) + its demo:
./.venv/bin/python -m fontbuild.build_keyboard   # dist/SoulsKeys.ttf + SoulsKeys-VF.ttf
./.venv/bin/python tools/make_qmk_table.py       # demo/qmk/cipher_table.h
./.venv/bin/python tools/make_demo_assets.py     # demo/cipher_table.js + demo/SoulsKeys-VF.ttf
# then open demo/index.html  (see demo/BUILD.md for the hardware runbook)
```

## Encode and decode by hand

```bash
./.venv/bin/python -m cipher.encode "hello world"            # prints PUA stream
./.venv/bin/python -m cipher.encode "hello world" \
  | ./.venv/bin/python -m cipher.decode                      # prints "hello world"
```

## Base font and license

Glyph outlines come from [Jost](https://github.com/indestructible-type/Jost), licensed under
the SIL Open Font License, instanced to a static Regular. Redistribution of the
built font must carry the OFL notice.
