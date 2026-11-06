#!/usr/bin/env python3
"""Puts the music and sounds under the demo video.

test/demo/demo_video_test.dart writes, next to the silent video, which music
the app asked for and which sounds it played, frame by frame
(app/build/demo/sounds.txt). This mixes the same files from app/assets/sounds
into one track, at about the app's own balance, and writes
app/build/demo/demo.mp4.

    python3 tools/demo_audio.py
"""
import pathlib
import subprocess
import sys
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEMO = ROOT / "app/build/demo"
SOUNDS = ROOT / "app/assets/sounds"
RATE = 22050
MUSIC_GAIN, SFX_GAIN = 0.5, 0.85
FADE = 0.35  # seconds, when the music changes


def load(name):
    with wave.open(str(SOUNDS / f"{name}.wav")) as w:
        rate, n, width = w.getframerate(), w.getnframes(), w.getsampwidth()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
        if w.getnchannels() > 1:
            data = data.reshape(-1, w.getnchannels()).mean(axis=1)
    assert width == 2
    if rate != RATE:
        t = np.arange(int(len(data) * RATE / rate)) * rate / RATE
        data = np.interp(t, np.arange(len(data)), data)
    return data


def main():
    lines = (DEMO / "sounds.txt").read_text().split("\n")
    fps = int(lines[0].split()[1])
    frames = int(lines[1].split()[1])
    total = int(frames / fps * RATE) + RATE
    music = np.zeros(total)
    sfx = np.zeros(total)
    changes = []
    cache = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        frame, kind, name = line.split()
        at = int(int(frame) / fps * RATE)
        if kind == "sfx":
            s = cache.setdefault(name, load(name))
            end = min(total, at + len(s))
            sfx[at:end] += s[: end - at]
        else:
            changes.append((at, None if name == "-" else name))
    # Each piece of music loops from its start until the next one.
    changes.append((total, None))
    fade = int(FADE * RATE)
    for (start, name), (end, _) in zip(changes, changes[1:]):
        if name is None or end <= start:
            continue
        loop = cache.setdefault(name, load(name))
        n = end - start
        piece = np.tile(loop, n // len(loop) + 1)[:n].copy()
        ramp = min(fade, n // 2)
        piece[:ramp] *= np.linspace(0, 1, ramp)
        piece[n - ramp:] *= np.linspace(1, 0, ramp)
        music[start:end] += piece
    mix = music * MUSIC_GAIN + sfx * SFX_GAIN
    peak = np.abs(mix).max()
    if peak > 0.95:
        mix *= 0.95 / peak
    pcm = (mix * 32767).astype(np.int16)
    out = DEMO / "demo_audio.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(DEMO / "demo_silent.mp4"), "-i", str(out),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(DEMO / "demo.mp4")],
        check=True,
    )
    print(f"{DEMO / 'demo.mp4'}: {frames / fps:.1f} s, peak {peak:.2f}")


if __name__ == "__main__":
    sys.exit(main())
