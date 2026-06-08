// src/keys.js
// Pure: map a keydown on the reveal dial to the next reveal value.
// Returns the new value clamped to 0..1000, or null if the key is not a
// reveal control key (so the caller can let it pass through untouched).
//
// Coarse + fine, mirroring the design spec:
//   Arrow:        +/- 10  (normal, audible step)
//   Shift+Arrow:  +/-  1  (fine homing-in)
//   PageUp/Down:  +/- 50  (fast travel)
//   Home / End:   0 / 1000
import { AXIS_MAX } from './constants.js'

const COARSE = 10
const FINE = 1
const FAST = 50

function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x))
}

export function nextReveal(current, { key, shiftKey = false } = {}) {
  const step = shiftKey ? FINE : COARSE
  let next
  switch (key) {
    case 'ArrowRight':
    case 'ArrowUp':
      next = current + step
      break
    case 'ArrowLeft':
    case 'ArrowDown':
      next = current - step
      break
    case 'PageUp':
      next = current + FAST
      break
    case 'PageDown':
      next = current - FAST
      break
    case 'Home':
      next = 0
      break
    case 'End':
      next = AXIS_MAX
      break
    default:
      return null
  }
  return clamp(next, 0, AXIS_MAX)
}
