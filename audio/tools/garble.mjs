// tools/garble.mjs
// Canonical offline asset builder. Node + macOS only (uses `say` to synthesize
// voices transiently in /tmp; no clean audio is ever committed or shipped). Run:
//   node tools/garble.mjs
//
// THIS FILE is the only place the focal values exist. The method is a code-division
// OVERLAP: three channels - a spoken message and two nursery-rhyme decoys - are each
// phase-scrambled at their own focal dial value and SUMMED into one block the length
// of a single clip. Descrambling at a channel's focal (the runtime's -alpha rotation)
// reconstructs that voice while the other two stay scrambled and remain a wash of
// noise. Tuning the dial is like a radio: noise everywhere, one voice surfacing as
// you pass its focal. The two-voice floor also masks the message from speech-to-text
// (a transcriber gets only gibberish at every focal), so no adversarial perturbation
// is needed. The message is long, so the block is OVERLAP_BLOCK_LEN; the short rhymes
// loop to fill it.
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

// Three channels at well-separated focals. The message is fit to the block; the
// short rhymes loop to fill it so every channel plays for the whole clip. The
// message's focal (650) lives only here, never in shipped code.
const CHANNELS = [
  { focal: 650, text: MESSAGE, loop: false },
  { focal: 200, text: 'Twinkle, twinkle, little star, how I wonder what you are.', loop: true },
  { focal: 900, text: 'Old MacDonald had a farm, E I E I O.', loop: true },
]

const TMP_AIFF = '/tmp/soa-clean.aiff'
const TMP_WAV = '/tmp/soa-clean.wav'
const OUT = 'public/assets/message.wav'

// Synthesize one phrase at the asset rate and return its raw mono samples,
// peak-normalized to 0.8 so no channel is louder than another.
function synth(text) {
  execFileSync('say', ['-o', TMP_AIFF, text])
  execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])
  const { sampleRate, samples } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) throw new Error(`clip rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  let peak = 0
  for (let i = 0; i < samples.length; i++) peak = Math.max(peak, Math.abs(samples[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < samples.length; i++) samples[i] *= g }
  return samples
}

// Fit a long clip to exactly N samples (truncate or zero-pad).
function fit(samples, n) {
  const out = new Float32Array(n)
  out.set(samples.subarray(0, Math.min(samples.length, n)))
  return out
}

try {
  const clips = CHANNELS.map((c) => {
    const raw = synth(c.text)
    const secs = (raw.length / ASSET_RATE).toFixed(1)
    if (!c.loop && raw.length > N) console.warn(`  message is ${secs}s, longer than the ${(N / ASSET_RATE).toFixed(1)}s block - truncated`)
    else console.log(`  channel @${c.focal}: ${secs}s ${c.loop ? '(looped to fill)' : '(fit to block)'}`)
    return c.loop ? tileToLength(raw, N) : fit(raw, N)
  })
  const focals = CHANNELS.map((c) => c.focal)
  const phi = buildPhaseMask(PHASE_SEED, N)
  const block = buildOverlap(clips, focals, phi, AXIS_MAX, ALPHA_MAX)

  // Summed scrambled clips can exceed unit amplitude; peak-normalize the whole block
  // (a global scale, so all channels stay equally loud) to avoid clipping.
  let peak = 0
  for (let i = 0; i < block.length; i++) peak = Math.max(peak, Math.abs(block[i]))
  if (peak > 0) { const g = 0.8 / peak; for (let i = 0; i < block.length; i++) block[i] *= g }

  writeWavMono(OUT, block, ASSET_RATE)
  console.log(
    `wrote ${OUT}: 1 block x ${N} samples at ${ASSET_RATE} Hz ` +
      `(${(block.length / ASSET_RATE).toFixed(1)}s), ${CHANNELS.length} overlapped channels`,
  )
} finally {
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
