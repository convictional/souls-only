// tools/garble.mjs
// Offline asset builder. Node + macOS only (uses `say` to synthesize voices
// transiently in /tmp; no clean audio is ever committed or shipped). Run with:
//   node tools/garble.mjs
//
// THIS FILE is the only place the focal values exist. The output is one mono WAV
// of STATIONS_DATA.length equal-length segments concatenated in time. Each segment
// is a short phrase synthesized in the same voice, fit to one block, level-matched,
// and phase-rotated at its own focal. The runtime maps the dial to a rotation
// amount and rotates every segment by its negation, so a segment resolves only
// where the dial matches its focal. Every segment is real, intelligible speech, so
// nothing in the asset distinguishes the message from the rhymes by signal alone —
// only by which words you recognize.
import { execFileSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { readWavMono, writeWavMono } from './wav.mjs'
import { buildPhaseMask, alphaForReveal, phaseTransform } from '../src/scramble.js'
import { mulberry32 } from '../src/rng.js'
// Read constants from constants.js, not reveal-engine.js: the latter imports the
// worklet via a `?url` specifier that plain Node cannot load.
import { AXIS_MAX, ASSET_RATE, BLOCK_LEN, PHASE_SEED, ALPHA_MAX } from '../src/constants.js'

// The message plus nine universally-known nursery rhymes, each at its own focal
// dial value. Focals are spread across the dial with ~90+ separation so each is a
// distinct tuning point with static between. The message's focal is just one of
// the ten; the layout shuffle below hides which time-slot carries it.
// The message segment is a pre-rendered, adversarially-perturbed clip (see
// tools/adversarial/perturb.py): Whisper-tiny transcribes it as "Little Miss
// Muffet", while a primed human hears the real words. It is embedded verbatim
// (no re-normalization, which would scale the perturbation). Decoys are TTS'd here.
const ADV_MESSAGE = 'tools/adversarial/message_adv.wav'
const STATIONS_DATA = [
  { focal: 650, clip: ADV_MESSAGE },
  { focal: 60, text: 'Twinkle, twinkle, little star, how I wonder what you are.' },
  { focal: 160, text: 'Mary had a little lamb, its fleece was white as snow.' },
  { focal: 250, text: 'Row, row, row your boat, gently down the stream.' },
  { focal: 360, text: 'The itsy bitsy spider climbed up the water spout.' },
  { focal: 460, text: 'Old MacDonald had a farm, E I E I O.' },
  { focal: 560, text: 'Humpty Dumpty sat on a wall, Humpty Dumpty had a great fall.' },
  { focal: 760, text: 'Baa, baa, black sheep, have you any wool?' },
  { focal: 850, text: 'Jack and Jill went up the hill to fetch a pail of water.' },
  { focal: 950, text: 'Hickory dickory dock, the mouse ran up the clock.' },
]
const STATIONS = STATIONS_DATA.length

// Seed for the slot permutation, so neither the message's time-slot nor the
// focal-vs-slot order is recoverable from the asset's layout.
const LAYOUT_SEED = 0x27d4eb2f

const TMP_AIFF = '/tmp/soa-clean.aiff'
const TMP_WAV = '/tmp/soa-clean.wav'
const OUT = 'public/assets/message.wav'

// Synthesize one phrase in the default system voice at the asset rate and return
// mono Float32 samples fit to exactly BLOCK_LEN (truncated or zero-padded) and
// peak-normalized, so no segment is louder than another (loudness must not betray
// which one is the message).
function renderClip(text) {
  execFileSync('say', ['-o', TMP_AIFF, text])
  execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])
  const { sampleRate, samples } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) throw new Error(`clip rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  const clip = new Float32Array(BLOCK_LEN)
  clip.set(samples.subarray(0, Math.min(samples.length, BLOCK_LEN)))
  let peak = 0
  for (let i = 0; i < clip.length; i++) peak = Math.max(peak, Math.abs(clip[i]))
  if (peak > 0) {
    const g = 0.8 / peak
    for (let i = 0; i < clip.length; i++) clip[i] *= g
  }
  return clip
}

// Load a pre-rendered clip (already at ASSET_RATE and BLOCK_LEN-sized, level-set)
// and fit it to exactly BLOCK_LEN without altering its samples.
function loadClip(path) {
  const { sampleRate, samples } = readWavMono(path)
  if (sampleRate !== ASSET_RATE) throw new Error(`${path} rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  const clip = new Float32Array(BLOCK_LEN)
  clip.set(samples.subarray(0, Math.min(samples.length, BLOCK_LEN)))
  return clip
}

try {
  // Decide which time-slot holds each phrase: a seeded permutation so the message
  // is not in an obvious position and a slot's order does not track its focal.
  const order = STATIONS_DATA.map((_, i) => i)
  const rng = mulberry32(LAYOUT_SEED)
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[order[i], order[j]] = [order[j], order[i]]
  }

  // Build each segment: synthesize, fit, level-match, phase-rotate at its focal.
  const phi = buildPhaseMask(PHASE_SEED, BLOCK_LEN)
  const asset = new Float32Array(BLOCK_LEN * STATIONS)
  for (let slot = 0; slot < STATIONS; slot++) {
    const { focal, text, clip: clipPath } = STATIONS_DATA[order[slot]]
    const clip = clipPath ? loadClip(clipPath) : renderClip(text)
    const garbled = phaseTransform(clip, phi, alphaForReveal(focal, AXIS_MAX, ALPHA_MAX))
    asset.set(garbled, slot * BLOCK_LEN)
  }

  writeWavMono(OUT, asset, ASSET_RATE)
  console.log(
    `wrote ${OUT}: ${STATIONS} segments x ${BLOCK_LEN} samples at ${ASSET_RATE} Hz ` +
      `(${(asset.length / ASSET_RATE).toFixed(1)}s)`,
  )
} finally {
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
