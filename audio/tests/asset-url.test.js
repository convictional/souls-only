// tests/asset-url.test.js
// Resolve which asset the demo loads from the page's query string. The shipped
// asset is the 3-channel overlap (message.wav); ?asset= can point at another file
// in /assets, basename-only (no path traversal out of the assets directory).
import { describe, it, expect } from 'vitest'
import { assetUrl } from '../src/asset-url.js'

describe('assetUrl', () => {
  it('defaults to the shipped overlap asset', () => {
    expect(assetUrl('')).toBe('/assets/message.wav')
  })

  it('loads an alternate asset named in ?asset=', () => {
    expect(assetUrl('?asset=other.wav')).toBe('/assets/other.wav')
  })

  it('falls back to the default when ?asset= is empty', () => {
    expect(assetUrl('?asset=')).toBe('/assets/message.wav')
  })

  it('strips path separators so it cannot escape /assets', () => {
    expect(assetUrl('?asset=../../secret.wav')).toBe('/assets/....secret.wav')
    expect(assetUrl('?asset=/etc/passwd')).not.toContain('/etc/')
  })
})
