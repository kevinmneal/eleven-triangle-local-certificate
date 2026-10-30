"""Render the README cartoon; optional Pillow >= 10.1, no proof dependencies.

Run `python3 tools/render_shaking.py` from any directory. The saved contact
coordinates are rounded only for drawing. The whole tray moves rigidly;
this is a joke about shaking, not a recorded optimizer or physics trajectory.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "certificate/certificates/source_local_v2.json.gz"
OUTPUT = ROOT / "docs/assets"
SIZE = (800, 450)
SCALE = 2
FPS = 20
SECONDS = 6.4
INK = "#243638"
MUTED = "#687775"
PAPER = "#faf6ed"
COLORS = ["#91bdaf", "#e1bda1", "#d7ded0", "#bcb3d2", "#edbd68",
          "#cad4bd", "#bcb3d2", "#edbd68", "#91bdaf", "#e6a18b", "#d7ded0"]


def font(size):
    return ImageFont.load_default(size=round(size * SCALE))


def frame(t, poses, radius):
    image = Image.new("RGB", tuple(v * SCALE for v in SIZE), PAPER)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=18, fill=INK):
        draw.text((x * SCALE, y * SCALE), value, font=font(size), fill=fill)

    def line(points, fill=INK, width=2):
        draw.line([(x * SCALE, y * SCALE) for x, y in points],
                  fill=fill, width=round(width * SCALE), joint="curve")

    if .9 < t < 3.7:
        envelope = min(1, (t - .9) / .5, (3.7 - t) / .65)
    else:
        envelope = 0
    phase = 2 * math.pi * 3.25 * (t - .9)
    dx = 10 * envelope * math.sin(phase)
    dy = 3 * envelope * math.sin(phase * 1.5)
    angle = .035 * envelope * math.sin(phase + .4)
    co, si = math.cos(angle), math.sin(angle)
    unit = 149 / radius

    def point(x, y):
        return (235 + dx + unit * (co * x - si * y),
                249 + dy - unit * (si * x + co * y))

    def polygon(points, fill, outline=INK, width=1.4):
        scaled = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
        draw.polygon(scaled, fill=fill)
        draw.line(scaled + scaled[:1], fill=outline,
                  width=round(width * SCALE), joint="curve")

    text(38, 27, "DID YOU TRY SHAKING IT?", size=31)
    text(40, 68, "eleven triangles / one stubborn pentagon", size=17, fill=MUTED)

    # Same orientation as certificate/geometry.py: inward normals at 2*pi*k/5.
    boundary = [point(-radius * math.sin((k + .5) * 2 * math.pi / 5),
                      -radius * math.cos((k + .5) * 2 * math.pi / 5))
                for k in range(5)]
    polygon([(x + 1, y + 8) for x, y in boundary], "#ded8c9", "#ded8c9")
    polygon(boundary, "#fffcf5", width=3)

    for i, (x, y, theta) in enumerate(poses):
        triangle = [point(x + math.sin(theta + k * 2 * math.pi / 3),
                          y + math.cos(theta + k * 2 * math.pi / 3))
                    for k in range(3)]
        polygon(triangle, COLORS[i])
        cx, cy = point(x, y)
        # Tiny unamused faces. Their gaze follows the shaking; the pieces don't.
        gaze = -1.2 * envelope * math.sin(phase)
        for ex in (-5, 5):
            center = ((cx + ex + gaze) * SCALE, (cy - 3) * SCALE)
            r = 1.7 * SCALE
            draw.ellipse((center[0] - r, center[1] - r,
                          center[0] + r, center[1] + r), fill=INK)
        line([(cx - 4, cy + 5), (cx + 4, cy + 5)], width=1.5)

    line(boundary + boundary[:1], width=3)
    if envelope > .15:
        # Motion marks, not flashing full-frame effects.
        for side in (-1, 1):
            x = 235 + side * (178 + 4 * envelope)
            line([(x, 212), (x - side * 5, 229), (x, 247)], MUTED)
            line([(x + side * 10, 221), (x + side * 7, 232),
                  (x + side * 10, 243)], MUTED, 1.5)

    if t < .9:
        headline, subline = "ONE MORE TRY.", "What could possibly go wrong?"
    elif t < 3.7:
        headline, subline = "SHAKING...", "Applying additional optimism."
    else:
        headline, subline = "STILL JAMMED.", "The triangles remain unconvinced."
    text(447, 172, headline, size=29)
    text(448, 216, subline, size=16, fill=MUTED)

    # Decorative effort meter, unrelated to any measured search quantity.
    text(448, 266, "EFFORT", size=12, fill=MUTED)
    for j in range(12):
        active = j < round(12 * envelope)
        x, height = 448 + j * 20, 8 + j * 1.4
        draw.rounded_rectangle((x * SCALE, (311 - height) * SCALE,
                                (x + 12) * SCALE, 311 * SCALE),
                               radius=2 * SCALE,
                               fill=("#d78662" if active else "#e3ded2"))
    line([(40, 407), (760, 407)], "#ded8c9", 1)
    text(40, 421, "KNOWN PACKING. UNKNOWN GLOBAL OPTIMUM.", size=12, fill=MUTED)
    text(640, 421, "cartoon edition", size=12, fill=MUTED)
    return image.resize(SIZE, Image.Resampling.LANCZOS)


def main():
    data = SOURCE.read_bytes()
    expected = "680ecd966e5391810df5d0d5782d9c78a3016e9f1c2544a4147f8af36353d4a8"
    if hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError("Unexpected source certificate")
    values = [float(v) for v in json.loads(gzip.decompress(data))["root"]["center"]]
    if len(values) != 34:
        raise RuntimeError("Expected eleven poses and a radius")
    poses = [values[i:i + 3] for i in range(0, 33, 3)]
    frames = [frame(i / FPS, poses, values[-1]) for i in range(round(SECONDS * FPS))]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames[-1].save(OUTPUT / "still-jammed.png", optimize=True)
    # One shared palette avoids color flicker between frames.
    sample = Image.new("RGB", (SIZE[0], 3 * SIZE[1]), PAPER)
    for i, index in enumerate((0, 40, 100)):
        sample.paste(frames[index], (0, i * SIZE[1]))
    palette = sample.quantize(colors=128)
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(OUTPUT / "still-jammed.gif", save_all=True,
                    append_images=indexed[1:], duration=1000 // FPS,
                    loop=0, optimize=True, disposal=1)
    print(f"Saved {OUTPUT / 'still-jammed.gif'}")


if __name__ == "__main__":
    main()
