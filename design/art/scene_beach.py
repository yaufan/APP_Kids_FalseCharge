"""海邊 (beach): one of the two free scenes.

The same floating isometric tile as the park (200 x 200 world units, 1.5 px per unit), but half
of it is golden sand (the back-left) and half is the sea (the front-right): a wavy shoreline with
foam, wet sand, shallow turquoise water that deepens to blue, and the sea's own blue sides on the
block. On the sand: a palm tree, a lifeguard chair, a beach umbrella over a towel, a surfboard, a
sand castle, a bucket and spade, a beach ball, a crab, shells and a starfish; on the sea a sailboat
and a swim ring; the sun (with a face) and a seagull in the summer sky. Extras: a dolphin, a
little fish and a second beach ball.

    background()   sky, clouds, the tile (sand, sea, foam), its sides: everything that never changes
    GROUND         where each thing on the tile stands, in world units (x to the right-front, y to the
                   left-front); the shoreline is shore_x(y), sand where x < shore_x(y)
    SKY_AT         sky things, in scene px

Colours 小變 hides against come from kit.TINT: the sand (TINT sand), the deep sea (TINT blue) and
the white towel (TINT white).
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, star_pts, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=186)
TILE = 200
P = ISO.P
INK = "#2B3158"
WHITE = "#FFFFFF"
METAL = "#8E98B6"
SKY = "#BFEAFF"
CLOUD_SH = "#A9DCF6"
SAND = TINT["sand"]
SAND_WET = "#E6BF80"
SAND_LINE = "#E2BC7C"
SAND_RIM = "#EBC584"
SAND_BODY = "#DDA463"
SEABED = "#E6BE84"
SHALLOW = "#78DDEA"
MID = "#5DB7F7"
DEEP = TINT["blue"]
WATER_SIDE = "#4FA6EE"
FOAM = WHITE
WOOD = TINT["wood"]
TRUNK = "#C99560"
TRUNK_D = "#A0703F"
FROND = "#4DBF63"
FROND_D = "#36A055"
RIB = "#2E8B4A"
COCO = "#8A5A34"
RED = "#FF5A5F"
BLUE = TINT["blue"]
YELLOW = "#FFD84A"
ORANGE = "#FF9838"
PINK = "#FF8FB8"
PURPLE = "#A77BFF"
GREEN = "#5BD08A"
TURQ = "#26C3B5"
TOWEL = TINT["white"]
CASTLE = "#E7B467"
CASTLE_D = "#C98F45"


def shore_x(y):
    """The shoreline: sand where x < shore_x(y), sea beyond (world units)."""
    return 84 + .33 * y + 7 * math.sin(math.pi * 3 * y / 200)


SHORE_YS = [i * 4 for i in range(51)]

# things on the tile, in world units (for boxes: the back corner of their footprint)
GROUND = {
    "palm": (12, 150),
    "surfboard": (8, 186),
    "chair": (4, 58),           # back corner; the chair is 24 x 24
    "umbrella": (56, 22),
    "towel": (46, 44),          # back corner; the towel is 44 x 24
    "ball": (86, 70),
    "castle": (62, 132),        # back corner; the castle is 30 x 30
    "bucket": (40, 172),
    "shells": (84, 192),
    "crab": (136, 184),
    "starfish": (100, 100),
    "boat": (172, 34),
    "swimring": (160, 130),
    "dolphin": (190, 100),
    "fish": (190, 170),
    "ball2": (114, 70),
}
SKY_AT = {
    "sun": (522, 76),
    "seagull": (176, 82),
}


def S(name, z=0.0):
    """Scene px of a thing's ground point."""
    x, y = GROUND[name]
    return P(x, y, z)


def depth(name, dz=0.0):
    x, y = GROUND[name]
    return x + y + dz


def shadow(x, y, r, op=1.0):
    return ISO.shadow(x, y, r, op=op)


def squash(shapes, k, about):
    """Flatten 2D shapes vertically about a point (things lying on the sand)."""
    ax, ay = about
    return [sh.affine(1, 0, 0, k, 0, ay * (1 - k)) for sh in shapes]


def profile(c, wfn):
    """A closed outline around a centre line c with a width profile wfn(t), t from 0 to 1."""
    m = len(c)
    L, R = [], []
    for i, (x, y) in enumerate(c):
        x0, y0 = c[max(i - 1, 0)]
        x1, y1 = c[min(i + 1, m - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln_, dx / ln_
        w = wfn(i / (m - 1)) / 2
        L.append((x + nx * w, y + ny * w))
        R.append((x - nx * w, y - ny * w))
    return L + R[::-1]


def quad(a, c, b, k=12):
    """Points of a quadratic curve from a to b, pulled toward c."""
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1])
            for t in (i / k for i in range(k + 1))]


# ================================================================ background
def band(off0, off1, wav=0.0, ph=0.0):
    """The sea between shore_x + off0 and shore_x + off1 (world), clipped to the tile."""
    def edge(off):
        return [(min(TILE, shore_x(y) + off + (wav * math.sin(y / 11 + ph) if off else 0)), y) for y in SHORE_YS]
    inner = edge(off0)
    outer = edge(off1) if off1 is not None else [(TILE, y) for y in SHORE_YS]
    return inner + outer[::-1]


def wave(x, y, L=16, amp=1.6, z=0.0):
    """A little white wave crest on the sea, running along the shore (world point)."""
    pts = [P(x + amp * math.sin(t / L * 2 * math.pi), y + t - L / 2, z) for t in (i * L / 8 for i in range(9))]
    return pts


def cloud(cx, cy, s):
    c = tf(crs([(-34, 6), (-38, -4), (-26, -12), (-14, -22), (6, -22), (18, -12), (32, -10), (34, 6)]), s=s, dx=cx, dy=cy)
    return [Sh(tf(c, dy=3), CLOUD_SH, only="ab"), Sh(c, WHITE)]


def background():
    g = Group()
    g.add(Sh([(0, 0), (600, 0), (600, 600), (0, 600)], SKY, tag="screen"), -9000)
    for (cx, cy), s in CLOUDS:
        g.add(cloud(cx, cy, s), -8000)
    # the island's shadow on the air below
    cx, cy = P(TILE / 2, TILE / 2, -20)
    g.add(Sh(ellp(cx, cy + 44, 226, 24), "#3B5A7A", tag="shadow", op=.9), -7000)
    # the block: the sand's side (left face, up to the shore), the sea's side (water over a sandy bed)
    xs = shore_x(TILE)
    g.add(ISO.box(0, 0, -21, xs, TILE, 16, SAND_BODY)[:1], -6000)
    g.add(ISO.box(0, 0, -5, xs, TILE, 5, SAND_RIM)[:1], -5990)
    g.add(ISO.box(xs, 0, -21, TILE - xs, TILE, 9, SEABED)[:1] + ISO.box(0, 0, -21, TILE, TILE, 9, SEABED)[1:2], -6000)
    g.add(ISO.box(xs, 0, -12, TILE - xs, TILE, 12, WATER_SIDE)[:1] + ISO.box(0, 0, -12, TILE, TILE, 12, WATER_SIDE)[1:2], -5990)
    g.add([line([P(xs + 1, TILE, -1.6), P(TILE, TILE, -1.6), P(TILE, 0, -1.6)], WHITE, 2.2, op=.55)], -5980)
    peb = []
    for i in range(9):          # shells and pebbles in the sand's side
        t = (i + .5) / 9
        x, z = 6 + t * (xs - 12), -8 - (i * 7 % 11)
        sx, sy = P(x, TILE, z)
        peb.append(oval(sx, sy, 3.4 - (i % 3) * .5, 2, col=mix(SAND_BODY, WHITE, .35), tag="detail"))
    for i, (y, z, r) in enumerate(((22, -5, 2.4), (58, -8, 1.8), (96, -4, 2.8), (134, -7, 2), (172, -5, 2.2))):   # bubbles in the water
        sx, sy = P(TILE, y, z)
        peb.append(oval(sx, sy, r, col=WHITE, op=.6, tag="detail"))
    sx, sy = P(xs + 20, TILE, -6)
    peb.append(oval(sx, sy, 2.2, col=WHITE, op=.6, tag="detail"))
    g.add(peb, -5800)
    # the top: the sea in three bands, then the sand, wet sand and foam along the shore
    g.add(ISO.flat(band(-2, 13, 2), 0, SHALLOW), -5000)
    g.add(ISO.flat(band(11, 24, 2.5, 1.3), 0, MID), -4990)
    g.add(ISO.flat(band(22, None, 3, 2.1), 0, DEEP), -4980)
    sand = [(0, 0)] + [(shore_x(y), y) for y in SHORE_YS] + [(0, TILE)]
    g.add(ISO.flat(sand, 0, SAND), -4900)
    wet = [(shore_x(y) + .5, y) for y in SHORE_YS] + [(shore_x(y) - 9 - 2.5 * math.sin(y / 13), y) for y in SHORE_YS][::-1]
    g.add(ISO.flat(wet, 0, SAND_WET), -4890)
    foam = [(shore_x(y) - 1.5, y) for y in SHORE_YS] + [(shore_x(y) + 4 + 3 * abs(math.sin(y * math.pi / 16)), y) for y in SHORE_YS][::-1]
    g.add(ISO.flat(foam, 0, FOAM), -4880)
    # a second line of foam a little way out, broken into pieces
    for y0, y1 in ((2, 30), (44, 78), (92, 120), (134, 166), (178, 198)):
        ys = [y0 + (y1 - y0) * i / 10 for i in range(11)]
        g.add(line([P(shore_x(y) + 14 + 1.5 * math.sin(y / 5), y) for y in ys], WHITE, 2.4, op=.85), -4870)
    for x, y in WAVES:
        g.add(line(wave(x, y), WHITE, 2, op=.8), -4860)
    # the sand: ripples, little pebbles, dune grass
    for pts in RIPPLES:
        g.add(line([P(x, y) for x, y in crs(pts, 5, closed=False)], SAND_LINE, 1.8), -4800)
    for x, y in PEBBLES:
        sx, sy = P(x, y)
        g.add(oval(sx, sy, 2.2, 1.3, col=mix(SAND, "#B98A4C", .45), tag="detail"), -4790)
    for x, y in GRASS:
        sx, sy = P(x, y)
        g.add(line([(sx - 6, sy - 9), (sx - 2, sy), (sx - 1, sy - 13), (sx + 1, sy), (sx + 5, sy - 10)], "#6DBE5A", 2), x + y)
    return g.shapes()


CLOUDS = [((410, 48), .8), ((92, 474), .75), ((540, 484), .9), ((54, 92), .55)]
WAVES = [(150, 8), (176, 30), (188, 6), (140, 64), (172, 66), (194, 44), (158, 104), (186, 118), (176, 150), (196, 160),
         (168, 186), (128, 40)]
RIPPLES = [[(10, 92), (16, 102), (14, 116)], [(70, 150), (78, 160), (76, 174)], [(30, 6), (38, 14), (40, 26)],
           [(86, 60), (90, 70), (88, 82)], [(18, 190), (26, 196)]]
PEBBLES = [(30, 80), (54, 98), (24, 136), (88, 140), (40, 188), (70, 20), (6, 40), (84, 196), (120, 186)]
GRASS = [(4, 30), (4, 44), (3, 96), (6, 132), (4, 186), (26, 3), (48, 4)]


# ================================================================ things
# ---------------------------------------------------------------- palm tree (its trunk leans to the left: flip shows)
def frond(T, ang, L, W, droop, col):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    tip = (T[0] + L * ux, T[1] + L * uy + droop)
    p1 = (T[0] + L * .35 * ux, T[1] + L * .35 * uy - 9)
    p2 = (T[0] + L * .72 * ux, T[1] + L * .72 * uy - 6 + droop * .35)
    c = crs([T, p1, p2, tip], 6, closed=False)
    m = len(c)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        x0, y0 = c[max(i - 1, 0)]
        x1, y1 = c[min(i + 1, m - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln_, dx / ln_
        t = i / (m - 1)
        w = W * math.sin(math.pi * t) ** .6 * (1 - .25 * t) * (1.0 if i % 2 else .6)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return [Sh(left + right[::-1], col), line(c[1:-2], RIB, 1.4)]


def palm(nuts=3):
    x, y = GROUND["palm"]
    sx, sy = P(x, y)
    g = Group()
    g.add(shadow(x + 2, y + 2, 11, .8), -1)
    c = crs([(0, 0), (-2, -34), (-12, -72), (-28, -104), (-38, -116)], 8, closed=False)
    o = [Sh(profile(c, lambda t: 17 - 7 * t), TRUNK, cel=.5)]
    for k in range(3, len(c) - 3, 4):
        px, py = c[k]
        qx, qy = c[k + 1]
        dx, dy = qx - px, qy - py
        ln_ = math.hypot(dx, dy) or 1
        dx, dy = dx / ln_, dy / ln_
        hw = (17 - 7 * k / (len(c) - 1)) / 2 * .9
        o.append(line([(px - dy * hw + dx * 3.5, py + dx * hw + dy * 3.5), (px, py), (px + dy * hw + dx * 3.5, py - dx * hw + dy * 3.5)],
                      TRUNK_D, 1.8))
    g.add(transform(o, dx=sx, dy=sy), 0)
    T = (sx - 38, sy - 116)
    back = Group()
    for ang, L, droop in ((-150, 58, 30), (-95, 40, 16), (-30, 58, 30)):
        back.add(frond(T, ang, L, 8.5, droop, FROND_D))
    g.add(back.shapes(), 1)
    front = Group()
    for ang, L, droop in ((-125, 50, 28), (-55, 50, 28), (175, 66, 40), (5, 66, 40), (138, 54, 30), (42, 54, 30)):
        front.add(frond(T, ang, L, 9, droop, FROND))
    g.add(front.shapes(), 2)
    nut_at = ((-7, 7), (6, 8), (-1, 14))[:nuts]
    g.add([oval(T[0] + dx, T[1] + dy, 7.4, col=COCO, cel=.8) for dx, dy in nut_at], 3)
    return g.shapes()


# ---------------------------------------------------------------- lifeguard chair (facing the sea)
def chair(col=ORANGE):
    x, y = GROUND["chair"]
    W = 24
    g = Group()
    g.add(shadow(x + W / 2 + 3, y + W / 2 + 3, 20, .6), -10)
    for lx, ly in ((x, y), (x + W, y), (x, y + W), (x + W, y + W)):
        g.add(ISO.box(lx - 1.7, ly - 1.7, 0, 3.4, 3.4, 40, WOOD), lx + ly)
    g.add(ISO.line3([(x, y + W, 4), (x + W, y + W, 34)], WOOD, 1.8), x + y + W + .5)
    g.add(ISO.line3([(x + W, y + W, 4), (x, y + W, 34)], WOOD, 1.8), x + y + W + .6)
    # the ladder up the sea side
    for ly in (y + 6, y + W - 6):
        g.add(ISO.line3([(x + W + 14, ly, 0), (x + W, ly, 40)], WOOD, 2.2), x + y + 2 * W + 6)
    for k in range(1, 5):
        t = k / 5
        g.add(ISO.line3([(x + W + 14 - 14 * t, y + 6, 40 * t), (x + W + 14 - 14 * t, y + W - 6, 40 * t)], WOOD, 1.8), x + y + 2 * W + 6.1)
    g.add(ISO.box(x - 2, y - 2, 40, W + 4, W + 4, 3, col), x + y + W + 10)
    g.add(ISO.box(x + 5, y + 4, 43, W - 9, W - 8, 4, col), x + y + W + 11)
    g.add(ISO.box(x + 2, y + 3, 43, 3, W - 6, 17, col), x + y + W + 10.5)
    for ay in (y + 3, y + W - 5):
        g.add(ISO.box(x + 5, ay, 47, W - 10, 2, 6, col), x + y + W + 11 + (ay - y) * .01)
    for px_, py_ in ((x - 1, y - 1), (x + W + 1, y - 1), (x - 1, y + W + 1), (x + W + 1, y + W + 1)):
        g.add(ISO.line3([(px_, py_, 43), (px_, py_, 66)], METAL, 1.6), x + y + W + 12 + (px_ + py_ - x - y) * .01)
    g.add(ISO.box(x - 5, y - 5, 66, W + 10, W + 10, 3, col), x + y + W + 14)
    for k in range(3):
        s0 = x - 5 + (W + 10) * (2 * k + 1) / 7
        g.add(ISO.flat([(s0, y - 5), (s0 + (W + 10) / 7, y - 5), (s0 + (W + 10) / 7, y + W + 5), (s0, y + W + 5)], 69.05, WHITE),
              x + y + W + 14.1)
        g.add(ISO.face([(s0, y + W + 5, 66), (s0 + (W + 10) / 7, y + W + 5, 66), (s0 + (W + 10) / 7, y + W + 5, 69), (s0, y + W + 5, 69)],
                       "#E8ECF4"), x + y + W + 14.2)
    fx, fy = P(x + W / 2, y + W / 2, 69)
    g.add([line([(fx, fy), (fx, fy - 26)], METAL, 1.8), Sh(crs([(fx + 1, fy - 26), (fx + 17, fy - 23), (fx + 15, fy - 17), (fx + 1, fy - 16)], 4), RED)],
          x + y + W + 15)
    return g.shapes()


# ---------------------------------------------------------------- beach umbrella (red and white; blue; dots)
def canopy(c1, c2, dots=False):
    o = []
    apex = (0, -42)
    k = 8
    for i in range(k):
        a0, a1 = -56 + 112 * i / k, -56 + 112 * (i + 1) / k
        pa, pb = (a0, -6 + abs(a0) * .06), (a1, -6 + abs(a1) * .06)
        mid = ((a0 + a1) / 2, -1 + abs(a0 + a1) * .035)
        base = c1 if (dots or i % 2 == 0) else c2
        t = i / (k - 1)
        col = mix(base, WHITE, .18 * (1 - 2 * t)) if t < .5 else kit.tone(base, 1 - .14 * (t - .45), 1.02)
        o.append(Sh(crs([apex, pb, mid, pa], 6), col))
    if dots:
        for dx, dy, r in ((-36, -12, 4.2), (-18, -24, 4), (2, -14, 4.6), (22, -26, 3.8), (36, -10, 4), (-2, -33, 3), (-44, -2, 3),
                          (16, -4, 3.4), (-24, -5, 3.2), (44, -1, 2.8)):
            o.append(oval(dx, dy, r, col=WHITE, tag="detail"))
    o.append(oval(0, -43, 3.6, col=c1 if c1 != WHITE else RED, cel=.5))
    return o


def umbrella(c1=RED, c2=WHITE, dots=False):
    x, y = GROUND["umbrella"]
    sx, sy = P(x, y)
    g = Group()
    g.add(shadow(x + 2, y + 6, 26, .5), -2)
    g.add(shadow(x, y, 3.5, .9), -1)
    top = (sx + 7, sy - 88)
    g.add([line([(sx, sy), top], "#D9A56C", 3.6), line([(sx + .4, sy - 4), (sx + 1.6, sy - 18)], "#B98356", 3.6)], 0)
    g.add(transform(canopy(c1, c2, dots), dx=top[0], dy=top[1] + 7, rot=9, s=1.15), 1)
    return g.shapes()


# ---------------------------------------------------------------- towel (white with blue stripes: 小變 hides on it)
def towel(col=TOWEL, stripe=BLUE):
    x, y = GROUND["towel"]
    L, D = 44, 24
    g = Group()
    g.add(ISO.box(x, y, 0, L, D, 1, col, top=col), 0)
    for s0 in (5, 9.5, L - 13.5, L - 9):
        g.add(ISO.flat([(x + s0, y), (x + s0 + 2.6, y), (x + s0 + 2.6, y + D), (x + s0, y + D)], 1.02, stripe), 1)
        g.add(ISO.face([(x + s0, y + D, 0), (x + s0 + 2.6, y + D, 0), (x + s0 + 2.6, y + D, 1), (x + s0, y + D, 1)], stripe), 1.1)
    fr = []
    for ex in (x, x + L):
        for k in range(7):
            yy = y + 2 + k * (D - 4) / 6
            a, b = P(ex, yy, .8), P(ex + (-2.6 if ex == x else 2.6), yy, .3)
            fr.append(line([a, b], stripe, 1.2))
    g.add(fr, 2)
    return g.shapes()


# ---------------------------------------------------------------- surfboard (stuck in the sand)
def surfboard(col=TURQ, flowers=False):
    x, y = GROUND["surfboard"]
    sx, sy = P(x, y)
    board = crs([(0, -104), (9, -94), (14, -66), (14, -30), (12, -6), (10, 2), (-10, 2), (-12, -6), (-14, -30), (-14, -66), (-9, -94)], 5)
    o = [Sh(board, col, cel=.6)]
    if flowers:
        for fx, fy, c in ((-4, -82, WHITE), (5, -60, YELLOW), (-5, -38, WHITE), (4, -17, PINK)):
            for a in range(0, 360, 72):
                o.append(oval(fx + 3.6 * math.cos(math.radians(a)), fy + 3.6 * math.sin(math.radians(a)), 2.9, col=c, tag="detail"))
            o.append(oval(fx, fy, 1.8, col=ORANGE, tag="detail"))
    else:
        o.append(Sh(crs([(0, -99), (2.4, -84), (2.4, -6), (-2.4, -6), (-2.4, -84)], 4), WHITE))
        o.append(Sh([(-14, -64), (14, -64), (14, -57), (-14, -57)], RED))
        o.append(Sh([(-14, -53), (14, -53), (14, -49), (-14, -49)], YELLOW))
    o = transform(o, rot=-8)
    o.append(oval(0, 1.5, 17, 5, col=SAND_RIM))
    o.append(oval(-3, 0, 9, 2.6, col=SAND, tag="detail"))
    return shadow(x + 2, y + 2, 9, .7) + transform(o, dx=sx, dy=sy)


# ---------------------------------------------------------------- beach ball
def ball_sprite(R=13.5):
    """A beach ball resting on its bottom point (origin)."""
    cx, cy = 0, -R
    al = math.radians(-28)
    ax, ay = math.sin(al), -math.cos(al)          # the axis through the two poles
    p1, p2 = (cx + R * ax, cy + R * ay), (cx - R * ax, cy - R * ay)
    nx, ny = -ay, ax

    def mer(b):
        return [(p1[0] + (p2[0] - p1[0]) * t + nx * b * R * math.sin(math.pi * t), p1[1] + (p2[1] - p1[1]) * t + ny * b * R * math.sin(math.pi * t))
                for t in (i / 16 for i in range(17))]
    o = [oval(cx, cy, R, col=WHITE)]
    cuts = (-1, -.62, -.2, .2, .62, 1)
    cols = (RED, WHITE, YELLOW, WHITE, BLUE)
    for b0, b1, c in zip(cuts, cuts[1:], cols):
        if c != WHITE:
            o.append(Sh(mer(b0) + mer(b1)[::-1], c))
    o.append(oval(p1[0], p1[1], 3, col=WHITE))
    o.append(oval(cx - R * .42, cy - R * .45, R * .26, R * .16, col=WHITE, rot=-35, op=.85, tag="detail"))
    return o


def ball(s=1.0):
    x, y = GROUND["ball"]
    sx, sy = P(x, y)
    return shadow(x + 1.5, y + 1.5, 8, .9) + transform(ball_sprite(), dx=sx, dy=sy, s=s)


def ball2():
    x, y = GROUND["ball2"]
    sx, sy = P(x, y)
    o = [line(ellp(sx, sy - 2, 21, 7, 30) + [ellp(sx, sy - 2, 21, 7, 30)[0]], WHITE, 2, op=.75)]
    return o + transform(ball_sprite(), dx=sx, dy=sy + 3, rot=40)


# ---------------------------------------------------------------- sand castle (3 towers; 2; a star on its flag)
def castle(towers=3, star=False):
    x, y = GROUND["castle"]
    Sz = 30
    g = Group()
    g.add(shadow(x + Sz / 2 + 3, y + Sz / 2 + 3, 24, .6), -10)
    g.add(ISO.box(x, y, 0, Sz, Sz, 12, CASTLE), 0)
    for k in range(4):     # merlons on the two front walls
        t = 2 + k * 7.6
        g.add(ISO.box(x + t, y + Sz - 3.5, 12, 3.6, 3.5, 3.6, CASTLE), 1 + k * .01)
        g.add(ISO.box(x + Sz - 3.5, y + t, 12, 3.5, 3.6, 3.6, CASTLE), 1 + k * .01)
    # the door on the front-left wall, shells on the walls
    door = [P(x + 11 + 8 * (.5 - .5 * math.cos(math.pi * i / 10)), y + Sz, 6 + 4 * math.sin(math.pi * i / 10)) for i in range(11)]
    door = [P(x + 11, y + Sz, 0)] + door + [P(x + 19, y + Sz, 0)]
    g.add(Sh(door, "#9A6638"), 1.5)
    for (px_, py_, pz), c in (((x + 4, y + Sz, 6), PINK), ((x + 26, y + Sz, 5), WHITE), ((x + Sz, y + 6, 6), WHITE), ((x + Sz, y + 22, 7), PINK)):
        sx, sy = P(px_, py_, pz)
        g.add(oval(sx, sy, 2.4, 1.8, col=c, tag="detail"), 1.6)

    def tower(cx, cy, z0, h, R, d):
        g.add(ISO.cyl(cx, cy, z0, R, h, CASTLE), d)
        for zz in (z0 + h * .35, z0 + h * .7):     # the bucket's rings
            sx, sy = P(cx, cy, zz)
            rx, ry = R * 1.2247 * 1.5, R * .7071 * 1.5
            g.add(line([(sx + rx * math.cos(math.pi * i / 12), sy + ry * math.sin(math.pi * i / 12)) for i in range(13)], CASTLE_D, 1.3), d + .01)
        for a in (0, 90, 180, 270):
            ca, sa = math.cos(math.radians(a + 45)), math.sin(math.radians(a + 45))
            g.add(ISO.box(cx + ca * R * .7 - 1.6, cy + sa * R * .7 - 1.6, z0 + h, 3.2, 3.2, 3.4, CASTLE), d + .02 + (ca + sa) * .001)
        sx, sy = P(cx, cy, z0 + h * .55)
        g.add(Sh(rrect(sx - 2, sy - 3.5, 4, 7, 2), "#8A5A30"), d + .015)
    if towers >= 3:
        tower(x + Sz - 3, y + 3, 0, 24, 5.6, x + y + Sz)
    tower(x + 3, y + Sz - 3, 0, 24, 5.6, x + y + Sz + .5)
    g.add(ISO.box(x + 8, y + 8, 12, 14, 14, 10, CASTLE), x + y + Sz + 1)
    tower(x + 15, y + 15, 22, 14, 6, x + y + Sz + 2)
    fx, fy = P(x + 15, y + 15, 39)
    flag = [Sh(crs([(fx + 1, fy - 24), (fx + 13, fy - 26), (fx + 24, fy - 21), (fx + 23, fy - 11), (fx + 12, fy - 15), (fx + 1, fy - 12)], 4), RED)]
    if star:
        flag.append(Sh(kit.star_pts(5.2, 2.3, fx + 12, fy - 19), WHITE))
    g.add([line([(fx, fy), (fx, fy - 26)], "#8A5A30", 1.8)] + flag, x + y + Sz + 3)
    return g.shapes()


# ---------------------------------------------------------------- bucket and spade
def bucket(col="#5E9BFF"):
    x, y = GROUND["bucket"]
    g = Group()
    g.add(shadow(x + 2, y + 2, 11, .8), -1)
    g.add(ISO.cyl(x, y, 0, 8, 13, col), 0)
    g.add(ISO.disc(x, y, 13.1, 6.3, SAND_WET), 1)
    a, b = P(x - 5.6, y + 5.6, 12.5), P(x + 5.6, y - 5.6, 12.5)
    top = P(x, y, 25)
    g.add(line(crs([a, ((a[0] + top[0]) / 2 - 3, (a[1] + top[1]) / 2 - 2), top, ((b[0] + top[0]) / 2 + 3, (b[1] + top[1]) / 2 - 2), b], 5, closed=False),
               METAL, 1.8), 2)
    # the spade leaning on the bucket
    bx, by = P(x + 15, y + 6)
    hx, hy = P(x + 4, y + 2, 20)
    sp = [line([(bx - 1, by - 8), (hx, hy)], "#FFB020", 3), line([(hx - 4, hy - 1), (hx + 4, hy + 1)], "#FFB020", 3.2),
          Sh(crs([(bx - 7, by - 9), (bx + 4, by - 11), (bx + 6, by - 2), (bx + 1, by + 3), (bx - 5, by + 1)], 4), YELLOW, cel=.4)]
    g.add(sp, 3)
    return g.shapes()


# ---------------------------------------------------------------- crab (walking to the left, one claw up), turtle
CRAB = RED


def crab_sprite(col=CRAB, hat=False):
    dark = kit.tone(col, .78, 1.05)
    o = []
    for k in range(3):        # legs on the right, trailing
        bx, by = 8 + k * 4, -8 + k * 1.5
        o.append(line([(bx, by), (bx + 9, by - 4 + k * 2), (bx + 14, by + 8 - k)], dark, 2.6))
    for k in range(2):        # legs on the left
        bx, by = -8 - k * 4, -6 + k
        o.append(line([(bx, by), (bx - 6, by - 2), (bx - 10, by + 7)], dark, 2.6))
    # the low claw on the right
    o.append(line([(14, -14), (24, -20), (27, -26)], dark, 3.2))
    o.append(Sh(crs([(22, -28), (28, -36), (34, -32), (33, -24), (27, -22)], 4), col, cel=.6))
    o.append(Sh(crs([(30, -30), (36, -38), (38, -32)], 3), col, cel=.4))
    o.append(oval(0, -15, 21, 13, col=col, cel=1.0))
    for ex, ey in ((-9, -36), (2, -38)):     # eyes on stalks
        o.append(line([(ex + 2, -24), (ex, ey + 4)], dark, 2.6))
        o.append(oval(ex, ey, 5.2, col=WHITE))
        o.append(oval(ex - 1.6, ey + .4, 2.6, 3, col=INK))
        o.append(oval(ex - 2.4, ey - .6, .9, col=WHITE, tag="detail"))
    o.append(line(crs([(-14, -12), (-9, -9), (-4, -11)], 4, closed=False), INK, 1.6))
    o.append(oval(-15, -16, 3, 1.8, col="#FFB3C6", op=.85, tag="detail"))
    o.append(oval(6, -20, 3, 2, col=WHITE, op=.5, tag="detail"))
    # the big claw, held up in front
    o.append(line([(-15, -18), (-26, -26), (-30, -36)], dark, 3.6))
    o.append(Sh(crs([(-36, -36), (-27, -38), (-22, -46), (-28, -55), (-38, -52), (-42, -44)], 4), col, cel=.7))
    o.append(Sh(crs([(-40, -52), (-46, -62), (-38, -64), (-33, -56)], 3), col, cel=.5))
    if hat:
        o.append(oval(-2, -45, 15, 4.4, col="#F2C76B", rot=-8))
        o.append(Sh(crs([(-10, -46), (-9, -56), (-2, -60), (6, -56), (6, -47)], 4), "#F2C76B", cel=.6))
        o.append(Sh([(-9.6, -48.5), (6.2, -50.7), (6.2, -47.4), (-9.8, -45.6)], RED))
    return o


def turtle_sprite():
    shell, skin = "#3FAE63", "#9BDB7A"
    o = [Sh(crs([(14, -6), (24, -4), (16, 0)], 3), skin)]
    o.append(Sh(crs([(10, -4), (22, 2), (14, 4)], 3), skin))
    o.append(Sh(crs([(-14, -4), (-22, 2), (-12, 3)], 3), skin))
    o.append(Sh(crs([(-28, -16), (-26, -24), (-34, -30), (-42, -26), (-42, -18), (-34, -12)], 4), skin, cel=.6))
    o.append(oval(-36, -24, 2.2, 2.8, col=INK))
    o.append(oval(-36.8, -25, .8, col=WHITE, tag="detail"))
    o.append(line(crs([(-41, -18), (-38, -16), (-35, -18)], 3, closed=False), INK, 1.3))
    o.append(Sh(crs([(-22, -6), (-20, -20), (-8, -30), (8, -30), (20, -20), (24, -6)], 6), shell, cel=1.0))
    for cx_, cy_ in ((-8, -18), (6, -18), (-1, -25)):
        o.append(Sh([(cx_ + 5 * math.cos(math.radians(a)), cy_ + 4 * math.sin(math.radians(a))) for a in range(0, 360, 60)], "#7ED08A", tag="detail"))
    o.append(Sh(rrect(-24, -8, 50, 5, 2.5), "#E9D98A"))
    return o


def critter(name, sprite, s=1.0, sh_r=13):
    x, y = GROUND[name]
    sx, sy = P(x, y)
    return shadow(x + 1, y + 1, sh_r, .8) + transform(sprite, dx=sx, dy=sy, s=s)


def crab(col=CRAB):
    return critter("crab", crab_sprite(col), 1.05)


def turtle():
    return critter("crab", turtle_sprite(), 1.15)


# ---------------------------------------------------------------- starfish, shells
def starfish(col=ORANGE):
    x, y = GROUND["starfish"]
    sx, sy = P(x, y)
    pts = crs(star_pts(23, 10.5, rot=-90 + 10), 4)
    o = [Sh(pts, col, cel=.5)]
    for i in range(5):
        a = math.radians(-90 + 10 + 72 * i)
        for r in (8, 14):
            o.append(oval(r * math.cos(a), r * math.sin(a), 1.9 if r == 8 else 1.5, col=mix(col, WHITE, .5), tag="detail"))
    o.append(oval(-3.5, -2, 1.6, 2, col=INK))
    o.append(oval(3.5, -2, 1.6, 2, col=INK))
    o.append(line(crs([(-3, 2.5), (0, 4.4), (3, 2.5)], 3, closed=False), INK, 1.2))
    o = squash(o, .64, (0, 0))
    return [oval(sx + 1, sy + 1.5, 21, 7, col="#3B5A7A", tag="shadow", op=.7)] + transform(o, dx=sx, dy=sy - 1)


def shell_sprite(col):
    dark = kit.tone(col, .8, 1.1)
    o = [Sh(crs([(0, 0), (-11, -6), (-13, -15), (-7, -22), (0, -23.5), (7, -22), (13, -15), (11, -6)], 5), col, cel=.5)]
    for a in (-60, -35, -12, 12, 35, 60):
        r = math.radians(a - 90)
        o.append(line([(0, -3), (17 * math.cos(r) * .78, -2 + 19 * math.sin(r))], dark, 1.1))
    o.append(Sh([(-4.5, -1), (4.5, -1), (5.5, 3), (-5.5, 3)], dark))
    return o


SHELLS = ((-24, 2, -20, "#FFB3C6"), (0, 7, 6, "#FFE9C9"), (25, 0, 26, "#FFC07A"))


def shells(which=(0, 1, 2)):
    x, y = GROUND["shells"]
    sx, sy = P(x, y)
    o = []
    for i in which:
        dx, dy, rot, c = SHELLS[i]
        o += [oval(sx + dx + 1, sy + dy + 1, 11, 4, col="#3B5A7A", tag="shadow", op=.7)]
        o += transform(squash(shell_sprite(c), .78, (0, 0)), dx=sx + dx, dy=sy + dy, rot=rot, s=1.1)
    return o


# ---------------------------------------------------------------- boat (bow to the left)
def sail(top, foot, clew, pull):
    """A sail: the luff straight from top to foot, the leech curved from top to clew."""
    return [foot] + quad(top, pull, clew, 10)[::-1][:-1] + [top]


def band_in(poly_pts, y0, y1):
    """The part of a (convex-ish) shape between two heights, as a polygon."""
    out = []
    for yy in (y0, y1):
        xs = []
        m = len(poly_pts)
        for i in range(m):
            (xa, ya), (xb, yb) = poly_pts[i], poly_pts[(i + 1) % m]
            if (ya - yy) * (yb - yy) <= 0 and ya != yb:
                xs.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
        out.append((min(xs), max(xs), yy))
    (a0, a1, ya), (b0, b1, yb) = out
    return [(a0, ya), (a1, ya), (b1, yb), (b0, yb)]


def boat_sprite(sails=YELLOW):
    o = [line(crs([(-58, 2), (-40, -1), (-20, 2), (0, -1), (20, 2), (40, -1), (56, 2)], 5, closed=False), WHITE, 3.4, op=.8)]
    o.append(line([(1, -16), (1, -126)], "#8A5A30", 3))
    main = sail((4, -122), (4, -24), (50, -24), (40, -84))
    jib = sail((-2, -110), (-2, -26), (-44, -26), (-36, -70))
    for s_ in (main, jib):
        o.append(Sh(s_, sails, cel=.35))
        o.append(Sh(band_in(s_, -62, -54), WHITE))
    o.append(line([(3, -23), (50, -23)], "#8A5A30", 2.4))
    o.append(Sh(crs([(1, -128), (16, -124), (1, -119)], 3), RED))
    hull = crs([(-58, -24), (-40, -17), (0, -15), (42, -17), (48, -24), (44, -10), (28, 0), (-30, 0), (-48, -10)], 5)
    o.append(Sh(hull, WHITE, cel=.6))
    o.append(Sh(band_in(hull, -11, -7), BLUE))
    o.append(line(crs([(-54, 3), (-36, 0), (-16, 3), (4, 0), (24, 3), (44, 0), (54, 3)], 5, closed=False), WHITE, 3, op=.9))
    return o


def boat(sails=YELLOW):
    x, y = GROUND["boat"]
    sx, sy = P(x, y)
    return transform(boat_sprite(sails), dx=sx, dy=sy, s=.95)


# ---------------------------------------------------------------- swim ring (floats on the sea)
def swimring(col=RED):
    x, y = GROUND["swimring"]
    sx, sy = P(x, y)
    R, r = 32, 17
    k = .577
    o = [line(ellp(sx, sy + 2, R + 9, (R + 9) * k, 40) + [ellp(sx, sy + 2, R + 9, (R + 9) * k, 40)[0]], WHITE, 2.2, op=.7)]

    def arc(rr, a0, a1, dy=0.0, n_=8):
        return [(sx + rr * math.cos(math.radians(a0 + (a1 - a0) * i / n_)), sy + dy + rr * k * math.sin(math.radians(a0 + (a1 - a0) * i / n_)))
                for i in range(n_ + 1)]
    segs = [(-22.5 + 45 * i, 22.5 + 45 * i, col if i % 2 == 0 else WHITE) for i in range(8)]
    for a0, a1, c in segs:      # the outer side, seen at the front
        lo, hi = max(a0, 0), min(a1, 180)
        if lo < hi:
            o.append(Sh(arc(R, lo, hi) + arc(R, hi, lo, 6), kit.a_dark(c) if c != WHITE else "#D6DEEC"))
        lo, hi = max(a0, 180), min(a1, 360)
        if lo < hi:           # the inside of the hole, at the back
            o.append(Sh(arc(r, lo, hi) + arc(r, hi, lo, 5), kit.a_dark(c) if c != WHITE else "#D6DEEC"))
    for a0, a1, c in segs:
        o.append(Sh(arc(R, a0, a1) + arc(r, a1, a0), c))
    o.append(line(arc((R + r) / 2 + 3, 200, 250, -1), WHITE, 2.6, op=.7))
    return o


# ---------------------------------------------------------------- sky: sun with a face, seagull
def sun(face="smile"):
    cx, cy = SKY_AT["sun"]
    o = []
    for i in range(12):
        a = math.radians(i * 30 + 6)
        L = 46 if i % 2 == 0 else 39
        a1, a2 = a - .14, a + .14
        o.append(Sh([(cx + 30 * math.cos(a1), cy + 30 * math.sin(a1)), (cx + L * math.cos(a), cy + L * math.sin(a)),
                     (cx + 30 * math.cos(a2), cy + 30 * math.sin(a2))], "#FFB534" if i % 2 == 0 else "#FFC93C"))
    o.append(oval(cx, cy, 31, col=YELLOW, cel=.8))
    o.append(oval(cx - 17, cy + 7, 5.5, 3.4, col="#FF9DB6", op=.85, tag="detail"))
    o.append(oval(cx + 17, cy + 7, 5.5, 3.4, col="#FF9DB6", op=.85, tag="detail"))
    if face == "glasses":
        for ex in (-11, 11):
            o.append(Sh(rrect(cx + ex - 9, cy - 11, 18, 12, 5), INK))
            o.append(Sh(crs([(cx + ex - 5, cy - 8), (cx + ex - 1, cy - 9), (cx + ex - 5, cy - 4)], 3), WHITE, op=.7, tag="detail"))
        o.append(line([(cx - 3, cy - 7), (cx + 3, cy - 7)], INK, 2.6))
        o.append(line([(cx - 20, cy - 8), (cx - 28, cy - 11)], INK, 2.2))
        o.append(line([(cx + 20, cy - 8), (cx + 28, cy - 11)], INK, 2.2))
        o.append(Sh(crs([(cx - 11, cy + 6), (cx, cy + 15), (cx + 11, cy + 6), (cx, cy + 9)], 5), INK))
    else:
        for ex in (-10, 10):
            o.append(oval(cx + ex, cy - 5, 3.4, 4.4, col=INK))
            o.append(oval(cx + ex - 1.1, cy - 6.4, 1.2, col=WHITE, tag="detail"))
        o.append(line(crs([(cx - 9, cy + 6), (cx, cy + 12), (cx + 9, cy + 6)], 6, closed=False), INK, 2.6))
    return o


def gull_sprite():
    """A seagull flying to the left, wings up (origin at the middle of its body)."""
    grey, far_grey, tip = "#C9D2E2", "#AEB9CF", "#4E5876"

    def wing(c, col):
        out = [Sh(profile(c, lambda t: 2 + 13 * (1 - t) ** .8), col)]
        k = len(c) * 2 // 3
        out.append(Sh(profile(c[k - 1:], lambda t: 2 + 13 * (1 - (t * (len(c) - k) + k - 1) / (len(c) - 1)) ** .8), tip))
        return out
    o = wing(crs([(6, -4), (14, -18), (24, -27), (38, -30)], 6, closed=False), far_grey)
    o.append(Sh(crs([(12, -1), (25, -6), (26, 1), (14, 4)], 3), "#E4E9F2"))
    o.append(oval(0, 0, 16, 7.5, col=WHITE, cel=.6))
    o.append(oval(-15, -4, 7.4, col=WHITE, cel=.6))
    o.append(Sh(crs([(-21, -6), (-30, -3.5), (-21, -1.5)], 3), "#FFB020"))
    o.append(oval(-17, -6, 1.7, col=INK))
    o += wing(crs([(-2, -3), (-9, -19), (-20, -30), (-36, -33)], 6, closed=False), grey)
    return o


def seagull():
    cx, cy = SKY_AT["seagull"]
    return transform(gull_sprite(), dx=cx, dy=cy, s=1.25)


# ---------------------------------------------------------------- extras: dolphin, fish
def dolphin():
    x, y = GROUND["dolphin"]
    sx, sy = P(x, y)
    col, belly = "#6E9FDC", "#DDEBFA"
    c = crs([(30, -4), (24, -26), (6, -44), (-18, -48), (-36, -38)], 6, closed=False)
    o = [line(ellp(22, 0, 16, 6, 24) + [ellp(22, 0, 16, 6, 24)[0]], WHITE, 2.4, op=.8)]
    body = [Sh(profile(c, lambda t: 6 + 16 * math.sin(math.pi * min(1, t * 1.05)) ** .8), col, cel=.8)]
    body.append(Sh(crs([(27, -8), (36, -2), (40, -12), (30, -12)], 4), col))      # tail flukes
    body.append(Sh(crs([(0, -46), (6, -58), (10, -45)], 4), kit.tone(col, .85)))      # fin
    body.append(Sh(crs([(-8, -38), (-4, -26), (2, -36)], 4), kit.tone(col, .85)))     # flipper
    body.append(Sh(crs([(-34, -34), (-20, -38), (-6, -36), (-18, -32)], 4), belly, tag="detail"))
    body.append(oval(-24, -44, 2, 2.4, col=INK))
    body.append(oval(-24.6, -45, .8, col=WHITE, tag="detail"))
    body.append(line([(-40, -38), (-34, -36)], INK, 1.2))
    for dx, dy, r in ((-40, -6, 2.6), (-34, -16, 2), (-46, -14, 1.8), (34, -10, 2.2), (40, -18, 1.8)):
        body.append(oval(dx, dy, r, col=WHITE, op=.9, tag="detail"))
    return transform(o + body, dx=sx, dy=sy, flip=True)


def fish():
    x, y = GROUND["fish"]
    sx, sy = P(x, y)
    col, fin = ORANGE, "#F27A1E"
    o = [line(ellp(sx + 6, sy, 13, 4.6, 24) + [ellp(sx + 6, sy, 13, 4.6, 24)[0]], WHITE, 2, op=.8)]
    body = [Sh(crs([(8, -13), (21, -22), (23, -15), (19, -6)], 3), fin, cel=.4),
            Sh(crs([(-4, -23), (3, -31), (10, -24)], 3), fin),
            oval(0, -16, 13, 8.5, col=col, rot=-25, cel=.8),
            Sh(tf(rrect(-2, -9, 4.4, 18, 2.2), rot=-25, dx=2, dy=-17), WHITE),
            oval(-7, -20, 3.3, col=WHITE), oval(-7.8, -20, 1.8, col=INK),
            line(crs([(-12, -14), (-9.5, -12.5), (-8, -14)], 3, closed=False), INK, 1.2)]
    o += transform(body, dx=sx, dy=sy)
    for dx, dy, r in ((-14, -6, 1.9), (18, -2, 1.6), (-10, -32, 1.5), (26, -26, 1.3)):
        o.append(oval(sx + dx, sy + dy, r, col=WHITE, op=.9, tag="detail"))
    return o


# ================================================================ lineup (哪一個不一樣？): the crab
def lineup_crab(col=CRAB, hat=False):
    return transform([oval(-4, 0, 40, 6, col="#E6BF80", op=.7)] + crab_sprite(col, hat), s=1.5)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("beach", "海邊", "beach")
    sa.background(background)
    C = kit
    z = {k: int(depth(k)) for k in GROUND}
    sa.thing("palm", "椰子樹", "palm tree", {"palm": palm, "palm_one": lambda: palm(1)},
             [C.gone("椰子樹不見了！"), C.count("palm_one", "椰子變少了！"), C.flip("椰子樹彎向另一邊了！")],
             big=True, z=z["palm"])
    sa.thing("chair", "救生員椅", "lifeguard chair", {"chair": chair, "chair_green": lambda: chair(GREEN)},
             [C.color("chair_green", "救生員椅變成綠色了！"), C.gone("救生員椅不見了！")],
             big=True, z=z["chair"])
    sa.thing("umbrella", "海灘傘", "beach umbrella",
             {"umbrella": umbrella, "umbrella_blue": lambda: umbrella(BLUE), "umbrella_dots": lambda: umbrella(dots=True)},
             [C.color("umbrella_blue", "海灘傘變成藍色了！"), C.pattern("umbrella_dots", "海灘傘變成點點了！"), C.gone("海灘傘不見了！")],
             big=True, z=z["umbrella"])
    sa.thing("towel", "毛巾", "beach towel", {"towel": towel, "towel_pink": lambda: towel(PINK, WHITE)},
             [C.color("towel_pink", "毛巾變成粉紅色了！"), C.gone("毛巾不見了！")],
             big=True, z=z["towel"])
    sa.thing("surfboard", "衝浪板", "surfboard",
             {"surfboard": surfboard, "surfboard_orange": lambda: surfboard(ORANGE), "surfboard_flowers": lambda: surfboard(flowers=True)},
             [C.color("surfboard_orange", "衝浪板變成橘色了！"), C.pattern("surfboard_flowers", "衝浪板變成花花的了！"), C.gone("衝浪板不見了！")],
             z=z["surfboard"])
    sa.thing("castle", "沙堡", "sand castle",
             {"castle": castle, "castle_two": lambda: castle(2), "castle_star": lambda: castle(star=True)},
             [C.gone("沙堡不見了！"), C.count("castle_two", "沙堡少了一座塔！"), C.pattern("castle_star", "沙堡的旗子多了一顆星星！"),
              C.size(1.3, "沙堡變大了！")],
             big=True, z=z["castle"])
    sa.thing("bucket", "小水桶", "bucket and spade", {"bucket": bucket, "bucket_red": lambda: bucket(RED)},
             [C.color("bucket_red", "小水桶變成紅色了！"), C.gone("小水桶不見了！")],
             z=z["bucket"])
    sa.thing("ball", "海灘球", "beach ball", {"ball": ball},
             [C.size(1.6, "海灘球變大了！"), C.gone("海灘球不見了！")],
             z=z["ball"])
    sa.thing("crab", "螃蟹", "crab", {"crab": crab, "crab_blue": lambda: crab(BLUE), "crab_turtle": turtle},
             [C.color("crab_blue", "螃蟹變藍色了！"), C.swap("crab_turtle", "螃蟹變成小烏龜了！"), C.flip("螃蟹轉向另一邊了！")],
             big=True, z=z["crab"])
    sa.thing("starfish", "海星", "starfish", {"starfish": starfish, "starfish_purple": lambda: starfish(PURPLE)},
             [C.color("starfish_purple", "海星變成紫色了！"), C.gone("海星不見了！"), C.size(1.5, "海星變大了！")],
             z=z["starfish"])
    sa.thing("shells", "貝殼", "shells", {"shells": shells, "shells_two": lambda: shells((0, 2))},
             [C.count("shells_two", "貝殼少了一個！"), C.gone("貝殼不見了！")],
             z=z["shells"])
    sa.thing("boat", "帆船", "sailboat", {"boat": boat, "boat_red": lambda: boat(RED)},
             [C.color("boat_red", "帆船的帆變成紅色了！"), C.flip("帆船轉向另一邊了！"), C.gone("帆船不見了！")],
             big=True, z=z["boat"])
    sa.thing("swimring", "救生圈", "swim ring", {"swimring": swimring, "swimring_yellow": lambda: swimring(YELLOW)},
             [C.color("swimring_yellow", "救生圈變成黃色了！"), C.gone("救生圈不見了！")],
             big=True, z=z["swimring"])
    sa.thing("sun", "太陽", "sun", {"sun": sun, "sun_glasses": lambda: sun("glasses")},
             [C.face_("sun_glasses", "太陽戴上太陽眼鏡了！"), C.gone("太陽不見了！")],
             big=True, z=1)
    sa.thing("seagull", "海鷗", "seagull", {"seagull": seagull},
             [C.gone("海鷗不見了！"), C.flip("海鷗轉向另一邊了！"), C.size(1.4, "海鷗變大了！")],
             big=True, z=2)
    sa.extra("dolphin", "海豚", "dolphin", dolphin, "多了一隻海豚！", z=z["dolphin"], big=True)
    sa.extra("fish", "小魚", "fish", fish, "多了一條小魚！", z=z["fish"])
    sa.extra("ball2", "海灘球", "beach ball", ball2, "多了一顆海灘球！", z=z["ball2"])
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"crab_line": lineup_crab, "crab_line_blue": lambda: lineup_crab(BLUE), "crab_line_hat": lambda: lineup_crab(hat=True)}, "螃蟹",
              # the hat is something added (「多了一個」, for 2-3 years too): an art change without a type
              [C.color("crab_line_blue", "這隻螃蟹是藍色的！"), {"kind": "art", "art": "crab_line_hat", "said": "這隻螃蟹戴了帽子！"},
               C.flip("這隻螃蟹轉向另一邊！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((160, 306), 44, "castle", "sand"), ((418, 312), 42, "boat", "blue"), ((316, 272), 40, "ball", "white")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("crab", 0), ("castle", 0), ("umbrella", 1), ("boat", 1), ("shells", 0), ("dolphin", "extra:dolphin")]


if __name__ == "__main__":
    scene().build()
