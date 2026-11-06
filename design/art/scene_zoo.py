"""動物園 (zoo): a floating zoo island (the park's isometric tile, 200 x 200 world units, 1.5 px per
unit) under a warm afternoon sky.

The back half of the tile is a sandy savanna behind a low wooden fence (an acacia tree, a giraffe,
an elephant, a zebra, a lion on his rock), the left corner a bamboo grove with a panda, the right
corner a pool (penguins on a rock, a hippo), and the front a stone path with a little train, a
turtle, two flamingos at a puddle and a sign with a paw print. A monkey sits in the acacia; the sun
and a flying parrot are in the sky.

    background()        sky, clouds, the tile (grass, savanna sand, soil), paths, the pool and the
                        puddle, the acacia, bamboo, fences, rocks, bushes: everything that never
                        changes (bg.svg, 600 x 600)
    one function per thing and per variant, returning shapes in scene px; each thing's box is the
                        bounding box of all its variants (kit.SceneArt)
    PLACE               where each thing stands (scene px): move things here, then run
                        `python3 build.py layout zoo`, `python3 build.py zoo` and
                        `python3 build.py preview zoo out.png`

Colours that 小變 hides against come from kit.TINT (bamboo bushes = leaf, the savanna = sand, the
acacia trunk = wood). HIDES gives each hide spot as (centre, size, the thing drawn in front of part
of him, tint); his z is that thing's z minus one.
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, star_pts, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=186)
TILE = 200
INK = "#2B3158"
WHITE = "#FFFFFF"
METAL = "#7C86A8"
SKY = "#FFE0D2"            # a warm peach afternoon (the park's sky is blue)
GRASS = "#A3E487"
GRASS_RIM = "#7FD06E"
SOIL = "#E3A877"
STONE = "#E2E7F1"
PATH = "#EADFD2"           # pale paving stones
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
CHEEK = "#FF9DB6"
P = ISO.P

# Where things are, in scene px: for things on the ground, the point they stand on (at() turns it
# into world units); for things in the sky, their centre.
PLACE = {
    "giraffe": (300, 237),
    "tree": (206, 254),        # the savanna tree's foot (background); 小變 hides on its trunk
    "monkey": (160, 190),      # where he sits on the tree's branch
    "elephant": (183, 286),
    "zebra": (414, 280),
    "lion": (298, 346),        # on his flat rock
    "panda": (76, 346),
    "hippo": (410, 361),       # on the water line
    "penguins": (512, 326),    # their feet on the rock (its foot is 10 px lower)
    "flamingos": (190, 403),   # in the puddle
    "train": (300, 442),       # the middle of the train
    "turtle": (396, 424),
    "sign": (240, 446),
    "sun": (70, 66),
    "parrot": (512, 88),
    "butterfly": (178, 78),
    "bird": (410, 52),
    "babyele": (246, 308),
}
POOL = (162, 62, 30)            # world centre and radius of the water


def at(name_or_xy):
    """World (x, y) of a ground point given in scene px (a PLACE name or a point)."""
    X, Y = PLACE[name_or_xy] if isinstance(name_or_xy, str) else name_or_xy
    a = (X - ISO.ox) / (kit.C30 * ISO.k)
    b = (Y - ISO.oy) / (kit.S30 * ISO.k)
    return (a + b) / 2, (b - a) / 2


def depth(name, dz=0.0):
    x, y = at(name)
    return x + y + dz


def shadow(x, y, r, op=1.0):
    return ISO.shadow(x, y, r, op=op)


def stand(name, sprite, s=1.0, r=12, dx=0.0, dy=0.0, sh_op=.8):
    """A 2D sprite (origin at its feet) standing on PLACE[name], with a ground shadow."""
    X, Y = PLACE[name]
    x, y = at((X, Y))
    return shadow(x + 1, y + 1, r, sh_op) + transform(sprite, dx=X + dx, dy=Y + dy, s=s)


def above(pts, y0=0.0):
    """The part of a polygon above the line y = y0 (screen y smaller): for things in water."""
    out = []
    m = len(pts)
    for i in range(m):
        p, q = pts[i], pts[(i + 1) % m]
        pin, qin = p[1] <= y0, q[1] <= y0
        if pin:
            out.append(p)
        if pin != qin:
            t = (y0 - p[1]) / (q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * t, y0))
    return out


def blob(cx, cy, r, rot=0.0, k=5, seed=0):
    """A rounded irregular spot (giraffe spots, turtle shell plates)."""
    pts = []
    for i in range(k):
        a = math.radians(rot + 360 * i / k)
        rr = r * (1 + .18 * math.sin(i * 2.3 + seed))
        pts.append((cx + rr * math.cos(a), cy + rr * .86 * math.sin(a)))
    return crs(pts, 4)


def eye(x, y, r=2.4, col=INK):
    return [oval(x, y, r, r * 1.25, col=col), oval(x - r * .4, y - r * .55, r * .4, col=WHITE, tag="detail")]


def cheek(x, y, rx=3.6, ry=2.2):
    return oval(x, y, rx, ry, col=CHEEK, op=.8, tag="detail")


def smile(x, y, w=4.0, col=INK, lw=1.3):
    return line(crs([(x - w, y - 1), (x, y + 1.5), (x + w, y - 1)], 4, closed=False), col, lw)


# ================================================================ background
# in world units (x right-front, y left-front, 0..200): the sand of the savanna and the fence in front of it
SAVANNA = [(5, 5), (128, 5), (134, 22), (132, 44), (138, 70), (144, 98), (138, 122), (118, 138), (84, 146), (50, 150),
           (22, 152), (5, 150)]
FENCE = [(141, 84), (143, 104), (137, 126), (116, 142), (84, 150), (50, 155), (24, 157), (5, 156)]
# in scene px
PATH_MAIN = [(300, 468), (300, 450), (298, 424), (300, 402), (330, 392), (372, 398), (404, 404)]
PATH_LEFT = [(300, 402), (262, 392), (232, 380), (196, 372), (150, 368), (118, 372)]
BAMBOO = [(52, 326, 92), (66, 312, 112), (96, 306, 104), (122, 302, 86), (40, 338, 70)]
BUSHES = [((116, 326), 9), ((132, 318), 7), ((102, 334), 6), ((478, 410), 7), ((356, 456), 7)]
ROCKS = [((262, 230), 6), ((372, 228), 5)]
DRY_TUFTS = [(240, 236), (350, 212), (196, 266), (380, 258), (282, 296), (236, 330), (360, 300), (140, 296)]
TUFTS = [(150, 392), (216, 430), (344, 424), (444, 404), (268, 470), (96, 382), (520, 352), (380, 448)]
LITTLE_FLOWERS = [(126, 392), (232, 426), (336, 436), (458, 394), (268, 476)]


def background():
    g = Group()
    g.add(Sh([(0, 0), (600, 0), (600, 600), (0, 600)], SKY, tag="screen"), -9000)
    for (cx, cy), s in zip(((132, 152), (470, 176), (530, 500)), (.85, .8, .9)):
        c = tf(crs([(-34, 6), (-38, -4), (-26, -12), (-14, -22), (6, -22), (18, -12), (32, -10), (34, 6)], 5), s=s, dx=cx, dy=cy)
        g.add([Sh(tf(c, dy=3), "#F6C3B4", only="ab"), Sh(c, WHITE)], -8000)
    cx, cy = P(TILE / 2, TILE / 2, -20)
    g.add(Sh(ellp(cx, cy + 44, 226, 24), "#3B5A7A", tag="shadow", op=.9), -7000)
    g.add(ISO.box(0, 0, -21, TILE, TILE, 15, SOIL)[:2], -6000)
    g.add(ISO.box(0, 0, -6, TILE, TILE, 6, GRASS_RIM, top=GRASS), -5900)
    peb = []
    for i in range(12):
        t = (i + .5) / 12
        if i % 2 == 0:
            x, y, z = 6 + t * (TILE - 12), TILE, -9 - (i * 7 % 10)
        else:
            x, y, z = TILE, 6 + t * (TILE - 12), -9 - (i * 5 % 10)
        sx, sy = P(x, y, z)
        peb.append(oval(sx, sy, 3.8 - (i % 3) * .5, 2.2, col=mix(SOIL, WHITE, .32), tag="detail"))
    g.add(peb, -5800)
    # the savanna: sand (小變 hides on it)
    g.add(ISO.flat(crs(SAVANNA, 4), 0, SAND), -5500)
    # paths of pale paving stones
    for pts, w in ((PATH_MAIN, 16), (PATH_LEFT, 13)):
        c = crs([at(p) for p in pts], 4, closed=False)
        g.add(ISO.flat(tube(c, w), 0, mix(PATH, "#B9A48E", .4), only="ab"), -5000)
        g.add(ISO.flat(tube(c, w - 2.8), 0, PATH), -4990)
    # the pool: stone rim, water, ripples; the penguins' rock at its back
    px, py, R = POOL
    g.add([sh.copy(only="ab") for sh in ISO.cyl(px, py, 0, R + 4, 2.5, STONE)], -4000)
    g.add(ISO.disc(px, py, 2.5, R + 4, STONE, only="c"), -4000)
    g.add(ISO.disc(px, py, 2.5, R, WATER_D), -3990)
    g.add(ISO.disc(px + 1.4, py + 1.4, 1.2, R - 1.8, WATER), -3980)
    for dx, dy, l_ in ((10, 14, 8), (14, -10, 6), (-14, 22, 6)):
        sx, sy = P(px + dx, py + dy, 1.2)
        g.add(line([(sx - l_, sy), (sx, sy - 2.4), (sx + l_, sy)], WHITE, 1.8, op=.85), -3970)
    rx, ry = at((PLACE["penguins"][0], PLACE["penguins"][1] + 10))
    rock = ISO.cyl(rx, ry, 0, 17, 6.7, "#C9D1E2", top=TINT["white"])
    g.add([sh.copy(only="ab") for sh in rock[:2]] + [Sh(rock[0].pts[:-2] + rock[1].pts[1:], "#C9D1E2", only="c"), rock[2]], -3900)
    # the flamingos' puddle
    fx, fy = at("flamingos")
    g.add(ISO.disc(fx - 1, fy - 3, 0, 13, WATER_D), -3800)
    g.add(ISO.disc(fx, fy - 2, 0, 11.6, WATER), -3790)
    # the lion's flat rock
    lx, ly = at("lion")
    g.add(ISO.box(lx - 20, ly - 12, 0, 34, 24, 4, "#C3B6A6", top="#DCD1C3"), lx + ly - 30)
    for p, r in ROCKS:
        x, y = at(p)
        g.add(ISO.ball(x, y, 0, r, "#BDB1A3", sq=.7), x + y)
    # dry tufts on the sand, green ones on the grass, little flowers
    for pts, col in ((DRY_TUFTS, "#C9A44E"), (TUFTS, "#6CC66A")):
        g.add([line([(sx - 4, sy - 5), (sx - 1.5, sy), (sx, sy - 7), (sx + 1.5, sy), (sx + 4, sy - 5)], col, 1.7) for sx, sy in pts], -2000)
    for i, (sx, sy) in enumerate(LITTLE_FLOWERS):
        x, y = at((sx, sy))
        col = (PINK, YELLOW, WHITE, PURPLE)[i % 4]
        fl = [line([(sx, sy), (sx, sy - 8)], "#4FAE5C", 1.7)]
        fl += [oval(sx + 3.2 * math.cos(math.radians(a)), sy - 9 + 3.2 * math.sin(math.radians(a)), 2.5, col=col, tag="detail")
               for a in range(0, 360, 72)]
        fl.append(oval(sx, sy - 9, 1.8, col="#FFE27A", tag="detail"))
        g.add(fl, x + y)
    # wooden fences: along the two back edges and in front of the savanna. Style A draws boxes;
    # b and c draw strokes (one element per colour, which keeps those files small)
    rails, posts = [], []
    for along in ("x", "y"):
        ends = [(6, 4), (194, 4)] if along == "x" else [(4, 6), (4, 194)]
        for zz in (5, 10):
            if along == "x":
                g.add(ISO.box(6, 3.4, zz, 188, 1.4, 2.2, WOOD, only="a"), 6 + zz * .01)
            else:
                g.add(ISO.box(3.4, 6, zz, 1.4, 188, 2.2, WOOD, only="a"), 6 + zz * .01)
            rails.append(line([P(x, y, zz + 1) for x, y in ends], WOOD, 3, only="bc"))
        for i in range(8):
            a = 6 + i * 26.86
            x, y = (a, 4) if along == "x" else (4, a)
            g.add(ISO.box(x - 1.5, y - 1.5, 0, 3, 3, 13, WOOD, only="a"), x + y - 2)
            posts.append(line([P(x, y, 0), P(x, y, 13)], WOOD, 4.4, only="bc"))
    g.add(rails + posts, 4)
    fence = crs(FENCE, 3, closed=False)
    front_rails = [ISO.line3([(x, y, zz) for x, y in fence], WOOD, 1.7) for zz in (4, 8.5)]
    g.add(front_rails, 230)
    for i, (x, y) in enumerate(fence[::2]):
        g.add(ISO.box(x - 1.4, y - 1.4, 0, 2.8, 2.8, 10.5, WOOD, only="a"), x + y)
        g.add(line([P(x, y, 0), P(x, y, 10.5)], WOOD, 4.2, only="bc"), 240)
    # the bamboo grove at the left corner and leaf bushes (小變 hides in them)
    for sx, sy, h in BAMBOO:
        x, y = at((sx, sy))
        g.add(bamboo_stalk(sx, sy, h), x + y - 3)
    for p, r in BUSHES:
        x, y = at(p)
        g.add(ISO.shadow(x + 3, y + 3, r * .9), -3000)
        g.add(ISO.ball(x, y, 0, r, LEAF), x + y)
    g.add(savanna_tree(), depth("tree"))
    return g.shapes()


def bamboo_stalk(sx, sy, h):
    o = [line([(sx, sy), (sx, sy - h)], "#7CCB5C", 5.2)]
    o += [line([(sx - 2.6, sy - k * 18), (sx + 2.6, sy - k * 18)], "#4E9E44", 1.6) for k in range(1, int(h // 18) + 1)]
    for dx, dy, rot in ((7, -h + 6, -20), (-7, -h + 14, 20), (8, -h * .55, -26)):
        o.append(oval(sx + dx, sy + dy, 8, 2, col="#58B858", rot=rot, tag="detail"))
    return o


def savanna_tree():
    """A fat-trunked savanna tree with a flat crown; the trunk is wood (小變 hides on it)."""
    x, y = at("tree")
    sx, sy = P(x, y)
    o = ISO.shadow(x + 4, y + 3, 15, .6)
    o.append(Sh(tube(crs([(sx, sy), (sx + 1, sy - 34), (sx + 3, sy - 66)], 4, closed=False), 30, 20, caps=False), WOOD, cel=.5))
    o.append(oval(sx, sy, 15, 4.4, col=WOOD))
    for ex, ey in ((-40, -84), (38, -80)):
        o.append(Sh(tube([(sx + 2, sy - 58), (sx + ex * .5, sy + ey + 6), (sx + ex, sy + ey)], 8, 5, caps=False), WOOD))
    crown = [(-74, -86), (-62, -98), (-36, -104), (-14, -114), (16, -112), (44, -100), (70, -92), (66, -78), (36, -76),
             (8, -86), (-20, -84), (-44, -78), (-68, -78)]
    o.append(Sh(crs([(sx + dx, sy + dy) for dx, dy in crown], 5), "#86C45C", cel=.8))
    return o


# ================================================================ things
# ---------------------------------------------------------------- giraffe (facing left)
GIR = "#FFC845"
GIR_SPOT = "#E58A3A"
HOOF = "#7A5232"
GIR_SPOTS = [(-6, -62, 4.8, 10), (8, -66, 5, 40), (20, -58, 4.6, 0), (4, -52, 3.8, 70), (-14, -55, 3.4, 20), (30, -60, 3, 30),
             (-14, -76, 3.6, 0), (-17, -88, 3.4, 30), (-20, -100, 3, 60), (-22, -110, 2.6, 10)]


def giraffe_sprite(col=GIR, spot=GIR_SPOT):
    far = kit.tone(col, .9, 1.02)
    light = mix(col, WHITE, .5)
    o = [line(crs([(28, -62), (34, -52), (35, -38)], 5, closed=False), spot, 2.2), oval(35, -35, 3.2, 5, col=spot)]
    for lx in (-11, 21):
        o.append(Sh(rrect(lx - 3.2, -52, 6.4, 50, 3.2), far))
        o.append(Sh(rrect(lx - 3.4, -6, 6.8, 6, 2), HOOF))
    o.append(oval(5, -58, 29, 17, col=col, cel=1.0))
    o.append(Sh(tube(crs([(-12, -62), (-18, -88), (-24, -114)], 6, closed=False), 17, 11), col, cel=.5))
    for lx in (-17, 15):
        o.append(Sh(rrect(lx - 3.6, -50, 7.2, 48, 3.4), col, cel=.3))
        o.append(Sh(rrect(lx - 3.8, -6, 7.6, 6, 2), HOOF))
    for sx, sy, r, rot in GIR_SPOTS:
        o.append(Sh(blob(sx, sy, r, rot, seed=sx), spot))
    o.append(line(crs([(-5, -68), (-10, -92), (-16, -114)], 5, closed=False), spot, 3.4))
    o.append(Sh(crs([(-14, -122), (-20, -132), (-30, -134), (-40, -128), (-47, -120), (-45, -112), (-34, -110), (-20, -112)]), col, cel=1.0))
    o.append(oval(-41, -117, 7.5, 6, col=light))
    for ox in (-21, -29):
        o.append(line([(ox, -130), (ox + 1, -142)], spot, 2.6))
        o.append(oval(ox + 1, -143, 3.2, col=spot))
    o.append(Sh(crs([(-16, -126), (-5, -133), (-11, -122)], 4), col))
    o += eye(-31, -124, 2.6)
    o.append(oval(-45, -119, 1.2, col=kit.dk(col, .5)))
    o.append(smile(-39, -113, 3.4))
    o.append(cheek(-26, -116))
    return o


def giraffe(col=GIR, spot=GIR_SPOT):
    return stand("giraffe", giraffe_sprite(col, spot), s=1.1, r=11)


# ---------------------------------------------------------------- elephant (facing left)
GREY = "#A8B3CF"


def elephant_sprite(col=GREY):
    dark = kit.tone(col, .86)
    inner = "#FFC2D4" if col == GREY else mix(col, WHITE, .5)
    o = [line(crs([(40, -40), (46, -32), (46, -24)], 4, closed=False), dark, 2.2), oval(46, -22, 2.6, 3.6, col=dark)]
    for lx in (-12, 24):
        o.append(Sh(rrect(lx - 7, -30, 14, 30, 6), dark))
    o.append(oval(9, -38, 36, 27, col=col, cel=1.0))
    for lx in (-18, 18):
        o.append(Sh(rrect(lx - 7.5, -28, 15, 28, 6.5), col, cel=.3))
        for tx in (-4, 0, 4):
            o.append(oval(lx + tx, -2.6, 1.8, 1.5, col="#F2F5FA", tag="detail"))
    o.append(oval(-28, -50, 21, 20, col=col, cel=1.0))
    o.append(Sh(tube(crs([(-40, -44), (-50, -36), (-54, -24), (-55, -13), (-50, -6)], 5, closed=False), 13, 7), col, cel=.4))
    for yy in (-30, -22, -15):
        o.append(line([(-57, yy), (-50, yy - 1)], dark, 1.2))
    o.append(Sh(crs([(-40, -37), (-48, -31), (-50, -27), (-44, -33)], 4), "#FFF8E8"))
    o.append(Sh(crs([(-20, -68), (-6, -67), (3, -54), (-1, -36), (-13, -30), (-20, -40), (-22, -56)]), col, cel=.6))
    o.append(Sh(crs([(-16, -62), (-6, -61), (-2, -51), (-5, -40), (-12, -37), (-16, -46), (-17, -56)]), inner))
    o += eye(-34, -56, 2.6)
    o.append(cheek(-37, -45))
    return o


def elephant(col=GREY):
    return stand("elephant", elephant_sprite(col), s=.95, r=13)


def babyele():
    return stand("babyele", elephant_sprite(), s=.5, r=8)


# ---------------------------------------------------------------- zebra / pony (facing left)
ZEBRA = "#F0F1F5"          # near-white that still prints a light tint in riso (paper white would vanish)
PONY = "#C98A55"


def zebra_sprite(kind="stripes"):
    """kind: stripes (the zebra), dots (its stripes turned into dots), horse (a pony)."""
    horse = kind == "horse"
    col = PONY if horse else ZEBRA
    mark = "#6B4226" if horse else INK
    far = kit.tone(col, .88) if horse else "#DCE0EA"
    o = [line(crs([(30, -48), (36, -40), (37, -30)], 4, closed=False), col if not horse else mark, 2.6),
         Sh(crs([(34, -32), (40, -31), (39, -22), (36, -20), (33, -24)], 3), mark)]
    legs_far, legs_near = (-11, 21), (-17, 15)
    for lx in legs_far:
        o.append(Sh(rrect(lx - 3.2, -42, 6.4, 40, 3.2), far))
        o.append(Sh(rrect(lx - 3.4, -5, 6.8, 5, 1.8), "#3E4566"))
    o.append(oval(5, -48, 29, 16, col=col, cel=1.0))
    neck = crs([(-12, -52), (-20, -68), (-26, -80)], 5, closed=False)
    o.append(Sh(tube(neck, 20, 14), col, cel=.5))
    for lx in legs_near:
        o.append(Sh(rrect(lx - 3.6, -42, 7.2, 40, 3.4), col, cel=.3))
        o.append(Sh(rrect(lx - 3.8, -5, 7.6, 5, 1.8), "#3E4566"))
    # the mane along the back of the neck: dark (striped with white on the zebra)
    mane = crs([(-5, -56), (-12, -72), (-19, -88)], 5, closed=False)
    o.append(Sh(tube(mane, 7, 6), mark))
    if not horse:
        for t in (.22, .5, .78):
            i = int(t * (len(mane) - 1))
            mx, my = mane[i]
            o.append(line([(mx - 3.6, my + 1.2), (mx + 3.6, my - 1.2)], WHITE, 1.6))
    # the head, pointing down-left
    head = crs([(-18, -92), (-28, -97), (-40, -93), (-49, -82), (-53, -73), (-47, -66), (-37, -69), (-24, -78)])
    o.append(Sh(head, col, cel=1.0))
    o.append(Sh(crs([(-20, -92), (-20, -104), (-13, -93)], 3), col))
    o.append(oval(-48, -72, 6.6, 6.2, rot=20, col="#3E4566" if not horse else "#8A5A3A"))
    o.append(oval(-51, -74, 1.3, col=WHITE if not horse else "#5A3A26", tag="detail"))
    if horse:
        o.append(Sh(crs([(-30, -95), (-36, -88), (-44, -78), (-41, -76), (-34, -86)], 3), "#FFF3E2", tag="detail"))
        o.append(Sh(tube(crs([(-25, -97), (-18, -100)], 3, closed=False), 7, 4), mark))
    o += eye(-33, -85, 2.5)
    o.append(cheek(-37, -75, 3, 1.8))
    if horse:
        return o
    # stripes (or dots): tapering bands over the body, across the neck, on the legs and the face
    bands = []
    for x in (-12, -3, 6, 15, 24):
        hh = 16 * math.sqrt(max(0, 1 - ((x - 5) / 29) ** 2))
        top, bot = (x + 2, -48 - hh + 1.5), (x - 1.5, -48 + hh * .55)
        bands.append((top, bot, 5.6, 1.6))
    for t in (.15, .45, .75):
        i = int(t * (len(neck) - 1))
        (x0, y0), (x1, y1) = neck[max(0, i - 1)], neck[min(len(neck) - 1, i + 1)]
        ln_ = math.hypot(x1 - x0, y1 - y0)
        nx, ny = (y1 - y0) / ln_, -(x1 - x0) / ln_
        cx, cy = neck[i]
        w = 9.5 - t * 3
        bands.append(((cx + nx * w, cy + ny * w), (cx - nx * w * .4, cy - ny * w * .4), 4.8, 1.8))
    for lx in legs_near + legs_far:
        for yy in (-30, -21, -12):
            bands.append(((lx - 3, yy), (lx + 3, yy + 1), 2.6, 2.6))
    for a, b, w0, w1 in bands:
        if kind == "dots":
            o.append(oval(a[0] * .6 + b[0] * .4, a[1] * .6 + b[1] * .4, w0 * .6 + 1, col=INK))
        else:
            o.append(Sh(tube([a, b], w0, w1), INK))
    return o


def zebra(kind="stripes"):
    return stand("zebra", zebra_sprite(kind), s=1.0, r=10)


# ---------------------------------------------------------------- lion / tiger (body facing left, face to us)
LION = "#FFC24D"
MANE = "#E8833A"


def lion_sprite():
    face = "#FFE3A3"
    o = [line(crs([(28, -26), (38, -34), (41, -46)], 5, closed=False), LION, 2.6), oval(41, -48, 4, 5, col=MANE)]
    for lx in (-4, 22):
        o.append(Sh(rrect(lx - 4.5, -22, 9, 22, 4), kit.tone(LION, .9)))
    o.append(oval(9, -27, 26, 15, col=LION, cel=1.0))
    for lx in (-10, 16):
        o.append(Sh(rrect(lx - 5, -20, 10, 20, 4.5), LION, cel=.3))
        o.append(oval(lx - 1, -2.6, 6, 3, col=mix(LION, WHITE, .4), tag="detail"))
    cx, cy = -20, -46
    pts = []
    for i in range(24):
        a = math.radians(i * 15)
        rr = 25 if i % 2 == 0 else 21
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    o.append(Sh(crs(pts, 3), MANE, cel=1.0))
    for ex in (-32, -8):
        o.append(oval(ex, -61, 5.5, col=LION))
        o.append(oval(ex, -60.5, 2.8, col="#E8A24E", tag="detail"))
    o.append(oval(cx, cy + 1, 15, 14, col=face, cel=.7))
    o.append(oval(cx - 4, cy + 7, 5, 3.8, col="#FFF3D6"))
    o.append(oval(cx + 4, cy + 7, 5, 3.8, col="#FFF3D6"))
    o.append(Sh(crs([(cx - 4, cy + 2), (cx + 4, cy + 2), (cx, cy + 6)], 3), "#7A4A2E"))
    o += eye(cx - 6, cy - 3, 2.4)
    o += eye(cx + 6, cy - 3, 2.4)
    o.append(cheek(cx - 11, cy + 4, 3, 1.8))
    o.append(cheek(cx + 11, cy + 4, 3, 1.8))
    return o


def tiger_sprite():
    col, stripe, white = "#FF9A3C", "#3E3550", "#FFF6EA"
    o = [line(crs([(28, -26), (38, -34), (41, -46)], 5, closed=False), col, 3), oval(41, -47, 2.4, 3, col=stripe)]
    for lx in (-4, 22):
        o.append(Sh(rrect(lx - 4.5, -22, 9, 22, 4), kit.tone(col, .9)))
    o.append(oval(9, -27, 26, 15, col=col, cel=1.0))
    for lx in (-10, 16):
        o.append(Sh(rrect(lx - 5, -20, 10, 20, 4.5), col, cel=.3))
        o.append(oval(lx - 1, -2.6, 6, 3, col=white, tag="detail"))
    for x in (2, 11, 20, 28):
        hh = 15 * math.sqrt(max(0, 1 - ((x - 9) / 26) ** 2))
        o.append(Sh(crs([(x - 2.5, -27 - hh + 1), (x + 2.5, -27 - hh + 1), (x - 1, -27 + hh * .2)], 3), stripe))
    for lx in (-10, 16):
        o.append(line([(lx - 3.5, -14), (lx + 2, -13)], stripe, 2.2))
    for t in ((36, -36), (39.5, -41)):
        o.append(line([(t[0] - 3, t[1] + 1), (t[0] + 3, t[1] - 1)], stripe, 2.2))
    cx, cy = -20, -44
    for ex in (-33, -7):
        o.append(oval(ex, -60, 6, col=col))
        o.append(oval(ex, -59.5, 3, col=white, tag="detail"))
    o.append(oval(cx, cy, 19, 17, col=col, cel=1.0))
    o.append(oval(cx - 6, cy + 6, 8, 6, col=white))
    o.append(oval(cx + 6, cy + 6, 8, 6, col=white))
    for dx in (-5, 0, 5):
        o.append(Sh(crs([(cx + dx - 1.8, cy - 16), (cx + dx + 1.8, cy - 16), (cx + dx, cy - 9)], 3), stripe))
    for sgn in (-1, 1):
        o.append(Sh(crs([(cx + sgn * 19, cy - 2), (cx + sgn * 19, cy + 3), (cx + sgn * 12, cy)], 3), stripe))
    o.append(Sh(crs([(cx - 3.6, cy + 2), (cx + 3.6, cy + 2), (cx, cy + 5.5)], 3), "#FF7A9A"))
    o += eye(cx - 7, cy - 3, 2.4)
    o += eye(cx + 7, cy - 3, 2.4)
    return o


def lion(kind="lion"):
    sp = lion_sprite() if kind == "lion" else tiger_sprite()
    return stand("lion", sp, s=1.0, r=9, dy=-4 * 1.5, sh_op=.6)


# ---------------------------------------------------------------- panda with bamboo (sitting, facing a little left)
PANDA_K = "#2E3146"


def panda_sprite(dark=PANDA_K, face="happy"):
    white = ZEBRA
    o = [oval(14, -10, 9, 8, col=dark, cel=.4)]
    o.append(oval(2, -24, 22, 22, col=white, cel=1.0))
    o.append(oval(-11, -6, 9, 7.5, col=dark, cel=.5))
    o.append(oval(-13, -5, 4.4, 3.4, col="#F0D6CF", tag="detail"))
    o.append(oval(10, -5, 8, 6.5, col=dark, cel=.5))
    # its bamboo, held across the belly
    stalk = [(-2, -8), (-26, -72)]
    o.append(line(stalk, "#8BD35F", 6.6))
    for t in (.2, .45, .7):
        x = stalk[0][0] + (stalk[1][0] - stalk[0][0]) * t
        y = stalk[0][1] + (stalk[1][1] - stalk[0][1]) * t
        o.append(line([(x - 3.2, y - 1.2), (x + 3.2, y + 1.2)], "#4E9E44", 1.8))
    for dx, dy, rot in ((-36, -74, 25), (-30, -82, -60), (-37, -63, -20)):
        o.append(oval(dx, dy, 9, 3.4, col="#58B858", rot=rot))
    o.append(Sh(tube(crs([(-11, -40), (-16, -36), (-19, -40)], 4, closed=False), 10, 9), dark, cel=.4))
    o.append(Sh(tube(crs([(15, -40), (20, -32), (19, -24)], 4, closed=False), 10, 9), dark, cel=.4))
    for ex in (-13, 15):
        o.append(oval(ex, -70, 7.5, col=dark, cel=.4))
    o.append(oval(1, -56, 21, 18, col=white, cel=1.0))
    o.append(oval(-8, -58, 6, 4.8, col=dark, rot=-35))
    o.append(oval(9, -58, 6, 4.8, col=dark, rot=35))
    if face == "happy":
        o.append(oval(-8, -58.5, 1.8, col=WHITE))
        o.append(oval(9, -58.5, 1.8, col=WHITE))
        o.append(oval(0, -51, 3.2, 2.2, col=dark))
        o.append(smile(0, -47.5, 3.2, dark))
    else:
        o.append(oval(-8, -58.5, 3, col=WHITE))
        o.append(oval(9, -58.5, 3, col=WHITE))
        o.append(oval(-8, -58, 1.5, col=INK))
        o.append(oval(9, -58, 1.5, col=INK))
        o.append(oval(0, -52, 3.2, 2.2, col=dark))
        o.append(oval(0, -45.5, 3.4, 4.2, col="#C9405A"))
    o.append(cheek(-12, -49, 3, 1.8))
    o.append(cheek(14, -49, 3, 1.8))
    return o


def panda(dark=PANDA_K, face="happy"):
    return stand("panda", panda_sprite(dark, face), s=1.2, r=12)


# ---------------------------------------------------------------- hippo in the pool (facing left)
HIPPO = "#A99BD8"


def hippo_sprite(col=HIPPO, open_=False):
    """Swimming: the back and the big head above the water line (y = 0)."""
    light = mix(col, WHITE, .35)
    nose = kit.dk(col, .45)
    o = [oval(-2, 0, 46, 7, col=WHITE, op=.55)]
    o.append(Sh(above(ellp(22, 0, 22, 11)), col, cel=1.0))
    if not open_:
        o.append(Sh(above(ellp(-8, -2, 22, 24)), col, cel=1.0))
        o.append(Sh(above(ellp(-25, -2, 18, 15)), light, cel=.6))
        for nx in (-34, -24):
            o.append(oval(nx, -12, 2.6, 1.8, col=nose))
        for ex in (-14, 1):
            o.append(oval(ex, -26, 7, 6.5, col=col, cel=.6))
            o += eye(ex, -27, 2.8)
        for ex in (-6, 10):
            o.append(oval(ex, -34, 3.8, 3.4, col=col))
            o.append(oval(ex, -34, 1.8, col=CHEEK, tag="detail"))
        o.append(cheek(-10, -12))
        o.append(smile(-28, -5, 5))
    else:
        o.append(Sh(above(ellp(-8, -4, 20, 18)), col, cel=1.0))
        o.append(Sh(above(crs([(-2, -6), (-24, -2), (-38, -4), (-41, -10), (-28, -13), (-8, -13)])), light, cel=.5))
        o.append(Sh(crs([(-6, -12), (-30, -14), (-44, -24), (-42, -33), (-24, -26), (-8, -19)]), "#E86A8A"))
        o.append(oval(-30, -17, 8, 3.2, col="#FF9DB6", rot=-12))
        o.append(Sh(crs([(-6, -17), (-22, -28), (-43, -36), (-48, -45), (-35, -50), (-14, -41), (-2, -28)]), light, cel=.6))
        for tx, ty in ((-36, -19), (-25, -16)):
            o.append(Sh(rrect(tx - 2.2, ty - 6, 4.4, 7, 1.6), WHITE))
        for nx, ny in ((-44, -45), (-37, -47)):
            o.append(oval(nx, ny, 2.2, 1.5, col=nose))
        for ex in (-6, 6):
            o.append(oval(ex, -27, 6.5, 6, col=col, cel=.6))
            o += eye(ex, -28, 2.6)
        for ex in (1, 14):
            o.append(oval(ex, -33, 3.4, 3, col=col))
    return o


def hippo(col=HIPPO, open_=False):
    X, Y = PLACE["hippo"]
    return transform(hippo_sprite(col, open_), dx=X, dy=Y, s=1.0)


# ---------------------------------------------------------------- penguins on the rock (facing left)
NAVY = "#33406E"


def penguin_sprite(col=NAVY, scarf=False):
    o = [oval(-5, -1.2, 5, 2.4, col=ORANGE), oval(4, -1.2, 5, 2.4, col=ORANGE)]
    o.append(oval(0, -19, 12.5, 18.5, col=col, cel=1.0))
    o.append(Sh(crs([(-11, -26), (-6, -34), (0, -31), (2, -20), (0, -6), (-7, -3.5), (-11.5, -12)]), WHITE))
    o.append(Sh(crs([(6, -25), (13.5, -14), (10, -9), (6, -15)]), kit.dk(col, .2) if col == NAVY else kit.tone(col, .8)))
    o += eye(-5, -28, 2, INK)
    o.append(Sh([(-10.5, -29.5), (-19, -27), (-10.5, -24.5)], ORANGE))
    o.append(cheek(-7, -22.5, 2.4, 1.5))
    if scarf:
        o.append(Sh(crs([(-11, -22), (0, -19.5), (11, -22), (11, -17), (0, -14), (-11, -16.5)], 4), RED))
        o.append(Sh(rrect(5, -18, 5, 13, 2), RED))
        o.append(line([(-8, -18.5), (8, -18.5)], WHITE, 1.4))
    return o


PENG = ((0, -3, 1.0), (-18, 2, .95), (18, 1, .95))     # the middle one stands at the back (drawn first)


def penguins(n_=3):
    X, Y = PLACE["penguins"]
    o = []
    for i, (dx, dy, s) in enumerate(PENG):
        if n_ == 2 and i == 0:
            continue
        o += transform(penguin_sprite(), dx=X + dx, dy=Y + dy, s=s * 1.2)
    return o


# ---------------------------------------------------------------- flamingos in the puddle (facing left)
FLAMINGO = "#FF8FB8"


def flamingo_sprite(col=FLAMINGO):
    leg = kit.tone(col, .8, 1.1)
    o = [line([(2, 0), (2, -32)], leg, 2.2), line([(3, -31), (12, -24), (6, -17)], leg, 2.2)]
    o.append(Sh(crs([(-10, -38), (-2, -46), (12, -45), (24, -41), (14, -33), (0, -30)]), col, cel=1.0))
    o.append(Sh(crs([(0, -40), (10, -43), (18, -39), (8, -35)]), kit.tone(col, .88, 1.1)))
    o.append(Sh(tube(crs([(-6, -42), (-12, -52), (-6, -62), (-3, -70), (-8, -78)], 5, closed=False), 5.5, 4.5), col))
    o.append(oval(-9, -79, 5.8, 5.2, col=col, cel=.6))
    o.append(Sh(crs([(-13, -82), (-21, -79), (-22, -72), (-19, -73), (-14, -77)], 3), "#FFF4E0"))
    o.append(Sh(crs([(-21.5, -77), (-22, -72), (-19, -73), (-19.5, -76)], 3), INK))
    o += eye(-9, -81, 1.7)
    return o


def flamingos(col=FLAMINGO):
    X, Y = PLACE["flamingos"]
    back = transform(flamingo_sprite(col), dx=X + 16, dy=Y - 6, s=.92)
    front = transform(flamingo_sprite(col), dx=X - 8, dy=Y + 1, s=1.0)
    ripples = [oval(X + 16, Y - 6, 7, 2.2, col=WHITE, op=.6), oval(X - 8, Y + 1, 8, 2.4, col=WHITE, op=.6)]
    return ripples + back + front


# ---------------------------------------------------------------- parrot (flying, facing left)
def parrot_sprite(body=RED, w1=YELLOW, w2=BLUE):
    o = [Sh(tube(crs([(12, 4), (30, 13), (48, 24)], 5, closed=False), 9, 3), body),
         Sh(tube(crs([(12, 7), (27, 18), (38, 32)], 5, closed=False), 6, 2.5), w2)]
    o.append(Sh(crs([(4, -6), (16, -26), (34, -36), (38, -28), (26, -10), (14, 0)]), w2))
    o.append(oval(4, 0, 18, 10, col=body, rot=18, cel=1.0))
    o.append(Sh(crs([(-2, -2), (8, -18), (24, -26), (28, -18), (18, -4), (8, 2)]), w1, cel=.4))
    o.append(oval(-15, -6, 10.5, col=body, cel=1.0))
    o.append(oval(-18, -5, 5, 4.4, col=WHITE))
    o += eye(-18, -6, 1.9)
    o.append(Sh(crs([(-23, -9), (-31, -6), (-30, 2), (-26, -1), (-23, -3)], 3), "#F2E6D0"))
    o.append(Sh(crs([(-26, 0), (-23, 3), (-22, -1)], 3), "#3E4566"))
    return o


def parrot(body=RED, w1=YELLOW, w2=BLUE):
    cx, cy = PLACE["parrot"]
    return transform(parrot_sprite(body, w1, w2), dx=cx - 4, dy=cy + 2, s=1.3)


# ---------------------------------------------------------------- sun
def sun(face="smile"):
    cx, cy = PLACE["sun"]
    o = []
    for i in range(10):
        a = math.radians(i * 36 + 8)
        a1, a2 = a - .17, a + .17
        o.append(Sh([(cx + 30 * math.cos(a1), cy + 30 * math.sin(a1)), (cx + 44 * math.cos(a), cy + 44 * math.sin(a)),
                     (cx + 30 * math.cos(a2), cy + 30 * math.sin(a2))], "#FFC93C"))
    o.append(oval(cx, cy, 31, col=YELLOW, cel=.8))
    o.append(cheek(cx - 16, cy + 6, 5.5, 3.4))
    o.append(cheek(cx + 16, cy + 6, 5.5, 3.4))
    if face == "smile":
        for ex in (-10, 10):
            o += eye(cx + ex, cy - 5, 3.4)
    else:
        o += eye(cx - 10, cy - 5, 3.4)
        o.append(line([(cx + 5, cy - 4), (cx + 10, cy - 8), (cx + 15, cy - 4)], INK, 2.6))
    o.append(line(crs([(cx - 9, cy + 6), (cx, cy + 12), (cx + 9, cy + 6)], 6, closed=False), INK, 2.6))
    return o


# ---------------------------------------------------------------- train (runs along x, to the right-front)
def train(col=RED):
    X, Y = PLACE["train"]
    cx, cy = at((X, Y))
    L, D = 48, 15
    x0, y0 = cx - L / 2, cy - D / 2
    dark = "#3E4566"
    g = Group()
    g.add(shadow(cx, cy, 24, .7), -10)

    def wheel(wx, r=4.2):
        pts = [P(wx + r * math.cos(t), y0 + D + .3, 4.2 + r * math.sin(t)) for t in [2 * math.pi * i / 20 for i in range(20)]]
        hub = [P(wx + 1.4 * math.cos(t), y0 + D + .4, 4.2 + 1.4 * math.sin(t)) for t in [2 * math.pi * i / 12 for i in range(12)]]
        return [Sh(pts, dark), Sh(hub, "#DDE3F0", tag="detail")]
    # the carriage (back) and the engine (front, bigger x)
    g.add(ISO.box(x0, y0 + 1, 3, 20, D - 2, 4, dark), 1)
    g.add(ISO.box(x0, y0 + 1, 7, 20, D - 2, 9, YELLOW), 2)
    for px_ in (x0 + 1, x0 + 17.5):
        g.add(ISO.box(px_, y0 + 1.5, 16, 1.5, 1.5, 9, METAL), 2.5)
    g.add(ISO.box(x0 - 1, y0, 25, 22, D, 2.5, col), 3)
    g.add(ISO.box(x0 + 22, y0 + 1, 3, 26, D - 2, 4, dark), 4)
    g.add(ISO.box(x0 + 22, y0 + 1, 7, 11, D - 2, 20, col), 5)
    g.add(ISO.box(x0 + 23.5, y0 + D - 1.2, 15, 8, .4, 7, "#CFEFFF", left="#CFEFFF"), 5.1)
    g.add(ISO.box(x0 + 21, y0, 27, 14, D, 3, YELLOW), 5.5)
    g.add(ISO.box(x0 + 33, y0 + 2, 7, 15, D - 4, 12, col), 6)
    g.add(ISO.cyl(x0 + 42.5, y0 + D / 2, 19, 2.6, 9, dark), 7)
    g.add(ISO.cyl(x0 + 42.5, y0 + D / 2, 27, 3.6, 2.5, dark), 7.1)
    sx, sy = P(x0 + 48, y0 + D / 2, 13)
    g.add([oval(sx, sy, 3, 2.6, col="#FFE58A", cel=.5)], 8)
    for wx in (x0 + 5, x0 + 15, x0 + 27, x0 + 42):
        g.add(wheel(wx), 9)
    return g.shapes()


# ---------------------------------------------------------------- turtle (facing left)
TURTLE = "#4FB873"
TURTLE_SKIN = "#A5DE7E"


def turtle_sprite(shell=TURTLE):
    skin = TURTLE_SKIN
    o = [oval(-8, -3, 4.5, 3.4, col=kit.tone(skin, .85)), oval(12, -3, 4.5, 3.4, col=kit.tone(skin, .85))]
    o.append(Sh(crs([(17, -6), (24, -4), (17, -3)], 3), skin))
    o.append(Sh(tube(crs([(-14, -6), (-20, -9), (-24, -13)], 4, closed=False), 7, 8), skin))
    o.append(oval(-25, -15, 7, 6, col=skin, cel=.7))
    o += eye(-27, -17, 1.7)
    o.append(smile(-27, -12, 2.4, INK, 1.1))
    o.append(Sh(crs([(-19, -6), (-15, -19), (-2, -26), (11, -23), (19, -12), (19, -6)], 6), shell, cel=1.0))
    o.append(Sh(rrect(-20, -8, 40, 4.6, 2.3), kit.tone(shell, .8)))
    lt = mix(shell, WHITE, .35)
    for dx, dy, r in ((0, -17, 4.4), (-10, -12, 3.2), (10, -13, 3.4)):
        o.append(Sh(blob(dx, dy, r, 18, 6), lt, tag="detail"))
    o.append(oval(-12, -3, 4.5, 3.4, col=skin))
    o.append(oval(8, -3, 4.5, 3.4, col=skin))
    return o


def turtle(shell=TURTLE):
    return stand("turtle", turtle_sprite(shell), s=1.1, r=10)


# ---------------------------------------------------------------- sign with a paw print (no words)
def sign(kind="paw"):
    X, Y = PLACE["sign"]
    x, y = at((X, Y))
    o = ISO.shadow(x + 1, y + 1, 6, .7)
    o += ISO.box(x - 1.5, y - 1.5, 0, 3, 3, 30, WOOD)
    bx, by = X, Y - 50
    o.append(Sh(rrect(bx - 20, by - 15, 40, 30, 6), WOOD))
    o.append(Sh(rrect(bx - 16.5, by - 11.5, 33, 23, 4), "#FFF4DE"))
    if kind == "paw":
        brown = "#8A5A3A"
        o.append(oval(bx, by + 3.5, 6.5, 5.2, col=brown))
        for dx, dy in ((-8, -2.5), (-3, -7.5), (3, -7.5), (8, -2.5)):
            o.append(oval(bx + dx, by + dy, 2.6, 3.1, col=brown))
    else:
        o.append(Sh(crs(star_pts(10.5, 5, bx, by + .5), 2), "#FFB21E"))
    return o


# ---------------------------------------------------------------- monkey sitting on the acacia branch (facing left)
MONKEY = "#A86B42"
MONKEY_FACE = "#F5D2A8"


def monkey_sprite(food="banana"):
    col, face = MONKEY, MONKEY_FACE
    o = [line(crs([(6, -2), (11, 8), (9, 19), (3, 22), (0, 17)], 5, closed=False), col, 3.2)]
    for lx in (-4, 4):
        o.append(line([(lx, -4), (lx - 1, 9)], col, 4.4))
        o.append(oval(lx - 1.5, 10, 3, 2.2, col=face))
    o.append(oval(0, -12, 10, 12, col=col, cel=1.0))
    o.append(oval(-2, -10, 6, 7.5, col=face))
    for ex in (-11, 11):
        o.append(oval(ex, -31, 4.5, col=col))
        o.append(oval(ex, -31, 2.4, col=face, tag="detail"))
    o.append(oval(0, -30, 11, 10, col=col, cel=1.0))
    o.append(oval(-3.5, -31, 5, 5.5, col=face))
    o.append(oval(3.5, -31, 5, 5.5, col=face))
    o.append(oval(0, -25.5, 6.5, 4.6, col=face))
    o += eye(-3.5, -31.5, 1.8)
    o += eye(3.5, -31.5, 1.8)
    o.append(smile(0, -25, 2.8, "#6B4226", 1.2))
    o.append(line(crs([(-6, -16), (-11, -18), (-13, -24)], 4, closed=False), col, 4.4))
    if food == "banana":
        o.append(Sh(crs([(-14, -22), (-22, -28), (-24, -38), (-20, -33), (-14, -28)], 4), "#FFE04A", cel=.4))
        o.append(oval(-13.5, -21.5, 1.4, col="#8A6A2A"))
    else:
        o.append(oval(-17, -28, 6, 5.6, col=RED, cel=.7))
        o.append(line([(-17, -33), (-16, -37)], "#7A5232", 1.4))
        o.append(oval(-13.5, -36, 2.6, 1.3, col=GREEN, rot=-20))
    o.append(oval(-13, -23, 2.6, col=col))
    return o


def monkey(food="banana"):
    X, Y = PLACE["monkey"]
    return transform(monkey_sprite(food), dx=X, dy=Y, s=1.25)


# ---------------------------------------------------------------- extras
def butterfly():
    cx, cy = PLACE["butterfly"]
    o = [oval(-13, -10, 17, 13, col=YELLOW, rot=-25, cel=.6), oval(13, -10, 17, 13, col=YELLOW, rot=25, cel=.6),
         oval(-10, 9, 11, 9, col=ORANGE, rot=20, cel=.5), oval(10, 9, 11, 9, col=ORANGE, rot=-20, cel=.5)]
    for dx, dy, r in ((-16, -12, 4.4), (16, -12, 4.4), (-11, 10, 3), (11, 10, 3)):
        o.append(oval(dx, dy, r, col=WHITE, tag="detail", op=.9))
    o.append(Sh(rrect(-2.6, -16, 5.2, 32, 2.6), INK))
    o.append(line([(-1, -15), (-6, -26), (-9, -27)], INK, 1.4))
    o.append(line([(1, -15), (6, -26), (9, -27)], INK, 1.4))
    return transform(o, dx=cx, dy=cy, rot=10, s=1.1)


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


# ================================================================ lineup (哪一個不一樣？): a penguin
def lineup_penguin(col=NAVY, scarf=False):
    return transform([oval(0, 0, 16, 3.5, col="#C9D1E2", op=.7)] + penguin_sprite(col, scarf), s=3.4)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("zoo", "動物園", "zoo")
    sa.background(background)
    C = kit
    z = {k: int(depth(k)) for k in PLACE}
    z["monkey"] = z["tree"] + 2                       # he sits in the tree
    z["penguins"] = int(depth((PLACE["penguins"][0], PLACE["penguins"][1] + 10)))   # the rock's foot
    sa.thing("giraffe", "長頸鹿", "giraffe", {"giraffe": giraffe, "giraffe_blue": lambda: giraffe("#8CCBFF", "#3F86E0")},
             [C.color("giraffe_blue", "長頸鹿變成藍色了！"), C.gone("長頸鹿不見了！"), C.flip("長頸鹿轉向另一邊了！")],
             big=True, z=z["giraffe"])
    sa.thing("elephant", "大象", "elephant", {"elephant": elephant, "elephant_pink": lambda: elephant("#FFA6C8")},
             [C.color("elephant_pink", "大象變成粉紅色了！"), C.gone("大象不見了！"), C.flip("大象轉向另一邊了！")],
             big=True, z=z["elephant"])
    sa.thing("zebra", "斑馬", "zebra", {"zebra": zebra, "zebra_dots": lambda: zebra("dots"), "zebra_pony": lambda: zebra("horse")},
             [C.pattern("zebra_dots", "斑馬的條紋變成點點了！"), C.swap("zebra_pony", "斑馬變成小馬了！"), C.gone("斑馬不見了！"),
              C.flip("斑馬轉向另一邊了！")],
             big=True, z=z["zebra"])
    sa.thing("lion", "獅子", "lion", {"lion": lion, "lion_tiger": lambda: lion("tiger")},
             [C.swap("lion_tiger", "獅子變成老虎了！"), C.gone("獅子不見了！"), C.size(1.3, "獅子變大了！")],
             big=True, z=z["lion"])
    sa.thing("panda", "熊貓", "panda", {"panda": panda, "panda_brown": lambda: panda("#8A5A3C"), "panda_wow": lambda: panda(face="wow")},
             [C.color("panda_brown", "熊貓變成咖啡色了！"), C.face_("panda_wow", "熊貓嚇了一跳！"), C.gone("熊貓不見了！"),
              C.flip("熊貓轉向另一邊了！")],
             big=True, z=z["panda"])
    sa.thing("hippo", "河馬", "hippo", {"hippo": hippo, "hippo_pink": lambda: hippo("#FF9EC4"), "hippo_open": lambda: hippo(open_=True)},
             [C.color("hippo_pink", "河馬變成粉紅色了！"), C.face_("hippo_open", "河馬張開大嘴巴了！"), C.gone("河馬不見了！")],
             big=True, z=z["hippo"])
    sa.thing("penguins", "企鵝", "penguins", {"penguins": penguins, "penguins_two": lambda: penguins(2)},
             [C.count("penguins_two", "企鵝少了一隻！"), C.gone("企鵝不見了！"), C.flip("企鵝轉向另一邊了！")],
             big=True, z=z["penguins"])
    sa.thing("flamingos", "紅鶴", "flamingos", {"flamingos": flamingos, "flamingos_blue": lambda: flamingos("#7FB5FF")},
             [C.color("flamingos_blue", "紅鶴變成藍色了！"), C.gone("紅鶴不見了！"), C.flip("紅鶴轉向另一邊了！")],
             big=True, z=z["flamingos"])
    sa.thing("train", "小火車", "little train", {"train": train, "train_blue": lambda: train(BLUE)},
             [C.color("train_blue", "小火車變成藍色了！"), C.gone("小火車不見了！"), C.flip("小火車轉向另一邊了！")],
             big=True, z=z["train"])
    sa.thing("parrot", "鸚鵡", "parrot", {"parrot": parrot, "parrot_blue": lambda: parrot(BLUE, YELLOW, GREEN)},
             [C.color("parrot_blue", "鸚鵡變成藍色了！"), C.gone("鸚鵡不見了！"), C.flip("鸚鵡轉向另一邊了！")],
             big=True, z=3)
    sa.thing("sun", "太陽", "sun", {"sun": sun, "sun_wink": lambda: sun("wink")},
             [C.face_("sun_wink", "太陽眨眼睛了！"), C.gone("太陽不見了！")],
             big=True, z=1)
    sa.thing("monkey", "猴子", "monkey", {"monkey": monkey, "monkey_apple": lambda: monkey("apple")},
             [C.swap("monkey_apple", "猴子的香蕉變成蘋果了！"), C.gone("猴子不見了！"), C.flip("猴子轉向另一邊了！")],
             z=z["monkey"])
    sa.thing("turtle", "烏龜", "turtle", {"turtle": turtle, "turtle_orange": lambda: turtle(ORANGE)},
             [C.color("turtle_orange", "烏龜變成橘色了！"), C.gone("烏龜不見了！"), C.flip("烏龜轉向另一邊了！"), C.size(1.5, "烏龜變大了！")],
             z=z["turtle"])
    sa.thing("sign", "牌子", "sign", {"sign": sign, "sign_star": lambda: sign("star")},
             [C.pattern("sign_star", "牌子上的腳印變成星星了！"), C.gone("牌子不見了！")],
             z=z["sign"])
    sa.extra("butterfly", "蝴蝶", "butterfly", butterfly, "多了一隻蝴蝶！", z=900, big=True)
    sa.extra("babyele", "小象", "baby elephant", babyele, "多了一隻小象！", z=z["babyele"])
    sa.extra("bird", "小鳥", "bird", bird, "多了一隻小鳥！", z=4)
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"penguin": lineup_penguin, "penguin_blue": lambda: lineup_penguin(BLUE), "penguin_scarf": lambda: lineup_penguin(scarf=True)},
              "企鵝",
              # the scarf is something added (「多了一個」, for 2-3 years too): an art change without a type
              [C.color("penguin_blue", "這隻企鵝是藍色的！"), {"kind": "art", "art": "penguin_scarf", "said": "這隻企鵝圍了圍巾！"},
               C.flip("這隻企鵝轉向另一邊！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((114, 322), 38, "panda", "leaf"), ((209, 219), 34, "elephant", "wood"), ((336, 308), 38, "lion", "sand")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("giraffe", 0), ("zebra", 0), ("penguins", 0), ("train", 0), ("hippo", 1), ("butterfly", "extra:butterfly")]


if __name__ == "__main__":
    scene().build()
