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

## Current status: Phase 1 complete

The smallest end-to-end loop from the brief is working and verified:

- lowercase a-z, one deterministic PUA pair per letter
- spaces and punctuation pass through unchanged (not yet obfuscated)
- encoder, font builder, and a font-only decoder all agree
- verified in a browser: a human reads the plaintext; page-text extraction of
  the rendered block yields only PUA noise

Not yet implemented (next milestones): multiple homophonic pairs per letter with
random selection, zero-width noise injection, positional abuse, and full
case/digit/punctuation coverage. See the open questions in the brief.

## Layout

```
docs/superpowers/      design spec and implementation plans
cipher/carriers.py     carrier allocation: the one shared source of truth
cipher/encode.py       plaintext -> carrier codepoint stream
cipher/decode.py       font tables -> plaintext (round-trip oracle)
fontbuild/glyphs.py    add blank zero-width carrier glyphs to the base
fontbuild/features.py  cmap population + GSUB liga compilation
fontbuild/build_font.py  orchestrate the pipeline -> dist/SoulsOnly.ttf
tools/make_preview.py  generate dist/preview.html
tests/                 pytest suite (run via python -m pytest)
base/Jost-Regular.ttf  instanced OFL base font (glyph outlines)
dist/SoulsOnly.ttf     the built cipher font
```

## Setup and run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
bash scripts/fetch_base_font.sh        # if base/Jost-Regular.ttf is missing

./.venv/bin/python -m fontbuild.build_font   # build the font
./.venv/bin/python -m pytest                 # run the suite
./.venv/bin/python tools/make_preview.py     # regenerate the preview
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
