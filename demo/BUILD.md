# Build & demo runbook

Goal: a wired Keychron, reflashed so each key types its Souls Only cipher codes,
plus a laptop showing the Souls Only font decoding it live and the REVL axis
scattering/revealing the glyphs.

The hard dependency is a genuinely **QMK/VIA** board (this build used a
Keychron V1 Max). Everything else is generated from the repo.

## The scheme (one source of truth)

The cipher covers the full US-QWERTY printable charset: lowercase letters,
UPPERCASE letters (Shift+letter), digits 0-9, and all symbols. Shift handling
is done in the firmware, so every key on the board is ciphered. Each character
is two half-glyphs addressed by a pool of 2-character ASCII codes, so a
character is typed as **two random codes = four ASCII symbols** (homophones:
different bytes every keypress). The Souls Only font ligates each code into a
half-glyph and tiles the two halves into the character.

Every logical input is exactly 4 stream characters, so editing keys work in
whole characters: Backspace deletes one character (4 chars), Left/Right arrows
move by one character (4 chars), Space is a 4-char code, and Return is a real
newline plus 3 zero-width pad characters.

The **REVL** variable axis controls readability: text is fully readable at
**REVL = 650** (the midpoint of the axis); dragging toward 0 or toward 1000
distorts the glyphs, so a sweep to max does not reveal the text.
`cipher/keyboard.py` is the single source of truth; it generates the font's
GSUB, the QMK table, and the browser demo table, so they cannot drift.

---

## Part A - Laptop side (do this first; no hardware needed)

This works today, before the keyboard arrives, and proves the concept on its own.
Run from the repo root.

1. Build the font (static + the REVL variable font):
   ```
   .venv/bin/python -m fontbuild.build_keyboard
   ```
   Produces `dist/SoulsOnly.ttf` and `dist/SoulsOnly-VF.ttf`.

2. Generate the matching QMK table and the browser-demo assets (one source of
   truth keeps them synced with the font):
   ```
   .venv/bin/python tools/make_qmk_table.py     # -> demo/qmk/cipher_table.h
   .venv/bin/python tools/make_demo_assets.py   # -> demo/cipher_table.js + demo/SoulsOnly-VF.ttf
   ```

3. Open the demo page:
   ```
   open demo/index.html
   ```

4. Smoke test WITHOUT the keyboard:
   - Leave **"Simulate cipher keyboard"** ticked and just type normally. The page
     encodes each letter into two random codes as you type, so the left box reads
     normally (Souls Only font) and the right box fills with ASCII noise. This
     reproduces exactly what the real keyboard emits.
   - Drag **REVL** to 650 (the midpoint): the glyphs are fully readable. Dragging
     toward 0 or 1000 distorts them - a sweep to max does not reveal the text.
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

This was done and flashed successfully on 2026-05-29. The exact working recipe on
macOS (Apple Silicon), with the gotchas that cost time:

1. Keychron's fork (the Max boards are NOT in mainline QMK). The V1 Max lives at
   `keyboards/keychron/v1_max/ansi_encoder` (NOT `keychron/v1/v1_max/...`), and it
   is present on the fork's default branch (`2025q3`).
   ```
   git clone --depth 1 https://github.com/Keychron/qmk_firmware.git ~/qmk_firmware
   git -C ~/qmk_firmware submodule update --init --recursive --depth 1   # large (ChibiOS)
   ```

2. Toolchain. The Homebrew `qmk` formula installs a BROKEN python interpreter
   (its `qmk` shim points at a missing path) and pins `arm-none-eabi-gcc@8` /
   `avr-gcc@8` behind extra taps. What actually works:
   ```
   brew tap osx-cross/arm && brew tap osx-cross/avr
   brew install qmk/qmk/qmk          # pulls arm-none-eabi-gcc@8 + binutils + dfu-util
   <repo>/.venv/bin/pip install qmk  # use a CLEAN python for the qmk CLI, not brew's
   <repo>/.venv/bin/qmk config user.qmk_home="$HOME/qmk_firmware"
   ```
   `arm-none-eabi-gcc@8` and `arm-none-eabi-binutils` are keg-only, so put their
   Cellar `bin` dirs on PATH for the compile:
   ```
   export PATH="/opt/homebrew/Cellar/arm-none-eabi-gcc@8/8.5.0_2/bin:/opt/homebrew/Cellar/arm-none-eabi-binutils/2.41/bin:/opt/homebrew/bin:$PATH"
   ```

3. Create the `cipher` keymap from `default` and drop in the generated table:
   ```
   cd ~/qmk_firmware/keyboards/keychron/v1_max/ansi_encoder/keymaps
   cp -r default cipher
   cp <repo>/demo/qmk/cipher_table.h cipher/
   cp <repo>/demo/qmk/rules.mk cipher/        # VIA_ENABLE = yes
   ```
   Then append the cipher block from `demo/qmk/keymap_cipher.c` (the
   `#include "cipher_table.h"`, the `cipher_on` / `kb_emitting` / `rng_seeded`
   state, `emit_char`, and `process_record_user`) to the END of `cipher/keymap.c`,
   keeping the existing `keymaps[]` and `encoder_map[]`. No merge conflict: the
   default keymap does NOT define `process_record_user`, and Keychron's
   `keychron_task.c` calls `process_record_user` BEFORE `process_record_keychron`,
   so returning `true` for non-ciphered keys leaves all Fn keys (BT, RGB, knob,
   battery) working. The `rules.mk` (`VIA_ENABLE = yes`) is REQUIRED for the
   Keychron Launcher (launcher.keychron.com) to recognise the board; the stock
   `default` keymap omits VIA, so without this rules.mk the Launcher connects but
   cannot load the keymap.

4. Compile and flash (MCU is STM32F401, bootloader `stm32-dfu`, flashed by
   `dfu-util` which `qmk flash` calls automatically):
   ```
   <repo>/.venv/bin/qmk compile -kb keychron/v1_max/ansi_encoder -km cipher
   <repo>/.venv/bin/qmk flash   -kb keychron/v1_max/ansi_encoder -km cipher
   ```
   `qmk flash` polls for the bootloader, so start it, THEN enter DFU: board in
   WIRED mode (data cable, side toggle on Cable), pop the Spacebar keycap, hold the
   PCB reset button while plugging in (~3 s). It can take 1-2 minutes to detect.

   If `qmk flash` throws a transient USB error mid-write (`ERASE_PAGE get_status`
   or `LIBUSB_ERROR_OVERFLOW`) the board stays in DFU and is NOT bricked (the
   bootloader region is protected). The reliable fallback is to call dfu-util
   directly with an explicit device id and a clean leave (this is what finally
   stuck on 2026-05-29):
   ```
   dfu-util -a 0 -d 0483:df11 -s 0x08000000:leave -D \
     ~/qmk_firmware/.build/keychron_v1_max_ansi_encoder_cipher.bin
   ```
   If it keeps erroring, unplug and re-enter DFU for a clean USB state, and try a
   different cable/port (avoid hubs).

5. Test: press **Right Ctrl** to toggle cipher mode ON (it is the key just RIGHT
   of **Fn** on the bottom row, between Fn and the arrows; do NOT grab Left Ctrl
   by reflex). Open `demo/index.html` (Simulate OFF), type: letters read correctly,
   the raw pane shows garbage. Right Ctrl again returns to a normal keyboard.

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
5. Drag REVL toward 0 or 1000: "The glyphs distort at either extreme." Drag to
   650: "Right here - the midpoint - is where the text snaps into focus."
6. Type a capital, a number, and a symbol (e.g. Hi! 42 @x). Press Backspace
   once - a whole character disappears. Press Left/Right - the cursor steps by
   a whole character. "Every keystroke, uppercase or symbol, is fully ciphered."
7. Turn cipher OFF, type your name normally. "And it is still a normal keyboard."

## Known limits (say them if asked)
- The full printable charset is ciphered (lowercase, uppercase, digits, symbols)
  with homophones (random codes per keypress). Non-printable control characters
  other than Space, Return, Backspace, and Left/Right arrows pass through unciphered.
- Codes are ASCII, so a determined reader can dump the font + table and reverse
  it; and the REVL readable point is REVL=650 (the midpoint), so a targeted
  attacker who knows the schema can find it. This is a statement device: strong
  against bulk/casual scraping, weak against a targeted attacker. The font is the
  key, and it ships to readers.
- Homophones (random codes per keypress) defeat simple frequency analysis on the
  stream; the shared bowl/stem half-glyphs add image-level ambiguity.
- Wired for reliability; a Bluetooth build is the v2.
