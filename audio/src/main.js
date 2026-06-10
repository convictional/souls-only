import { RevealEngine } from './reveal-engine.js'
import { nextReveal } from './keys.js'
import { assetUrl, assetBlockLen } from './asset-url.js'
import { ASSET_RATE } from './constants.js'

// Which asset to load: the shipped ten-station file by default, or ?asset=<name>
// for an alternate (e.g. the overlap experiment, ?asset=overlap-3.wav). The
// overlap asset packs all stations into one longer block, so it needs a matching
// block length for the engine to descramble correctly.
const ASSET = assetUrl(location.search)
const BLOCK = assetBlockLen(location.search)

const toggle = document.getElementById('toggle')
const slider = document.getElementById('revl')
const valueLabel = document.getElementById('revlValue')

const ctx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: ASSET_RATE })
const engine = new RevealEngine(ctx, { blockLen: BLOCK })
engine.connect(ctx.destination)

let loaded = false
let loading = false
let playing = false

// Rendering a dial change costs one inverse FFT per segment, so coalesce rapid
// drag events to one render per animation frame: update the dial/label instantly,
// but only re-tune the audio to the latest value each frame. This keeps scrubbing
// smooth and always lands on the value the dial is actually showing.
let pendingReveal = null
let renderQueued = false

function flushReveal() {
  renderQueued = false
  if (pendingReveal === null) return
  const v = pendingReveal
  pendingReveal = null
  engine.setReveal(v)
}

function applyReveal(v) {
  slider.value = String(v)
  valueLabel.textContent = String(v)
  pendingReveal = v
  if (!renderQueued) {
    renderQueued = true
    requestAnimationFrame(flushReveal)
  }
}

applyReveal(Number(slider.value))

slider.addEventListener('input', () => {
  applyReveal(Number(slider.value))
})

// Keyboard scrubbing is handled on the slider itself, not the document, so it
// keeps working for screen reader users (their browse mode passes arrow keys
// through only when a form control is focused). preventDefault stops the native
// range from also stepping, which would double the movement.
slider.addEventListener('keydown', (e) => {
  const v = nextReveal(Number(slider.value), e)
  if (v === null) return
  e.preventDefault()
  applyReveal(v)
})

toggle.addEventListener('click', async () => {
  if (loading) return
  // Browsers require a user gesture to start audio.
  if (ctx.state === 'suspended') await ctx.resume()
  if (!loaded) {
    loading = true
    try {
      await engine.load(ASSET)
      await engine.init()
      loaded = true
    } finally {
      loading = false
    }
  }
  if (!playing) {
    engine.setReveal(Number(slider.value))
    engine.start()
    playing = true
    toggle.textContent = 'Stop'
    // Land focus on the dial so a keyboard or screen reader user can scrub
    // immediately without hunting for the control.
    slider.focus()
  } else {
    engine.stop()
    playing = false
    toggle.textContent = 'Play'
  }
})
