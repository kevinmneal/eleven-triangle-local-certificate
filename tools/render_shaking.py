"""Render the README cartoon. Optional Pillow >= 10.1; no proof dependencies.

The saved contact coordinates define the opening and closing tableaux only.
In between, characters shrink, bounce in a small rigid-body cartoon simulation,
then follow choreographed return arcs. Squash, faces and reactions are drawn
for comedy. None of these frames is a recorded search or a proof calculation.

Run: python3 tools/render_shaking.py
"""
import gzip
import hashlib
import json
import math
import random
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "certificate/certificates/source_local_v2.json.gz"
OUTPUT = ROOT / "docs/assets"
SIZE, SCALE, FPS, SECONDS = (840, 660), 2, 25, 8.8
INK, MUTED, PAPER = "#26383b", "#677570", "#faf6ed"
COLORS = ["#8cbfb0", "#e6bca0", "#bdd3a5", "#b7acd5", "#f0bf60",
          "#c3d5ca", "#c3b7df", "#edca74", "#94cbbb", "#e89d87", "#cdd5aa"]
TAU = 2 * math.pi


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def body_scale(t):
    return 1 - .36 * ease((t - .8) / .5) + .36 * ease((t - 5.75) / .85)


@dataclass
class Body:
    x: float
    y: float
    theta: float
    vx: float = 0
    vy: float = 0
    omega: float = 0
    hit_time: float = -100
    hit_power: float = 0


def vertices(body, size):
    return [(body.x + size * math.sin(body.theta + k * TAU / 3),
             body.y + size * math.cos(body.theta + k * TAU / 3)) for k in range(3)]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def pair_contact(a, b, size):
    if (b.x - a.x) ** 2 + (b.y - a.y) ** 2 > (2 * size) ** 2:
        return None
    av, bv = vertices(a, size), vertices(b, size)
    depth, normal = 1e6, None
    for points in (av, bv):
        for k in range(3):
            p, q = points[k], points[(k + 1) % 3]
            nx, ny = -(q[1] - p[1]), q[0] - p[0]
            length = math.hypot(nx, ny)
            axis = nx / length, ny / length
            ap, bp = [dot(p, axis) for p in av], [dot(p, axis) for p in bv]
            overlap = min(max(ap), max(bp)) - max(min(ap), min(bp))
            if overlap <= 0:
                return None
            if overlap < depth:
                depth, normal = overlap, axis
    if dot((b.x - a.x, b.y - a.y), normal) < 0:
        normal = -normal[0], -normal[1]
    support_a = max(av, key=lambda p: dot(p, normal))
    support_b = min(bv, key=lambda p: dot(p, normal))
    point = ((support_a[0] + support_b[0]) / 2,
             (support_a[1] + support_b[1]) / 2)
    return depth, normal, point


def velocity(body, arm):
    return body.vx - body.omega * arm[1], body.vy + body.omega * arm[0]


def react(body, t, impulse):
    if impulse > .1:
        body.hit_time, body.hit_power = t, min(1, impulse / 1.2)


def tick(bodies, radius, t, dt):
    size, inv_inertia = .64, 4 / .64 ** 2
    ramp = ease((t - 1.25) / .45) * (1 - ease((t - 4.35) / .65))
    for i, body in enumerate(bodies):
        # A shaken tray plus little individual kicks make each character move.
        body.vx += (13 * math.sin(19 * t) * ramp + 1.8 * math.sin(i * 2 + t)) * dt
        body.vy += (-1.8 + 17 * math.cos(16 * t) * ramp) * dt
        body.vx *= .998
        body.vy *= .998
        body.omega *= .998
        body.omega = max(-8, min(8, body.omega))
        body.x += body.vx * dt
        body.y += body.vy * dt
        # Geometry uses clockwise angles from +y; omega is conventional CCW.
        body.theta -= body.omega * dt

    for _ in range(3):
        for i, a in enumerate(bodies):
            for b in bodies[i + 1:]:
                contact = pair_contact(a, b, size)
                if contact is None:
                    continue
                depth, n, point = contact
                shift = max(0, depth - .0001) * .48
                a.x -= shift * n[0]
                a.y -= shift * n[1]
                b.x += shift * n[0]
                b.y += shift * n[1]
                ra, rb = (point[0] - a.x, point[1] - a.y), (point[0] - b.x, point[1] - b.y)
                va, vb = velocity(a, ra), velocity(b, rb)
                approach = dot((vb[0] - va[0], vb[1] - va[1]), n)
                if approach < 0:
                    j = -1.65 * approach / (2 + inv_inertia * (cross(ra, n) ** 2 + cross(rb, n) ** 2))
                    a.vx -= j * n[0]
                    a.vy -= j * n[1]
                    b.vx += j * n[0]
                    b.vy += j * n[1]
                    a.omega -= inv_inertia * j * cross(ra, n)
                    b.omega += inv_inertia * j * cross(rb, n)
                    react(a, t, j)
                    react(b, t, j)
        for body in bodies:
            for k in range(5):
                n = math.sin(k * TAU / 5), math.cos(k * TAU / 5)
                point = min(vertices(body, size), key=lambda p: dot(p, n))
                gap = dot(point, n) + radius * math.cos(math.pi / 5)
                if gap >= 0:
                    continue
                body.x -= gap * n[0]
                body.y -= gap * n[1]
                arm = point[0] - body.x, point[1] - body.y
                approach = dot(velocity(body, arm), n)
                if approach < 0:
                    j = -1.7 * approach / (1 + inv_inertia * cross(arm, n) ** 2)
                    body.vx += j * n[0]
                    body.vy += j * n[1]
                    body.omega += inv_inertia * j * cross(arm, n)
                    react(body, t, j)


def animate(poses, radius):
    rng = random.Random(20261030)
    bodies = [Body(*pose, vx=rng.uniform(-1.6, 1.6), vy=rng.uniform(.8, 2),
                   omega=rng.choice((-1, 1)) * rng.uniform(2, 4)) for pose in poses]
    trajectory, end = [], None
    for frame_index in range(round(SECONDS * FPS)):
        t = frame_index / FPS
        if 1.25 <= t < 5:
            for substep in range(8):
                tick(bodies, radius, t + substep / (FPS * 8), 1 / (FPS * 8))
        elif t >= 5:
            if end is None:
                end = [replace(body) for body in bodies]
            for i, (body, old, target) in enumerate(zip(bodies, end, poses)):
                u = min(1, max(0, (t - 5 - .045 * (i % 5)) / (1.02 + .06 * (i % 3))))
                f = ease(u)
                body.x = old.x + f * (target[0] - old.x) + .15 * math.sin(math.pi * u) * math.cos(i)
                body.y = old.y + f * (target[1] - old.y) + .45 * math.sin(math.pi * u)
                turn = (target[2] - old.theta + math.pi) % TAU - math.pi
                if i == 6:
                    turn += TAU  # One last gratuitous somersault.
                body.theta = old.theta + f * turn
                body.vx = body.vy = body.omega = 0
                # Keep the deliberately choreographed return inside the tray.
                for _ in range(4):
                    for k in range(5):
                        n = math.sin(k * TAU / 5), math.cos(k * TAU / 5)
                        gap = min(dot(v, n) for v in vertices(body, body_scale(t))) + radius * math.cos(math.pi / 5)
                        if gap < 0:
                            body.x -= gap * n[0]
                            body.y -= gap * n[1]
        trajectory.append([replace(body) for body in bodies])
    return trajectory


def font(size):
    return ImageFont.load_default(size=round(size * SCALE))


def frame(t, bodies, poses, radius):
    image = Image.new("RGB", tuple(v * SCALE for v in SIZE), PAPER)
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=18, fill=INK, anchor="mm"):
        draw.text((x * SCALE, y * SCALE), value, font=font(size), fill=fill, anchor=anchor)

    def line(points, fill=INK, width=2):
        draw.line([(round(x * SCALE), round(y * SCALE)) for x, y in points],
                  fill=fill, width=max(1, round(width * SCALE)), joint="curve")

    def polygon(points, fill, outline=INK, width=1.6):
        scaled = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
        draw.polygon(scaled, fill=fill)
        if outline:
            line(points + points[:1], outline, width)

    shake = ease((t - 1.15) / .4) * (1 - ease((t - 4.3) / .7))
    dx, dy = 12 * shake * math.sin(19 * t), 5 * shake * math.sin(16 * t)
    angle = .045 * shake * math.sin(19 * t + .4)
    co, si, unit = math.cos(angle), math.sin(angle), 209 / radius

    def point(x, y):
        return (420 + dx + unit * (co * x - si * y),
                354 + dy - unit * (si * x + co * y))

    boundary = [point(-radius * math.sin((k + .5) * TAU / 5),
                      -radius * math.cos((k + .5) * TAU / 5)) for k in range(5)]
    text(420, 42, "DID YOU TRY SHAKING IT?", 34)
    text(420, 83, "eleven triangles. one very bad afternoon.", 18, MUTED)
    polygon([(x + 2, y + 9) for x, y in boundary], "#dfd8ca", None)
    polygon(boundary, "#fffcf6", width=3)

    shapes = []
    for i, body in enumerate(bodies):
        stress = body.hit_power * math.exp(-max(0, t - body.hit_time) * 13) if t < 5 else 0
        sx, sy = 1 + .12 * stress, 1 / (1 + .12 * stress)
        size = body_scale(t)
        tri = [point(body.x + sx * size * math.sin(body.theta + k * TAU / 3),
                     body.y + sy * size * math.cos(body.theta + k * TAU / 3)) for k in range(3)]
        shapes.append(tri)
        if size < .99:
            polygon([(x + 1.5, y + 3) for x, y in tri], "#e1dacb", None)
    for i, tri in enumerate(shapes):
        polygon(tri, COLORS[i], width=2)

    for i, body in enumerate(bodies):
        cx, cy = point(body.x, body.y)
        rotation = -(body.theta - poses[i][2] + angle)
        c, s = math.cos(rotation), math.sin(rotation)

        def fp(x, y):
            return cx + c * x - s * y, cy + s * x + c * y

        def fl(points, fill=INK, width=1.9):
            line([fp(x, y) for x, y in points], fill, width)

        def oval(x, y, rx, ry, fill, outline=INK, width=1.4):
            polygon([fp(x + rx * math.cos(k * TAU / 24), y + ry * math.sin(k * TAU / 24))
                     for k in range(24)], fill, outline, width)

        active, returning, tired = 1.1 <= t < 5, 5 <= t < 6.5, t >= 6.5
        recent_hit = t - body.hit_time < .12 and active and i % 3 == 0
        if tired:
            mood = "dizzy" if i in (2, 6) and t < 7.4 else "annoyed"
        elif returning:
            mood = "hopeful"
        elif active:
            mood = "squeeze" if recent_hit else ("panic", "dizzy", "yell", "panic")[i % 4]
            if t < 1.8:
                mood = "panic"
        else:
            mood = "calm"
        blink = (t + i * .31) % 3.3 < .10 and mood in ("calm", "hopeful", "annoyed")
        gaze_x = max(-2, min(2, -body.vx * 1.2)) if active else (1.4 if i % 2 else -1.4)
        gaze_y = max(-1.5, min(1.5, body.vy)) if active else 0

        for ex in (-8, 8):
            if blink:
                fl([(ex - 4, -6), (ex + 4, -6)], width=2)
                continue
            if mood == "squeeze":
                direction = 1 if ex < 0 else -1
                fl([(ex - 4 * direction, -10), (ex + 2 * direction, -6), (ex - 4 * direction, -2)], width=2.2)
                continue
            ey = 7.2 if mood in ("panic", "yell") else 5.6
            oval(ex, -6, 5.6, ey, "#fffefa")
            if mood == "dizzy":
                spiral = []
                for k in range(30):
                    a = k / 29 * 3.5 * math.pi + t * 4
                    r = 4 * k / 29
                    spiral.append((ex + r * math.cos(a), -6 + r * math.sin(a)))
                fl(spiral, width=1.3)
            else:
                oval(ex + gaze_x, -5.4 + gaze_y, 2.5, 2.9, INK, None)
                oval(ex + gaze_x - .7, -6.4 + gaze_y, .8, .8, "#fffefa", None)
            if mood == "annoyed":
                polygon([fp(ex - 6, -12), fp(ex + 6, -12), fp(ex + 6, -6), fp(ex - 6, -8)], COLORS[i], None)
                fl([(ex - 5, -8), (ex + 5, -6)], width=1.8)
            brow_y = -18 if mood in ("panic", "yell") else (-13 if mood == "annoyed" else -15)
            tilt = (2 if ex < 0 else -2) if mood == "annoyed" else (-1 if ex < 0 else 1)
            fl([(ex - 5, brow_y + tilt), (ex + 5, brow_y - tilt)], width=1.8)

        if mood in ("panic", "yell"):
            oval(0, 10, 4.5 if mood == "panic" else 8, 6 if mood == "panic" else 7, INK)
            if mood == "yell":
                oval(1, 13, 4, 2.4, "#ee928d", None)
                fl([(-4, 5.5), (4, 5.5)], "#fffefa", 2.7)
        elif mood in ("annoyed", "squeeze"):
            fl([(-6, 11), (0, 8.5), (6, 11)], width=2)
        elif mood == "dizzy":
            fl([(-7, 9), (-3, 7), (1, 10), (5, 8)], width=1.8)
        else:
            fl([(-5, 7), (-3, 10), (0, 11), (3, 10), (5, 7)], width=1.7)

        if active and i in (0, 3, 9):
            # Sweat follows the face, so a tumbling character keeps its expression.
            polygon([fp(19, -16), fp(22, -10), fp(20, -6), fp(16, -8)], "#69b7cf", INK, 1)
        if active and i in (2, 6, 9):
            for sign in (-1, 1):
                wave = 4 * math.sin(t * 25 + i)
                fl([(sign * 19, 5), (sign * 25, 1), (sign * 26, -7 + wave)], width=2)
                oval(sign * 26, -7 + wave, 3, 3, "#fffefa", width=1)
        if tired and i == 6 and t < 7.6:
            for k in range(3):
                a = t * 5 + k * TAU / 3
                star_x, star_y = cx + 23 * math.cos(a), cy - 24 + 5 * math.sin(a)
                polygon([(star_x + (4 if j % 2 == 0 else 1.8) * math.cos(j * math.pi / 4),
                          star_y + (4 if j % 2 == 0 else 1.8) * math.sin(j * math.pi / 4))
                         for j in range(8)], "#df9a32", None)

    line(boundary + boundary[:1], width=3)
    if shake > .2:
        for side in (-1, 1):
            x = 420 + side * 235
            line([(x, 295), (x - side * 9, 324), (x, 350)], MUTED, 2.2)
            line([(x + side * 13, 306), (x + side * 8, 326), (x + side * 13, 343)], MUTED, 1.6)

    def bubble(x, y, word, left=False):
        width = max(60, 16 + draw.textlength(word, font=font(20)) / SCALE)
        box = ((x - width / 2) * SCALE, (y - 20) * SCALE,
               (x + width / 2) * SCALE, (y + 20) * SCALE)
        draw.rounded_rectangle(box, radius=12 * SCALE, fill="#fffefa", outline=INK, width=2 * SCALE)
        sign = -1 if left else 1
        polygon([(x - sign * 7, y + 19), (x - sign * 19, y + 32), (x + sign * 5, y + 19)], "#fffefa", INK, 1.5)
        line([(x - sign * 6, y + 19), (x + sign * 4, y + 19)], "#fffefa", 2.4)
        text(x, y, word, 20)

    if .85 <= t < 1.7:
        bubble(685, 205, "uh oh.", True)
    elif 2 <= t < 3.15:
        bubble(126, 245, "HEY!")
    elif 3.35 <= t < 4.7:
        bubble(710, 410, "WHOA", True)
    elif 5.2 <= t < 6.35:
        bubble(692, 226, "...better?", True)
    elif t >= 6.85:
        bubble(150, 227, "no.")

    if t < 1.25:
        caption = "just a little shake."
    elif t < 2.8:
        caption = "OH. THAT'S A LOT."
    elif t < 4.4:
        caption = "EVERY TRIANGLE FOR ITSELF."
    elif t < 5:
        caption = "okay, okay, STOP."
    elif t < 6.5:
        caption = "wait... did that help?"
    else:
        caption = "STILL. JAMMED."
    text(420, 585, caption, 30)
    text(420, 628, "exaggerated cartoon motion / actual research below", 13, MUTED)
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
    trajectory = animate(poses, values[-1])
    frames = [frame(i / FPS, bodies, poses, values[-1]) for i, bodies in enumerate(trajectory)]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames[-1].save(OUTPUT / "triangle-tantrum.png", optimize=True)
    # A shared palette avoids color flicker; sample all expression/motion stages.
    sample = Image.new("RGB", (SIZE[0] * 3, SIZE[1] * 2), PAPER)
    for i, index in enumerate((0, 38, 67, 100, 143, 195)):
        sample.paste(frames[index], ((i % 3) * SIZE[0], (i // 3) * SIZE[1]))
    palette = sample.quantize(colors=160)
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(OUTPUT / "triangle-tantrum.gif", save_all=True,
                    append_images=indexed[1:], duration=1000 // FPS,
                    loop=0, optimize=True, disposal=1)
    print(f"Saved {OUTPUT / 'triangle-tantrum.gif'}")


if __name__ == "__main__":
    main()
