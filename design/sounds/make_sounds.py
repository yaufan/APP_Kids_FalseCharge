"""眼尖尖大挑戰 (Sharp Eyes): every sound in the app, made here from sine
waves and noise, so every one is ours: nothing recorded, nothing downloaded,
and every tune written for this app.

- Music (WAV, 16,000 Hz): three tunes, each with its own metre, key and
  instruments, and each unlike the sibling apps' tunes:
  - music_home: curious and playful, on tiptoe (4/4, A minor turning to C
    major): a soft clarinet over pizzicato strings, a sneaky tick on the
    off-beats; the second half brightens up.
  - music_play: while searching: calm, focused and cheerful (4/4, A flat,
    soft seventh chords): a vibraphone sings a slow tune over a gently
    rolling marimba and a light shaker. Quieter than the home tune.
  - music_rest: a lullaby (4/4, slow, D flat): a celesta sings over warm
    pads and a soft bass like a heartbeat; a music box answers.
  Each tune is as long as its bars, and what still rings at the end is
  carried round to the start, so it loops without a seam.
- Short sounds (WAV, 22,050 Hz): taps, finds, the chameleon 小變's voice,
  and a short sound for each scene as it opens (birds in the park, a wave
  at the beach...).
- For children from 2: fun, warm and soft. Nothing harsh or sudden; a tap
  in the wrong place is a soft, neutral "pup", never a buzzer.
- Voices are a buzz through formant filters, as in the sibling apps.
- Every random choice uses a fixed seed, so each run writes the same files.
- Every short sound is set to the same loudness as heard through a phone
  speaker (A-weighting, and nothing under 250 Hz), plus or minus a few dB
  where it should sit softer, with its peak at most 0.72. The music is set
  the same way, about 8 dB under the short sounds. Low sounds get a little
  of their own overtones added (`carry`), so a phone still carries them.

The helpers (t_of, env, sweep, decay, lowpass, bandpass, highpass, norm,
partial, bell, marimba, xylo, place, tune_loop, resonator, voice, ease,
glide, above, spans, melody, root_of, pluck_bass, metal, woodblock, shaker,
kick, jingle, noise_through, music_box_note, carry, round_off, celesta,
chime, a_weight, loudness, chord_tones, harmonics, pizz, toy_horn, spring,
tidy, phone_ready, level, write, seam, report, read, preview) come from
想一想樂園's design/sounds/make_sounds.py (which took most of them from
小卡認天下, 動物小餐廳 and 字母寵物); the seam check now also compares the
jump with the steps right around it. New here: the clarinet, vibraphone,
warm pad, a little room (echoes, for things far away), crowd babble, bird
chirps, the lead-over-band check, every tune and every sound.

    python3 design/sounds/make_sounds.py                  # writes app/assets/sounds/*.wav
    python3 design/sounds/make_sounds.py preview OUT.m4a  # and a listening preview
"""
import pathlib
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import fftconvolve, lfilter, resample_poly

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "assets" / "sounds"
SR = 22050       # short sounds and voices
LOOP_SR = 16000  # music
LIMIT = 3_500_000  # bytes, the whole folder

# Notes (Hz), with flats as well as sharps.
NOTE = {f"{n}{o}": 440 * 2 ** ((k - 9) / 12 + o - 4)
        for o in range(1, 9) for k, n in enumerate("C C# D D# E F F# G G# A A# B".split())}
for _o in range(1, 9):
    for _flat, _sharp in (("Db", "C#"), ("Eb", "D#"), ("Gb", "F#"), ("Ab", "G#"), ("Bb", "A#")):
        NOTE[f"{_flat}{_o}"] = NOTE[f"{_sharp}{_o}"]


# ---------------------------------------------------------------- helpers (from 想一想樂園)


def t_of(dur, sr=SR):
    return np.arange(int(dur * sr)) / sr


def env(n, attack=0.005, release=0.05, sr=SR):
    """Up quickly, down smoothly: no clicks at either end."""
    e = np.ones(n)
    a, r = max(1, min(n, int(attack * sr))), max(1, min(n, int(release * sr)))
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def sweep(f, sr=SR):
    """A sine whose frequency follows the array [f] (Hz per sample)."""
    return np.sin(2 * np.pi * np.cumsum(f) / sr)


def decay(n, tau, sr=SR):
    return np.exp(-np.arange(n) / (tau * sr))


def lowpass(x, cutoff, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spec, len(x))


def bandpass(x, lo, hi, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (lo / np.maximum(freqs, 1)) ** 4) / (1 + (freqs / hi) ** 4)
    return np.fft.irfft(spec, len(x))


def highpass(x, cutoff, sr=SR):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    spec *= 1 / (1 + (cutoff / np.maximum(freqs, 1e-3)) ** 4)
    return np.fft.irfft(spec, len(x))


def norm(x):
    return x / max(1e-9, np.abs(x).max())


def partial(freq, t, sr):
    """A sine at [freq], or silence if it is too high for [sr] (it would fold
    back down as a wrong note)."""
    return np.sin(2 * np.pi * freq * t) if freq < 0.45 * sr else np.zeros_like(t)


def bell(freq, dur=0.5, sr=SR, bright=1.0):
    """A soft glockenspiel note: a few partials, the high ones dying first."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.35))
         + 0.35 * bright * partial(freq * 2.76, t, sr) * np.exp(-t / (dur * 0.12))
         + 0.15 * bright * partial(freq * 5.4, t, sr) * np.exp(-t / (dur * 0.06)))
    return x * env(len(t), 0.002, 0.03, sr)


def marimba(freq, dur=0.5, sr=SR):
    t = t_of(dur, sr)
    x = partial(freq, t, sr) * np.exp(-t / (dur * 0.3)) + 0.2 * partial(freq * 4, t, sr) * np.exp(-t / (dur * 0.05))
    return x * env(len(t), 0.003, 0.03, sr)


def xylo(freq, dur=0.5, sr=LOOP_SR):
    """A wooden xylophone bar: the marimba's knock with a little ring on top."""
    wood = 0.8 * marimba(freq, dur, sr)
    ring = 0.15 * bell(freq, dur * 0.8, sr, bright=0.3)
    wood[:len(ring)] += ring
    return wood


def place(total, parts, sr=SR):
    """[parts]: (start seconds, signal) mixed into [total] seconds."""
    out = np.zeros(int(total * sr))
    for start, sig in parts:
        i = int(start * sr)
        j = min(len(out), i + len(sig))
        out[i:j] += sig[: j - i]
    return out


def tune_loop(seconds, notes, sr=LOOP_SR):
    """[notes]: (start seconds, signal); what rings past [seconds] wraps to the start."""
    n = int(round(seconds * sr))
    tail = max(len(sig) + int(start * sr) for start, sig in notes) - n
    out = np.zeros(n + max(0, tail))
    for start, sig in notes:
        i = int(start * sr)
        out[i:i + len(sig)] += sig
    loop = out[:n].copy()
    if tail > 0:
        loop[:tail] += out[n:]
    return loop


def resonator(x, freq, bw, sr=SR, block=64):
    """A two-pole resonance at [freq] Hz (a number, or one per sample, for a
    sound that changes) of bandwidth [bw] Hz."""
    freq = np.broadcast_to(np.asarray(freq, dtype=float), x.shape)
    y, zi = np.zeros_like(x), np.zeros(2)
    r = np.exp(-np.pi * bw / sr)
    for i in range(0, len(x), block):
        th = 2 * np.pi * freq[i] / sr
        y[i:i + block], zi = lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x[i:i + block], zi=zi)
    return y


def voice(f0, formants, rng, breath=0.03, rough=0.0, sr=SR):
    """A voice at pitch [f0] (Hz per sample) through [formants]: (Hz or Hz
    per sample, bandwidth, gain). [rough] jitters the pitch, for a growl."""
    n = len(f0)
    if rough:
        f0 = f0 * (1 + rough * lowpass(rng.standard_normal(n), 60, sr) * 3)
    buzz = 2 * (np.cumsum(f0) / sr % 1) - 1 + breath * rng.standard_normal(n)
    out = np.zeros(n)
    for f, bw, gain in formants:
        y = resonator(buzz, f, bw, sr)
        out += gain * y / max(1e-9, np.abs(y).max())
    return lowpass(out, 3800, sr)  # soft, not a kazoo


def ease(u):
    """0 to 1, smoothly, over u in 0..1."""
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def glide(t, *points):
    """A value that moves smoothly between (time, value) [points]."""
    ts, vs = zip(*points)
    out = np.interp(t, ts, vs)
    return lowpass(out - out.mean(), 25) + out.mean() if len(t) > 64 else out


def above(name, low):
    """The note called [name] (no octave) at or just above the note [low]."""
    for o in range(1, 9):
        if NOTE[f"{name}{o}"] >= NOTE[low] * 0.999:
            return f"{name}{o}"
    raise ValueError(name)


def spans(bars, beats_per_bar):
    """Bars like "F" or "Gm-C" (two chords, half a bar each) -> (beat, length in beats, chord)."""
    out = []
    for i, bar in enumerate(bars):
        parts = bar.split("-")
        each = beats_per_bar / len(parts)
        out += [(i * beats_per_bar + k * each, each, c) for k, c in enumerate(parts)]
    return out


def melody(tune, beat, start=0.0, swing=0.0, bars=None, beats_per_bar=4):
    """[tune]: (note or None for a rest, beats) one after another ->
    (seconds, note, seconds long). [swing] (in beats) delays each note that
    falls halfway through a beat, for a lilt. [bars]: check the tune fills them."""
    if bars is not None:
        assert abs(sum(b for _, b in tune) - bars * beats_per_bar) < 1e-9, tune
    out, b = [], 0.0
    for name, beats in tune:
        if name:
            late = swing if abs(b % 1 - 0.5) < 1e-6 else 0.0
            out.append((start + (b + late) * beat, name, (beats - late) * beat))
        b += beats
    return out


def root_of(chord):
    return chord[:2] if len(chord) > 1 and chord[1] in "#b" else chord[0]


def pluck_bass(freq, dur=1.0, sr=LOOP_SR):
    """A plucked double bass: round, short, warm."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.35))
         + 0.45 * partial(freq * 2, t, sr) * np.exp(-t / (dur * 0.15))
         + 0.15 * partial(freq * 3, t, sr) * np.exp(-t / (dur * 0.08)))
    return x * env(len(t), 0.006, 0.08, sr)


def metal(freq, dur, sr=SR, ratios=(1, 1.59, 2.14, 2.65, 3.15), amps=(1, .6, .45, .3, .2), taus=(.5, .3, .2, .15, .1)):
    """A small metal ting (a bell, a coin): partials that are not
    whole-number multiples; [taus] are fractions of [dur]."""
    t = t_of(dur, sr)
    x = sum(a * partial(freq * r, t, sr) * np.exp(-t / (dur * k)) for r, a, k in zip(ratios, amps, taus))
    return x * env(len(t), 0.0008, 0.03, sr)


def woodblock(freq, sr=LOOP_SR, dur=0.09):
    t = t_of(dur, sr)
    x = partial(freq, t, sr) * np.exp(-t / 0.018) + 0.45 * partial(freq * 2.3, t, sr) * np.exp(-t / 0.007)
    return x * env(len(t), 0.0008, 0.02, sr)


def shaker(rng, sr=LOOP_SR, dur=0.06):
    n = int(dur * sr)
    return norm(bandpass(rng.standard_normal(n), 3000, 7000, sr)) * env(n, 0.006, dur * 0.8, sr)


def kick(sr=LOOP_SR, dur=0.16):
    n = int(dur * sr)
    return sweep(np.geomspace(130, 55, n), sr) * decay(n, 0.05, sr) * env(n, 0.002, 0.04, sr)


def jingle(rng, dur=0.2, sr=SR):
    """A tambourine's little cymbals."""
    t = t_of(dur, sr)
    x = sum(rng.uniform(0.4, 1.0) * partial(f, t, sr) * np.exp(-t / rng.uniform(0.03, 0.07))
            for f in rng.uniform(4500, 9000, 8))
    x += 0.5 * norm(bandpass(rng.standard_normal(len(t)), 5000, 10000, sr)) * np.exp(-t / 0.02)
    return x * env(len(t), 0.001, 0.04, sr)


def noise_through(rng, centre, bw, n, sr=SR):
    """Noise through a resonance that can move: the voice of air and water."""
    return norm(resonator(rng.standard_normal(n), centre, bw, sr))


def music_box_note(freq, dur, sr=LOOP_SR, bright=1.0):
    """A music box's comb: bright at first, then a long soft ring."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / 0.9)
         + 0.4 * bright * partial(freq * 3.0, t, sr) * np.exp(-t / 0.18)
         + 0.18 * bright * partial(freq * 5.2, t, sr) * np.exp(-t / 0.06))
    return x * env(len(t), 0.002, 0.08, sr)


def carry(x, amount=0.3, lo=500, hi=3000, drive=2.5, sr=SR):
    """Phone speakers hardly play anything under about 300 Hz. For a low
    sound, add its own overtones (a soft saturation of it, kept to [lo]..[hi]
    Hz): a phone plays those, and the ear still hears the low note."""
    peak = max(1e-9, np.abs(x).max())
    over = bandpass(np.tanh(drive * x / peak), lo, hi, sr)
    return x + amount * peak * norm(over)


def round_off(x, drive=2.0):
    """Round off the tallest peaks (a soft saturation), so a sound made of
    quick hits can be as loud as the others without going over the peak."""
    return np.tanh(drive * norm(x)) / np.tanh(drive)


def celesta(freq, dur=1.0, sr=LOOP_SR):
    """A celesta: a felt hammer on a small steel bar over a wooden box. A
    sweet, round tone with a little of its octave, and a soft tick."""
    t = t_of(dur, sr)
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.3))
         + 0.25 * partial(freq * 2, t, sr) * np.exp(-t / (dur * 0.12))
         + 0.06 * partial(freq * 4.1, t, sr) * np.exp(-t / 0.02))
    return x * env(len(t), 0.0015, 0.05, sr)


def chime(freq, dur, sr=SR):
    """A soft, warm bell: whole-number partials (no glockenspiel clang), two
    tones a hair apart so it shimmers as it rings."""
    t = t_of(dur, sr)
    x = ((partial(freq, t, sr) + 0.5 * partial(freq * 1.003, t, sr)) * np.exp(-t / (dur * 0.38))
         + 0.28 * partial(freq * 2.0, t, sr) * np.exp(-t / (dur * 0.16))
         + 0.1 * partial(freq * 3.01, t, sr) * np.exp(-t / (dur * 0.07)))
    return x * env(len(t), 0.003, 0.08, sr)


def a_weight(x, sr):
    """[x] as the ear hears it out of a phone: A-weighting (the ear is less
    sensitive to low and very high sounds) and nothing under about 250 Hz."""
    spec = np.fft.rfft(x)
    f2 = np.fft.rfftfreq(len(x), 1 / sr) ** 2
    ra = 12194 ** 2 * f2 ** 2 / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194 ** 2))
    phone = 1 / (1 + (250 ** 2 / np.maximum(f2, 1e-6)) ** 2)
    return np.fft.irfft(spec * ra * 1.2589 * phone, len(x))


def loudness(x, sr):
    """How loud [x] sounds, roughly, in dB: the weighted power in 200 ms
    windows (the ear adds up about that long, so a click sounds softer than
    a note as loud), over the windows within 20 dB of the loudest one."""
    y = a_weight(np.asarray(x, dtype=np.float64), sr) ** 2
    w, hop = int(0.2 * sr), int(0.025 * sr)
    y = np.concatenate([y, np.zeros(max(0, w - len(y)))])
    c = np.concatenate([[0], np.cumsum(y)])
    e = (c[w::hop] - c[:len(c) - w:hop]) / w
    return 10 * np.log10(max(1e-12, np.mean(e[e >= e.max() * 0.01])))


QUALITY = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10),
           "maj7": (0, 4, 7, 11), "7sus": (0, 5, 7, 10)}  # the last two are new here


def chord_tones(chord, low):
    """The notes (Hz) of [chord], root first, the root at or just above [low]."""
    root = root_of(chord)
    f = NOTE[above(root, low)]
    return [f * 2 ** (s / 12) for s in QUALITY[chord[len(root):]]]


def harmonics(f, sr=SR, tilt=1.0):
    """A bright tone at pitch [f] (Hz per sample) with every harmonic up to
    near half the sample rate, each 1/k^[tilt]: a sawtooth without the
    harsh folded-back tones."""
    ph = 2 * np.pi * np.cumsum(f) / sr
    top = int(0.45 * sr // np.max(f))
    return sum(np.sin(k * ph) / k ** tilt for k in range(1, max(2, top + 1)))


def pizz(freq, dur=0.5, sr=LOOP_SR, pos=0.14):
    """A pizzicato string, plucked with a finger: it rings only a moment,
    the high harmonics dying first; low notes ring a little longer."""
    t = t_of(dur, sr)
    tau = min(0.3, 0.07 + 50 / freq)
    x = np.zeros_like(t)
    for k in range(1, 9):
        x += abs(np.sin(np.pi * k * pos)) / k * partial(freq * k, t, sr) * np.exp(-t * (1 + 0.7 * (k - 1)) / tau)
    return x * env(len(t), 0.0012, 0.04, sr)


def toy_horn(freq, dur, sr=SR):
    """A soft toy trumpet: every harmonic, the high ones quieter, opening up
    as it speaks; a little vibrato on a long note."""
    t = t_of(dur, sr)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * ease((t - 0.15) / 0.2)
    ph = 2 * np.pi * np.cumsum(freq * vib) / sr
    opening = ease(t / 0.05)
    x = np.zeros_like(t)
    for k in range(1, 9):
        if freq * k < 0.4 * sr:
            x += (1 if k == 1 else opening) / k ** 1.4 * np.sin(k * ph)
    return lowpass(x, 3500, sr) * env(len(t), 0.015, min(0.1, dur * 0.4), sr)


def spring(f0, dur, wobble=0.12, sr=SR):
    """A cartoon spring: it shoots up, wobbles, settles (畫畫小鎮's boing)."""
    t = t_of(dur, sr)
    f = f0 * (1 + 1.0 * (1 - np.exp(-t / 0.03))) * (1 + wobble * np.sin(2 * np.pi * 14 * t) * np.exp(-t / 0.15))
    return (sweep(f, sr) + 0.2 * sweep(2 * f, sr)) * env(len(t), 0.003, 0.06, sr) * decay(len(t), dur * 0.4, sr)


# ---------------------------------------------------------------- new helpers


def clarinet(freq, dur, rng, sr=LOOP_SR):
    """A soft clarinet: a hollow, woody tone (its tube makes the odd
    harmonics strong and the even ones weak), the overtones blooming just
    after the note starts, a breath of air in it, and a slow vibrato only on
    long notes."""
    t = t_of(dur, sr)
    n = len(t)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * ease((t - 0.3) / 0.3)
    ph = 2 * np.pi * np.cumsum(freq * vib) / sr
    bloom = ease(t / 0.04)
    x = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.06), (3, 0.42), (4, 0.05), (5, 0.2), (6, 0.03), (7, 0.08), (9, 0.03)):
        if freq * k < 0.45 * sr:
            x += a * (1 if k == 1 else bloom) * np.sin(k * ph)
    breath = 0.035 * norm(bandpass(rng.standard_normal(n), freq * 1.5, min(freq * 6, 0.45 * sr), sr))
    return (x + breath) * env(n, 0.018, min(0.05, dur * 0.35), sr)


def vibes(freq, dur=1.8, sr=LOOP_SR, motor=4.2, depth=0.28):
    """A vibraphone, with soft mallets: an aluminium bar (tuned so its next
    mode is two octaves up, and a faint one above that) ringing long, with
    the gentle wah-wah of the motor fans turning above the tubes."""
    t = t_of(dur, sr)
    trem = 1 - depth * (0.5 - 0.5 * np.cos(2 * np.pi * motor * t))
    x = (partial(freq, t, sr) * np.exp(-t / (dur * 0.4))
         + 0.2 * partial(freq * 4, t, sr) * np.exp(-t / 0.12)
         + 0.04 * partial(freq * 10, t, sr) * np.exp(-t / 0.015))
    return x * trem * env(len(t), 0.002, 0.12, sr)


def pad(chord, length, low="Ab3", sr=LOOP_SR):
    """A warm pad, like soft strings far away: the chord held, fading in over
    most of a second and out over a second after [length] (so it melts into
    the next), each tone three voices a hair apart (so it breathes), with a
    little of their octave."""
    d = length + 1.0
    t = t_of(d, sr)
    shape = ease(t / 0.7) * (1 - ease((t - length + 0.1) / 1.0))
    x = np.zeros_like(t)
    for f in chord_tones(chord, low)[:3]:
        for det in (0.996, 1.0, 1.004):
            x += np.sin(2 * np.pi * f * det * t) + 0.22 * np.sin(2 * np.pi * 2 * f * det * t)
    return x * shape / 9


def under(f, chord):
    """A second voice for the tune: the highest note of [chord] a third to a
    sixth below [f] (any octave), so it always fits the chord."""
    tones = [c * 2 ** o for c in chord_tones(chord, "C2") for o in range(6)]
    fits = [c for c in tones if f * 2 ** (-9.5 / 12) <= c <= f * 2 ** (-2.5 / 12)]
    return max(fits) if fits else f / 2


def chord_at(span_list, b):
    """The chord sounding at beat [b]."""
    return [c for s, _, c in span_list if s <= b + 1e-9][-1]


def room(x, rng, tau=0.18, sr=SR):
    """The echoes of a little space around [x] (a soft tail of noise dying
    away over about [tau] seconds), on their own and as loud as [x]: mix a
    little in, for something far away."""
    n = int(4 * tau * sr)
    tt = np.arange(n) / sr
    ir = lowpass(rng.standard_normal(n), 3000, sr) * np.exp(-tt / tau)
    ir[:int(0.012 * sr)] = 0  # the first echoes come a moment after the sound
    return norm(fftconvolve(x, ir)[:len(x)]) * np.abs(x).max()


def fade_out(x, seconds, sr=SR):
    """Fade the last [seconds] of [x] gently away (a scene sound ends softly)."""
    m = min(len(x), int(seconds * sr))
    x = x.copy()
    x[-m:] *= (1 - ease(np.linspace(0, 1, m)))
    return x


def chirp(points, dur, sr=SR):
    """A bird's chirp: a pure whistle whose pitch follows (fraction of
    [dur], Hz) [points], swelling in and out."""
    t = t_of(dur, sr)
    fs, hz = zip(*points)
    f = np.interp(t / dur, fs, hz)
    return (sweep(f, sr) + 0.12 * sweep(2 * f, sr)) * np.sin(np.pi * t / dur) ** 1.2


VOWEL = {"i": (300, 2300, 3000), "e": (480, 1950, 2800), "a": (850, 1400, 2700), "o": (500, 900, 2600), "u": (350, 800, 2400)}


def babble(rng, dur, pitch, size=1.0):
    """One far-off voice talking (no words): syllables of random vowels and
    pitch around [pitch], with little pauses."""
    n = int(dur * SR)
    f0, amp = np.zeros(n), np.zeros(n)
    fs = [np.zeros(n) for _ in range(3)]
    i = 0
    while i < n:
        m = min(n - i, int(rng.uniform(0.07, 0.18) * SR))
        v = VOWEL["ieaou"[rng.integers(0, 5)]]
        f0[i:i + m] = pitch * rng.uniform(0.88, 1.18) * np.linspace(1.04, 0.96, m)
        for k in range(3):
            fs[k][i:i + m] = v[k] * size
        if rng.random() > 0.18:
            amp[i:i + m] = rng.uniform(0.4, 1.0) * np.sin(np.pi * np.arange(m) / m) ** 0.8
        i += m
    f0 = lowpass(f0 - f0.mean(), 40) + f0.mean()
    fs = [lowpass(f - f.mean(), 40) + f.mean() for f in fs]
    return voice(f0, [(fs[0], 120, 1.0), (fs[1], 170, 0.5), (fs[2], 260, 0.15)], rng, breath=0.25) * amp


# ---------------------------------------------------------------- music


class Tune:
    """A tune: its length, the tune itself and the band (lists of (seconds,
    signal)), and the soft top it is played through."""

    def __init__(self, seconds, lead, band, cutoff):
        self.seconds, self.lead, self.band, self.cutoff = seconds, lead, band, cutoff

    def render(self, lead=True, band=True):
        notes = (self.lead if lead else []) + (self.band if band else [])
        return lowpass(tune_loop(self.seconds, notes), self.cutoff, LOOP_SR)


def music_home():
    """The home screen: curious and playful, on tiptoe. 4/4 in A minor,
    turning to C major for the second half. A soft clarinet plays a sneaky
    tune of short, light notes with little rests (and a cheeky chromatic
    step in the first bar); pizzicato strings tiptoe under it: a plucked
    bass on one and three, short plucked chords on two and four, and a tiny
    wooden tick on every off-beat. The second half brightens: the tune goes
    up, a glockenspiel twinkles along, a soft drum and a shaker join in, and
    at the very end the bass tiptoes down E-D-C-B back to the start."""
    beat, swing = 0.375, 0.08
    bars = ["Am", "Dm", "E7", "Am", "Am", "Dm", "F-E7", "Am", "C", "G7", "C-Am", "Dm-E7"]
    tune = [("A4", .5), ("C5", .5), ("E5", .5), (None, .5), ("D#5", .5), ("E5", .5), (None, 1),
            ("F5", .5), (None, .5), ("E5", .5), ("D5", .5), ("A4", 1), (None, 1),
            ("G#4", .5), ("B4", .5), ("D5", .5), (None, .5), ("C5", .5), ("B4", .5), ("G#4", .5), (None, .5),
            ("A4", 1), (None, .5), ("E4", .5), ("A4", .5), (None, 1.5),
            ("A4", .5), ("C5", .5), ("E5", .5), (None, .5), ("F5", .5), ("E5", .5), (None, 1),
            ("D5", .5), ("F5", .5), ("A5", 1), ("G5", .5), ("F5", .5), (None, 1),
            ("E5", .5), ("F5", .5), ("A5", 1), ("G#5", .5), (None, .5), ("B5", .5), ("D6", .5),
            ("C6", 1), ("A5", .5), ("E5", .5), ("A5", 1), (None, 1),
            ("G5", .5), ("E5", .5), ("G5", .5), ("C6", .5), (None, .5), ("B5", .5), ("C6", 1),
            ("D6", .5), ("B5", .5), ("G5", .5), (None, .5), ("F5", .5), ("G5", .5), (None, 1),
            ("E5", .5), ("G5", .5), ("C6", 1), ("A5", .5), ("C6", .5), ("E6", 1),
            ("D6", .5), ("C6", .5), ("A5", .5), ("F5", .5), ("E5", 1), (None, 1)]
    rng = np.random.default_rng(101)
    lead, band = [], []
    for at, n, d in melody(tune, beat, swing=swing, bars=12):
        f = NOTE[n]
        held = d * 0.9 if d >= beat - 1e-9 else d * 0.6  # quavers short and light, on tiptoe
        lead.append((at, 0.5 * clarinet(f, held, rng)))
        if at >= 32 * beat - 1e-9:  # the bright half: a glockenspiel twinkles along
            lead.append((at, 0.07 * bell(2 * f, 0.45, LOOP_SR, bright=0.4)))
    for b, length, chord in spans(bars, 4):
        r = NOTE[above(root_of(chord), "G2")]
        band.append((b * beat, 0.95 * pizz(r, 0.5)))
        if length == 4:
            fifth = r * 2 ** (7 / 12)
            band.append(((b + 2) * beat, 0.8 * pizz(fifth / 2 if fifth > NOTE["D3"] else fifth, 0.45)))
        for off in ((1, 3) if length == 4 else (1,)):
            band += [((b + off) * beat + 0.006 * k, 0.2 * pizz(f, 0.3)) for k, f in enumerate(chord_tones(chord, "G3"))]
    for k, n in enumerate(["D3", "C3", "B2"]):  # the bass tiptoes down into the start again
        band.append(((46.5 + 0.5 * k + (swing if k != 1 else 0)) * beat, 0.75 * pizz(NOTE[n], 0.35)))
    for b in range(48):
        if b < 32:  # on tiptoe: a tiny wooden tick on each off-beat
            band.append(((b + 0.5 + swing) * beat, 0.06 * woodblock(2100, dur=0.04)))
        else:  # the bright half: a soft drum on one and three, a shaker on the off-beats
            if b % 2 == 0:
                band.append((b * beat, 0.25 * kick()))
            band.append(((b + 0.5 + swing) * beat, 0.05 * shaker(rng)))
    band.append((32 * beat, 0.08 * metal(3300, 0.8, LOOP_SR, ratios=(1, 2.7, 4.1), amps=(1, .4, .2), taus=(.5, .2, .1))))
    return Tune(len(bars) * 4 * beat, lead, band, 5000)


def music_play():
    """While searching: calm, focused and cheerful, and out of the way. 4/4
    in A flat, on soft seventh chords. A vibraphone sings a slow tune of long
    notes, its motor making them gently waver; in the second half a second
    vibraphone voice joins below it. A marimba rolls softly up and down each
    chord in quavers, a plucked bass sits on each bar, and a light shaker
    keeps time; little three-note marimba answers fill the gap at the end of
    each half."""
    beat = 0.55
    bars = ["Abmaj7", "Fm7", "Dbmaj7", "Eb7sus", "Abmaj7", "Cm7", "Dbmaj7-Bbm7", "Eb7"]
    tune = [("Eb5", 1.5), ("C5", .5), ("Eb5", 1), ("G5", 1),
            ("Ab5", 2), ("G5", 1), ("F5", 1),
            ("F5", 1.5), ("Eb5", .5), ("C5", 1), ("Ab4", 1),
            ("Bb4", 3), (None, 1),
            ("Eb5", 1.5), ("C5", .5), ("Eb5", 1), ("Ab5", 1),
            ("G5", 2), ("Bb5", 1), ("G5", 1),
            ("Ab5", 1.5), ("F5", .5), ("Db5", 1), ("F5", 1),
            ("G5", 1), ("F5", 1), ("Eb5", 1), (None, 1)]
    rng = np.random.default_rng(102)
    sp = spans(bars, 4)
    lead, band = [], []
    for at, n, d in melody(tune, beat, bars=8):
        f = NOTE[n]
        lead.append((at, 0.55 * vibes(f, max(1.4, d + 0.7))))
        if at >= 16 * beat - 1e-9:  # the second half: a second voice below
            lead.append((at, 0.2 * vibes(under(f, chord_at(sp, at / beat)), max(1.4, d + 0.7))))
    for b, n in ((14, "Bb5"), (14.5, "Db6"), (15, "Eb6"), (31, "Bb5"), (31.5, "Eb6")):
        lead.append((b * beat, 0.16 * marimba(NOTE[n], 0.5, LOOP_SR)))
    for b, length, chord in sp:
        c = chord_tones(chord, "Bb2")
        roll = [c[0], c[2], 2 * c[0], 2 * c[1], 2 * c[0], c[3], c[2], c[1]] if length == 4 else [c[0], c[2], 2 * c[0], 2 * c[1]]
        for k, f in enumerate(roll):
            band.append(((b + 0.5 * k) * beat, (0.6 if k == 0 else 0.38) * rng.uniform(0.9, 1.1) * marimba(f, 0.6, LOOP_SR)))
        band.append((b * beat, 0.8 * pluck_bass(NOTE[above(root_of(chord), "E2")], 1.2)))
    for e in range(64):
        band.append((e * 0.5 * beat, (0.05 if e % 2 else 0.028) * shaker(rng, dur=0.07)))
    return Tune(len(bars) * 4 * beat, lead, band, 4200)


def music_rest():
    """Rest time: a slow lullaby in D flat, four slow beats a bar (the
    sibling apps rock in three or six). A celesta sings over warm, slowly
    breathing pads; a soft bass goes like a heartbeat on one and three; a
    music box answers at the end of the first half and sings along an octave
    up in the second; three soft chimes ring at the very end."""
    beat = 0.6
    bars = ["Db", "Bbm", "Gb", "Ab", "Db", "Fm", "Gb-Ebm", "Ab7"]
    tune = [("Ab5", 2), ("F5", 1), ("Db5", 1),
            ("Db5", 1), ("F5", 1), ("Bb5", 2),
            ("Bb5", 1.5), ("Ab5", .5), ("Gb5", 1), ("Db5", 1),
            ("Eb5", 3), (None, 1),
            ("Ab5", 2), ("F5", 1), ("Db5", 1),
            ("F5", 1), ("Ab5", 1), ("C6", 2),
            ("Bb5", 1), ("Ab5", 1), ("Gb5", 1), ("Eb5", 1),
            ("C5", 2), (None, 1), ("Eb5", 1)]
    lead, band = [], []
    for at, n, d in melody(tune, beat, bars=8):
        f = NOTE[n]
        lead.append((at, 0.6 * celesta(f, max(1.6, d + 1.0))))
        if at >= 16 * beat - 1e-9:  # the second half: the music box sings along an octave up
            lead.append((at, 0.13 * music_box_note(2 * f, 2.0, bright=0.3)))
    for b, n in ((14, "C7"), (14.5, "Ab6"), (15, "Eb6")):  # the music box answers
        lead.append((b * beat, 0.2 * music_box_note(NOTE[n], 2.0, bright=0.3)))
    for b, n in ((30, "Db7"), (30.33, "Ab6"), (30.67, "F6")):  # soft chimes at the end
        band.append((b * beat, 0.15 * chime(NOTE[n], 1.6, LOOP_SR)))
    for b, length, chord in spans(bars, 4):
        band.append((b * beat, 0.4 * pad(chord, length * beat)))
        r = NOTE[above(root_of(chord), "G2")]
        band.append((b * beat, 0.9 * pluck_bass(r, 2.0)))
        if length == 4:
            band.append(((b + 2) * beat, 0.45 * pluck_bass(r, 1.6)))
    return Tune(len(bars) * 4 * beat, lead, band, 2600)


# name: (make, loudness in dB beside the short sounds: about 8 under them).
MUSIC = {
    "music_home": (music_home, -8),
    "music_play": (music_play, -9.5),
    "music_rest": (music_rest, -9),
}


# ---------------------------------------------------------------- playing


def tap():
    """A button: a small, soft wooden tick."""
    t = t_of(0.07)
    x = (partial(1150, t, SR) * np.exp(-t / 0.012) + 0.3 * partial(2700, t, SR) * np.exp(-t / 0.004)
         + 0.12 * partial(4300, t, SR) * np.exp(-t / 0.002))
    return x * env(len(t), 0.0008, 0.02)


def found():
    """A difference found: a bright, satisfying ding! A quick grace note from
    below (B5 up to E6), the ding itself (two tones a hair apart, so it
    shimmers, its octave, and the tink of the strike), a warm note under it,
    and a little tail of sparkles running up and fading."""
    rng = np.random.default_rng(402)
    t = t_of(0.75)
    f = NOTE["E6"]
    ding = ((np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 1.0035 * t)) * np.exp(-t / 0.28)
            + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.1)
            + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / 0.04)
            + 0.15 * np.sin(2 * np.pi * 5.2 * f * t) * np.exp(-t / 0.008)) * env(len(t), 0.0015, 0.1)
    parts = [(0, 0.35 * celesta(NOTE["B5"], 0.12, SR)), (0.045, 0.75 * ding), (0.045, 0.22 * chime(NOTE["E5"], 0.6))]
    for k, n in enumerate(["B6", "E7", "G#7", "B7"]):
        parts.append((0.17 + 0.05 * k, (0.13 - 0.02 * k) * bell(NOTE[n], 0.28, bright=0.3)))
    m = int(0.45 * SR)
    shimmer = norm(bandpass(rng.standard_normal(m), 6500, 9500)) * np.sin(np.pi * np.arange(m) / m) ** 2
    return place(0.8, parts + [(0.15, 0.035 * shimmer)])


def miss():
    """A tap where nothing changed: a very soft, neutral "pup", like a tiny
    bubble popping. It does not go down, so it never sounds sad; never a buzzer."""
    t = t_of(0.12)
    f = np.interp(t, [0, 0.02, 0.12], [360, 500, 470])
    x = (sweep(f) + 0.25 * sweep(2 * f)) * env(len(t), 0.004, 0.05) * decay(len(t), 0.035)
    return lowpass(x, 1800)


def circle():
    """The ring drawn round a find: a quick felt-tip swoosh, once round. The
    scratch goes up and back down in pitch as the pen goes round, with a
    faint squeak of felt on paper and a little grain."""
    rng = np.random.default_rng(404)
    dur = 0.3
    t = t_of(dur)
    n = len(t)
    centre = 1800 + 1700 * np.sin(np.pi * t / dur)
    swish = noise_through(rng, centre, 1600, n)
    squeak = norm(resonator(rng.standard_normal(n), centre * 1.3, 90))
    grain = 0.75 + 0.25 * norm(lowpass(rng.standard_normal(n), 90))
    shape = ease(t / 0.035) * (1 - ease((t - 0.2) / 0.1))
    return (0.8 * swish + 0.3 * squeak) * grain * shape


def all_found():
    """Every difference found: a joyful little fanfare, 1.5 s. A soft drum
    roll, two pickups (ta-ta) on a toy trumpet, a clarinet and a xylophone,
    then TAA up a fourth onto a big F chord (the trumpet in three parts,
    the clarinet low under it, the xylophone, a plucked bass, a tambourine and a soft cymbal),
    and sparkles raining down."""
    rng = np.random.default_rng(405)
    parts = []
    for k in range(9):  # the drum roll, swelling
        m = int(0.05 * SR)
        tm = np.arange(m) / SR
        hit = (norm(bandpass(rng.standard_normal(m), 1200, 6000)) * np.exp(-tm / 0.01)
               + 0.6 * np.sin(2 * np.pi * 210 * tm) * np.exp(-tm / 0.02)) * env(m, 0.0008, 0.01)
        parts.append((0.027 * k, (0.08 + 0.025 * k) * hit))
    for at in (0.24, 0.35):
        parts += [(at, 0.32 * toy_horn(NOTE["C5"], 0.08)), (at, 0.25 * clarinet(NOTE["C5"], 0.08, rng, SR)),
                  (at, 0.35 * xylo(NOTE["C5"], 0.25, SR))]
    land = 0.47
    parts += [(land, a * toy_horn(NOTE[n], 0.7)) for n, a in (("A5", 0.36), ("F5", 0.26), ("C5", 0.22))]
    parts += [(land, 0.3 * clarinet(NOTE["F4"], 0.65, rng, SR)), (land, 0.45 * xylo(NOTE["F5"], 0.7, SR)),
              (land, 0.4 * carry(pluck_bass(NOTE["F3"], 0.8, SR), 0.3)), (land, 0.22 * jingle(rng))]
    m = int(0.6 * SR)
    cym = norm(bandpass(rng.standard_normal(m), 5000, 10000)) * np.exp(-np.arange(m) / (0.18 * SR)) * env(m, 0.002, 0.1)
    parts.append((land, 0.08 * cym))
    for k, n in enumerate(["F7", "C7", "A6", "C7", "F6", "A6", "C6"]):
        parts.append((0.72 + 0.075 * k + rng.uniform(-0.01, 0.01), (0.2 - 0.018 * k) * bell(NOTE[n], 0.35, bright=0.4)))
    return place(1.48, parts)


def star():
    """A star for the album: a quick glockenspiel turn up (E6, A6, C#7, E7)
    and a high top note that twinkles, flickering like a star."""
    run = ["E6", "A6", "C#7", "E7"]
    parts = [(0.05 * i, (0.35 + 0.08 * i) * bell(NOTE[n], 0.4, bright=0.5)) for i, n in enumerate(run)]
    t = t_of(0.7)
    f = NOTE["A7"]
    top = ((np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.006 * t)) * np.exp(-t / 0.22)
           * (0.65 + 0.35 * np.cos(2 * np.pi * 13 * t)) * env(len(t), 0.002, 0.1))
    return place(0.95, parts + [(0.2, 0.3 * top), (0.2, 0.25 * chime(NOTE["A6"], 0.7))])


def stamp():
    """The album stamp: a rubber stamp pressed down, ka-THUNK (a tiny tap as
    it touches, a soft rubbery thunk and squash on the desk, the wooden
    handle's knock), then a little "tchp" as the rubber lets go of the
    paper. Its peaks are rounded off, so a quick hit can be as loud as the
    others."""
    rng = np.random.default_rng(406)
    t = t_of(0.22)
    n = len(t)
    hit = rng.standard_normal(n) * np.exp(-t / 0.003)
    tone = sweep(np.geomspace(320, 150, n)) * np.exp(-t / 0.06)
    desk = norm(resonator(hit, 420, 60)) * np.exp(-t / 0.08)
    handle = norm(resonator(hit, 950, 120)) * np.exp(-t / 0.03)
    squash = norm(bandpass(rng.standard_normal(n), 300, 1500)) * ease(t / 0.004) * np.exp(-t / 0.045)
    thunk = round_off(carry(0.5 * tone + 0.6 * desk + 0.35 * handle + 0.5 * squash, 0.4), 2.5) * env(n, 0.001, 0.06)
    m = int(0.012 * SR)
    touch = norm(highpass(rng.standard_normal(m), 2500)) * np.exp(-np.arange(m) / (0.0015 * SR)) * env(m, 0.0003, 0.004)
    d = 0.09
    td = t_of(d)
    lift = noise_through(rng, np.interp(td, [0, d], [900, 2200]), 600, len(td)) * np.sin(np.pi * td / d) ** 2
    return place(0.36, [(0, 0.15 * touch), (0.008, thunk), (0.22, 0.4 * lift)])


def hint():
    """The magnifying-glass hint: a soft magic twinkle. Celesta notes run up
    a five-note scale like a wand being waved, ringing into each other, over
    a breath of shimmer that swells and fades."""
    rng = np.random.default_rng(407)
    run = ["D6", "E6", "G6", "A6", "D7", "E7"]
    parts = [(0.06 * k, (0.22 + 0.03 * k) * celesta(NOTE[n], 0.45, SR)) for k, n in enumerate(run)]
    m = int(0.6 * SR)
    tm = np.arange(m) / SR
    shimmer = norm(bandpass(rng.standard_normal(m), 5000, 9000)) * np.sin(np.pi * tm / 0.6) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * 11 * tm))
    return lowpass(place(0.8, parts + [(0, 0.05 * shimmer)]), 9000)


def magic():
    """小變's "變！": a playful whoosh up and, at its top, a soft pop and a
    cartoon spring going boing as the thing changes, with a twinkle."""
    rng = np.random.default_rng(408)
    dur = 0.3
    t = t_of(dur)
    n = len(t)
    whoosh = noise_through(rng, 400 * 8 ** ease(t / dur), 800, n) * ease(t / 0.22) * (1 - ease((t - 0.24) / 0.06))
    tp = t_of(0.04)
    pop = sweep(np.geomspace(600, 1500, len(tp))) * np.sin(np.pi * tp / 0.04)
    return place(0.8, [(0, 0.55 * whoosh), (0.25, 0.3 * pop), (0.27, 0.9 * spring(300, 0.45, wobble=0.16)),
                       (0.3, 0.1 * bell(NOTE["C7"], 0.3, bright=0.3)), (0.37, 0.08 * bell(NOTE["G7"], 0.3, bright=0.3))])


def giggle():
    """小變's cheeky giggle: hi-hi-hi-hi-hiii, short voiced notes on a bright
    vowel, quick and bouncy: up, then down, and a longer last one that curls
    up at the end (cheeky, not mocking)."""
    rng = np.random.default_rng(409)
    parts = []
    for k, (at, f, dur) in enumerate([(0.0, 640, 0.06), (0.085, 720, 0.06), (0.17, 690, 0.06),
                                      (0.255, 620, 0.06), (0.35, 600, 0.17)]):
        t = t_of(dur)
        if k == 4:
            f0 = glide(t, (0, f), (dur * 0.4, f * 0.95), (dur, f * 1.25))
        else:
            f0 = np.linspace(f * 1.05, f * 0.94, len(t))
        x = voice(f0, [(900, 150, 1.0), (2300, 220, 0.5), (3300, 300, 0.12)], rng, breath=0.15)
        x *= np.sin(np.pi * t / dur) ** 0.7
        m = int(0.022 * SR)
        h = norm(bandpass(rng.standard_normal(m), 1500, 5500)) * np.hanning(m) * 0.15  # the "h"
        parts += [(at, h), (at + 0.015, x)]
    return place(0.6, parts)


def peek():
    """小變 found in its hiding place: a surprised "oop!". A voiced tone jumps
    up as the mouth opens from "oo" to "oh", is cut short as the lips close,
    and they let go with a tiny "p"."""
    rng = np.random.default_rng(410)
    dur = 0.24
    t = t_of(dur)
    f0 = glide(t, (0, 380), (0.06, 620), (0.18, 600), (dur, 520))
    f1 = glide(t, (0, 330), (0.07, 560), (0.17, 540), (dur, 300))
    f2 = glide(t, (0, 800), (0.07, 1000), (0.17, 950), (dur, 700))
    x = voice(f0, [(f1, 110, 1.0), (f2, 150, 0.5), (2600, 260, 0.1)], rng, breath=0.05)
    x *= ease(t / 0.02) * (1 - ease((t - 0.18) / 0.05))
    m = int(0.02 * SR)
    p = norm(lowpass(rng.standard_normal(m), 2000)) * np.exp(-np.arange(m) / (0.004 * SR)) * env(m, 0.0005, 0.005)
    return carry(place(0.32, [(0, x), (0.235, 0.2 * p)]), 0.2)


def switch_style():
    """Changing the art style: a page flipping over (a few quick papery
    flaps of air, ffrrp, and a soft pat as it lands), then two chime notes
    going up: a new look."""
    rng = np.random.default_rng(411)
    dur = 0.16
    t = t_of(dur)
    n = len(t)
    flaps = sum(a * np.exp(-((t - c) / 0.012) ** 2) for c, a in ((0.02, 1), (0.055, 0.75), (0.085, 0.55), (0.11, 0.35)))
    paper = norm(bandpass(rng.standard_normal(n), 900, 7000))
    air = noise_through(rng, glide(t, (0, 600), (dur, 1400)), 500, n)
    flip = (0.7 * paper + 0.5 * air) * flaps * env(n, 0.002, 0.02)
    tp = t_of(0.05)
    pat = norm(lowpass(rng.standard_normal(len(tp)), 1800)) * np.exp(-tp / 0.008) * env(len(tp), 0.0008, 0.01)
    return place(0.75, [(0, 0.8 * flip), (0.135, 0.3 * pat),
                        (0.16, 0.4 * chime(NOTE["C6"], 0.5)), (0.25, 0.45 * chime(NOTE["G6"], 0.5))])


def next_picture():
    """On to the next picture: a light, airy whoosh going by."""
    rng = np.random.default_rng(412)
    dur = 0.38
    t = t_of(dur)
    n = len(t)
    centre = glide(t, (0, 600), (0.22, 2600), (dur, 2000))
    x = noise_through(rng, centre, 1300, n) + 0.3 * norm(bandpass(rng.standard_normal(n), 4000, 8000))
    return x * ease(t / 0.16) * (1 - ease((t - 0.2) / 0.18))


def rest_time():
    """Time to rest: 小變 yawns (a small, breathy "haa~" opening wide and
    sinking to "oh"), sighs it out, then a warm chime falls two notes."""
    rng = np.random.default_rng(413)
    dur = 0.85
    t = t_of(dur)
    f0 = glide(t, (0, 470), (0.15, 560), (0.55, 420), (dur, 330))
    f1 = glide(t, (0, 600), (0.2, 950), (0.55, 820), (dur, 520))
    f2 = glide(t, (0, 1700), (0.2, 1450), (dur, 950))
    yawn = voice(f0, [(f1, 150, 1.0), (f2, 190, 0.45), (3000, 300, 0.08)], rng, breath=0.35) * env(len(t), 0.12, 0.3)
    d = 0.4
    ts = t_of(d)
    sigh = (noise_through(rng, 550, 200, len(ts)) + 0.5 * noise_through(rng, 1000, 300, len(ts))) * np.sin(np.pi * ts / d) ** 2
    return place(1.48, [(0, 0.8 * yawn), (0.7, 0.16 * sigh),
                       (0.8, 0.45 * chime(NOTE["A5"], 0.7)), (1.0, 0.3 * chime(NOTE["E5"], 0.5))])


# ---------------------------------------------------------------- the scenes opening


def amb_park():
    """The park: a light breeze in the trees, and two little birds: a
    bulbul (白頭翁) singing a jaunty four-note phrase, and a quick high trill
    answering."""
    rng = np.random.default_rng(501)
    dur = 1.45
    t = t_of(dur)
    n = len(t)
    breeze = noise_through(rng, glide(t, (0, 500), (0.7, 900), (dur, 600)), 700, n)
    leaves = norm(bandpass(rng.standard_normal(n), 3000, 7000)) * (0.5 + 0.5 * norm(lowpass(rng.standard_normal(n), 12)))
    air = (0.5 * breeze + 0.15 * leaves) * ease(t / 0.35) * (1 - ease((t - 0.85) / 0.55))
    bulbul = [(0, chirp([(0, 1900), (1, 2600)], 0.07)), (0.09, chirp([(0, 2800), (1, 2300)], 0.06)),
              (0.17, chirp([(0, 2100), (0.5, 3000), (1, 2700)], 0.09)), (0.29, chirp([(0, 3100), (1, 2500)], 0.12))]
    trill = [(0.04 * k, 0.6 * chirp([(0, 4200 + 300 * (k % 2)), (0.5, 4600), (1, 4300)], 0.03)) for k in range(7)]
    parts = [(0, air)] + [(0.2 + at, 0.5 * s) for at, s in bulbul] + [(0.85 + at, 0.35 * s) for at, s in trill]
    return fade_out(place(dur, parts), 0.2)


def amb_market():
    """The night market: a soft, busy murmur of people talking (many quiet
    voices at once, no words) and a stall's little hand bell, ding-ding."""
    rng = np.random.default_rng(502)
    dur = 1.45
    n = int(dur * SR)
    crowd = sum(rng.uniform(0.5, 1.0) * np.roll(babble(rng, dur, p, s), rng.integers(0, n))
                for p, s in ((130, 0.95), (165, 1.0), (195, 1.05), (225, 1.1), (250, 1.12), (280, 1.15), (210, 1.0)))
    crowd = lowpass(crowd, 2800)
    crowd = (crowd + 0.4 * room(crowd, rng, 0.2)) * ease(np.arange(n) / (0.2 * SR))
    ring = dict(ratios=(1, 2.03, 2.94, 4.17), amps=(1, .5, .3, .15), taus=(.5, .25, .15, .1))
    parts = [(0, 0.5 * norm(crowd)), (0.4, 0.4 * metal(1850, 0.6, **ring)), (0.58, 0.32 * metal(1850, 0.6, **ring)),
             (0.95, 0.15 * metal(1850, 0.45, **ring))]
    return fade_out(place(dur, parts), 0.35)


def gull(rng, dur, peak):
    """A seagull's "kee-ow": a high, nasal call that rises and falls."""
    t = t_of(dur)
    f0 = glide(t, (0, 0.8 * peak), (0.3 * dur, peak), (dur, 0.65 * peak))
    return voice(f0, [(1900, 300, 1.0), (3000, 350, 0.4)], rng, breath=0.1) * env(len(t), 0.02, 0.08)


def amb_beach():
    """The beach: one gentle wave rolling in and washing back (a soft swell
    of surf, then the fizz of foam), and a seagull calling, far off."""
    rng = np.random.default_rng(503)
    dur = 1.48
    t = t_of(dur)
    n = len(t)
    surf = noise_through(rng, glide(t, (0, 350), (0.55, 1100), (dur, 600)), 900, n)
    low = norm(lowpass(rng.standard_normal(n), 500))
    swell = ease(t / 0.55) * (1 - ease((t - 0.6) / 0.85))
    fizz = norm(bandpass(rng.standard_normal(n), 2500, 8000)) * (0.6 + 0.4 * norm(lowpass(rng.standard_normal(n), 30)))
    foam = ease((t - 0.45) / 0.2) * (1 - ease((t - 0.75) / 0.7))
    wave_ = carry(0.6 * surf + 0.4 * low, 0.15) * swell + 0.25 * fizz * foam
    calls = place(dur, [(0.15, gull(rng, 0.26, 1050)), (0.5, 0.8 * gull(rng, 0.3, 980))])
    calls = lowpass(calls + 0.4 * room(calls, rng, 0.15), 4000)
    return fade_out(0.8 * wave_ + 0.3 * calls, 0.25)


def amb_zoo():
    """The zoo: a far-off elephant's friendly toot (a trunk trumpet that
    rises and wobbles, softened by distance), and a few bird calls: a quick
    pi-pi before it and a tropical wheet-whoo after."""
    rng = np.random.default_rng(504)
    dur = 0.8
    t = t_of(dur)
    f = glide(t, (0, 260), (0.1, 470), (0.45, 520), (dur, 430)) * (1 + 0.025 * np.sin(2 * np.pi * 7 * t))
    tone = harmonics(f, tilt=1.0)
    toot = (bandpass(tone, 350, 2600) + 0.6 * norm(resonator(tone, 1100, 250))) * ease(t / 0.07) * (1 - ease((t - 0.55) / 0.25))
    toot = lowpass(toot, 2200)
    toot = place(1.48, [(0.2, norm(toot))])
    toot = toot + 0.35 * room(toot, rng, 0.2)
    birds = [(0.02, chirp([(0, 3200), (1, 3600)], 0.05)), (0.1, chirp([(0, 3300), (1, 3700)], 0.05)),
             (1.0, chirp([(0, 1800), (1, 2600)], 0.12)), (1.15, chirp([(0, 2600), (0.3, 2700), (1, 1700)], 0.2))]
    return fade_out(0.6 * toot + place(1.48, [(at, 0.3 * s) for at, s in birds]), 0.15)


def yay(rng, f, dur=0.32, size=1.15):
    """A small, happy "yay!" (ye-ay), jumping up."""
    t = t_of(dur)
    f0 = glide(t, (0, f), (0.08, f * 1.25), (dur, f * 1.05))
    f1 = np.interp(t, [0, 0.05, 0.2, dur], [300, 750, 700, 450]) * size
    f2 = np.interp(t, [0, 0.05, 0.2, dur], [2300, 1800, 1900, 2200]) * size
    return voice(f0, [(f1, 130, 1.0), (f2, 180, 0.55), (3000 * size, 300, 0.12)], rng, breath=0.1) * env(len(t), 0.02, 0.1)


def amb_party():
    """The birthday party: a party blower unrolling with a happy buzzy toot
    (and its paper crinkling), then a small cheer: three little "yay"s and a
    sparkle of bells going up."""
    rng = np.random.default_rng(505)
    dur = 0.5
    t = t_of(dur)
    n = len(t)
    f = glide(t, (0, 330), (0.1, 410), (dur, 430)) * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))
    reed = harmonics(f, tilt=1.1) * (0.8 + 0.2 * np.sin(2 * np.pi * 28 * t))
    blow = bandpass(reed, 450, 3200) * ease(t / 0.03) * (1 - ease((t - 0.38) / 0.12))
    crinkle = np.zeros(n)
    for i in rng.integers(0, int(0.18 * SR), 22):
        crinkle[i:i + 50] += rng.uniform(0.3, 1) * np.exp(-np.arange(50) / 7) * rng.choice([-1, 1])
    blower = 0.7 * norm(blow) + 0.25 * norm(bandpass(crinkle, 3000, 8000))
    parts = [(0, blower)]
    parts += [(0.55 + 0.02 * k, 0.16 * yay(rng, p)) for k, p in enumerate((500, 580, 660))]
    for k, nm in enumerate(["C6", "E6", "G6", "C7", "E7", "G7", "C8"]):
        parts.append((0.6 + 0.06 * k + rng.uniform(-0.01, 0.01), (0.2 - 0.015 * k) * bell(NOTE[nm], 0.35, bright=0.4)))
    return fade_out(place(1.4, parts), 0.2)


def amb_kitchen():
    """The kitchen: something gently sizzling in a pan (a soft hiss full of
    tiny crackles) and a pot lid set down, clink-clink, settling."""
    rng = np.random.default_rng(506)
    dur = 1.4
    t = t_of(dur)
    n = len(t)
    hiss = norm(bandpass(rng.standard_normal(n), 2500, 9000)) * (0.7 + 0.3 * norm(lowpass(rng.standard_normal(n), 6)))
    pops = np.zeros(n)
    for i in rng.integers(0, n - 200, 90):
        k = rng.integers(40, 120)
        pops[i:i + k] += rng.uniform(0.2, 1) * rng.standard_normal(k) * np.exp(-np.arange(k) / (k / 5))
    sizzle = (0.35 * hiss + 0.8 * norm(bandpass(pops, 1500, 8000))) * ease(t / 0.08)
    lid = dict(ratios=(1, 1.47, 2.09, 2.56, 3.39), amps=(1, .7, .5, .35, .2), taus=(.45, .3, .2, .15, .1))
    parts = [(0, 0.35 * sizzle), (0.45, 0.5 * metal(1350, 0.55, **lid)), (0.58, 0.3 * metal(1350, 0.4, **lid)),
             (0.66, 0.15 * metal(1350, 0.3, **lid))]
    return fade_out(place(dur, parts), 0.35)


# ---------------------------------------------------------------- the list

# name: (make, loudness in dB beside the others: below 0 sits softer).
EFFECTS = {
    "tap": (tap, -4), "found": (found, 0), "miss": (miss, -6), "circle": (circle, -4), "all_found": (all_found, 0),
    "star": (star, -1), "stamp": (stamp, -2), "hint": (hint, -3), "magic": (magic, -1), "giggle": (giggle, -1),
    "peek": (peek, -1), "switch_style": (switch_style, -2), "next": (next_picture, -4), "rest": (rest_time, -2),
}
AMBIENCE = {
    "amb_park": (amb_park, -4), "amb_market": (amb_market, -4), "amb_beach": (amb_beach, -4),
    "amb_zoo": (amb_zoo, -3), "amb_party": (amb_party, -3), "amb_kitchen": (amb_kitchen, -4),
}
SHORT = {**EFFECTS, **AMBIENCE}
LONGEST = 1.5  # seconds, every short sound
TARGET = -21.0  # dB, the loudness of a short sound at 0 (about where the sibling apps' sit)
MAX_PEAK = 0.72


# ---------------------------------------------------------------- writing and checking


def tidy(x, sr=SR):
    """A short sound: drop the silent end, then fade both ends so neither clicks."""
    x = np.asarray(x, dtype=np.float64)
    loud = np.nonzero(np.abs(x) > np.abs(x).max() * 1e-3)[0]
    x = x[: min(len(x), loud[-1] + int(0.01 * sr))]
    return x * env(len(x), 0.002, 0.012, sr)


def phone_ready(x, sr=SR):
    """Take out what a phone cannot play anyway (under 70 Hz), for more room
    under the peak. The filter works on the whole sound at once and wraps
    round, so pad it with silence on both sides first: what it rings before
    the start and after the end then stays out of the sound."""
    pad_ = int(0.1 * sr)
    return highpass(np.concatenate([np.zeros(pad_), x, np.zeros(pad_)]), 70, sr)[pad_:]


def level(x, offset, sr=SR):
    """[x] at the loudness TARGET + [offset] dB, unless that would put its
    peak over MAX_PEAK: then at MAX_PEAK. Returns the peak."""
    x = norm(x)
    return min(MAX_PEAK, 10 ** ((TARGET + offset - loudness(x, sr)) / 20))


def write(path, x, peak, sr):
    x = np.asarray(x, dtype=np.float64)
    x = x / max(1e-9, np.abs(x).max()) * peak
    data = np.round(x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())
    return data


def seam(data, sr):
    """A loop's seam, checked two ways: the jump from the last sample back to
    the first (beside the biggest step from one sample to the next in the
    20 ms either side of it: a click would stand out above them), and the
    sound over 3 kHz in the 20 ms around the seam (a click would show as a
    burst there) beside the loudest 20 ms anywhere else in the loop."""
    x = data.astype(np.float64)
    steps = np.abs(np.diff(x))
    jump = abs(x[0] - x[-1])
    half = len(x) // 2
    h = highpass(np.roll(x, half), 3000, sr) ** 2  # the seam now sits at [half]
    w = int(0.02 * sr)
    c = np.concatenate([[0], np.cumsum(h)])
    starts = np.arange(0, len(h) - w + 1, w // 2)
    at = half - w // 2
    here = c[at + w] - c[at]
    others = (c[starts + w] - c[starts])[np.abs(starts - at) >= w]
    near = np.concatenate([steps[-w:], steps[:w]]).max()  # the biggest step in the 20 ms either side
    return jump, near, here / max(1e-9, others.max())


def report(name, data, sr, loop, want=None):
    x = data.astype(np.float64) / 32767
    peak = np.abs(x).max()
    loud = loudness(x, sr)
    clipped = int(np.sum(np.abs(data) >= 32767))
    if loop:
        jump, near, burst = seam(data, sr)
        edge = f"seam jump {jump:3.0f} (biggest step near it {near:.0f}), seam highs {burst:.2f} of the loudest elsewhere"
    else:
        edge = f"ends {int(data[0]):+d} / {int(data[-1]):+d}"
    short = "" if want is None or loud > want - 0.5 else f"  ({want - loud:.1f} dB under, held by the peak)"
    print(f"  {name:15s} {len(x) / sr:5.2f} s  {len(data) * 2 + 44:9,d} bytes  peak {peak:.2f}  "
          f"loudness {loud:6.1f} dB  clipped {clipped}  {edge}{short}")


def read(path):
    with wave.open(str(path), "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32767, w.getframerate()


def preview(path, loop_seconds=8.0, gap=0.5):
    """A listening preview: [loop_seconds] of each tune, then every short
    sound in order, [gap] apart. Prints where each one starts."""
    path = pathlib.Path(path)
    sr, pieces, at = 22050, [], 0.0
    print(f"preview {path}:")
    for name in list(MUSIC) + list(SHORT):
        x, rate = read(OUT / f"{name}.wav")
        if rate != sr:
            x = resample_poly(x, sr, rate)
        if name in MUSIC:
            x = x[: int(loop_seconds * sr)] * env(int(loop_seconds * sr), 0.01, 0.5, sr)
        print(f"  {int(at // 60)}:{at % 60:04.1f}  {name}")
        pieces += [x, np.zeros(int((1.0 if name in MUSIC else gap) * sr))]
        at += (len(x) + len(pieces[-1])) / sr
    wav = path.with_suffix(".wav")
    write(wav, np.concatenate(pieces), np.abs(np.concatenate(pieces)).max(), sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "aac", "-b:a", "96k", str(path)], check=True)
    wav.unlink()
    print(f"  total {at:.1f} s")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".keep").unlink(missing_ok=True)
    print("music (16,000 Hz, loops), about 8 dB under the short sounds:")
    for name, (make, offset) in MUSIC.items():
        tune = make()
        x = tune.render()
        assert 16 <= len(x) / LOOP_SR <= 20, (name, len(x) / LOOP_SR)
        report(name, write(OUT / f"{name}.wav", x, level(x, offset, LOOP_SR), LOOP_SR), LOOP_SR, True)
        over = loudness(tune.render(band=False), LOOP_SR) - loudness(tune.render(lead=False), LOOP_SR)
        print(f"  {'':15s} the tune is {over:.1f} dB over the band (through a phone)")
    print(f"short sounds (22,050 Hz), loudness {TARGET:.0f} dB plus or minus, peaks at most {MAX_PEAK}:")
    for name, (make, offset) in SHORT.items():
        x = tidy(phone_ready(make()))
        assert len(x) / SR <= LONGEST, (name, len(x) / SR)
        data = write(OUT / f"{name}.wav", x, level(x, offset), SR)
        assert data[0] == 0 and data[-1] == 0, name
        report(name, data, SR, False, TARGET + offset)
    names = {p.stem for p in OUT.glob("*.wav")}
    assert names == set(MUSIC) | set(SHORT), names ^ (set(MUSIC) | set(SHORT))
    total = sum(p.stat().st_size for p in OUT.glob("*.wav"))
    print(f"{len(MUSIC) + len(SHORT)} sounds, {total:,} bytes ({total / 1024 / 1024:.2f} MiB) in {OUT}")
    assert total < LIMIT, f"the sounds must stay under {LIMIT:,} bytes"
    if len(sys.argv) == 3 and sys.argv[1] == "preview":
        preview(sys.argv[2])


if __name__ == "__main__":
    main()
