import { RevealEngine } from './reveal-engine.js'
import { nextReveal } from './keys.js'
import { ASSET_RATE } from './constants.js'

const toggle = document.getElementById('toggle')
const slider = document.getElementById('revl')
const valueLabel = document.getElementById('revlValue')

const ctx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: ASSET_RATE })
const engine = new RevealEngine(ctx)
engine.connect(ctx.destination)

let loaded = false
let loading = false
let playing = false

function applyReveal(v) {
  slider.value = String(v)
  valueLabel.textContent = String(v)
  engine.setReveal(v)
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
      await engine.load('/assets/message.wav')
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
