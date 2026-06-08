// src/reveal-worklet.js
// Loops a precomputed buffer and plays it. The main thread renders the
// descrambled signal for the current dial position (one inverse FFT) and posts
// the new buffer here; the processor swaps it in while keeping its playback
// position continuous. This file has no imports and bundles cleanly as a
// standalone worklet. No focal value lives here.
class RevealProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super()
    this.buf = options.processorOptions.buffer
    this.N = this.buf.length
    this.pos = 0
    this.port.onmessage = (e) => {
      if (e.data && e.data.buffer) {
        this.buf = e.data.buffer
        this.N = this.buf.length
        if (this.pos >= this.N) this.pos = 0
      }
    }
  }

  process(inputs, outputs) {
    const channels = outputs[0]
    const out = channels[0]
    for (let k = 0; k < out.length; k++) {
      out[k] = this.buf[this.pos]
      this.pos = this.pos + 1
      if (this.pos >= this.N) this.pos = 0
    }
    for (let c = 1; c < channels.length; c++) channels[c].set(out)
    return true
  }
}

registerProcessor('reveal-processor', RevealProcessor)
