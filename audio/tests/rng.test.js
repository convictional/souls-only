// tests/rng.test.js
import { describe, it, expect } from 'vitest'
import { mulberry32 } from '../src/rng.js'

describe('mulberry32', () => {
  it('is deterministic for a given seed', () => {
    const a = mulberry32(12345)
    const b = mulberry32(12345)
    expect([a(), a(), a()]).toEqual([b(), b(), b()])
  })

  it('produces different sequences for different seeds', () => {
    const a = mulberry32(1)
    const b = mulberry32(2)
    expect(a()).not.toEqual(b())
  })

  it('returns values in [0, 1)', () => {
    const r = mulberry32(99)
    for (let i = 0; i < 1000; i++) {
      const v = r()
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThan(1)
    }
  })
})
