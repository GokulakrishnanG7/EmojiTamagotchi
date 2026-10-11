"""Generates music/_default_theme.wav (a cheerful chiptune loop). Standard library only.
Run:  python tools/generate_default_music.py
"""
import math, os, struct, wave

RATE = 22050
BPM = 140
EIGHTH = 60.0 / BPM / 2

CHORDS = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]   # C  Am  F  G
ARP = [0, 1, 2, 1, 0, 1, 2, 1]


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def square(f, t):
    return 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0


def triangle(f, t):
    return 2 / math.pi * math.asin(math.sin(2 * math.pi * f * t))


def tone(wave_fn, f, dur, vol, decay):
    n = int(dur * RATE)
    return [vol * wave_fn(f, i / RATE) * math.exp(-decay * i / RATE) * min(1.0, i / 120) for i in range(n)]


def add(buf, start, samples):
    for i, s in enumerate(samples):
        if start + i < len(buf):
            buf[start + i] += s


bars = 16
total = int(bars * 8 * EIGHTH * RATE)
buf = [0.0] * total
for bar in range(bars):
    chord = CHORDS[bar % 4]
    octave = 12 if (bar // 4) % 2 == 0 else 24
    for step in range(8):
        start = int((bar * 8 + step) * EIGHTH * RATE)
        add(buf, start, tone(square, freq(chord[ARP[step]] + octave), EIGHTH * 0.95, 0.16, 5))
        if step % 4 == 0:
            add(buf, start, tone(triangle, freq(chord[0] - 12), EIGHTH * 3.6, 0.38, 1.5))
        if step in (2, 6) and bar % 4 in (1, 3):
            add(buf, start, tone(square, freq(chord[2] + 24), EIGHTH * 0.9, 0.08, 6))

peak = max(abs(x) for x in buf) or 1.0
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "music", "_default_theme.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.8 * 32767)) for x in buf))
print("Wrote", os.path.normpath(out))
