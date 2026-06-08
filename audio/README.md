# souls-only-audio

The audio sibling of [Souls Only](../README.md) (this repository). A spoken message is
delivered already garbled into noise and reassembles into an intelligible voice
only at a hidden point on a single reveal dial, like tuning an analog radio.

The dial runs 0 to 1000 and starts at 0 (noise). The clean recording never
ships: the asset is a phase-scrambled recording (its frequency content is
intact but its phase is randomized, so the voice is genuinely destroyed into
noise, not just buried under static). The running code reconstructs the voice
only at one hidden dial position. The position is not stored in the shipped
code as a value or a curve. It can be found by ear, or by a program that
renders the audio and judges it, but not by reading the code.

This is a parallel artwork, not an accessibility remedy for the font, and not an
anti-AI cipher. At the focal point the message is simply intelligible.

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
scramble and its cancellation, the engine dial-to-rotation mapping and its
reconstruction at the focal position, the keyboard logic) and a guard that the
focal value never appears in shipped code. The perceptual morph is verified by
ear with the checklist below.

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
- A hidden point exists where the voice is clearly intelligible.
- Moving away from it in either direction dissolves back into noise.
- The clear point is findable by ear but not at an end.

## How the hiding works

A per-frequency phase mask is generated from a public seed. Offline, the clean
recording's spectrum has its phase rotated by `focal_amount * mask` and is
written back to the time domain: same magnitude spectrum, scrambled phase, so
the voice becomes noise. At runtime the engine rotates the asset's phase the
other way by `dial_amount * mask`, where the dial maps linearly to the amount.
The two rotations cancel only where `dial_amount` equals the `focal_amount`
baked into the asset, reconstructing the voice. The focal amount is not in the
shipped code; finding it requires rendering the audio and judging it.

## Embedding

`RevealEngine` (in `src/reveal-engine.js`) takes a raw 0..1000 reveal value via
`setReveal`, the same integer the font's REVL slider emits, so one control can
drive both font and audio.
