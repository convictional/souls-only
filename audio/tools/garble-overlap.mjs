// tools/garble-overlap.mjs
// EXPERIMENT (feat/overlap-stations): code-division overlap layout.
// Offline asset builder, Node + macOS only (uses `say`). Run with:
//   node tools/garble-overlap.mjs
//
// Sums N phase-coded clips into ONE long block (OVERLAP_BLOCK_LEN, ~47.5s). Each
// clip is phase-rotated at its own focal; descrambling at focal j (the runtime's
// -alpha) reconstructs clip j while the others stay scrambled and remain an
// additive noise floor. The point is to HEAR that tradeoff: one voice surfacing
// out of a wash rather than over silence. Builds two variants to compare:
//   overlap-2.wav  message + one rhyme   (noise floor ~1/sqrt(1))
//   overlap-3.wav  message + two rhymes  (noise floor ~1/sqrt(2), harder to hear)
//
// The message is a long spoken passage (fit to the block); the short nursery
// rhymes are LOOPED to fill the same length and play throughout. NOTE: the message
// is a plain TTS clip - the Whisper-tiny perturbation (perturb.py) was tuned for
// the old short line and is not applied here.
import { execFileSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { readWavMono, writeWavMono } from './wav.mjs'
import { buildPhaseMask } from '../src/scramble.js'
import { buildOverlap, tileToLength } from './overlap.mjs'
import { AXIS_MAX, ASSET_RATE, OVERLAP_BLOCK_LEN, PHASE_SEED, ALPHA_MAX } from '../src/constants.js'

const N = OVERLAP_BLOCK_LEN

const MESSAGE =
  'First, a tiny bit of hidden static is mixed in, too small for a person to ' +
  'notice, but just enough to fool speech-to-text AI into hearing the nursery ' +
  'rhyme Little Miss Muffet instead. Then that line and two real nursery rhymes ' +
  'are all scrambled into noise and layered on top of each other in a single ' +
  'short clip, same length as the original message, with all three voices hiding ' +
  'in the same wash of static. A tuning dial pulls one voice out at a time: turn ' +
  'it to one spot and a nursery rhyme surfaces, turn it to another and the real ' +
  'message rises up through the murmur of the other two, and only a person who ' +
  'knows what to listen for can pick it out.'

const TWINKLE = 'Twinkle, twinkle, little star, how I wonder what you are.'
const MACDONALD = 'Old MacDonald had a farm, E I E I O.'

// The message keeps focal 650; each variant adds well-separated rhyme focals.
const VARIANTS = [
  {
    out: 'public/assets/overlap-2.wav',
    stations: [
      { focal: 650, text: MESSAGE, loop: false },
      { focal: 200, text: TWINKLE, loop: true },
    ],
  },
  {
    out: 'public/assets/overlap-3.wav',
    stations: [
      { focal: 650, text: MESSAGE, loop: false },
      { focal: 200, text: TWINKLE, loop: true },
      { focal: 900, text: MACDONALD, loop: true },
    ],
  },
]

const TMP_AIFF = '/tmp/soa-ov-clean.aiff'
const TMP_WAV = '/tmp/soa-ov-clean.wav'

// Synthesize one phrase at the asset rate and return its raw mono samples,
// peak-normalized to 0.8 so no station is louder than another. Cached by text so
// a phrase shared across variants is only spoken once.
const synthCache = new Map()
function synth(text) {
  if (synthCache.has(text)) return synthCache.get(text)
  execFileSync('say', ['-o', TMP_AIFF, text])
  execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])
  const { sampleRate, samples } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) throw new Error(`clip rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  let peak = 0
  for (let i = 0; i < samples.length; i++) peak = Math.max(peak, Math.abs(samples[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < samples.length; i++) samples[i] *= g }
  synthCache.set(text, samples)
  return samples
}

// Fit a long clip to exactly N samples (truncate or zero-pad).
function fit(samples, n) {
  const out = new Float32Array(n)
  out.set(samples.subarray(0, Math.min(samples.length, n)))
  return out
}

function buildVariant({ out, stations }) {
  const clips = stations.map((s) => {
    const raw = synth(s.text)
    const secs = (raw.length / ASSET_RATE).toFixed(1)
    if (!s.loop && raw.length > N) console.warn(`  message is ${secs}s, longer than the ${(N / ASSET_RATE).toFixed(1)}s block - truncated`)
    else console.log(`  station @${s.focal}: ${secs}s ${s.loop ? '(looped to fill)' : '(fit to block)'}`)
    return s.loop ? tileToLength(raw, N) : fit(raw, N)
  })
  const focals = stations.map((s) => s.focal)
  const phi = buildPhaseMask(PHASE_SEED, N)
  const block = buildOverlap(clips, focals, phi, AXIS_MAX, ALPHA_MAX)

  // Summed scrambled clips can exceed unit amplitude; peak-normalize the whole
  // block (a global scale, so all stations stay equally loud) to avoid clipping.
  let peak = 0
  for (let i = 0; i < block.length; i++) peak = Math.max(peak, Math.abs(block[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < block.length; i++) block[i] *= g }

  writeWavMono(out, block, ASSET_RATE)
  console.log(`wrote ${out}: ${(block.length / ASSET_RATE).toFixed(1)}s, ${stations.length} overlapped stations\n`)
}

try {
  for (const v of VARIANTS) {
    console.log(`building ${v.out} (${v.stations.length} stations):`)
    buildVariant(v)
  }
} finally {
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
