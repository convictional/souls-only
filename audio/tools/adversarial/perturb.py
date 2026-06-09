#!/usr/bin/env python3
"""tools/adversarial/perturb.py  (offline, never shipped)

Targeted audio adversarial attack against Whisper-tiny. Synthesizes the real
message in the same voice the decoys use, then optimizes a small additive
perturbation so that Whisper-tiny transcribes it as an innocuous nursery rhyme
(the disguise target) -- while the speech stays clearly intelligible to a human
ear. A primed human at the message focal hears the real words; an attacker who
runs Whisper-tiny over all ten stations gets ten clean, distinct rhymes and no
odd-one-out.

The perturbation is defined at the asset rate (22050 Hz) but the loss is measured
AFTER Whisper's own resample to 16 kHz and log-mel front-end, so it survives that
(otherwise destructive) step. macOS only (uses `say`). Run:

    tools/adversarial/.venv/bin/python tools/adversarial/perturb.py

Outputs tools/adversarial/message_adv.wav (22050 Hz, 16-bit, exactly BLOCK_LEN
samples, peak 0.8) which tools/garble.mjs embeds as the message segment verbatim.
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio
import whisper

# --- must match src/constants.js -------------------------------------------------
ASSET_RATE = 22050
BLOCK_LEN = 65536  # ~2.97 s at 22050

# --- config ----------------------------------------------------------------------
MESSAGE = "This is a souls only audio message."
# Disguise target: a nursery rhyme that is NOT one of the nine decoys, so the ten
# Whisper transcripts stay distinct (no duplicate tell).
TARGET = " Little Miss Muffet sat on a tuffet, eating her curds and whey."
MODEL = "tiny"          # the attacker's transcriber we target
DEVICE = "cpu"          # CPU is reliable for STFT/complex grads; tiny is small
STEPS = 1500
LR = 2e-3
EPS = 0.06              # L-inf bound on the perturbation (~-24 dB vs 0.8 peak)
L2_WEIGHT = 0.5         # pull the perturbation small within the L-inf box
WHISPER_RATE = 16000

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN_WAV = os.path.join(HERE, "message.clean.wav")  # transient, gitignored
OUT_WAV = os.path.join(HERE, "message_adv.wav")
TMP_AIFF = "/tmp/soa-adv-clean.aiff"


def synth_clean():
    """Synthesize the message with `say`, convert to 22050 mono, fit to BLOCK_LEN,
    peak-normalize to 0.8 -- identical preprocessing to garble.mjs renderClip()."""
    subprocess.run(["say", "-o", TMP_AIFF, MESSAGE], check=True)
    subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", f"LEI16@{ASSET_RATE}", "-c", "1", TMP_AIFF, CLEAN_WAV],
        check=True,
    )
    os.remove(TMP_AIFF)
    samples, rate = sf.read(CLEAN_WAV, dtype="float32")
    assert rate == ASSET_RATE, f"{rate} != {ASSET_RATE}"
    if samples.ndim > 1:
        samples = samples[:, 0]
    clip = np.zeros(BLOCK_LEN, dtype=np.float32)
    n = min(len(samples), BLOCK_LEN)
    clip[:n] = samples[:n]
    peak = np.max(np.abs(clip))
    if peak > 0:
        clip *= 0.8 / peak
    return clip


def whisper_mel(audio16k, model):
    """Differentiable: pad/trim to 30 s and compute Whisper's log-mel."""
    audio16k = whisper.pad_or_trim(audio16k)
    return whisper.log_mel_spectrogram(audio16k, model.dims.n_mels)


def build_target_tokens(model):
    kwargs = dict(language="en", task="transcribe")
    try:
        tokenizer = whisper.tokenizer.get_tokenizer(
            model.is_multilingual, num_languages=model.num_languages, **kwargs
        )
    except (AttributeError, TypeError):
        tokenizer = whisper.tokenizer.get_tokenizer(model.is_multilingual, **kwargs)
    sot = list(tokenizer.sot_sequence_including_notimestamps)
    text = tokenizer.encode(TARGET)
    full = sot + text + [tokenizer.eot]
    dec_in = torch.tensor(full[:-1], dtype=torch.long, device=DEVICE)
    labels = torch.tensor(full[1:], dtype=torch.long, device=DEVICE)
    # Only score the text + eot positions (the sot/lang/task tokens are given).
    text_start = len(sot) - 1
    mask = torch.zeros_like(labels, dtype=torch.bool)
    mask[text_start:] = True
    return dec_in, labels, mask, tokenizer


def transcribe(model, audio16k_np):
    opts = whisper.DecodingOptions(language="en", without_timestamps=True, fp16=False)
    result = whisper.decode(model, whisper_mel(torch.from_numpy(audio16k_np).float(), model), opts)
    return result.text.strip()


def main():
    print(f"loading whisper-{MODEL} on {DEVICE} ...", flush=True)
    model = whisper.load_model(MODEL, device=DEVICE)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)

    clip = synth_clean()
    clip_t = torch.from_numpy(clip).to(DEVICE)
    resampler = torchaudio.transforms.Resample(ASSET_RATE, WHISPER_RATE).to(DEVICE)

    # Baseline: what does Whisper hear on the clean message?
    clean16 = resampler(clip_t).detach().cpu().numpy()
    print("clean transcript :", repr(transcribe(model, clean16)), flush=True)

    dec_in, labels, mask, tok = build_target_tokens(model)
    print("target           :", repr(TARGET.strip()), flush=True)

    delta = torch.zeros(BLOCK_LEN, device=DEVICE, requires_grad=True)
    opt = torch.optim.Adam([delta], lr=LR)
    ce = torch.nn.CrossEntropyLoss(reduction="none")

    for step in range(STEPS):
        opt.zero_grad()
        adv22 = clip_t + delta
        adv16 = resampler(adv22)
        mel = whisper_mel(adv16, model)
        audio_features = model.encoder(mel.unsqueeze(0))
        logits = model.decoder(dec_in.unsqueeze(0), audio_features)[0]
        loss_ctc = (ce(logits, labels) * mask).sum() / mask.sum()
        loss_l2 = (delta ** 2).mean()
        loss = loss_ctc + L2_WEIGHT * loss_l2
        loss.backward()
        opt.step()
        with torch.no_grad():
            delta.clamp_(-EPS, EPS)
            (clip_t + delta).clamp_(-1.0, 1.0)  # keep in range; delta absorbs it below
            delta.data = (torch.clamp(clip_t + delta, -1.0, 1.0) - clip_t)
        if step % 100 == 0 or step == STEPS - 1:
            print(f"  step {step:4d}  ctc={loss_ctc.item():.4f}  l2={loss_l2.item():.6f}", flush=True)

    adv22 = torch.clamp(clip_t + delta, -1.0, 1.0).detach().cpu().numpy().astype(np.float32)
    sf.write(OUT_WAV, adv22, ASSET_RATE, subtype="PCM_16")

    # Verify what the attacker would actually get, from the written 16-bit file.
    adv_read, _ = sf.read(OUT_WAV, dtype="float32")
    adv16 = resampler(torch.from_numpy(adv_read).float()).detach().cpu().numpy()
    snr = 10 * np.log10(np.mean(clip ** 2) / max(np.mean((adv_read - clip) ** 2), 1e-12))
    print("-" * 60, flush=True)
    print("adv transcript   :", repr(transcribe(model, adv16)), flush=True)
    print(f"perturbation SNR : {snr:.1f} dB (higher = less audible)", flush=True)
    print(f"wrote {OUT_WAV}", flush=True)


if __name__ == "__main__":
    main()
