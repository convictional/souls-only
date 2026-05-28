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

## Current status: milestone 1 (closed)

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
font-cipher-brief.md     the design brief (source of intent)
src/cipher.py            the mapping tables: the one shared source of truth
src/encode.py            plaintext  -> PUA codepoint stream
src/build_font.py        base font + cipher.py -> build/SoulsOnly.ttf
src/decode.py            font tables -> plaintext (test oracle / "the adversary")
test/roundtrip.py        encode -> decode -> assert equality, on sample texts
test/make_preview.py     generate test/preview.html for a browser
base/Inter-Regular.ttf   instanced OFL base font (glyph outlines)
build/SoulsOnly.ttf      the built cipher font
build/fea/cipher.fea     the generated OpenType feature file (inspectable)
scripts/fetch_base_font.sh  re-fetch and instance the base font
```

## Setup and run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt

# if base/Inter-Regular.ttf is missing:
bash scripts/fetch_base_font.sh

./.venv/bin/python src/build_font.py      # build the font
./.venv/bin/python test/roundtrip.py      # run the round-trip checks

# visual check in a browser:
./.venv/bin/python test/make_preview.py
./.venv/bin/python -m http.server 8753    # then open localhost:8753/test/preview.html
```

## Encode and decode by hand

```bash
./.venv/bin/python src/encode.py "hello world"            # prints PUA stream
./.venv/bin/python src/encode.py "hello world" \
  | ./.venv/bin/python src/decode.py                      # prints "hello world"
```

## Base font and license

Glyph outlines come from [Inter](https://github.com/rsms/inter), licensed under
the SIL Open Font License, instanced to a static Regular. Redistribution of the
built font must carry the OFL notice.
