# Project: Human-Readable, AI-Illegible Typeface (Glyph-Layer Cipher)

## Goal
Build a font where the **rendered glyphs** spell human-readable text, but the **underlying codepoint stream** (what gets copy-pasted, extracted from HTML/PDF, or scraped and fed to an LLM) is noise. The font itself acts as the decoder, applied only at the rendering layer, never to the stored bytes. Plus a paired Python encoder that turns plaintext into the obfuscated codepoint stream.

This is a deliberate craft / statement project, not a claim of unbreakable security (see Limitations).

## Core architectural insight
A font has two separate streams people usually conflate:
- **Codepoint stream:** the stored bytes. What a scraper/LLM sees. What copy-paste yields.
- **Glyph stream:** what gets drawn after `cmap` maps codepoints to glyphs and GSUB/GPOS transform them.

Normally these correspond tightly. This project deliberately **decouples** them: glyph stream = the truth, codepoint stream = garbage. The encoder produces the garbage; the font's GSUB/cmap rules visually reconstruct the truth.

## Mechanisms available (weakest to strongest)
1. **`cmap` remap** (floor, weak): codepoint X points at glyph that looks like Y. This is a monoalphabetic substitution cipher, trivially broken by frequency analysis even without tools. Not sufficient alone.
2. **GSUB ligature substitution** (the unlock): collapses a *sequence* of input glyphs into a *single* output glyph. So codepoints "fi" can render as a glyph shaped like "e". Breaks the one-to-one relationship; codepoint count and glyph count diverge; word boundaries in the stream stop matching word boundaries on screen.
3. **`calt` chaining contextual substitution** (state machine): "glyph X, when preceded by Y and followed by Z, becomes W." The *same* codepoint can render as *different* letters depending on context, and *different* codepoints can render as the *same* letter. This is a polyalphabetic cipher in font rules, which is what defeats frequency analysis (no stable per-symbol mapping to count).
4. **GPOS kerning** (positioning, not shape): not central to the cipher, but available.

## Candidate schemes (combine these)
**A. Homophonic pairs in the Private Use Area (primary scheme).**
- Encode each plaintext letter as a *pair* of codepoints drawn from Unicode PUA (U+E000 to U+F8FF).
- A GSUB ligature rule renders each pair as one visible glyph.
- Two payoffs:
  1. PUA codepoints are semantically empty: an LLM sees no dictionary words, no English structure, just meaningless private characters.
  2. Give each letter *many* possible pairs and pick randomly at encode time. The most frequent letters (e, t, a, o) get many encodings that all render identically. This flattens the frequency distribution (classical homophonic cipher trick, implemented at the glyph layer).
- Encoder does: plaintext -> randomized PUA-pair sequence. Font GSUB undoes it visually.

**B. Noise injection.**
- Intersperse junk PUA codepoints that the font maps to zero-advance-width (invisible) glyphs.
- Humans never see them; the text stream is padded with garbage that wrecks tokenization and pair-frequency attacks.

**C. Positional abuse (optional, advanced).**
- Hijack OpenType positional features (`init`/`medi`/`fina`/`isol`, the Arabic-shaping machinery) so a glyph's rendering depends on its position in a word. Adds an independent axis of context dependence on top of A and B.

## Limitations (design with clear eyes)
- **The font is the key, and it ships to every reader.** Anyone can download the web font and parse its `cmap`/GSUB with `fontTools` in ~20 lines of Python to reconstruct the mapping. Strong against *bulk, undifferentiated* scraping (nobody writes a per-site font decoder at scale); weak against a *targeted* adversary.
- **Vision bypass.** Render + screenshot + a multimodal model reads the pixels. This defends the *text stream*, not the *pixels*.
- **Collateral cost:** breaks copy-paste, screen readers (accessibility), and search/SEO indexing. Specifically defeats GEO. So this is a wrong fit for content meant to be cited by AI engines, and a right fit for a deliberate statement piece where "a human must read this" is the point.

## Recommended tooling / build path
Fits a code-first workflow:
- **`fontTools`** (Python) for everything: load an open base font for glyph shapes, script the `cmap` remap, build GSUB rules.
- Author OpenType features in **FEA** (Adobe feature file format) and compile with **`feaLib`**, or manipulate the tables directly.
- Write the **encoder in Python alongside the font** so both halves of the cipher are versioned together. They must stay in sync: the encoder's pair tables and the font's ligature rules are the same secret expressed twice.
- Pick a permissively licensed open base font for the glyph outlines (e.g. an OFL face) so redistribution is clean.

## Suggested first milestone (smallest end-to-end loop)
Prove the decoupling works before adding homophonic randomness or noise:
1. Pick an OFL base font. Confirm it loads and re-saves with `fontTools`.
2. Define a tiny mapping for a single test word: assign each letter ONE PUA pair (deterministic for now).
3. Write the Python encoder: plaintext -> PUA-pair codepoint string.
4. Build the GSUB ligature rules (FEA -> `feaLib`) so each PUA pair renders as the correct visible glyph.
5. Map the PUA codepoints in `cmap` to placeholder/invisible glyphs so the *unligated* stream shows nothing meaningful.
6. Test: render the encoded string in a browser/HTML page with the font, confirm a human sees the real word, confirm the raw HTML/copy-paste yields PUA garbage.

Once that loop is closed, layer in: (a) multiple homophonic pairs per letter with random selection, (b) zero-width noise injection, (c) a round-trip test harness that verifies every encoded sample renders back to the original plaintext.

## Open design questions to decide while building
- Character set scope: lowercase only first, or full case + punctuation + digits?
- How many homophones per letter (tradeoff: flatter frequency vs. font size and rule count)?
- Noise density and whether noise is purely zero-width or also includes decoy renderable glyphs.
- Whether to ship a "decoder" utility (parses the font + reverses it) for your own testing, kept private.

## Style note
No em dashes in any generated writing or docs for this project.
