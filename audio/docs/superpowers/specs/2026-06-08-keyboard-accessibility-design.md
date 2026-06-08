# Keyboard Accessibility Design

**Goal:** Make the reveal dial fully operable by keyboard and screen reader, so an unsighted listener can scrub left and right and find the focal point by ear, with exact parity to a sighted user.

## Background

The artwork is a single 0..1000 reveal dial. The voice is intelligible only at a hidden focal point (650); both ends are scatter. The entire point is that the focal point is discoverable only by ear. Nothing in the page may hint which values are audible.

The current page uses a native `<input type="range">`. It has two accessibility gaps:

1. No accessible label, so a screen reader announces "slider" with no name.
2. `step="1"` over a 0..1000 range means each arrow press changes the sound imperceptibly, so keyboard scrubbing feels broken.

## Convention (why not global keys)

Screen readers (VoiceOver, NVDA, JAWS) run a browse mode that intercepts arrow keys to read the page. Arrow keys reach page code only when focus is on a real form control such as a range input, which switches the reader into forms/focus mode. A global `document`-level arrow listener therefore does not work for screen reader users: the reader consumes the keys first.

So the control itself handles the keys, and we bring focus to it. This is the accessible convention and it also gives the "scrub from anywhere" convenience without breaking screen readers.

## Design

### Control and focus

- Keep the native `<input type="range">` as the single reveal control (mouse, touch, keyboard).
- Give it an accessible name via `aria-label` (for example "Reveal"). The name must not hint at the focal point.
- When the user presses Play, move keyboard focus to the slider so a keyboard or screen reader user lands on the dial and can scrub immediately. No hunting for the control.
- The visible instruction note is updated to mention the keys. It must not name any value or hint at the focal point.

### Key mapping (coarse + fine), handled on the slider

- Arrow Left / Down: -10. Arrow Right / Up: +10. Normal, audible step.
- Shift + Arrow: +/- 1. Fine homing-in.
- Page Down: -50. Page Up: +50. Fast travel.
- Home: 0. End: 1000.
- All results clamped to 0..1000.

The handler is attached to the slider element (not the document). For every key it handles, it computes the new value, updates the slider value, the visible readout, and `engine.setReveal`, then calls `preventDefault` so the native range handling does not also fire (no double-stepping). Keys it does not handle pass through untouched.

### No focal hints

- No "found it" or "clear" cue anywhere (visual, ARIA, or live region).
- No focal label or value markers.
- The screen reader announces only the current position number, which is the same number already shown on screen. A blind user and a sighted user both learn "it is clear here" only by listening. No new information is introduced.

## Components

- `src/keys.js` (new, pure): given the current reveal value and a key descriptor (`key`, `shiftKey`), return the next clamped reveal value, or `null` if the key is not a reveal control key. Pure and unit-tested like the rest of the core.
- `src/main.js` (modified): attach a `keydown` listener on the slider that uses `src/keys.js`, updates slider value + readout + engine, and calls `preventDefault` when a key was handled. Move focus to the slider on Play.
- `index.html` (modified): add `aria-label` to the slider; update the instruction note to mention the keys without hinting at any value.
- `README.md` (modified): add a short manual accessibility checklist alongside the listening checklist.

## Testing

- `src/keys.js` is unit-tested (Vitest): each key maps to the right delta; Shift halves the step to the fine value; Page keys use the fast value; Home/End jump to the ends; results clamp at both ends; unhandled keys return `null`.
- Screen reader behavior is verified manually (VoiceOver) via a short checklist, since the focal point is unknowable by design and cannot be asserted in a unit test:
  - Tabbing to the dial announces its name and current value.
  - Pressing Play moves focus to the dial.
  - Each arrow press announces the new position and is audible.
  - Shift + arrow makes a finer change; Page keys make a larger jump.
  - Nothing announces or indicates the focal point; the voice becoming clear is heard, never spoken.

## Out of scope

- Global (document-level) key handling. It is an anti-pattern for screen reader users and is intentionally not used.
- Any visual or audible cue that marks the focal point.
