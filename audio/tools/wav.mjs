// tools/wav.mjs
// Minimal 16-bit PCM mono WAV read/write for offline tooling (Node only).
import { readFileSync, writeFileSync } from 'node:fs'

// Returns { sampleRate, samples } where samples is a Float32Array in [-1, 1].
// Reads the first channel only; scans chunks rather than assuming a fixed header.
export function readWavMono(path) {
  const buf = readFileSync(path)
  if (buf.toString('ascii', 0, 4) !== 'RIFF' || buf.toString('ascii', 8, 12) !== 'WAVE') {
    throw new Error('not a RIFF/WAVE file')
  }
  let sampleRate = 0
  let channels = 1
  let bitsPerSample = 16
  let dataOffset = -1
  let dataLength = 0
  let p = 12
  while (p + 8 <= buf.length) {
    const id = buf.toString('ascii', p, p + 4)
    const size = buf.readUInt32LE(p + 4)
    const body = p + 8
    if (id === 'fmt ') {
      channels = buf.readUInt16LE(body + 2)
      sampleRate = buf.readUInt32LE(body + 4)
      bitsPerSample = buf.readUInt16LE(body + 14)
    } else if (id === 'data') {
      dataOffset = body
      dataLength = size
    }
    p = body + size + (size % 2) // chunks are word-aligned
  }
  if (dataOffset < 0) throw new Error('no data chunk')
  if (bitsPerSample !== 16) throw new Error(`expected 16-bit PCM, got ${bitsPerSample}`)
  const frames = Math.floor(dataLength / 2 / channels)
  const samples = new Float32Array(frames)
  for (let i = 0; i < frames; i++) {
    const s = buf.readInt16LE(dataOffset + i * 2 * channels) // first channel
    samples[i] = s / 32768
  }
  return { sampleRate, samples }
}

// Writes a 16-bit PCM mono WAV from a Float32Array in [-1, 1].
export function writeWavMono(path, samples, sampleRate) {
  const n = samples.length
  const dataLength = n * 2
  const buf = Buffer.alloc(44 + dataLength)
  buf.write('RIFF', 0, 'ascii')
  buf.writeUInt32LE(36 + dataLength, 4)
  buf.write('WAVE', 8, 'ascii')
  buf.write('fmt ', 12, 'ascii')
  buf.writeUInt32LE(16, 16) // fmt chunk size
  buf.writeUInt16LE(1, 20) // PCM
  buf.writeUInt16LE(1, 22) // mono
  buf.writeUInt32LE(sampleRate, 24)
  buf.writeUInt32LE(sampleRate * 2, 28) // byte rate
  buf.writeUInt16LE(2, 32) // block align
  buf.writeUInt16LE(16, 34) // bits per sample
  buf.write('data', 36, 'ascii')
  buf.writeUInt32LE(dataLength, 40)
  for (let i = 0; i < n; i++) {
    let v = Math.max(-1, Math.min(1, samples[i]))
    buf.writeInt16LE(Math.round(v * 32767), 44 + i * 2)
  }
  writeFileSync(path, buf)
}
