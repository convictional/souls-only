# Build & demo runbook (Montreal onsite, Mon Jun 1)

Goal: a wired Keychron, reflashed so each lowercase key types its cipher code,
plus a laptop showing the Souls Demo font decoding it live. Build Saturday,
keep Sunday as buffer and rehearsal.

The hard dependency is buying a genuinely **QMK/VIA** board (see SHOPPING.md).
Everything else is in this folder.

---

## Part A — Laptop side (do this first; no hardware needed)

This works today, before the keyboard arrives, and proves the concept on its own.

1. Build the font and the matching QMK code table (one command keeps them synced):
   ```
   .venv/bin/python demo/build_demo_font.py
   ```
   Produces `demo/SoulsDemo.ttf` and `demo/qmk/cipher_table.h`.

2. Open the demo page in a browser:
   ```
   open demo/index.html
   ```

3. Smoke test WITHOUT the keyboard, two ways:
   - Paste a raw code string into the left box. `hello` encodes to
     `kqkkkjkqjkqjkxk`; paste it and you read **hello** while the right box shows
     garbage.
   - Or tick **"Simulate cipher keyboard"** and just type normally: the page
     encodes each letter into its code as you type, so the left box reads
     normally and the right box fills with garbage. This reproduces exactly what
     the real keyboard does.

   Either way, click "Toggle the font off" to reveal the same bytes are gibberish
   without the font. That toggle IS the demo.

   IMPORTANT: the cipher lives in the keyboard, not the font. The font only
   DECODES codes; it leaves normal letters alone. So typing `dog` on a normal
   keyboard with Simulate OFF shows `dog` (nothing encoded it). Simulate mode is
   the software stand-in for the keyboard, and your no-hardware backup for Monday.

---

## Part B — Keyboard side

### B1. Fastest smoke test: VIA macros (no compiling)

Use this to confirm the keyboard can emit multi-key codes at all, and as a
fallback if compiling runs long. VIA macro slots are limited (~16), so this
covers a demo phrase, not the whole alphabet.

1. Open https://usevia.app (Chrome/Edge) with the keyboard plugged in; authorize it.
2. In **Macros**, define one macro per letter you need, typing the code from
   `demo/qmk/cipher_table.h` (e.g. macro M0 = `kqkkk` is wrong, that is two
   letters; one macro = one letter's 3-char code, e.g. `a` = `kkk`).
3. In **Keymap**, assign those macros onto the matching letter keys.
4. Open `demo/index.html`, focus the left box, type those letters: they should
   read correctly. This proves the loop end to end.

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
   add the `#include "cipher_table.h"`, the `static bool cipher_on`, and the
   `process_record_user` body. If the default `keymap.c` already defines
   `process_record_user`, keep its body and add ours at the top.

3. Compile and flash:
   ```
   qmk compile -kb keychron/v1/v1_max/ansi_encoder -km cipher
   ```
   Put the board into bootloader (Keychron: usually a reset button on the PCB, or
   the documented Fn combo), then flash the resulting firmware with **QMK Toolbox**
   or `qmk flash`.

4. Test: plug in wired, press **Right Ctrl** to turn cipher mode ON, open
   `demo/index.html`, and type. Letters should read correctly; the raw pane shows
   garbage. Press Right Ctrl again to type normally (passwords, the URL bar, etc).

### Recovery
If anything goes wrong, reflash Keychron's factory firmware (from their QMK guide
above or the Keychron Launcher) to restore the board. The board is never bricked
as long as you can enter bootloader.

---

## Demo script (≈60 seconds)

1. "This keyboard types a cipher. Watch." Open `demo/index.html`.
2. Turn cipher mode ON (Right Ctrl). Type a sentence. It reads normally on the left.
3. Point at the right pane: "That is what the computer actually stored. That is
   what a scraper or an LLM sees."
4. Click "Toggle the font off": the readable text collapses into the same garbage.
   "The font is the only decoder, and it only runs at the rendering layer. The
   bytes are always noise."
5. Turn cipher OFF, type your name normally. "And it is still a normal keyboard."

## Known limits (say them if asked)
- Lowercase letters only in the demo; capitals/punctuation pass through unciphered.
- Deterministic single code per letter (no homophones/noise yet), so this demo is
  a monoalphabetic substitution. The real design layers in homophones, contextual
  rules, and noise to defeat frequency analysis.
- Wired for reliability; the Bluetooth full build (KMK on nRF52840) is the v2.
