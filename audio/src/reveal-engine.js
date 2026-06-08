// src/reveal-engine.js
import { transform } from './fft.js'
import { buildPhaseMask, alphaForReveal, rotatePhase } from './scramble.js'
import { AXIS_MAX, ASSET_RATE, PHASE_SEED, ALPHA_MAX, BLOCK_LEN } from './constants.js'
import revealWorkletUrl from './reveal-worklet.js?url'

// The focal values are NOT here. The asset is STATIONS phase-scrambled blocks
// concatenated in time; the dial maps linearly to a phase-rotation amount
// (alpha) and the engine descrambles every block by -alpha. A block resolves only
// where alpha matches the rotation baked into it offline, which this code does
// not know. Playback follows whichever station resolves at the current dial, so
// the dial behaves like a radio: static between stations, a voice (or babble)
// emerging as you tune onto one.
export const PHASE_SEED_DEFAULT = PHASE_SEED
export const ALPHA_MAX_DEFAULT = ALPHA_MAX

// Kurtosis of a block (peakiness). Phase-noise sits near 3 (Gaussian); a resolved
// speech/babble block spikes well above it. Used to pick the currently-tuned
// station for playback — not to find the focal (the engine has no focal to find).
function blockKurtosis(a, base, L) {
  let mean = 0
  for (let i = 0; i < L; i++) mean += a[base + i]
  mean /= L
  let m2 = 0
  let m4 = 0
  for (let i = 0; i < L; i++) {
    const d = a[base + i] - mean
    const d2 = d * d
    m2 += d2
    m4 += d2 * d2
  }
  m2 /= L
  m4 /= L
  return m2 > 0 ? m4 / (m2 * m2) : 0
}

export class RevealEngine {
  constructor(audioContext, opts = {}) {
    this.ctx = audioContext
    this.axisMax = AXIS_MAX
    this.alphaMax = opts.alphaMax ?? ALPHA_MAX
    this.phaseSeed = opts.phaseSeed ?? PHASE_SEED
    this.blockLen = opts.blockLen ?? BLOCK_LEN

    this.buffer = null
    this.revl = 0
    this.alpha = alphaForReveal(0, this.axisMax, this.alphaMax)

    // Per-block cached spectra of the garbled asset, the shared per-bin phase
    // mask, and the layout (block count, total samples).
    this._reG = [] // Float64Array per block
    this._imG = []
    this._phi = null
    this._n = 0 // total samples across all blocks
    this._blocks = 0

    this.master = this.ctx.createGain()
    this.node = null
  }

  async load(url) {
    const resp = await fetch(url)
    if (!resp.ok) throw new Error(`failed to load ${url}: ${resp.status}`)
    const arr = await resp.arrayBuffer()
    this.buffer = await this.ctx.decodeAudioData(arr)
    this._prepare()
    return this.buffer
  }

  // Build the shared phase mask and cache the forward FFT of each block, so each
  // dial change only costs one inverse FFT per block. The asset is treated as
  // consecutive blocks of `blockLen` samples; any trailing remainder is ignored.
  _prepare() {
    const data = this.buffer.getChannelData(0)
    const L = this.blockLen
    const blocks = Math.floor(data.length / L)
    this._blocks = blocks
    this._n = blocks * L
    this._phi = buildPhaseMask(this.phaseSeed, L)
    this._reG = []
    this._imG = []
    for (let b = 0; b < blocks; b++) {
      const re = new Float64Array(L)
      const im = new Float64Array(L)
      const base = b * L
      for (let i = 0; i < L; i++) re[i] = data[base + i]
      transform(re, im, false)
      this._reG.push(re)
      this._imG.push(im)
    }
  }

  async init() {
    if (this.ctx.sampleRate !== ASSET_RATE) {
      console.warn(
        `RevealEngine: AudioContext sampleRate ${this.ctx.sampleRate} does not match ASSET_RATE ${ASSET_RATE}; the asset will be resampled and the scramble will not cancel (noise at every setting).`,
      )
    }
    await this.ctx.audioWorklet.addModule(revealWorkletUrl)
    return this
  }

  connect(dest) {
    this.master.connect(dest)
    return this
  }

  // Descramble every block's cached spectrum at the current alpha and write the
  // real time-domain result into the concatenated output buffer. A block resolves
  // to clean audio only where alpha matches the focal rotation baked into it.
  _render() {
    const L = this.blockLen
    const out = new Float32Array(this._n)
    for (let b = 0; b < this._blocks; b++) {
      const re = this._reG[b].slice()
      const im = this._imG[b].slice()
      rotatePhase(re, im, this._phi, -this.alpha)
      transform(re, im, true)
      const base = b * L
      for (let i = 0; i < L; i++) out[base + i] = re[i]
    }
    return out
  }

  // Render all blocks at the current alpha and return only the block that
  // resolves most strongly right now (highest kurtosis = most speech/babble-like).
  // This is what plays: turning the dial swaps which station you're tuned to in
  // real time. Between focals every block is equal phase-noise, so you hear
  // continuous static; nearing a focal, that block rises above the noise floor and
  // fades in. The engine never knows which focal is the real message — it just
  // plays whatever resolves at the current setting.
  _renderTuned() {
    const L = this.blockLen
    const full = this._render()
    let bestK = -Infinity
    let bestBase = 0
    for (let b = 0; b < this._blocks; b++) {
      const k = blockKurtosis(full, b * L, L)
      if (k > bestK) {
        bestK = k
        bestBase = b * L
      }
    }
    return full.slice(bestBase, bestBase + L)
  }

  setReveal(revl) {
    this.revl = Math.max(0, Math.min(this.axisMax, revl))
    this.alpha = alphaForReveal(this.revl, this.axisMax, this.alphaMax)
    if (this.node && this._blocks) {
      const out = this._renderTuned()
      this.node.port.postMessage({ buffer: out }, [out.buffer])
    }
    return this.revl
  }

  start() {
    if (this.node) return this
    if (!this.buffer) throw new Error('load() a buffer before start()')
    const out = this._renderTuned()
    this.node = new AudioWorkletNode(this.ctx, 'reveal-processor', {
      outputChannelCount: [2],
      processorOptions: { buffer: out },
    })
    this.node.connect(this.master)
    return this
  }

  stop() {
    if (this.node) {
      this.node.disconnect()
      this.node = null
    }
    return this
  }
}
