// src/reveal-engine.js
import { transform } from './fft.js'
import { buildPhaseMask, alphaForReveal, rotatePhase } from './scramble.js'
import { AXIS_MAX, ASSET_RATE, PHASE_SEED, ALPHA_MAX } from './constants.js'
import revealWorkletUrl from './reveal-worklet.js?url'

// The focal value is NOT here. The asset is a phase-scrambled recording; the
// dial maps linearly to a phase-rotation amount (alpha) and the engine renders
// the descrambled signal by rotating the cached asset spectrum by -alpha. The
// voice reconstructs only where alpha matches the amount baked into the asset
// offline, which this code does not know.
export const PHASE_SEED_DEFAULT = PHASE_SEED
export const ALPHA_MAX_DEFAULT = ALPHA_MAX

export class RevealEngine {
  constructor(audioContext, opts = {}) {
    this.ctx = audioContext
    this.axisMax = AXIS_MAX
    this.alphaMax = opts.alphaMax ?? ALPHA_MAX
    this.phaseSeed = opts.phaseSeed ?? PHASE_SEED

    this.buffer = null
    this.revl = 0
    this.alpha = alphaForReveal(0, this.axisMax, this.alphaMax)

    // Cached spectrum of the garbled asset, and the per-bin phase mask.
    this._reG = null
    this._imG = null
    this._phi = null
    this._n = 0

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

  // Build the phase mask and cache the forward FFT of the garbled asset, so each
  // dial change only costs one inverse FFT.
  _prepare() {
    const data = this.buffer.getChannelData(0)
    const n = data.length
    this._n = n
    this._phi = buildPhaseMask(this.phaseSeed, n)
    this._reG = new Float64Array(n)
    this._imG = new Float64Array(n)
    for (let i = 0; i < n; i++) this._reG[i] = data[i]
    transform(this._reG, this._imG, false)
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

  // Descramble the cached asset spectrum at the current alpha and return the
  // real time-domain buffer. At the hidden focal alpha this is the clean voice.
  _render() {
    const n = this._n
    const re = this._reG.slice()
    const im = this._imG.slice()
    rotatePhase(re, im, this._phi, -this.alpha)
    transform(re, im, true)
    const out = new Float32Array(n)
    for (let i = 0; i < n; i++) out[i] = re[i]
    return out
  }

  setReveal(revl) {
    this.revl = Math.max(0, Math.min(this.axisMax, revl))
    this.alpha = alphaForReveal(this.revl, this.axisMax, this.alphaMax)
    if (this.node && this._reG) {
      const out = this._render()
      this.node.port.postMessage({ buffer: out }, [out.buffer])
    }
    return this.revl
  }

  start() {
    if (this.node) return this
    if (!this.buffer) throw new Error('load() a buffer before start()')
    const out = this._render()
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
