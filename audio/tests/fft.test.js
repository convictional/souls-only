// tests/fft.test.js
import { describe, it, expect } from 'vitest'
import { transform, isPow2 } from '../src/fft.js'

describe('isPow2', () => {
  it('recognizes powers of two', () => {
    expect(isPow2(1)).toBe(true)
    expect(isPow2(2)).toBe(true)
    expect(isPow2(1024)).toBe(true)
    expect(isPow2(3)).toBe(false)
    expect(isPow2(0)).toBe(false)
    expect(isPow2(6)).toBe(false)
  })
})

describe('transform', () => {
  it('throws on non-power-of-two length', () => {
    expect(() => transform(new Float64Array(3), new Float64Array(3))).toThrow(/power of two/)
  })

  it('FFT of an impulse is all ones', () => {
    const n = 8
    const re = new Float64Array(n)
    const im = new Float64Array(n)
    re[0] = 1
    transform(re, im, false)
    for (let k = 0; k < n; k++) {
      expect(re[k]).toBeCloseTo(1, 10)
      expect(im[k]).toBeCloseTo(0, 10)
    }
  })

  it('FFT of a constant concentrates all energy in bin 0', () => {
    const n = 8
    const re = new Float64Array(n).fill(2)
    const im = new Float64Array(n)
    transform(re, im, false)
    expect(re[0]).toBeCloseTo(16, 10) // N * value
    for (let k = 1; k < n; k++) {
      expect(re[k]).toBeCloseTo(0, 10)
      expect(im[k]).toBeCloseTo(0, 10)
    }
  })

  it('inverse(forward(x)) recovers x', () => {
    const n = 16
    const re = new Float64Array(n)
    const im = new Float64Array(n)
    const orig = []
    for (let i = 0; i < n; i++) {
      re[i] = Math.sin(i * 0.7) + 0.3 * i
      orig.push(re[i])
    }
    transform(re, im, false)
    transform(re, im, true)
    for (let i = 0; i < n; i++) {
      expect(re[i]).toBeCloseTo(orig[i], 10)
      expect(im[i]).toBeCloseTo(0, 10)
    }
  })
})
