// tests/keys.test.js
import { describe, it, expect } from 'vitest'
import { nextReveal } from '../src/keys.js'

const at = (current, key, opts = {}) => nextReveal(current, { key, ...opts })

describe('nextReveal coarse arrow step (+/- 10)', () => {
  it('right and up increase by 10', () => {
    expect(at(300, 'ArrowRight')).toBe(310)
    expect(at(300, 'ArrowUp')).toBe(310)
  })

  it('left and down decrease by 10', () => {
    expect(at(300, 'ArrowLeft')).toBe(290)
    expect(at(300, 'ArrowDown')).toBe(290)
  })
})

describe('nextReveal fine step with Shift (+/- 1)', () => {
  it('shift makes the arrow step 1', () => {
    expect(at(300, 'ArrowRight', { shiftKey: true })).toBe(301)
    expect(at(300, 'ArrowLeft', { shiftKey: true })).toBe(299)
    expect(at(300, 'ArrowUp', { shiftKey: true })).toBe(301)
    expect(at(300, 'ArrowDown', { shiftKey: true })).toBe(299)
  })
})

describe('nextReveal fast travel with Page keys (+/- 50)', () => {
  it('page up increases by 50, page down decreases by 50', () => {
    expect(at(300, 'PageUp')).toBe(350)
    expect(at(300, 'PageDown')).toBe(250)
  })

  it('ignores shift on page keys (still 50)', () => {
    expect(at(300, 'PageUp', { shiftKey: true })).toBe(350)
  })
})

describe('nextReveal Home and End jump to the dial ends', () => {
  it('Home goes to 0, End goes to 1000', () => {
    expect(at(420, 'Home')).toBe(0)
    expect(at(420, 'End')).toBe(1000)
  })
})

describe('nextReveal clamps to 0..1000', () => {
  it('does not go below 0', () => {
    expect(at(5, 'ArrowLeft')).toBe(0)
    expect(at(5, 'PageDown')).toBe(0)
  })

  it('does not go above 1000', () => {
    expect(at(995, 'ArrowRight')).toBe(1000)
    expect(at(995, 'PageUp')).toBe(1000)
  })
})

describe('nextReveal ignores keys it does not handle', () => {
  it('returns null for unrelated keys', () => {
    expect(at(300, 'a')).toBe(null)
    expect(at(300, 'Enter')).toBe(null)
    expect(at(300, ' ')).toBe(null)
    expect(at(300, 'Tab')).toBe(null)
  })
})
