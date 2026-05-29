# Build & demo runbook (Montreal onsite, Mon Jun 1)

Goal: a wired Keychron, reflashed so each lowercase key types its Souls Keys
cipher codes, plus a laptop showing the Souls Keys font decoding it live and the
REVL axis scattering/revealing the glyphs. Build Saturday, keep Sunday as buffer
and rehearsal.

The hard dependency is buying a genuinely **QMK/VIA** board (see SHOPPING.md).
Everything else is generated from the repo.

## The scheme (one source of truth)

Every lowercase letter is two half-glyphs. Each half-glyph is addressed by a
pool of 2-character ASCII codes, so a letter is typed as **two random codes =
four ASCII symbols** (homophones: different bytes every keypress). The Souls Keys
font ligates each code into a half-glyph and tiles the two halves into the
letter; the **REVL** variable axis scatters the glyphs at 0 and assembles them at
1000. `cipher/keyboard.py` is the single source of truth; it generates the font's
GSUB, the QMK table, and the browser demo table, so they cannot drift.

---

## Part A - Laptop side (do this first; no hardware needed)

This works today, before the keyboard arrives, and proves the concept on its own.
Run from the repo root.

1. Build the font (static + the REVL variable font):
   ```
   .venv/bin/python -m fontbuild.build_keyboard
   ```
   Produces `dist/SoulsKeys.ttf` and `dist/SoulsKeys-VF.ttf`.

2. Generate the matching QMK table and the browser-demo assets (one source of
   truth keeps them synced with the font):
   ```
   .venv/bin/python tools/make_qmk_table.py     # -> demo/qmk/cipher_table.h
   .venv/bin/python tools/make_demo_assets.py   # -> demo/cipher_table.js + demo/SoulsKeys-VF.ttf
   ```

3. Open the demo page:
   ```
   open demo/index.html
   ```

4. Smoke test WITHOUT the keyboard:
   - Leave **"Simulate cipher keyboard"** ticked and just type normally. The page
     encodes each letter into two random codes as you type, so the left box reads
     normally (Souls Keys font) and the right box fills with ASCII noise. This
     reproduces exactly what the real keyboard emits.
   - Drag **REVL** left: the glyphs scatter into noise; drag right: they assemble.
   - Click **"Toggle the font off"**: the readable text collapses into the same
     garbage bytes. That toggle, plus REVL, IS the demo.

   IMPORTANT: the cipher lives in the keyboard + font, not the page. The font only
   DECODES codes; normal letters are left alone. Simulate mode is the software
   stand-in for the keyboard, and your no-hardware backup for Monday.

---

## Part B - Keyboard side

### B1. Fastest smoke test: VIA macros (no compiling)

Confirms the board can emit multi-key codes at all, and is a fallback if
compiling runs long. VIA macro slots are limited (~16), so this covers a demo
phrase, not the whole alphabet. Note: macros are fixed strings, so this fallback
loses the per-keypress randomness (it picks one code per letter); it still
renders correctly, just without homophone variation.

1. Open https://usevia.app (Chrome/Edge) with the keyboard plugged in; authorize it.
2. In **Macros**, define one macro per letter you need. For each letter, pick any
   one left code + one right code for that letter from `demo/qmk/cipher_table.h`
   (e.g. `kb_left[0][0]` + `kb_right[0][0]` for `a`) and type the 4 characters as
   the macro body.
3. In **Keymap**, assign those macros onto the matching letter keys.
4. Open `demo/index.html` (turn Simulate **off**), focus the left box, type those
   letters: they should read correctly. This proves the loop end to end.

### B2. Full alphabet: custom QMK (the real demo)

1. Install QMK tooling and Keychron's fork (the Max boards are not in mainline QMK):
   ```
   # qmk CLI: https://docs.qmk.fm/#/newbs_getting_started
   git clone https://github.com/Keychron/qmk_firmware.git
   cd qmk_firmware
   ```
   Find the V1 Max keyboard under `keyboards/keychron/v1/v1_max` (check Keychron's
   QMK guide for the exact branch if the folder is missing on the default branch:
   https://www.keychron.com/blogs/news/how-to-set-up-qmk-environment-on-keychron-keyboards ).

2. Copy the default keymap to a new `cipher` keymap, then add the cipher logic:
   ```
   cp -r keyboards/keychron/v1/v1_max/ansi_encoder/keymaps/default \
         keyboards/keychron/v1/v1_max/ansi_encoder/keymaps/cipher
   cp <this-repo>/demo/qmk/cipher_table.h \
         keyboards/keychron/v1/v1_max/ansi_encoder/keymaps/cipher/
   ```
   Then merge `demo/qmk/keymap_cipher.c` into that keymap's `keymap.c`:
   add the `#include "cipher_table.h"`, the `static bool cipher_on` / `rng_seeded`
   state, and the `process_record_user` body (it emits a random left code then a
   random right code per letter). If the default `keymap.c` already defines
   `process_record_user`, keep its body and add ours at the top.

3. Compile and flash:
   ```
   qmk compile -kb keychron/v1/v1_max/ansi_encoder -km cipher
   ```
   Put the board into bootloader (Keychron: usually a reset button on the PCB, or
   the documented Fn combo), then flash with **QMK Toolbox** or `qmk flash`.

4. Test: plug in wired, press **Right Ctrl** to turn cipher mode ON, open
   `demo/index.html` (Simulate off), and type. Letters read correctly; the raw
   pane shows garbage. Press Right Ctrl again to type normally (passwords, the URL
   bar, etc).

### Recovery
If anything goes wrong, reflash Keychron's factory firmware (from their QMK guide
or the Keychron Launcher) to restore the board. The board is never bricked as
long as you can enter bootloader.

---

## Demo script (≈75 seconds)

1. "This keyboard types a cipher. Watch." Open `demo/index.html`.
2. Turn cipher mode ON (Right Ctrl). Type a sentence. It reads normally on the left.
3. Point at the right pane: "That is what the computer actually stored. That is
   what a scraper or an LLM sees. And it is different every keystroke."
4. Click "Toggle the font off": the readable text collapses into the same garbage.
   "The font is the only decoder, and it only runs at the rendering layer."
5. Drag REVL to 0: "By default the font doesn't even show the letters; they
   scatter. You pull the message together." Drag back to 1000.
6. Turn cipher OFF, type your name normally. "And it is still a normal keyboard."

## Known limits (say them if asked)
- Lowercase letters only; capitals/punctuation pass through unciphered.
- Codes are ASCII, so a determined reader can dump the font + table and reverse
  it; and the REVL reveal is one bounded axis, so an automated sweep + OCR can
  defeat it. This is a statement device: strong against bulk/casual scraping,
  weak against a targeted attacker. The font is the key, and it ships to readers.
- Homophones (random codes per keypress) defeat simple frequency analysis on the
  stream; the shared bowl/stem half-glyphs add image-level ambiguity.
- Wired for reliability; a Bluetooth build is the v2.
