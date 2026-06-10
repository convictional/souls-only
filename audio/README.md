# souls-only-audio

The audio sibling of [Souls Only](../README.md) (this repository). A spoken message is
delivered already garbled into noise and reassembles into an intelligible voice
only at a hidden point on a single reveal dial, like tuning an analog radio.

The dial runs 0 to 1000 and starts at 0 (noise). The clean recording never
ships: the asset is phase-scrambled (its frequency content is intact but its
phase is randomized, so the voice is genuinely destroyed into noise, not just
buried under static). The running code reconstructs the voice only at one hidden
dial position. The position is not stored in the shipped code as a value or a
curve. It can be found by ear, but a program that renders the audio and runs
speech-to-text gets only gibberish.

The method is a code-division **overlap**. Three channels — the spoken message
and two nursery-rhyme decoys (Twinkle Twinkle and Old MacDonald) — are each
phase-scrambled at their own focal dial value and **summed into one clip the
length of a single recording**. Descrambling at a channel's focal rebuilds that
voice while the other two stay a wash of noise; the short decoys loop so every
channel plays the whole way through. Tuning works like a radio: noise everywhere,
one voice surfacing as you pass its focal.

That overlap is also the anti-machine layer. A speech-to-text model run at any
focal hears the target voice buried under the other two and transcribes only
gibberish — so no adversarial perturbation is needed; the two-voice noise floor
masks the words on its own. The only thing that recovers the message is a human
**primed by the words on screen**, picking the voice they were set to hear out of
the murmur — the same top-down priming the font relies on, turned into the defense.

This is a parallel artwork, not an accessibility remedy for the font, and not an
unbreakable cipher. At the focal point the message is simply intelligible.

## Run

```
npm install
npm run dev
```

Open the printed URL, click Play, and scrub the dial to find the clear point.
There is also a 9:16 explainer at `/vertical-demo.html` (the source of the demo
GIF in the root README).

## Test

```
npm test
```

Unit tests cover the deterministic core (seeded RNG, the radix-2 FFT, the phase
scramble and its cancellation, the overlap sum and its per-channel descramble, the
loop-to-fill helper, the engine dial-to-rotation mapping and tuned playback, the
keyboard logic, and the asset-URL resolver) and a guard that the focal value never
appears in shipped code. The perceptual reveal is verified by ear with the
checklist below.

## Regenerating the asset

The garbled asset is produced offline by `node tools/garble.mjs` (macOS; uses
`say`). That tool is the only place the focal values live: it synthesizes the
message and the two decoy rhymes in /tmp, loops the short decoys to fill the block,
phase-scrambles each channel at its focal, sums them, writes
`public/assets/message.wav`, and deletes the clean audio. It is self-contained —
rebuilding the asset needs nothing more than `node tools/garble.mjs` and `say`.

The block is `OVERLAP_BLOCK_LEN` (2^20 samples, ~47.5s at 22050 Hz) so it holds the
long message; the decoys loop to the same length.

> Legacy: `tools/adversarial/` holds an earlier defense — a perturbation tuned to
> steer Whisper-tiny's transcription to "Little Miss Muffet" on a short message
> clip. The overlap masks speech-to-text on its own, so that toolchain is **no
> longer wired into the build**; it is kept as research.

## Keyboard and screen reader

The dial is fully operable by keyboard. Arrow keys step by 10, Shift plus arrow
by 1, Page Up and Page Down by 50, and Home and End go to the ends. Pressing
Play moves focus to the dial. Nothing announces or marks the clear point; it is
only ever heard.

## An unsighted listener

Of the two media, the audio sibling is the one an unsighted person can actually
decode. The font's reveal is purely visual; here the message arrives as sound. A
screen reader announces the Play button, the labeled reveal dial, and the priming
text on the page, and the dial is driven entirely from the keyboard — so a blind
user can start playback and tune across the dial without sight. The decoding is
done by their own hearing: they sweep the dial, hear a voice rise out of the
static, and pick out the one speaking words they do not already know by heart. The
top-down priming a sighted reader gets from the on-screen text, the screen reader
speaks aloud, so the blind listener is set to hear the message just the same.

One honest caveat, and it cuts against the anti-machine layer. A screen reader
reads *text*; it does not transcribe arbitrary audio. The intended decode is by
ear, and a blind person who listens hears the true words. But a user who instead
pipes the audio through automatic speech-to-text is fed only the noise-floor
gibberish the overlap produces. The reveal is meant to be *heard*: that path is
fully accessible, while leaning on machine transcription rather than one's own ears
is precisely the path the design defeats.

## Listening checklist

- At 0 the output is noise.
- Sweeping the dial passes three channels where a voice surfaces from the static.
- Two channels are nursery rhymes you recognize; exactly one is the message.
- At a channel the chosen voice rises *through* the wash of the other two, not over
  silence — the overlap trades a clean reveal for a single short clip.
- Moving away from a focal in either direction dissolves back into noise.
- The real message is findable by ear but not at an end.

## How the hiding works

A per-frequency phase mask is generated from a public seed. Offline, three
equal-length channels are built — a long spoken message and two short rhymes
looped to fill the block — each in the same voice and level-matched. Each channel's
spectrum has its phase rotated by its own `focal_amount * mask`: same magnitude
spectrum, scrambled phase, so each channel is noise. The three scrambled channels
are **summed into one block** and the sum is peak-normalized.

At runtime the engine descrambles the block by `-dial_amount * mask`, where the
dial maps linearly to the amount. At a channel's focal the rotation cancels and
that voice reconstructs coherently, while the other two — rotated by a nonzero
residual — stay scrambled and act as an additive noise floor. The focal amounts are
not in the shipped code; they live only in `tools/garble.mjs`.

Summing N channels means the non-matching ones do not vanish; they remain noise of
roughly `1/sqrt(N-1)` the target's level. That is the cost of packing every channel
into one clip rather than concatenating them in time, and it is what masks the
message from a transcriber.

## Limitations

This raises the cost of an automated attack; it is not an unbreakable cipher.

- **A bounded dial can be swept.** The reveal is one 0–1000 control, so a program
  can render the output at every position. The overlap is what makes that sweep
  unhelpful, not impossible.
- **The masking is not airtight.** Speech-to-text run at the focal gets gibberish,
  but a few words can leak, and a larger or noise-robust transcriber could recover
  more. The defense degrades a machine read; it does not guarantee zero.
- **Anything a human can hear, an audio model can in principle hear too.** The
  point is intelligible by design, so a sufficiently capable listener — human or
  AI — finds it. The defense forces the attacker to actually listen rather than to
  read the code or score a waveform. It is a statement device, scoped as such.

## Embedding

`RevealEngine` (in `src/reveal-engine.js`) takes a raw 0..1000 reveal value via
`setReveal`, the same integer the font's REVL slider emits, so one control can
drive both font and audio.
