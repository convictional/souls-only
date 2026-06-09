// tools/garble-overlap.mjs
// EXPERIMENT (feat/overlap-stations): code-division overlap layout.
// Offline asset builder, Node + macOS only (uses `say`). Run with:
//   node tools/garble-overlap.mjs
//
// Unlike garble.mjs (which concatenates N stations in time -> a ~30s file), this
// sums THREE phase-coded clips into ONE block the length of a single clip (~3s).
// Each clip is phase-rotated at its own focal; descrambling at focal j (the
// runtime's -alpha) reconstructs clip j while the other two stay scrambled and
// remain an additive noise floor. The point of the experiment is to HEAR that
// tradeoff: a clean radio-tuner becomes one voice surfacing out of a two-voice wash.
import { execFileSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { readWavMono, writeWavMono } from './wav.mjs'
import { buildPhaseMask } from '../src/scramble.js'
import { buildOverlap } from './overlap.mjs'
import { AXIS_MAX, ASSET_RATE, BLOCK_LEN, PHASE_SEED, ALPHA_MAX } from '../src/constants.js'

// Three stations, well-separated focals. The message is the pre-rendered,
// adversarially-perturbed clip; the two decoys are TTS'd here.
const ADV_MESSAGE = 'tools/adversarial/message_adv.wav'
const STATIONS_DATA = [
  { focal: 650, clip: ADV_MESSAGE },
  { focal: 200, text: 'Twinkle, twinkle, little star, how I wonder what you are.' },
  { focal: 900, text: 'Old MacDonald had a farm, E I E I O.' },
]

const TMP_AIFF = '/tmp/soa-ov-clean.aiff'
const TMP_WAV = '/tmp/soa-ov-clean.wav'
const OUT = 'public/assets/overlap-3.wav'

// Synthesize one phrase at the asset rate, fit to exactly BLOCK_LEN, peak-normalize
// to 0.8 so no station is louder than another (loudness must not betray the message).
function renderClip(text) {
  execFileSync('say', ['-o', TMP_AIFF, text])
  execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])
  const { sampleRate, samples } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) throw new Error(`clip rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  const clip = new Float32Array(BLOCK_LEN)
  clip.set(samples.subarray(0, Math.min(samples.length, BLOCK_LEN)))
  let peak = 0
  for (let i = 0; i < clip.length; i++) peak = Math.max(peak, Math.abs(clip[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < clip.length; i++) clip[i] *= g }
  return clip
}

// Load a pre-rendered clip (already at ASSET_RATE and level-set), fit to BLOCK_LEN.
function loadClip(path) {
  const { sampleRate, samples } = readWavMono(path)
  if (sampleRate !== ASSET_RATE) throw new Error(`${path} rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  const clip = new Float32Array(BLOCK_LEN)
  clip.set(samples.subarray(0, Math.min(samples.length, BLOCK_LEN)))
  return clip
}

try {
  const clips = STATIONS_DATA.map((s) => (s.clip ? loadClip(s.clip) : renderClip(s.text)))
  const focals = STATIONS_DATA.map((s) => s.focal)
  const phi = buildPhaseMask(PHASE_SEED, BLOCK_LEN)

  const block = buildOverlap(clips, focals, phi, AXIS_MAX, ALPHA_MAX)

  // Three summed scrambled clips can exceed unit amplitude; peak-normalize the
  // whole block (a global scale, so all stations stay equally loud) to avoid clipping.
  let peak = 0
  for (let i = 0; i < block.length; i++) peak = Math.max(peak, Math.abs(block[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < block.length; i++) block[i] *= g }

  writeWavMono(OUT, block, ASSET_RATE)
  console.log(
    `wrote ${OUT}: 1 block x ${BLOCK_LEN} samples at ${ASSET_RATE} Hz ` +
      `(${(block.length / ASSET_RATE).toFixed(1)}s), ${STATIONS_DATA.length} overlapped stations`,
  )
} finally {
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
