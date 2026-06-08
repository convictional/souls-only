// tools/garble.mjs
// Offline: produce the multi-station phase-scrambled public/assets/message.wav.
// This is the ONLY place the focal values live. Run with: node tools/garble.mjs
// macOS only (uses `say` to synthesize the clean voice transiently in /tmp;
// the clean audio is never committed or shipped).
//
// The asset is STATIONS blocks of BLOCK_LEN concatenated in time. One block is
// the real message; the rest are babble decoys built by re-ordering the real
// clip's own frames (tools/babble.mjs), so every block shares the real clip's
// kurtosis AND its energy-envelope CV. Each block is phase-scrambled at its own
// focal rotation, so the dial resolves it only at that focal. A statistics sweep
// (kurtosis, envelope CV — the two metrics that have located the focal before)
// therefore finds STATIONS identical "stations" and cannot tell which speaks
// real words without recognizing speech — a human ear or STT.
import { execFileSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { readWavMono, writeWavMono } from './wav.mjs'
import { buildPhaseMask, alphaForReveal, phaseTransform } from '../src/scramble.js'
import { frameShuffle } from './babble.mjs'
import { mulberry32 } from '../src/rng.js'
// Read constants from constants.js, not reveal-engine.js: the latter imports the
// worklet via a `?url` specifier that plain Node cannot load.
import { AXIS_MAX, ASSET_RATE, BLOCK_LEN, STATIONS, PHASE_SEED, ALPHA_MAX } from '../src/constants.js'

// The focal dial value of the REAL message. Lives here, never in shipped code.
const FOCAL = 650
// Focal dial values for the decoy stations (STATIONS - 1 of them), spread across
// the dial with wide separation so each is its own tuning point with static
// between.
const DECOY_FOCALS = [180, 420, 880]
// Frame length (samples) for the babble shuffle: ~93ms at 22050, long enough to
// carry speech-like texture, short enough that word order is destroyed.
const FRAME_LEN = 2048
// Seed for the slot permutation, so the real message is not in an obvious time
// position and a station's time-slot does not track its focal order.
const LAYOUT_SEED = 0x27d4eb2f

const PHRASE = 'This is a souls only audio message.'
const TMP_AIFF = '/tmp/soa-clean.aiff'
const TMP_WAV = '/tmp/soa-clean.wav'
const OUT = 'public/assets/message.wav'

const FOCALS = [FOCAL, ...DECOY_FOCALS]
if (FOCALS.length !== STATIONS) {
  throw new Error(`have ${FOCALS.length} focals but STATIONS is ${STATIONS}`)
}

// 1. Synthesize the clean voice at the asset rate, transiently.
execFileSync('say', ['-o', TMP_AIFF, PHRASE])
execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])

try {
  // 2. Read clean samples.
  const { sampleRate, samples: clean } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) {
    throw new Error(`clean rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  }
  if (clean.length > BLOCK_LEN) {
    throw new Error(`clean is ${clean.length} samples, longer than BLOCK_LEN ${BLOCK_LEN}; shorten the phrase or raise BLOCK_LEN`)
  }

  // 3. Pad to the power-of-two block length so each block's FFT is exact.
  const realClip = new Float32Array(BLOCK_LEN)
  realClip.set(clean)

  // 4. Decide which time-slot holds the real message: permute the focal list so
  // neither the real block's position nor the focal-vs-slot order is obvious.
  const slotFocals = FOCALS.slice()
  const rng = mulberry32(LAYOUT_SEED)
  for (let i = slotFocals.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[slotFocals[i], slotFocals[j]] = [slotFocals[j], slotFocals[i]]
  }

  // 5. Build each block: the real clip at its focal, babble decoys (matched
  // statistics, scrambled word order) at theirs. Phase-scramble at the block's
  // focal rotation; descrambling at that same rotation in the runtime resolves it.
  const phi = buildPhaseMask(PHASE_SEED, BLOCK_LEN)
  const asset = new Float32Array(BLOCK_LEN * STATIONS)
  for (let s = 0; s < STATIONS; s++) {
    const focal = slotFocals[s]
    const clip = focal === FOCAL ? realClip : frameShuffle(realClip, PHASE_SEED ^ (focal + 1), FRAME_LEN)
    const garbled = phaseTransform(clip, phi, alphaForReveal(focal, AXIS_MAX, ALPHA_MAX))
    asset.set(garbled, s * BLOCK_LEN)
  }

  // 6. Write the garbled asset.
  writeWavMono(OUT, asset, ASSET_RATE)
  console.log(
    `wrote ${OUT}: ${STATIONS} stations x ${BLOCK_LEN} samples at ${ASSET_RATE} Hz ` +
      `(${(asset.length / ASSET_RATE).toFixed(1)}s); real message at focal dial ${FOCAL}`,
  )
} finally {
  // Always remove the transient clean audio.
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
