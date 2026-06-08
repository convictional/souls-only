// tests/no-leak.test.js
import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')

// Every .js module under src/ ships to the browser. Globbing (rather than a
// hardcoded list) means a new shipped module is guarded automatically.
const shippedFiles = readdirSync(join(root, 'src'))
  .filter((f) => f.endsWith('.js'))
  .map((f) => `src/${f}`)

describe('no focal-value leak in shipped code', () => {
  it('finds shipped src modules to check', () => {
    expect(shippedFiles.length).toBeGreaterThan(0)
  })

  for (const rel of shippedFiles) {
    it(`${rel} does not contain the focal literal 650`, () => {
      const text = readFileSync(join(root, rel), 'utf8')
      // \b650\b matches the focal value as a standalone number, the realistic shape
      // of an accidental leak; it ignores substrings inside larger numbers.
      expect(text).not.toMatch(/\b650\b/)
    })
  }

  it('the offline tool is where the focal value lives', () => {
    const tool = readFileSync(join(root, 'tools/garble.mjs'), 'utf8')
    // \b650\b matches the focal value as a standalone number, the realistic shape
    // of an accidental leak; it ignores substrings inside larger numbers.
    expect(tool).toMatch(/\b650\b/)
  })
})
