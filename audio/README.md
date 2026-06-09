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

To keep the message from being found by signal analysis, the asset carries **ten
stations** at different dial points, and every one is **real, universally-known
speech**: nine nursery rhymes (Twinkle Twinkle, Old MacDonald, Hickory Dickory
Dock, …) and the message. Because all ten stations are genuine speech, a sweep
that scores each dial position for "speech-likeness" peaks identically everywhere
and cannot rank them. Tuning works like a radio: static between stations, a voice
surfacing as you pass one. The only thing that separates the message from the
rhymes is recognizing which words are new — the one voice you do not already know
by heart.

That defeats a statistics sweep, but not a speech-to-text model run over each
station. So the message clip carries a second layer: a **targeted adversarial
perturbation** tuned against Whisper-tiny (`tools/adversarial/perturb.py`). A
small change — still plainly intelligible to a human ear — steers that model's
transcription to a *tenth* nursery rhyme ("Little Miss Muffet"). An attacker who
sweeps all ten focals and transcribes each gets ten distinct, ordinary rhymes; the
real words appear in none of them. A human tuning to the message, primed by the
words on screen, hears them plainly — the same top-down priming the font relies on,
turned into the defense.

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
resolution and the tuned playback that follows the resolving station, the keyboard
logic) and a guard that the focal value never appears in shipped code. The
perceptual morph is verified by ear with the checklist below.

## Regenerating the asset

The garbled asset is produced offline by `node tools/garble.mjs` (macOS; uses
`say`). That tool is the only place the focal values live: it synthesizes the nine
decoy rhymes in /tmp, scrambles each at its focal, embeds the pre-rendered message
clip (`tools/adversarial/message_adv.wav`), writes `public/assets/message.wav`,
and deletes the clean audio. Because `message_adv.wav` is committed, rebuilding
the scrambled asset needs nothing more than `node tools/garble.mjs` and `say`.

The message clip itself is the adversarially-perturbed message, built one-time by
the offline tool below. Its optimization is not bit-reproducible, so the committed
`message_adv.wav` is the canonical clip; you only need to re-run this to change the
message or the disguise target:

```
python3 -m venv tools/adversarial/.venv
tools/adversarial/.venv/bin/pip install torch torchaudio openai-whisper soundfile numpy
tools/adversarial/.venv/bin/python tools/adversarial/perturb.py   # -> tools/adversarial/message_adv.wav
node tools/adversarial/descramble_all.mjs                         # verify: descramble each station
tools/adversarial/.venv/bin/python tools/adversarial/verify.py    # transcribe each with whisper-tiny
```

The perturbation toolchain and `message_adv.wav` are committed so the build is
reproducible — `message_adv.wav` is plainly intelligible by ear (it *is* the
message), kept in the repo on purpose, not as a secret. Only the Python venv and
the `message.clean.wav` / `verify_*.wav` scratch stay local (gitignored).

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
user can start playback and tune through the stations without sight. The decoding
is done by their own hearing: they sweep the dial, hear a voice rise out of the
static at each station, and pick out the one speaking words they do not already
know by heart. The top-down priming a sighted reader gets from the on-screen text,
the screen reader speaks aloud, so the blind listener is set to hear the message
just the same.

One honest caveat, and it cuts against the anti-machine layer. A screen reader
reads *text*; it does not transcribe arbitrary audio. The intended decode is by
ear, and a blind person who listens hears the true words. But a user who instead
pipes the audio through automatic speech-to-text or an AI description tool is fed
the decoy — the adversarial perturbation that steers a transcriber to "Little
Miss Muffet" cannot tell an assistive pipeline from an attacker's. The reveal is
meant to be *heard*: that path is fully accessible, while leaning on machine
transcription rather than one's own ears is precisely the path the design
defeats.

## Listening checklist

- At 0 the output is noise.
- Sweeping the dial passes ten stations where a voice surfaces from the static.
- Nine stations are nursery rhymes you recognize; exactly one is the message.
- Moving away from any station in either direction dissolves back into noise.
- The real message is findable by ear but not at an end.

## How the hiding works

A per-frequency phase mask is generated from a public seed. Offline, the asset is
built as ten equal-length **blocks (stations)** concatenated in time, each a short
phrase synthesized in the same voice, fit to one block and level-matched. Each
block's spectrum has its phase rotated by its own `focal_amount * mask` and written
back to the time domain: same magnitude spectrum, scrambled phase, so each block is
noise. Which time-slot holds which phrase is shuffled, so the message's position is
not obvious.

At runtime the engine descrambles every block by `-dial_amount * mask`, where the
dial maps linearly to the amount, and plays whichever block resolves most strongly
at the current dial (highest kurtosis). A block resolves only where `dial_amount`
equals the `focal_amount` baked into it, so each station appears at its own dial
point with static between. The focal amounts are not in the shipped code; they live
only in `tools/garble.mjs`.

The message block additionally carries the adversarial perturbation described
above, so that a transcriber run on the resolved message reads it as a tenth rhyme.

## Limitations

This raises the cost of an automated attack; it is not an unbreakable cipher.

- **A bounded dial can be swept.** The reveal is one 0–1000 control, so a program
  can render the output at every position. The stations are what make that sweep
  unhelpful, not impossible.
- **All-speech stations defeat statistics, not transcription alone.** Because every
  station is real speech, no "speech-likeness" score can rank them. A solver must
  run speech-to-text and read which words are coherent — and *that* is what the
  adversarial layer targets.
- **The adversarial layer is tuned to Whisper-tiny specifically.** A different or
  larger transcriber, or a human-in-the-loop who simply listens to all ten
  stations, can still recover the message. The perturbation defeats one named
  model, not all listeners.
- **Anything a human can hear, an audio model can in principle hear too.** The
  point is intelligible by design, so a sufficiently capable listener — human or
  AI — finds it. The defense forces the attacker to actually listen rather than to
  read the code or score a waveform. It is a statement device, scoped as such.

## Embedding

`RevealEngine` (in `src/reveal-engine.js`) takes a raw 0..1000 reveal value via
`setReveal`, the same integer the font's REVL slider emits, so one control can
drive both font and audio.
