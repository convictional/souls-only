# souls-only-audio

The audio sibling of [Souls Only](../README.md) (this repository). A spoken message is
delivered already garbled into noise and reassembles into an intelligible voice
only at a hidden point on a single reveal dial, like tuning an analog radio.

The dial runs 0 to 1000 and starts at 0 (noise). The clean recording never
ships: the asset is phase-scrambled (its frequency content is intact but its
phase is randomized, so the voice is genuinely destroyed into noise, not just
buried under static). The running code reconstructs the voice only at one hidden
dial position. The position is not stored in the shipped code as a value or a
curve. It can be found by ear, or by a program that renders the audio and
recognizes the words, but not by reading the code.

To keep the focal point from being trivially found by waveform statistics, the
asset carries **several stations** at different dial points — one real message
and the rest **babble decoys** built from the message's own reordered frames (see
`tools/babble.mjs`). A decoy is a permutation of the real clip, so it has the
same kurtosis and the same energy-envelope coefficient of variation; a statistics
sweep lights up identically at every station and cannot tell which is real.
Tuning works like a radio: static between stations, a voice or babble surfacing
as you pass one. Only recognizing actual words separates the message from the
decoys.

This is a parallel artwork, not an accessibility remedy for the font, and not an
unbreakable cipher. At the focal point the message is simply intelligible.

## Run

```
npm install
npm run dev
```

Open the printed URL, click Play, and scrub the dial to find the clear point.

## Test

```
npm test
```

Unit tests cover the deterministic core (seeded RNG, the radix-2 FFT, the phase
scramble and its cancellation, the engine dial-to-rotation mapping, per-station
resolution and the tuned playback that follows the resolving station, the babble
decoys' matched kurtosis and envelope statistics, the keyboard logic) and a guard
that the focal value never appears in shipped code. The perceptual morph is
verified by ear with the checklist below.

## Regenerating the asset

The garbled asset is produced offline by `node tools/garble.mjs` (macOS; uses
`say`). That tool is the only place the focal value lives. It synthesizes the
clean voice in /tmp, garbles it, writes `public/assets/message.wav`, and deletes
the clean audio. The clean voice is never committed or served.

## Keyboard and screen reader

The dial is fully operable by keyboard. Arrow keys step by 10, Shift plus arrow
by 1, Page Up and Page Down by 50, and Home and End go to the ends. Pressing
Play moves focus to the dial. Nothing announces or marks the clear point; it is
only ever heard.

## Listening checklist

- At 0 the output is noise.
- Sweeping the dial passes several stations where signal surfaces from the static.
- Most stations are babble (no real words); exactly one is the intelligible message.
- Moving away from any station in either direction dissolves back into noise.
- The real message is findable by ear but not at an end.

## How the hiding works

A per-frequency phase mask is generated from a public seed. Offline, the asset is
built as several equal-length **blocks (stations)** concatenated in time. One
block is the clean message; the rest are **babble decoys** — the message's own
short frames reordered (`tools/babble.mjs`), which destroys word order while
preserving the exact sample multiset (so identical kurtosis) and the multiset of
frame energies (so identical envelope statistics). Each block's spectrum has its
phase rotated by its own `focal_amount * mask` and written back to the time
domain: same magnitude spectrum, scrambled phase, so each block is noise.

At runtime the engine descrambles every block by `-dial_amount * mask`, where the
dial maps linearly to the amount, and plays whichever block resolves most
strongly at the current dial (highest kurtosis). A block resolves only where
`dial_amount` equals the `focal_amount` baked into it, so each station appears at
its own dial point with static between — and a statistics sweep finds every
station alike. The focal amounts are not in the shipped code; which station is
the real message lives only in `tools/garble.mjs`.

## Limitations

This raises the cost of an automated attack; it is not an unbreakable cipher.

- **A bounded dial can be swept.** The reveal is one 0–1000 control, so a program
  can render the output at every position. The decoys are what make that sweep
  unhelpful, not impossible.
- **The decoys defeat *cheap* statistics, not speech recognition.** Frame-shuffle
  decoys share the real clip's kurtosis and energy-envelope CV — the two metrics
  that have located the focal in practice — so neither sweep can rank the
  stations. But a determined solver can run speech-to-text on each station and
  read which one is coherent words. That escalation still works; what's gone is
  the cheap, listen-free statistical shortcut.
- **Anything a human can hear, an audio model can in principle hear too.** The
  point is intelligible by design, so a sufficiently capable listener — human or
  AI — finds it. The defense forces the attacker to actually listen rather than
  to read the code or score a waveform. It is a statement device, scoped as such.

## Embedding

`RevealEngine` (in `src/reveal-engine.js`) takes a raw 0..1000 reveal value via
`setReveal`, the same integer the font's REVL slider emits, so one control can
drive both font and audio.
