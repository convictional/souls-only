#!/usr/bin/env python3
"""tools/adversarial/verify.py  (offline verification, never shipped)

Transcribes each descrambled station with Whisper-tiny exactly as an attacker
would (file -> ffmpeg resample to 16 kHz -> Whisper). Run descramble_all.mjs first
to produce the verify_<focal>.wav files. Expect: nine distinct nursery rhymes and
the message station (focal 650) ALSO reading as a rhyme (Little Miss Muffet) --
no odd-one-out.
"""
import glob
import os
import re

import whisper

HERE = os.path.dirname(os.path.abspath(__file__))
model = whisper.load_model("tiny", device="cpu")

files = sorted(
    glob.glob(os.path.join(HERE, "verify_*.wav")),
    key=lambda p: int(re.search(r"verify_(\d+)\.wav", p).group(1)),
)
for path in files:
    focal = re.search(r"verify_(\d+)\.wav", path).group(1)
    text = model.transcribe(path, language="en", without_timestamps=True, fp16=False)["text"].strip()
    flag = "  <-- message" if focal == "650" else ""
    print(f"focal {focal:>4} : {text!r}{flag}")
