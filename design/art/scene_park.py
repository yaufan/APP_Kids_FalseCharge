"""公園 (park): the template scene. Copy this file to make another scene.

A floating square of lawn (an isometric tile, 200 x 200 world units, 1.5 px per unit) under a
blue sky: a slide, a swing, a big apple tree, a bench, a balloon, a duck pond, a lamp, a flower
bed, an ice-cream cart, a bicycle, a dog, a cat and a ball; a kite and the sun in the sky.

    background()        sky, clouds, the tile (grass, soil), the sand path, the pond, fences,
                        bushes: everything that never changes (bg.svg, 600 x 600)
    one function per thing and per variant, returning shapes in scene px; each thing's box is
    the bounding box of all its variants (kit.SceneArt)
    PLACE               where each thing stands (scene px): move things here, then run
                        `python3 build.py park` and look at `python3 build.py preview park out.png`
                        (the check fails when puzzles could not find enough differences apart)

Colours that 小變 hides against come from kit.TINT (bush leaves, the sand path, bench wood).
HIDES gives each hide spot as (centre, size, the thing drawn in front of part of him, tint); his z
is that thing's z minus one, so it stays right when things move.
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=186)
TILE = 200
INK = "#2B3158"
WHITE = "#FFFFFF"
METAL = "#7C86A8"
SKY = "#D4F0FF"
GRASS = "#A3E487"
GRASS_RIM = "#7FD06E"
SOIL = "#EBB57E"
STONE = "#E2E7F1"
WATER = "#86D8F7"
WATER_D = "#56B3E2"
LEAF = TINT["leaf"]
SAND = TINT["sand"]
WOOD = TINT["wood"]
RED = "#FF5A5F"
BLUE = "#4C8DFF"
YELLOW = "#FFD84A"
ORANGE = "#FF9838"
PINK = "#FF8FB8"
PURPLE = "#B48CFF"
GREEN = "#5BD08A"
P = ISO.P

# Where things are, in scene px: for things on the ground, the point on the grass they stand on
# (at() turns it into world units); for things in the sky, their centre.
PLACE = {
    "tree": (300, 232),
    "slide": (190, 232),       # the tower's back corner
    "swing": (425, 236),       # the middle of the frame
    "pond": (468, 330),
    "lamp": (56, 334),
    "bench": (374, 322),       # the back-left end of the seat
    "balloon": (262, 364),     # the weight on the grass
    "icecream": (352, 402),    # the cart's back-left corner
    "flowers": (126, 350),     # the bed's back-left corner
    "bike": (300, 456),
    "dog": (446, 396),
    "cat": (192, 398),
    "ball": (318, 318),
    "kite": (98, 40),
    "sun": (530, 62),
    "butterfly": (306, 58),
    "bird": (186, 50),
    "balloon2": (524, 196),
}


def at(name_or_xy):
    """World (x, y) of a ground point given in scene px (a PLACE name or a point)."""
    X, Y = PLACE[name_or_xy] if isinstance(name_or_xy, str) else name_or_xy
    a = (X - ISO.ox) / (kit.C30 * ISO.k)
    b = (Y - ISO.oy) / (kit.S30 * ISO.k)
    return (a + b) / 2, (b - a) / 2


def depth(name, dz=0.0):
    x, y = at(name)
    return x + y + dz


# ================================================================ background
def background():
    g = Group()
    g.add(Sh([(0, 0), (600, 0), (600, 600), (0, 600)], SKY, tag="screen"), -9000)
    for (cx, cy), s in zip(((112, 214), (476, 182), (540, 500), (64, 486)), (1.0, .8, .9, .7)):
        c = tf(crs([(-34, 6), (-38, -4), (-26, -12), (-14, -22), (6, -22), (18, -12), (32, -10), (34, 6)]), s=s, dx=cx, dy=cy)
        g.add([Sh(tf(c, dy=3), "#BFE2F8", only="ab"), Sh(c, WHITE)], -8000)
    # the island's shadow on the air below
    cx, cy = P(TILE / 2, TILE / 2, -20)
    g.add(Sh(ellp(cx, cy + 44, 226, 24), "#3B5A7A", tag="shadow", op=.9), -7000)
    # the tile: soil, then a slab of grass
    g.add(ISO.box(0, 0, -21, TILE, TILE, 15, SOIL)[:2], -6000)      # the soil's top is under the grass
    g.add(ISO.box(0, 0, -6, TILE, TILE, 6, GRASS_RIM, top=GRASS), -5900)
    peb = []
    for i in range(14):
        t = (i + .5) / 14
        if i % 2 == 0:
            x, y, z = 6 + t * (TILE - 12), TILE, -9 - (i * 7 % 10)
        else:
            x, y, z = TILE, 6 + t * (TILE - 12), -9 - (i * 5 % 10)
        sx, sy = P(x, y, z)
        peb.append(oval(sx, sy, 3.8 - (i % 3) * .5, 2.2, col=mix(SOIL, WHITE, .32), tag="detail"))
    g.add(peb, -5800)
    # the sand path: from the front corner up the middle, to the slide and to the pond
    for pts, w in ((PATH_MAIN, 15), (PATH_POND, 11)):
        c = crs([at(p) for p in pts], 5, closed=False)
        g.add(ISO.flat(tube(c, w), 0, mix(SAND, "#D9B26A", .35), only="ab"), -5000)
        g.add(ISO.flat(tube(c, w - 2.8), 0, SAND), -4990)
    for p in PEBBLES:
        sx, sy = P(*at(p))
        g.add(oval(sx, sy, 2.8, 1.6, col=mix(SAND, "#C99A50", .4), tag="detail"), -4980)
    # the pond: stone ring, water with a darker inner wall, ripples, lily pads, reeds
    px, py = at("pond")
    R = 26
    g.add(ISO.cyl(px, py, 0, R + 5, 2.5, STONE), -4000)
    g.add(ISO.disc(px, py, 2.5, R, WATER_D), -3990)
    g.add(ISO.disc(px + 1.4, py + 1.4, 1.2, R - 1.8, WATER), -3980)
    for dx, dy, l_ in ((-13, -1, 10), (4, 13, 8), (9, -12, 7)):
        sx, sy = P(px + dx, py + dy, 1.2)
        g.add(line([(sx - l_, sy), (sx, sy - 2.4), (sx + l_, sy)], WHITE, 1.8, op=.85), -3970)
    for dx, dy in ((-15, 12), (15, -9)):
        sx, sy = P(px + dx, py + dy, 1.3)
        g.add([Sh([(sx, sy)] + ellp(sx, sy, 9, 5, 24)[3:22] + [(sx, sy)], "#6CCB6E"),
               oval(sx - 2, sy - 1, 2.4, col="#FFB3D0", tag="detail")], -3960)
    for x, y in ((px - 22, py - 25), (px - 15, py - 30), (px + 20, py - 28)):
        sx, sy = P(x, y)
        g.add([line([(sx, sy), (sx - 2, sy - 16), (sx + 1, sy - 27)], "#4FAE5C", 2.4),
               Sh(rrect(sx - 1.6, sy - 35, 5, 11, 2.5), WOOD)], x + y)
    # fences along the two back edges (in crayon: white strokes with a grey edge)
    crayon_fence = ([], [])
    for along in ("x", "y"):
        ends = [(6, 4), (194, 4)] if along == "x" else [(4, 6), (4, 194)]
        for zz in (4.5, 9.5):
            if along == "x":
                g.add(ISO.box(6, 3.4, zz, 188, 1.2, 2, WHITE, only="ab"), 6 + zz * .01)
            else:
                g.add(ISO.box(3.4, 6, zz, 1.2, 188, 2, WHITE, only="ab"), 6 + zz * .01)
            ln = [P(x, y, zz + 1) for x, y in ends]
            crayon_fence[0].append(line(ln, "#9AA3BC", 4.6, only="c"))
            crayon_fence[1].append(line(ln, WHITE, 2.4, only="c"))
        for i in range(14):
            a = 6 + i * 14.4
            x, y = (a, 4) if along == "x" else (4, a)
            g.add(ISO.box(x - 1.4, y - 1.4, 0, 2.8, 2.8, 13, WHITE, only="ab"), x + y - 2)
            post = [P(x, y, 0), P(x, y, 13)]
            crayon_fence[0].append(line(post, "#9AA3BC", 6, only="c"))
            crayon_fence[1].append(line(post, WHITE, 3.6, only="c"))
    g.add(crayon_fence[0] + crayon_fence[1], 4)
    # bushes (the leaf colour 小變 hides in), tufts and little flowers
    for p, r in BUSHES:
        x, y = at(p)
        g.add(ISO.shadow(x + 3, y + 3, r * .9), -3000)
        g.add(ISO.ball(x, y, 0, r, LEAF), x + y)
    for p in TUFTS:
        sx, sy = p
        g.add(line([(sx - 4, sy - 5), (sx - 1.5, sy), (sx, sy - 7), (sx + 1.5, sy), (sx + 4, sy - 5)], "#6CC66A", 1.7), -2000)
    for i, p in enumerate(LITTLE_FLOWERS):
        sx, sy = p
        x, y = at(p)
        col = (PINK, YELLOW, WHITE, PURPLE)[i % 4]
        fl = [line([(sx, sy), (sx, sy - 8)], "#4FAE5C", 1.7)]
        fl += [oval(sx + 3.2 * math.cos(math.radians(a)), sy - 9 + 3.2 * math.sin(math.radians(a)), 2.5, col=col, tag="detail")
               for a in range(0, 360, 72)]
        fl.append(oval(sx, sy - 9, 1.8, col="#FFE27A", tag="detail"))
        g.add(fl, x + y)
    return g.shapes()


# scenery, in scene px on the grass
PATH_MAIN = [(300, 478), (296, 440), (272, 404), (236, 384), (196, 362), (170, 334), (160, 306)]
PATH_POND = [(272, 404), (318, 392), (370, 378), (412, 362), (432, 352)]
PEBBLES = [(298, 456), (262, 396), (214, 374), (180, 346), (342, 386), (398, 368)]
BUSHES = [((106, 328), 9), ((122, 320), 7), ((134, 332), 6), ((84, 344), 6), ((442, 262), 8), ((456, 270), 6), ((376, 462), 8), ((390, 452), 6),
          ((230, 228), 7)]
TUFTS = [(250, 300), (196, 286), (350, 300), (420, 300), (300, 330), (240, 448), (460, 400), (140, 400), (504, 352), (380, 420),
         (330, 466)]
LITTLE_FLOWERS = [(206, 262), (218, 270), (340, 264), (504, 330), (512, 342), (110, 382), (262, 456), (450, 418), (430, 288)]


# ================================================================ things
def shadow(x, y, r, op=1.0):
    return ISO.shadow(x, y, r, op=op)


# ---------------------------------------------------------------- tree
def tree(crown=LEAF, apples=3):
    x, y = at("tree")
    g = Group()
    g.add(shadow(x + 3, y + 3, 22), -1)
    g.add(ISO.cyl(x, y, 0, 6.5, 30, WOOD), 0)
    blobs = [(x - 13, y + 7, 34, 18), (x + 9, y - 13, 36, 18), (x, y, 46, 27), (x + 11, y + 11, 30, 16)]
    for i, (bx, by, bz, br) in enumerate(sorted(blobs, key=lambda b: b[0] + b[1] + b[2] * .01)):
        g.add(ISO.ball(bx, by, bz - br, br, crown), 1 + i)
    for i, (fx, fy, fz) in enumerate(((x + 6, y + 16, 48), (x + 18, y - 2, 44), (x - 8, y + 22, 34))[:apples]):
        sx, sy = P(fx, fy, fz)
        g.add([oval(sx, sy, 5.4, col=RED, cel=.6), line([(sx, sy - 5), (sx + 1.5, sy - 8.5)], "#7A5232", 1.4)], 10 + i)
    return g.shapes()


# ---------------------------------------------------------------- slide
def slide(chute=YELLOW):
    x0, y0 = at("slide")
    g = Group()
    g.add(shadow(x0 + 14, y0 + 50, 22, .8), -50)
    post = "#5E9BFF"
    for px, py in ((x0, y0), (x0 + 22, y0), (x0, y0 + 22), (x0 + 22, y0 + 22)):
        g.add(ISO.box(px, py, 0, 3, 3, 66, post), px + py)
    for k in range(5):     # ladder up the left side
        g.add(ISO.box(x0 - 14 + k * 2.6, y0 + 2, k * 8.5 + 5, 2, 20, 2, post), x0 + y0 - 6 + k)
    for yy in (y0 + 1, y0 + 21):
        g.add(ISO.line3([(x0 - 15, yy + 1, 2), (x0 - 1, yy + 1, 44)], post, 2.4), x0 + yy - 4)
    g.add(ISO.box(x0, y0, 42, 25, 25, 4, "#FF7A7A"), x0 + y0 + 24)
    for zz in (50, 56):
        g.add(ISO.box(x0 + 24, y0 + 1, zz, 1.4, 23, 1.6, post), x0 + y0 + 26)
    g.add(ISO.pyramid(x0 - 3, y0 - 3, 66, 31, 31, 18, "#FF7A7A"), x0 + y0 + 50)
    g.add(ISO.ramp(x0 + 3, y0 + 25, y0 + 82, 45, 3, 19, 4, chute), x0 + y0 + 60)
    rail = kit.tone(chute, .9, 1.1)
    for xx in (x0 + 3, x0 + 19.6):
        g.add(ISO.line3([(xx + 1.2, y0 + 25, 49), (xx + 1.2, y0 + 82, 7)], rail, 2.4), x0 + y0 + 61)
    return g.shapes()


# ---------------------------------------------------------------- swing
def swing(frame=RED):
    L = 50
    xm, y0 = at("swing")
    x0 = xm - L / 2
    g = Group()
    g.add(shadow(x0 + L / 2, y0 + 10, 20, .7), -10)
    for xx in (x0, x0 + L):
        for dy in (-9, 9):
            g.add(ISO.line3([(xx, y0 + dy, 0), (xx, y0, 46)], frame, 3.4), xx + y0 + dy * .5)
    g.add(ISO.box(x0 - 2, y0 - 1.6, 45, L + 4, 3.2, 3.4, frame), x0 + y0 + 30)
    for sx in (x0 + 12, x0 + 36):
        for dx in (-5, 5):
            g.add(ISO.line3([(sx + dx, y0, 45), (sx + dx, y0, 12)], METAL, 1.0), sx + y0 + 1)
        g.add(ISO.box(sx - 6.5, y0 - 3.5, 9, 13, 7, 2.6, YELLOW), sx + y0 + 2)
    return g.shapes()


# ---------------------------------------------------------------- bench (wood: 小變 hides behind its back)
def bench(col=WOOD):
    x, y = at("bench")
    g = Group()
    g.add(shadow(x + 24, y + 9, 18, .8), -10)
    for lx in (x + 4, x + 42):
        g.add(ISO.box(lx, y + 3, 0, 3, 10, 9, METAL), x + y + 10)
        g.add(ISO.box(lx, y - 1, 9, 3, 3, 14, METAL), x + y + 9)
    g.add(ISO.box(x, y, 9, 50, 14, 3, col), x + y + 21)
    g.add(ISO.box(x, y - 2.5, 14, 50, 2.6, 5, col), x + y + 18)
    g.add(ISO.box(x, y - 2.5, 20.5, 50, 2.6, 5, col), x + y + 18.5)
    return g.shapes()


# ---------------------------------------------------------------- balloon (tied to a little weight on the grass)
def balloon_sprite(col):
    lt_ = mix(col, WHITE, .1)
    return [Sh(crs([(-5, 1), (5, 1), (0, -9)], 4), col),
            Sh(crs([(0, -6), (14, -12), (22, -30), (18, -50), (0, -60), (-18, -50), (-22, -30), (-14, -12)]), lt_, cel=1.0),
            oval(-9, -42, 4, 7.5, col=WHITE, rot=25, op=.8, tag="detail")]


def balloon(col=RED):
    x, y = at("balloon")
    g = Group()
    g.add(shadow(x, y, 7, .8), -1)
    g.add(ISO.box(x - 3, y - 3, 0, 6, 6, 5, "#9AA6C2"), 0)
    tie = P(x, y, 5)
    top = P(x - 10, y + 10, 62)
    mid = ((tie[0] + top[0]) / 2 + 8, (tie[1] + top[1]) / 2)
    g.add(line(crs([tie, mid, top], 8, closed=False), "#7C86A8", 1.3), 1)
    g.add(transform(balloon_sprite(col), dx=top[0], dy=top[1], s=1.55), 2)
    return g.shapes()


# ---------------------------------------------------------------- lamp
def lamp():
    x, y = at("lamp")
    g = Group()
    g.add(shadow(x + 2, y + 2, 6, .8), -1)
    g.add(ISO.cyl(x, y, 0, 4.5, 3, METAL), 0)
    g.add(ISO.cyl(x, y, 3, 1.9, 58, METAL), 1)
    g.add(ISO.box(x - 4, y - 4, 61, 8, 8, 2, "#5A6488"), 2)
    sx, sy = P(x, y, 69)
    g.add([oval(sx, sy, 15, col="#FFF2B0", tag="glow"), oval(sx, sy, 6.4, col="#FFE58A", cel=.6)], 3)
    g.add(ISO.pyramid(x - 5, y - 5, 75, 10, 10, 6, "#5A6488"), 4)
    return g.shapes()


# ---------------------------------------------------------------- ducks on the pond (they float: no shadow)
def duck_sprite(hat=False, col=YELLOW):
    """A rubber duck facing left, origin on the water line (about 106 x 90 units with the hat)."""
    dark = kit.tone(col, .9, 1.05) if col != YELLOW else "#F6B92E"
    o = [Sh(crs([(-36, -16), (-28, -3), (-6, 2), (22, 0), (40, -10), (50, -31), (44, -34), (34, -27), (12, -29),
                 (-14, -31), (-30, -27)]), col, cel=1.0)]
    o.append(Sh(crs([(0, -19), (14, -26), (27, -22), (21, -11), (5, -10)]), dark))
    o.append(oval(-18, -48, 19.5, col=col, cel=1.0))
    o.append(Sh(crs([(-33, -47), (-49, -46), (-56, -40), (-49, -34), (-33, -37)]), ORANGE, cel=.6))
    o.append(oval(-24, -53, 3.7, 4.7, col=INK))
    o.append(oval(-25.3, -54.8, 1.5, col=WHITE, tag="detail"))
    o.append(oval(-12, -41, 4.6, 2.8, col="#FF9DB6", op=.75, tag="detail"))
    if hat:
        o.append(Sh(crs([(-32, -64), (-30, -80), (-18, -88), (-5, -81), (-4, -64)]), RED, cel=1.0))
        o.append(Sh([(-31.4, -66.5), (-31, -73), (-4.6, -73), (-4.2, -66.5)], WHITE))
        o.append(oval(-18, -64, 23, 6.2, col=RED, rot=-6, cel=.6))
    return o


DUCKS = ((-12, 6), (6, -10), (14, 12))       # offsets from the pond centre


def ducks(n_=3):
    px, py = at("pond")
    g = Group()
    for i, (dx, dy) in enumerate(DUCKS):
        if n_ == 2 and i == 1:
            continue
        x, y = px + dx, py + dy
        sx, sy = P(x, y, 1.5)
        g.add([oval(sx + 2, sy + .5, 13, 3, col=WHITE, op=.5)], x + y - .1)
        g.add(transform(duck_sprite(), dx=sx, dy=sy, s=.36), x + y)
    return g.shapes()


# ---------------------------------------------------------------- flower bed
FLOWER_AT = (6, 15, 24, 33, 42)


def flowers(col=RED, which=FLOWER_AT):
    x, y = at("flowers")
    g = Group()
    g.add(ISO.box(x, y, 0, 48, 14, 7, "#E8946A"), x + y)
    g.add(ISO.flat([(x + 2, y + 2), (x + 46, y + 2), (x + 46, y + 12), (x + 2, y + 12)], 7.1, "#9A6A48"), x + y + .1)
    centre = "#FFE27A" if col != YELLOW else ORANGE
    for i, fx in enumerate(FLOWER_AT):
        if fx not in which:
            continue
        sx, sy = P(x + fx, y + 7, 7)
        h = 22 + (i % 2) * 6
        o = [line([(sx, sy), (sx + 1, sy - h)], "#4FAE5C", 2.2)]
        o.append(Sh(crs([(sx, sy - 6), (sx - 8, sy - 12), (sx - 3, sy - 9)], 5), "#5BC46A"))
        petals = [oval(sx + 1 + 5.4 * math.cos(math.radians(a)), sy - h + 5.4 * math.sin(math.radians(a)), 4.2, col=col, cel=.4)
                  for a in range(-90, 270, 72)]
        o += petals
        o.append(oval(sx + 1, sy - h, 3.3, col=centre, tag="detail"))
        g.add(o, x + y + 1 + i)
    return g.shapes()


# ---------------------------------------------------------------- ice-cream cart
def umbrella_sprite(c1, c2, dots=False):
    o = []
    apex = (0, -34)
    k = 6
    for i in range(k):
        a0, a1 = -42 + 84 * i / k, -42 + 84 * (i + 1) / k
        pa, pb = (a0, -6 + abs(a0) * .05), (a1, -6 + abs(a1) * .05)
        mid = ((a0 + a1) / 2, -2 + abs(a0 + a1) * .03)
        base = c1 if (dots or i % 2 == 0) else c2
        t = i / (k - 1)
        col = mix(base, WHITE, .2 * (1 - t)) if t < .5 else kit.tone(base, 1 - .12 * (t - .4), 1.02)
        o.append(Sh(crs([apex, pb, mid, pa], 6), col))
    if dots:
        for dx, dy, r in ((-26, -10, 3.4), (-12, -20, 3.2), (4, -12, 3.6), (18, -22, 3), (28, -8, 3.2), (-2, -27, 2.6), (-30, -3, 2.4), (12, -4, 2.8)):
            o.append(oval(dx, dy, r, col=WHITE, tag="detail"))
    o.append(oval(0, -35, 2.8, col=METAL))
    return o


def cone_sprite():
    return [Sh([(-7, -14), (7, -14), (0, 6)], "#E8B068"),
            line([(-4, -10), (3, -2)], "#C98E5A", 1.2), line([(4, -10), (-3, -2)], "#C98E5A", 1.2),
            oval(0, -19, 8.5, col="#FF9EC7", cel=.7), oval(-2, -28, 6.5, col="#FFF3D6", cel=.7), oval(1, -34, 2.4, col=RED)]


def icecream(body="#FF9EC7", dots=False):
    x, y = at("icecream")
    c2 = WHITE
    g = Group()
    g.add(shadow(x + 14, y + 8, 20, .8), -1)
    g.add(ISO.box(x, y, 6, 30, 16, 20, body), x + y)
    g.add(ISO.box(x - .2, y + 16, 15, 30.4, .4, 4, WHITE, left=WHITE), x + y + .05)     # stripe on the front
    for wx in (x + 6, x + 24):
        sx, sy = P(wx, y + 16.5, 6)
        g.add([oval(sx, sy, 6.4, col="#3E4566"), oval(sx, sy, 2.6, col="#DDE3F0")], x + y + .2)
    g.add(ISO.line3([(x + 30, y + 8, 24), (x + 42, y + 8, 30)], METAL, 1.8), x + y + .3)
    g.add(ISO.line3([(x + 15, y + 8, 26), (x + 15, y + 8, 64)], METAL, 1.6), x + y + .4)
    sx, sy = P(x + 15, y + 8, 66)
    g.add(transform(umbrella_sprite(body, c2, dots), dx=sx, dy=sy + 28, s=1.05), x + y + .5)
    cx, cy = P(x + 22, y + 4, 26)
    g.add(transform(cone_sprite(), dx=cx, dy=cy - 6, s=.9), x + y + .45)
    return g.shapes()


# ---------------------------------------------------------------- bicycle (side view, facing left)
def bike_sprite(frame=BLUE):
    o = []
    for wx in (-26, 26):
        o += [oval(wx, -15, 15, col="#3E4566"), oval(wx, -15, 11.2, col="#E9EEF6"), oval(wx, -15, 3, col=METAL)]
        for a in range(0, 180, 45):
            ca, sa = math.cos(math.radians(a)) * 11, math.sin(math.radians(a)) * 11
            o.append(line([(wx - ca, -15 - sa), (wx + ca, -15 + sa)], "#B7C0D6", .9))
    F, R, B, S, H = (-26, -15), (26, -15), (2, -14), (12, -38), (-17, -40)
    for a_, b_ in ((R, B), (B, S), (S, R), (B, H), (S, H)):
        o.append(line([a_, b_], frame, 4.2))
    o.append(line([H, F], frame, 3.6))
    o.append(line([H, (-15, -48), (-24, -50)], "#3E4566", 3.2))
    o.append(Sh(crs([(5, -41), (18, -42), (21, -39), (8, -38)], 4), "#3E4566"))
    o.append(line([(2, -14), (7, -6)], "#3E4566", 2.4))
    o.append(oval(B[0], B[1], 3.6, col=METAL))
    # a basket at the front
    o.append(Sh([(-36, -54), (-16, -54), (-18, -42), (-34, -42)], "#E8B068"))
    o.append(line([(-35, -50), (-17, -50)], "#C98E5A", 1.2))
    o.append(line([(-34, -46), (-18, -46)], "#C98E5A", 1.2))
    return o


def bike(frame=BLUE):
    x, y = at("bike")
    sx, sy = P(x, y)
    return shadow(x, y, 20, .7) + transform(bike_sprite(frame), dx=sx, dy=sy, s=1.3)


# ---------------------------------------------------------------- dog, cat, rabbit, ball (sprites facing left)
def dog_sprite(col="#D9A066"):
    ear = kit.tone(col, .72, 1.1) if col != WHITE else "#C98E5A"
    light = mix(col, WHITE, .5)
    o = [Sh(tube(crs([(20, -24), (28, -34), (32, -46)], 6, closed=False), 6, 4), col, cel=.5)]
    for lx in (-14, -6, 8, 16):
        o.append(Sh(rrect(lx - 3.4, -16, 6.8, 16, 3.2), col if lx in (-6, 16) else kit.tone(col, .9) if col != WHITE else "#ECE8E2", cel=.3))
    o.append(oval(0, -22, 23, 12, col=col, cel=1.0))
    o.append(oval(-4, -18, 12, 5, col=light, tag="detail"))
    o.append(Sh(rrect(-28, -32, 8, 4, 2), RED))
    o.append(oval(-24, -40, 13.5, col=col, cel=1.0))
    o.append(oval(-35, -35, 8, 6, col=light, cel=.4))
    o.append(oval(-41.5, -38, 3, 2.6, col=INK))
    o.append(oval(-27, -43, 2.4, 2.8, col=INK))
    o.append(oval(-27.8, -44, .9, col=WHITE, tag="detail"))
    o.append(Sh(crs([(-20, -52), (-10, -50), (-8, -36), (-13, -30), (-18, -38)]), ear, cel=.5))
    o.append(line(crs([(-38, -30), (-34, -28), (-30, -30)], 4, closed=False), INK, 1.4))
    return o


def cat_sprite(col="#FFA552"):
    dark = "#E8843A"
    o = [Sh(tube(crs([(12, -3), (26, -6), (30, -20), (24, -30)], 8, closed=False), 6.5, 4.2), col, cel=.6)]
    o.append(Sh(crs([(-14, 0), (14, 0), (17, -14), (10, -30), (-6, -32), (-15, -18)]), col, cel=1.0))
    o.append(oval(-7, -14, 6, 11, col="#FFE3BF"))
    for lx in (-10, -3):
        o.append(Sh(rrect(lx - 2.6, -12, 5.2, 12, 2.6), col, cel=.3))
    for k in range(3):
        o.append(line([(6 + k * 4, -27 + k), (10 + k * 4, -20 + k)], dark, 1.8))
    o.append(Sh(crs([(-17, -42), (-15, -58), (-8, -48)], 4), col))
    o.append(Sh(crs([(-4, -48), (2, -60), (5, -44)], 4), col))
    o.append(Sh(crs([(-15.6, -46), (-14.6, -54), (-10.4, -48)], 4), "#FFB3C6", tag="detail"))
    o.append(oval(-7, -40, 13, 11.5, col=col, cel=1.0))
    o.append(oval(-13, -41, 2.2, 3, col=INK))
    o.append(oval(-3, -41, 2.2, 3, col=INK))
    o.append(Sh(crs([(-10, -36), (-6, -36), (-8, -33.5)], 3), "#FF8FA8", tag="detail"))
    o.append(oval(-16, -35, 3, 1.8, col="#FF9DB6", op=.8, tag="detail"))
    for k in (-1, 1):
        o.append(line([(-14, -34 + k * 1.5), (-24, -35 + k * 3)], "#C9A27A", .9))
    return o


def rabbit_sprite():
    col, inner = "#F4F1EC", "#FFB3C6"
    o = [oval(15, -10, 6, col=WHITE, cel=.4)]
    o.append(Sh(crs([(-14, 0), (14, 0), (16, -14), (8, -28), (-6, -30), (-15, -16)]), col, cel=1.0))
    for lx in (-10, -3):
        o.append(Sh(rrect(lx - 3, -9, 6, 9, 3), col, cel=.3))
    for ex, rot in ((-12, -10), (-1, 8)):
        o.append(Sh(tf(rrect(-4.5, -30, 9, 30, 4.5), rot=rot, dx=ex, dy=-46), col, cel=.6))
        o.append(Sh(tf(rrect(-2.2, -26, 4.4, 22, 2.2), rot=rot, dx=ex, dy=-46), inner, tag="detail"))
    o.append(oval(-7, -38, 12.5, 11, col=col, cel=1.0))
    o.append(oval(-12, -39, 2.2, 3, col=INK))
    o.append(oval(-2, -39, 2.2, 3, col=INK))
    o.append(Sh(crs([(-9, -34), (-5, -34), (-7, -31.5)], 3), "#FF8FA8", tag="detail"))
    o.append(oval(-15, -33, 3, 1.8, col="#FF9DB6", op=.8, tag="detail"))
    return o


def critter(name, sprite, s=1.0):
    x, y = at(name)
    sx, sy = P(x, y)
    return shadow(x + 1, y + 1, 13, .8) + transform(sprite, dx=sx, dy=sy, s=s)


def ball(col=RED, dots=False):
    x, y = at("ball")
    sx, sy = P(x, y)
    R = 9 * ISO.k
    cx, cy = sx, sy - R
    o = shadow(x + 1.5, y + 1.5, 7, .9) + [oval(cx, cy, R, col=col, cel=1.0)]
    if dots:
        for dx, dy, r in ((-5, -4, 3), (5, 3, 3.2), (-3, 7, 2.4), (6, -7, 2.2), (-8, 3, 1.8)):
            o.append(oval(cx + dx, cy + dy, r, col=WHITE, tag="detail"))
    else:
        band = crs([(-R + 1, -2), (0, 2.5), (R - 1, -2), (R - 1.4, 3.4), (0, 8), (-R + 1.4, 3.4)], 6)
        o.append(Sh(tf(band, dx=cx, dy=cy), WHITE))
    o.append(oval(cx - 4.5, cy - 5, 3, 2, col=WHITE, rot=-30, op=.8, tag="detail"))
    return o


# ---------------------------------------------------------------- sky things (flat sprites)
def kite(c1=YELLOW, c2=RED, dots=False):
    cx, cy = PLACE["kite"]
    top, right, bot, left = (0, -44), (31, -6), (0, 50), (-31, -6)
    o = []
    tail = crs([(0, 50), (10, 62), (22, 64), (32, 58), (44, 64)], 6, closed=False)
    o.append(line(tail, METAL, 1.4))
    for i, k in enumerate((6, 13, 20)):
        x, y = tail[k]
        col = (c2, c1, c2)[i]
        o.append(Sh([(x, y), (x - 8, y - 5), (x - 7, y + 4)], col))
        o.append(Sh([(x, y), (x + 8, y - 4), (x + 7, y + 5)], col))
    o.append(line(crs([(0, 50), (-6, 64), (-4, 76), (-12, 86)], 6, closed=False), METAL, 1.0, op=.8))
    c = (0, -6)
    if dots:
        o.append(Sh([top, right, bot, left], c1, cel=.3))
        for dx, dy, r in ((-8, -22, 4.2), (9, -16, 3.6), (-14, -2, 3.4), (12, 6, 4), (-2, 12, 3.8), (2, 32, 3.2), (-3, -6, 3)):
            o.append(oval(dx, dy, r, col=WHITE, tag="detail"))
    else:
        o.append(Sh([top, right, c], c1))
        o.append(Sh([right, bot, c], c2))
        o.append(Sh([bot, left, c], c1))
        o.append(Sh([left, top, c], c2))
    o.append(line([top, bot], "#7A5232", 1.6))
    o.append(line([left, right], "#7A5232", 1.6))
    return transform(o, dx=cx, dy=cy, rot=-14, s=.78, about=(0, 0))


def sun(face="smile"):
    cx, cy = PLACE["sun"]
    o = []
    for i in range(10):
        a = math.radians(i * 36 + 8)
        a1, a2 = a - .17, a + .17
        o.append(Sh([(cx + 30 * math.cos(a1), cy + 30 * math.sin(a1)), (cx + 44 * math.cos(a), cy + 44 * math.sin(a)),
                     (cx + 30 * math.cos(a2), cy + 30 * math.sin(a2))], "#FFC93C"))
    o.append(oval(cx, cy, 31, col=YELLOW, cel=.8))
    o.append(oval(cx - 16, cy + 6, 5.5, 3.4, col="#FF9DB6", op=.85, tag="detail"))
    o.append(oval(cx + 16, cy + 6, 5.5, 3.4, col="#FF9DB6", op=.85, tag="detail"))
    if face == "smile":
        for ex in (-10, 10):
            o.append(line([(cx + ex - 5, cy - 3), (cx + ex, cy - 8), (cx + ex + 5, cy - 3)], INK, 2.6))
        o.append(line(crs([(cx - 9, cy + 6), (cx, cy + 12), (cx + 9, cy + 6)], 6, closed=False), INK, 2.6))
    else:
        for ex in (-10, 10):
            o.append(oval(cx + ex, cy - 5, 3.6, 4.6, col=INK))
            o.append(oval(cx + ex - 1.2, cy - 6.6, 1.3, col=WHITE, tag="detail"))
        o.append(oval(cx, cy + 9, 4.6, 5.6, col=INK))
    return o


def butterfly():
    cx, cy = PLACE["butterfly"]
    o = [oval(-13, -10, 17, 13, col=PINK, rot=-25, cel=.6), oval(13, -10, 17, 13, col=PINK, rot=25, cel=.6),
         oval(-10, 9, 11, 9, col=PURPLE, rot=20, cel=.5), oval(10, 9, 11, 9, col=PURPLE, rot=-20, cel=.5)]
    for dx, dy, r in ((-16, -12, 4.4), (16, -12, 4.4), (-11, 10, 3), (11, 10, 3)):
        o.append(oval(dx, dy, r, col=WHITE, tag="detail", op=.9))
    o.append(Sh(rrect(-2.6, -16, 5.2, 32, 2.6), INK))
    o.append(line([(-1, -15), (-6, -26), (-9, -27)], INK, 1.4))
    o.append(line([(1, -15), (6, -26), (9, -27)], INK, 1.4))
    return transform(o, dx=cx, dy=cy, rot=-12, s=1.12)


def bird():
    cx, cy = PLACE["bird"]
    col = "#5AA9F0"
    o = [Sh(crs([(10, -2), (24, -10), (20, 2)], 4), kit.tone(col, .85)),
         oval(0, 0, 14, 11, col=col, cel=.8),
         Sh(crs([(-4, -4), (8, -14), (12, -4)], 4), kit.tone(col, .85), cel=.4),
         oval(-6, 3, 7, 5, col="#EAF4FF", tag="detail"),
         Sh([(-14, -3), (-21, 0), (-14, 2)], ORANGE),
         oval(-8, -4, 1.9, col=INK)]
    return transform(o, dx=cx, dy=cy, s=1.2)


def balloon2():
    cx, cy = PLACE["balloon2"]
    o = [line(crs([(0, 0), (5, 10), (-3, 20), (1, 28)], 6, closed=False), METAL, 1.3)]
    o += balloon_sprite(YELLOW)
    return transform(o, dx=cx, dy=cy + 24, s=1.6)


# ================================================================ lineup (哪一個不一樣？): the rubber duck
def lineup_duck(hat=False, col=YELLOW):
    return transform([oval(4, 1, 52, 7, col="#86D8F7", op=.6)] + duck_sprite(hat, col), s=1.6)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("park", "公園", "park")
    sa.background(background)
    C = kit
    sa.thing("tree", "大樹", "tree", {"tree": tree, "tree_autumn": lambda: tree(ORANGE), "tree_apples": lambda: tree(apples=1)},
             [C.color("tree_autumn", "大樹變成橘色了！"), C.count("tree_apples", "樹上的蘋果變少了！"), C.size(.75, "大樹變小了！")],
             big=True, z=int(depth("tree")))
    sa.thing("slide", "溜滑梯", "slide", {"slide": slide, "slide_green": lambda: slide(GREEN)},
             [C.color("slide_green", "溜滑梯變成綠色了！"), C.gone("溜滑梯不見了！"), C.flip("溜滑梯轉向另一邊了！")],
             big=True, z=int(depth("slide", 20)))
    sa.thing("swing", "鞦韆", "swing", {"swing": swing, "swing_blue": lambda: swing(BLUE)},
             [C.color("swing_blue", "鞦韆變成藍色了！"), C.gone("鞦韆不見了！")],
             big=True, z=int(depth("swing")))
    sa.thing("bench", "長椅", "bench", {"bench": bench, "bench_blue": lambda: bench(BLUE)},
             [C.color("bench_blue", "長椅變成藍色了！"), C.gone("長椅不見了！"), C.flip("長椅轉向另一邊了！")],
             big=True, z=int(depth("bench")))
    sa.thing("balloon", "氣球", "balloon", {"balloon": balloon, "balloon_blue": lambda: balloon(BLUE)},
             [C.color("balloon_blue", "氣球變藍色了！"), C.gone("氣球不見了！"), C.size(1.3, "氣球變大了！")],
             big=True, z=int(depth("balloon")))
    sa.thing("ducks", "小鴨子", "ducks", {"ducks": ducks, "ducks_two": lambda: ducks(2)},
             [C.count("ducks_two", "小鴨子少了一隻！"), C.flip("小鴨子轉向另一邊了！")],
             z=int(depth("pond")))
    sa.thing("lamp", "路燈", "street lamp", {"lamp": lamp},
             [C.gone("路燈不見了！"), C.size(1.3, "路燈變高了！")], z=int(depth("lamp")))
    sa.thing("icecream", "冰淇淋車", "ice-cream cart",
             {"icecream": icecream, "icecream_blue": lambda: icecream("#7FC4FF"), "icecream_dots": lambda: icecream(dots=True)},
             [C.color("icecream_blue", "冰淇淋車變成藍色了！"), C.pattern("icecream_dots", "陽傘變成點點了！"), C.gone("冰淇淋車不見了！")],
             big=True, z=int(depth("icecream")))
    sa.thing("flowers", "花", "flowers",
             {"flowers": flowers, "flowers_yellow": lambda: flowers(YELLOW), "flowers_fewer": lambda: flowers(which=(6, 24, 42))},
             [C.color("flowers_yellow", "花變成黃色了！"), C.count("flowers_fewer", "花少了兩朵！"), C.gone("花不見了！")],
             big=True, z=int(depth("flowers")))
    sa.thing("bike", "腳踏車", "bicycle", {"bike": bike, "bike_red": lambda: bike(RED)},
             [C.color("bike_red", "腳踏車變成紅色了！"), C.flip("腳踏車轉向另一邊了！"), C.gone("腳踏車不見了！")],
             big=True, z=int(depth("bike")))
    sa.thing("dog", "小狗", "dog", {"dog": lambda: critter("dog", dog_sprite(), 1.2), "dog_white": lambda: critter("dog", dog_sprite(WHITE), 1.2)},
             [C.color("dog_white", "小狗變成白色了！"), C.gone("小狗不見了！"), C.flip("小狗轉向另一邊了！")],
             z=int(depth("dog")))
    sa.thing("cat", "小貓", "cat", {"cat": lambda: critter("cat", cat_sprite(), 1.2), "cat_rabbit": lambda: critter("cat", rabbit_sprite(), 1.2)},
             [C.swap("cat_rabbit", "小貓變成小兔子了！"), C.flip("小貓轉向另一邊了！"), C.gone("小貓不見了！")],
             z=int(depth("cat")))
    sa.thing("ball", "球", "ball", {"ball": ball, "ball_blue": lambda: ball(BLUE), "ball_dots": lambda: ball(dots=True)},
             [C.color("ball_blue", "球變成藍色了！"), C.pattern("ball_dots", "球變成點點了！"), C.size(1.5, "球變大了！")],
             z=int(depth("ball")))
    sa.thing("kite", "風箏", "kite", {"kite": kite, "kite_blue": lambda: kite(BLUE, GREEN), "kite_dots": lambda: kite(RED, RED, True)},
             [C.color("kite_blue", "風箏變成藍色和綠色了！"), C.pattern("kite_dots", "風箏變成點點了！"), C.gone("風箏不見了！")],
             big=True, z=2)
    sa.thing("sun", "太陽", "sun", {"sun": sun, "sun_wow": lambda: sun("wow")},
             [C.face_("sun_wow", "太陽嚇了一跳！"), C.gone("太陽不見了！")],
             big=True, z=1)
    sa.extra("butterfly", "蝴蝶", "butterfly", butterfly, "多了一隻蝴蝶！", z=900, big=True)
    sa.extra("balloon2", "黃氣球", "yellow balloon", balloon2, "多了一個黃色的氣球！", z=3, big=True)
    sa.extra("bird", "小鳥", "bird", bird, "多了一隻小鳥！", z=4)
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"duck": lineup_duck, "duck_hat": lambda: lineup_duck(True), "duck_blue": lambda: lineup_duck(col="#7FC4FF")}, "小鴨子",
              # the hat is something added (「多了一個」, for 2-3 years too): an art change without a type
              [C.color("duck_blue", "這隻小鴨是藍色的！"), {"kind": "art", "art": "duck_hat", "said": "這隻小鴨戴了帽子！"},
               C.flip("這隻小鴨轉向另一邊！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((118, 316), 46, "flowers", "leaf"), ((390, 312), 42, "icecream", "wood"), ((262, 402), 44, "bike", "sand")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("swing", 1), ("bench", 2), ("flowers", 0), ("bike", 0), ("tree", 2), ("butterfly", "extra:butterfly")]


if __name__ == "__main__":
    scene().build()
