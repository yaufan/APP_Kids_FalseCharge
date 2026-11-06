"""廚房 (kitchen): a home kitchen in Taiwan, as an isometric room on a floating tile.

A tile of cream and mint checks (200 x 200 world units, 1.5 px per unit) with two cream walls
along its back edges. Along the right wall: the sink under a window, the stove (a pot and a
kettle on it) and a tall white fridge at the end. Along the left wall: a counter with the rice
cooker (電鍋) and a cutting board, a wall clock, a shelf of mugs, an apron on a hook and a
broom. On the floor: a wooden table with a fruit bowl, a big potted plant, a red plastic stool
and the cat.

    background()        the warm backdrop, the tile and its checks, the walls, the tiles above the
                        counters, the cabinets, the sink and the stove: everything that never
                        changes (bg.svg, 600 x 600)
    one function per thing and per variant, returning shapes in scene px (kit.SceneArt boxes them)
    PLACE               where things are, in world units (x along the right wall, y along the left
                        wall, z up); move things here, then `python3 build.py layout kitchen`

Things hung on a wall are flat 2D drawings laid on the wall plane (on_rwall / on_lwall: a shear,
so they never get a `flip` change). Colours that 小變 hides against come from kit.TINT: the fridge
door is TINT white, the cabinet doors TINT wood, the plant TINT leaf.
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=206)
P = ISO.P
TILE = 200
WALL_H = 120          # wall height
CD = 30               # counter depth
CH = 32               # counter height (top of the worktop)
INK = "#2B3158"
WHITE = "#FFFFFF"
METAL = "#7C86A8"
DARK = "#3E4566"
BACK = "#FFE7CC"      # the warm backdrop around the room
WALL_R = "#FFF1D8"
WALL_L = "#FBE2BE"
SPLASH = "#D3F1EC"    # the tiles above the counters
FLOOR_A = "#FFF7EA"
FLOOR_B = "#9FDDD2"
SLAB = "#F4A766"
SLAB_TOP = "#FFD9AE"
TOP = "#FFF8EF"       # the worktop
TEAL = "#2FB3A3"
CAB = "#C99A70"       # cabinet frames (the doors are TINT wood)
LEAF = TINT["leaf"]
WOOD = TINT["wood"]
FRIDGE = TINT["white"]
RED = "#FF5A5F"
BLUE = "#4C8DFF"
YELLOW = "#FFD84A"
ORANGE = "#FF9838"
PINK = "#FF8FB8"
GREEN = "#5BD08A"
PURPLE = "#B48CFF"
CARROT = "#FF8A3D"
TERRACOTTA = "#E8794A"

# world positions (x, y): the point a thing stands on (its centre for round things)
PLACE = {
    "fridge": (160, 2),        # back-left corner of the fridge (38 x 38)
    "window": (20, 69),        # (x of its left edge, z of its bottom) on the right wall
    "sink": (24, 6),
    "stove": (70, 2),
    "pot": (86, 15),
    "kettle": (106, 8),
    "ricecooker": (15, 80),
    "board": (15, 125),
    "clock": (30, 90),         # (y, z) of its centre on the left wall
    "apron": (130, 110),       # (x, z) of the hook on the right wall
    "shelf": (138, 80),        # (y of its near end, z of the board) on the left wall
    "broom": (9, 188),
    "plant": (40, 180),
    "table": (104, 112),        # the table's back corner
    "cat": (176, 70),
    "stool": (44, 40),         # back-left corner: the step stool by the sink
    "mouse": (114, 200),
}


def shadow(x, y, r, op=1.0):
    return ISO.shadow(x, y, r, op=op)


def on_rwall(shapes, x, z, y=0.0, s=1.0):
    """A flat 2D drawing (u right, v down, in world units) laid on a plane y = const (the right
    wall, the front of the right counter, the fridge door), its origin at world (x, y, z)."""
    sx, sy = P(x, y, z)
    k = ISO.k * s
    return [sh.affine(kit.C30 * k, kit.S30 * k, 0, k, sx, sy) for sh in shapes]


def on_lwall(shapes, y, z, x=0.0, s=1.0):
    """The same on a plane x = const (the left wall, the front of the left counter); u runs
    towards the corner's left, i.e. to the right on screen."""
    sx, sy = P(x, y, z)
    k = ISO.k * s
    return [sh.affine(kit.C30 * k, -kit.S30 * k, 0, k, sx, sy) for sh in shapes]


def on_floor(shapes, x, y, z=0.0, s=1.0):
    """A flat 2D drawing (u along x, v along y) laid on a level plane at height z."""
    sx, sy = P(x, y, z)
    k = ISO.k * s
    return [sh.affine(kit.C30 * k, kit.S30 * k, -kit.C30 * k, kit.S30 * k, sx, sy) for sh in shapes]


def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


# ================================================================ background
def background():
    g = Group()
    g.add(Sh(rect(0, 0, 600, 600), BACK, tag="screen"), -9000)
    for (cx, cy), r in (((70, 70), 16), ((112, 40), 7), ((532, 470), 12), ((60, 520), 9)):
        g.add(oval(cx, cy, r, col="#FFD3A8", tag="detail"), -8500)
    # the island's shadow on the air below
    cx, cy = P(TILE / 2, TILE / 2, -20)
    g.add(Sh(ellp(cx, cy + 40, 226, 22), "#3B5A7A", tag="shadow", op=.9), -7000)
    # walls (the right one first: the left one covers the corner)
    g.add(ISO.box(-6, -6, -20, TILE + 6, 6, WALL_H + 20, WALL_R, top=WHITE, left=WALL_R, right=mix(SLAB, WALL_R, .35)), -6900)
    g.add(ISO.box(-6, 0, -20, 6, TILE, WALL_H + 20, WALL_L, top=WHITE, right=WALL_L, left=mix(SLAB, WALL_L, .35)), -6890)
    # the tile: a slab and a floor of cream and mint checks
    g.add(ISO.box(0, 0, -20, TILE, TILE, 15, SLAB)[:2], -6000)
    g.add(ISO.box(0, 0, -5, TILE, TILE, 5, SLAB_TOP, top=FLOOR_A), -5900)
    # checks: 25 units in a and b; a child draws them bigger (50 units) in c
    for q, only in ((25, "ab"), (50, "c")):
        m = TILE // q
        for i in range(1, m):
            for j in range(1, m):
                if (i + j) % 2 == 0:
                    g.add(ISO.flat(rect(i * q, j * q, q, q), 0, FLOOR_B, tag="detail", only=only), -5800)
    # wall tiles above the counters, a strip of skirting and the shelf
    for wall, L, at in ((on_rwall, 158, 0), (on_lwall, 142, 142)):
        g.add(wall([Sh(rect(0, 0, L, 26), SPLASH, tag="detail")] +
                   [line([(u, 0), (u, 26)], WHITE, 1.1, only="ab" if u % 26 else None) for u in range(13, L, 13)] +
                   [line([(0, 13), (L, 13)], WHITE, 1.1)], at, CH + 26, .1), -5000)
    sy, sz = PLACE["shelf"]
    g.add(ISO.box(0, sy - 2, sz - 3, 12, 56, 3, WOOD), -4900)
    for yy in (sy + 4, sy + 48):
        g.add(on_lwall([Sh([(0, 0), (4, 0), (0, 8)], kit.tone(WOOD, .8))], yy, sz - 3, .1), -4895)
    hx, hz = PLACE["apron"]
    g.add(on_rwall([oval(0, 0, 2.6, col=METAL)], hx, hz, .1), -4890)
    # a round rug under the table
    tx, ty, _ = table_top()
    g.add(ISO.disc(tx, ty, .05, 40, "#FFC58F"), -4800)
    g.add(ISO.disc(tx, ty, .06, 33, "#FFE3C2", tag="detail", only="ab"), -4790)
    g.add(ISO.disc(tx, ty, .07, 27, "#FFB37A", tag="detail"), -4780)
    # the counters: cabinets (wood doors), a worktop
    g.add(counters(), 0)
    g.add(sink(), 50)
    g.add(stove(), 60)
    return g.shapes()


def door_r(x0, w, z0, h, y):
    """A cabinet door on the front of the right counter (plane y)."""
    o = [Sh(rrect(0, 0, w, h, 1.6), WOOD, tag="detail"),
         oval(w - 4 if w < 30 else w / 2, 5 if w < 30 else 4, 1.6, col=TEAL)]
    return on_rwall(o, x0, z0 + h, y)


def counters():
    g = Group()
    # right run (with the corner): x 0..158, y 0..30
    g.add(ISO.box(0, 0, 0, 158, CD, CH - 3, CAB), 0)
    # left run: x 0..30, y 30..142
    g.add(ISO.box(0, CD, 0, CD, 112, CH - 3, CAB), 1)
    # doors: right run (the stove's oven takes x 66..110)
    for x0, w in ((32, 38), (114, 22), (136, 20)):
        g.add(door_r(x0 + 1, w - 2, 5, 21, CD + .1), 3)
    # doors on the left run (plane x = CD)
    for y0, w in ((34, 34), (70, 34), (106, 34)):
        o = [Sh(rrect(0, 0, w - 2, 21, 1.6), WOOD, tag="detail"), oval((w - 2) / 2, 4, 1.6, col=TEAL)]
        g.add(on_lwall(o, y0 + w - 1, 26, CD + .1), 3)
    # the worktop (a little overhang)
    for i, (x, y, w, d) in enumerate(((-1, -1, 160, CD + 2), (-1, CD + 1, CD + 2, 112))):
        top = ISO.box(x, y, CH - 3, w, d, 3, TOP, left=mix(TOP, "#E9D8C0", .6), right=mix(TOP, "#E9D8C0", .8))
        g.add([sh.copy(tag="detail") if sh.face != "top" else sh for sh in top], 4 + i)
    return g.shapes()


def sink():
    x, y = PLACE["sink"]
    o = [ISO.flat(rect(x, y, 34, 18), CH + .05, "#C9D6E8", tag="detail"),
         ISO.flat(rect(x + 2.5, y + 2.5, 29, 13), CH + .06, "#A9BBD6", tag="detail")]
    # the tap: a little gooseneck at the back
    tx, ty = x + 17, y - 2.5
    o += ISO.cyl(tx, ty, CH, 2.2, 2, METAL)
    o.append(ISO.line3([(tx, ty, CH + 2), (tx, ty, CH + 15), (tx, ty + 4, CH + 18), (tx, ty + 8, CH + 15), (tx, ty + 8, CH + 12)], METAL, 1.8))
    o.append(ISO.line3([(tx - 4, ty, CH + 4), (tx + 4, ty, CH + 4)], RED, 1.6))
    return o


def stove():
    x, y = PLACE["stove"]
    o = ISO.box(x, y + 1, CH, 44, 26, 1.2, DARK)
    for (bx, by), r in (((x + 14, y + 15), 9.5), ((x + 35, y + 8), 6.5)):
        sx, sy = P(bx, by, CH + 1.25)
        o.append(oval(sx, sy, r * 1.2247 * ISO.k, r * .7071 * ISO.k, col="#5A6488", tag="detail"))
        o.append(oval(sx, sy, r * .62 * 1.2247 * ISO.k, r * .62 * .7071 * ISO.k, col=DARK))
    # the oven in the cabinet below: a dark window, a handle, two knobs
    ov = [Sh(rrect(0, 0, 40, 22, 2), "#5A6488"), Sh(rrect(5, 7, 30, 12, 2), "#2E3350"),
          line([(8, 4), (32, 4)], "#C9D1E4", 1.6), oval(8, -3, 2, col=WHITE), oval(32, -3, 2, col=WHITE)]
    o += on_rwall(ov, x + 2, 27, CD + .1)
    return o


# ================================================================ things
# ---------------------------------------------------------------- fridge (TINT white: 小變 hides against its door)
def magnet_sprites(n_):
    heart = Sh(crs([(0, 3), (-4.6, -1.4), (-3.4, -4.6), (0, -2.8), (3.4, -4.6), (4.6, -1.4)], 5), RED, cel=.5)
    star = Sh(kit.star_pts(4.6, 2.2, 0, 0), YELLOW)
    dot = oval(0, 0, 3.6, col=BLUE, cel=.6)
    out = [(heart, (9, 10))]
    if n_ >= 3:
        out += [(star, (22, 18)), (dot, (12, 44))]
    return [s for sh, (u, v) in out for s in transform([sh], dx=u, dy=v)]


def fridge(col=FRIDGE, magnets=3):
    x0, y0 = PLACE["fridge"]
    w, d, h = 38, 38, 92
    fy = y0 + d + .15
    g = Group()
    # the white fridge prints as paper in riso: give its side a pale blue of its own
    g.add(ISO.box(x0, y0, 0, w, d, h, col, right="#C3D0EA" if col == FRIDGE else None), 0)
    seam = mix(col, "#8C96B0", .45)
    g.add(on_rwall([line([(1.5, 0), (w - 1.5, 0)], seam, 1.3)], x0, 62, fy), 1)
    g.add(on_rwall([Sh(rect(1, 0, w - 2, 3), mix(col, "#8C96B0", .3))], x0, 3, fy), 1)
    g.add(ISO.box(x0 + 4, fy, 66, 2.2, 2, 18, METAL), 2)
    g.add(ISO.box(x0 + 4, fy, 34, 2.2, 2, 22, METAL), 2)
    g.add(on_rwall(magnet_sprites(magnets), x0, h - 6, fy), 3)
    return g.shapes()


# ---------------------------------------------------------------- window over the sink (curtains)
WIN_W, WIN_H = 48, 40


def window(cur=ORANGE, dots=False):
    x0, z0 = PLACE["window"]
    W, Hh = WIN_W, WIN_H
    o = [Sh(rrect(-1, -1, W + 2, Hh + 2, 3), WHITE), Sh(rrect(3, 3, W - 6, Hh - 6, 2), "#BDE8FF")]
    o.append(Sh(tf(crs([(-9, 2), (-8, -3), (-2, -5), (3, -8), (9, -5), (11, 1)]), dx=W * .62, dy=Hh * .36), WHITE))
    o.append(Sh(tf(crs([(-9, 2), (-8, -3), (-2, -5), (3, -8), (9, -5), (11, 1)]), dx=W * .3, dy=Hh * .7, s=.7), WHITE))
    o.append(Sh(rect(W / 2 - 1.3, 2, 2.6, Hh - 4), WHITE))
    o.append(Sh(rect(2, Hh * .48 - 1.3, W - 4, 2.6), WHITE))
    o.append(line([(-6, -4), (W + 6, -4)], kit.tone(WOOD, .85), 2.2))
    for side in (0, 1):
        pts = [(-6, -4), (8, -4), (7, 8), (4, 20), (5, 30), (2, 33), (-5, 30), (-5, 18), (-4, 6)]
        if side:
            pts = [(W - x, y) for x, y in pts]
        o.append(Sh(crs(pts, 6), cur))
        mx = 2 if not side else W - 2
        o.append(line([(mx - 4, 24), (mx + 4, 24.5)], kit.tone(cur, .8, 1.1), 2))
        if dots:
            for u, v in ((-1, 3), (4, 11), (-2, 19), (3, 27)):
                o.append(oval(u if not side else W - u, v, 2.2, col=WHITE, tag="detail"))
    g = Group()
    g.add(on_rwall(o, x0, z0 + Hh, .2), 0)
    g.add(ISO.box(x0 - 3, 0, z0 - 3, W + 6, 6, 3, WHITE, left="#F1F4FA"), 1)
    # a little flower pot on the sill
    sx, sy = P(x0 + 9, 3, z0)
    fl = [Sh([(-4, 0), (4, 0), (5, -6), (-5, -6)], TERRACOTTA), line([(0, -6), (0, -13)], "#4FAE5C", 1.6),
          Sh(crs([(0, -9), (-5, -12), (-2, -9)], 4), LEAF)]
    fl += [oval(3 * math.cos(math.radians(a)), -15 + 3 * math.sin(math.radians(a)), 2.4, col=PINK, tag="detail") for a in range(0, 360, 72)]
    fl.append(oval(0, -15, 1.6, col=YELLOW, tag="detail"))
    g.add(transform(fl, dx=sx, dy=sy, s=1.1), 2)
    return g.shapes()


# ---------------------------------------------------------------- pot on the stove
def pot(col=TEAL):
    x, y = PLACE["pot"]
    z = CH + 1.2
    R, h = 14, 13
    g = Group()
    sx, sy = P(x, y, z)
    rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
    hh = h * ISO.k
    for side in (-1, 1):
        g.add([Sh(rrect(sx + side * (rx + 2) - 7, sy - hh * .78 - 3, 14, 6, 3), DARK)], -1)
    g.add(ISO.cyl(x, y, z, R, h, col), 0)
    g.add(ISO.disc(x, y, z + h, R + .8, mix(col, WHITE, .25)), 1)
    # the lid: a low dome and a knob
    tx, ty = sx, sy - hh
    dome = [(tx + rx * .96 * math.cos(math.pi + math.pi * i / 20), ty - ry * 1.5 * math.sin(math.pi * i / 20)) for i in range(21)]
    dome += [(tx + rx * .96 * math.cos(math.pi * i / 20), ty + ry * .9 * math.sin(math.pi * i / 20)) for i in range(1, 20)]
    g.add(Sh(dome, kit.tone(col, .92, 1.05), cel=.8), 2)
    g.add([Sh(rrect(tx - 5, ty - ry * 1.5 - 6, 10, 6, 2.5), DARK)], 3)
    return g.shapes()


# ---------------------------------------------------------------- kettle (a 2D sprite, spout to the left)
def kettle_sprite(col=YELLOW):
    dark = kit.tone(col, .8, 1.05)
    o = [Sh(crs([(-14, -5), (-10, -18), (12, -18), (16, -5), (16, -1), (-14, -1)], 6), col, cel=1.0)]
    o.append(Sh(tube(crs([(-11, -8), (-20, -14), (-25, -24)], 6, closed=False), 6, 3.4), col, cel=.4))
    o.append(oval(1, -19, 11, 3, col=dark))
    o.append(oval(1, -22, 2.8, col=DARK))
    o.append(line(crs([(-8, -18), (-6, -30), (8, -30), (10, -18)], 6, closed=False), DARK, 2.6))
    o.append(oval(-6, -10, 2.6, 4, col=WHITE, op=.7, tag="detail"))
    o.append(Sh(rect(-14, -3, 30, 3), dark))
    return o


def kettle(col=YELLOW):
    x, y = PLACE["kettle"]
    sx, sy = P(x, y, CH + 1.2)
    return transform(kettle_sprite(col), dx=sx, dy=sy, s=1.05)


# ---------------------------------------------------------------- rice cooker (電鍋: a round body, a domed lid, side handles; no logo)
def ricecooker(col=PINK):
    x, y = PLACE["ricecooker"]
    z = CH
    R, h = 15, 17
    sx, sy = P(x, y, z)
    rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
    hh = h * ISO.k
    g = Group()
    g.add(ISO.shadow(x + 1, y + 1, R + 1, z=CH, op=.7), -1)
    for side in (-1, 1):       # the two ears near the top
        g.add([Sh(rrect(sx + side * (rx + 1.5) - 6.5, sy - hh * .8 - 3.2, 13, 6.4, 3.2), DARK)], 0)
    g.add(ISO.cyl(x, y, z, R, h, col), 1)
    g.add(ISO.cyl(x, y, z + h * .52, R + .25, 1.6, mix(col, WHITE, .45)), 1.5)
    g.add(ISO.disc(x, y, z + h, R + .7, mix(col, WHITE, .3)), 2)
    tx, ty = sx, sy - hh
    dome = [(tx + rx * .9 * math.cos(math.pi + math.pi * i / 20), ty - ry * .95 * math.sin(math.pi * i / 20)) for i in range(21)]
    dome += [(tx + rx * .9 * math.cos(math.pi * i / 20), ty + ry * .9 * math.sin(math.pi * i / 20)) for i in range(1, 20)]
    g.add(Sh(dome, mix(col, WHITE, .14), cel=.9), 3)
    kt = ty - ry * .95
    g.add([Sh(rrect(tx - 3, kt - 6, 6, 6, 1.5), DARK), oval(tx, kt - 6.5, 6.5, 3.2, col="#5A6488", cel=.5)], 4)
    # the switch and the little light at the front
    fx, fy = P(x + R * .72, y + R * .72, z + 4)
    g.add([Sh(rrect(fx - 4.5, fy - 4, 9, 6, 2), DARK), oval(fx + 8, fy - 10, 2.2, col=YELLOW, tag="detail")], 5)
    return g.shapes()


# ---------------------------------------------------------------- wall clock (a face: smile / surprised)
def clock(rim=ORANGE, face="smile"):
    cy_, cz = PLACE["clock"]
    r = 26
    o = [oval(0, 0, r, col=rim), oval(0, 0, r - 5, col=WHITE)]
    for i in range(4):
        a = math.radians(i * 90)
        o.append(oval((r - 8.5) * math.cos(a), (r - 8.5) * math.sin(a), 1.8, col=INK, tag="detail"))
    o.append(line([(0, 0), (-7, -6)], INK, 2.4))
    o.append(line([(0, 0), (8, -9)], INK, 1.8))
    o.append(oval(0, 0, 1.8, col=RED))
    o.append(oval(-10, 7, 3, 1.8, col="#FF9DB6", op=.85, tag="detail"))
    o.append(oval(10, 7, 3, 1.8, col="#FF9DB6", op=.85, tag="detail"))
    if face == "smile":
        for ex in (-6, 6):
            o.append(line([(ex - 2.4, 4.6), (ex, 2.6), (ex + 2.4, 4.6)], INK, 1.6))
        o.append(line(crs([(-4.5, 9), (0, 12.5), (4.5, 9)], 6, closed=False), INK, 1.8))
    else:
        for ex in (-6, 6):
            o.append(oval(ex, 4, 2.2, 2.8, col=INK))
        o.append(oval(0, 12, 2.6, 3.2, col=INK))
    return on_lwall(o, cy_, cz, .2)


# ---------------------------------------------------------------- mugs on the shelf
def mug3d(x, y, z, col, dots=False):
    """A mug standing at world (x, y, z): a little cylinder, the handle to the right."""
    R, h = 5.2, 9
    sx, sy = P(x, y, z)
    rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
    hh = h * ISO.k
    o = [Sh(tube(crs([(sx + rx - 1, sy - hh * .8), (sx + rx + 5.5, sy - hh * .62), (sx + rx + 5, sy - hh * .25), (sx + rx - 1, sy - hh * .2)],
                     6, closed=False), 2.6), col)]
    o += ISO.cyl(x, y, z, R, h, col)
    o.append(oval(sx, sy - hh, rx, ry, col=mix(col, WHITE, .35)))
    o.append(oval(sx, sy - hh + .8, rx * .78, ry * .7, col=kit.tone(col, .6, 1.05)))
    if dots:
        for du, dv in ((-4, -4), (3, -8), (5, -2.5), (-2, -10)):
            o.append(oval(sx + du, sy + dv, 1.6, col=WHITE, tag="detail"))
    else:
        o.append(Sh([(sx - rx + .4, sy - hh * .5), (sx + rx - .4, sy - hh * .5), (sx + rx - .4, sy - hh * .5 + 2.6), (sx - rx + .4, sy - hh * .5 + 2.6)],
                    WHITE, tag="detail"))
    return o


def mugs(col=BLUE, n_=3, dots=False):
    y0, z0 = PLACE["shelf"]
    g = Group()
    for i, yy in enumerate((y0 + 8, y0 + 26, y0 + 44)):
        if n_ == 2 and i == 1:
            continue
        g.add(mug3d(6, yy, z0, col, dots), 6 + yy)
    return g.shapes()


# ---------------------------------------------------------------- cutting board with carrots (or cucumbers)
def carrot(col=CARROT, top="#4FAE5C"):
    o = [Sh(crs([(0, -3.4), (14, -1.6), (19, 0), (14, 1.6), (0, 3.4), (-1.4, 0)], 5), col, cel=.5)]
    for k in (5, 9):
        o.append(line([(k, -2.2), (k + 1, -.6)], kit.tone(col, .8), .9))
    o += [Sh(crs([(-1, -1), (-8, -5), (-6, -1)], 4), top), Sh(crs([(-1, 1), (-8, 4), (-6, 0)], 4), top)]
    return o


def cucumber():
    col = "#4FB36A"
    o = [Sh(tube(crs([(-1, 0), (9, -.6), (19, 0)], 6, closed=False), 6.4), col, cel=.5)]
    for u in (4, 9, 14):
        o.append(oval(u, -1.2, .9, col=mix(col, WHITE, .5), tag="detail"))
    return o


def board(n_=3, veg="carrot"):
    x, y = PLACE["board"]
    g = Group()
    g.add(ISO.box(x - 10, y - 15, CH, 20, 30, 1.6, "#E8C08A"), 0)
    sx, sy = P(x - 6, y + 11, CH + 1.6)
    g.add([oval(sx, sy, 2.6, 1.6, col=kit.tone("#E8C08A", .75))], 1)
    for i in range(3):
        if n_ == 2 and i == 1:
            continue
        sx, sy = P(x - 4 + i * 4, y - 8 + i * 6, CH + 3)
        sp = carrot() if veg == "carrot" else cucumber()
        g.add(transform(sp, dx=sx - 9, dy=sy, s=1.05, rot=-14), 2 + i)
    return g.shapes()


# ---------------------------------------------------------------- apron on a hook
def apron(col=ORANGE, dots=False):
    hx, hz = PLACE["apron"]
    o = [line(crs([(-6, 9), (-3, 1), (0, -1), (3, 1), (6, 9)], 6, closed=False), kit.tone(col, .85), 1.6)]
    o.append(Sh(crs([(-7, 8), (7, 8), (9, 20), (13, 40), (0, 42), (-13, 40), (-9, 20)], 6), col))
    o.append(line([(-9, 21), (-17, 27)], kit.tone(col, .85), 1.6))
    o.append(line([(9, 21), (17, 27)], kit.tone(col, .85), 1.6))
    o.append(Sh(rrect(-6, 26, 12, 9, 2.4), WHITE))
    if dots:
        for u, v in ((-3, 13), (4, 18), (-8, 31), (8, 33), (-1, 24), (-2, 39)):
            o.append(oval(u, v, 2.2, col=WHITE, tag="detail"))
    else:
        o.append(line([(-5, 15), (5, 15)], WHITE, 1.4))
    return on_rwall(o, hx, hz, .3)


# ---------------------------------------------------------------- broom (leans to the right)
def broom_sprite(col=YELLOW):
    dark = kit.tone(col, .78, 1.05)
    o = [line([(2, -24), (13, -96)], WOOD, 3.2)]
    o.append(Sh(crs([(-11, 0), (-6, -17), (5, -24), (12, -22), (14, -6), (12, 0)], 6), col))
    for u in (-6, -1, 4, 9):
        o.append(line([(u, -1), (u + 2, -14)], dark, 1.1))
    o.append(Sh([(-3, -18), (10, -21), (11, -24), (-1, -22)], RED))
    return o


def broom(col=YELLOW):
    x, y = PLACE["broom"]
    sx, sy = P(x, y)
    return shadow(x + 2, y + 2, 7, .7) + transform(broom_sprite(col), dx=sx, dy=sy, s=1.05)


# ---------------------------------------------------------------- the table and the fruit bowl
TABLE_W, TABLE_D, TABLE_H = 44, 36, 26


def table(col=WOOD):
    x, y = PLACE["table"]
    g = Group()
    g.add(shadow(x + TABLE_W / 2 + 3, y + TABLE_D / 2 + 3, 26, .7), -1)
    for lx, ly in ((x + 2, y + 2), (x + TABLE_W - 5, y + 2), (x + 2, y + TABLE_D - 5), (x + TABLE_W - 5, y + TABLE_D - 5)):
        g.add(ISO.box(lx, ly, 0, 3, 3, TABLE_H - 3, kit.tone(col, .9)), lx + ly)
    g.add(ISO.box(x, y, TABLE_H - 3, TABLE_W, TABLE_D, 3, col, top=col), 500)
    return g.shapes()


def table_top():
    x, y = PLACE["table"]
    return x + TABLE_W / 2, y + TABLE_D / 2, TABLE_H


def apple(col=RED):
    return [oval(0, -5, 5.4, 5, col=col, cel=.6), line([(0, -9.6), (1, -12.6)], "#7A5232", 1.3),
            Sh(crs([(1, -11), (6, -13.5), (3, -10)], 4), LEAF)]


def orange_fruit():
    return [oval(0, -5.2, 5.6, 5.2, col=ORANGE, cel=.6), oval(0, -10, 1, col="#4FAE5C", tag="detail"),
            Sh(crs([(.5, -10), (5, -12.5), (3, -9.4)], 4), "#4FAE5C")]


def fruit(n_=3, kind="apple"):
    cx, cy, z = table_top()
    sx, sy = P(cx - 4, cy - 4, z)
    g = Group()
    spots = ((-8, -9), (8, -9), (0, -14))
    for i, (u, v) in enumerate(spots):
        if n_ == 2 and i == 2:
            continue
        sp = apple() if kind == "apple" else orange_fruit()
        g.add(transform(sp, dx=sx + u * 1.1, dy=sy + v * 1.1 + 2, s=1.25), 1 + (i == 2) * -.5)
    bowl = [Sh([(sx - 17, sy - 9)] + [(sx + 17 * math.cos(math.radians(a)), sy - 9 + 11 * math.sin(math.radians(a))) for a in range(0, 181, 12)], WHITE, cel=.5),
            oval(sx, sy - 9, 17, 4, col="#E3F4F1"),
            Sh(rect(sx - 13, sy - 6, 26, 2.6), TEAL, tag="detail")]
    g.add(bowl[:2], 0)
    g.add(bowl[2:], 3)
    return g.shapes()


# ---------------------------------------------------------------- cat (and the dog it turns into), facing left
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


def dog_sprite(col="#D9A066"):
    ear = kit.tone(col, .72, 1.1)
    light = mix(col, WHITE, .5)
    o = [Sh(tube(crs([(14, -10), (22, -16), (26, -26)], 6, closed=False), 5, 3.4), col, cel=.5)]
    o.append(Sh(crs([(-14, 0), (14, 0), (17, -12), (10, -26), (-6, -28), (-15, -16)]), col, cel=1.0))
    o.append(oval(-6, -13, 6, 10, col=light))
    for lx in (-10, -3):
        o.append(Sh(rrect(lx - 2.6, -12, 5.2, 12, 2.6), col, cel=.3))
    o.append(Sh(rrect(-17, -30, 18, 4, 2), RED))
    o.append(oval(-8, -40, 13.5, 12, col=col, cel=1.0))
    o.append(oval(-18, -35, 8, 6, col=light, cel=.4))
    o.append(oval(-24, -37, 3, 2.6, col=INK))
    o.append(oval(-11, -44, 2.2, 2.8, col=INK))
    o.append(oval(-2, -44, 2.2, 2.8, col=INK))
    o.append(Sh(crs([(-20, -50), (-13, -54), (-10, -44), (-15, -34), (-21, -40)]), ear, cel=.5))
    o.append(Sh(crs([(2, -54), (9, -50), (8, -38), (3, -34), (-1, -44)]), ear, cel=.5))
    o.append(line(crs([(-21, -31), (-18, -29), (-15, -31)], 4, closed=False), INK, 1.4))
    return o


def critter(name, sprite, s=1.0, r=13):
    x, y = PLACE[name]
    sx, sy = P(x, y)
    return shadow(x + 1, y + 1, r, .8) + transform(sprite, dx=sx, dy=sy, s=s)


# ---------------------------------------------------------------- red plastic stool (塑膠椅凳)
def stool(col=RED):
    x, y = PLACE["stool"]
    S, h = 26, 17
    g = Group()
    g.add(shadow(x + S / 2 + 2, y + S / 2 + 2, 17, .7), -1)
    leg = kit.tone(col, .92)
    for lx, ly in ((x + 1, y + 1), (x + S - 6, y + 1), (x + 1, y + S - 6), (x + S - 6, y + S - 6)):
        g.add(ISO.box(lx, ly, 0, 5, 5, h - 3, leg), lx + ly)
    g.add(ISO.box(x + 2, y + 2, h - 8, S - 4, S - 4, 3, leg), 400)
    g.add(ISO.box(x, y, h - 3, S, S, 3, col), 500)
    g.add(on_floor([Sh(rrect(-6, -2, 12, 4, 2), kit.tone(col, .55, 1.1))], x + S / 2, y + S / 2, h + .05), 501)
    return g.shapes()


# ---------------------------------------------------------------- big potted plant (TINT leaf: 小變 hides in its leaves)
def plant(pot_col=TERRACOTTA):
    x, y = PLACE["plant"]
    g = Group()
    g.add(shadow(x + 2, y + 2, 14, .8), -1)
    R, h = 10, 18
    sx, sy = P(x, y)
    rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
    body = [(sx + rx * .8 * math.cos(math.radians(a)), sy + ry * .8 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    body += [(sx - rx, sy - h * ISO.k), (sx + rx, sy - h * ISO.k)]
    g.add([Sh(body, pot_col, cel=.8)], 0)
    tz = sy - h * ISO.k
    g.add([oval(sx, tz, rx + 1.5, ry + 1, col=mix(pot_col, WHITE, .2)), oval(sx, tz, rx - 1, ry - 1.5, col="#7A5232")], 1)
    leaves = [(-30, -40, 15, 7, -35), (28, -42, 15, 7, 32), (-18, -62, 15, 7, -62), (16, -64, 15, 7, 60), (-2, -72, 14, 7, 92),
              (-34, -22, 13, 6, -14), (33, -24, 13, 6, 12)]
    for i, (u, v, a, b, rot) in enumerate(leaves):
        lx, ly = sx + u, tz + v + 8
        stem = line(crs([(sx + u * .1, tz - 2), (sx + u * .55, tz + v * .5), (lx - math.cos(math.radians(rot)) * a * .7, ly - math.sin(math.radians(rot)) * a * .7)], 5, closed=False), "#3E9E50", 1.8)
        leaf = Sh(tf(crs([(-a, 0), (-a * .3, -b), (a * .5, -b * .8), (a, 0), (a * .5, b * .8), (-a * .3, b)], 6), rot=rot, dx=lx, dy=ly), LEAF, cel=.6)
        vein = line(tf([(-a * .8, 0), (a * .75, 0)], rot=rot, dx=lx, dy=ly), mix(LEAF, "#2E7D3C", .5), 1.1, op=.8)
        g.add([stem, leaf, vein], 2 + i * .1 + (v > -30) * 1)
    return g.shapes()


# ================================================================ extras
def mouse_sprite():
    col = "#A9B1C6"
    o = [line(crs([(10, -3), (18, -4), (22, -10), (28, -8)], 6, closed=False), "#C9A2B4", 1.4)]
    o.append(Sh(crs([(-12, 0), (12, 0), (11, -8), (2, -13), (-8, -11)]), col, cel=.8))
    o.append(oval(-7, -13, 4.6, col=col, cel=.4))
    o.append(oval(-7, -13, 2.6, col="#FFB3C6", tag="detail"))
    o.append(Sh(crs([(-10, -9), (-17, -4), (-10, -3)], 4), col))
    o.append(oval(-17, -4, 1.6, col="#FF8FA8", tag="detail"))
    o.append(oval(-11, -7, 1.3, col=INK))
    return o


def mouse():
    return critter("mouse", mouse_sprite(), 1.15, 8)


def balloon():
    cx, cy = 512, 92
    lt_ = mix(PINK, WHITE, .1)
    o = [line(crs([(0, 0), (5, 14), (-3, 28), (2, 44)], 6, closed=False), METAL, 1.3)]
    o += [Sh(crs([(-5, 1), (5, 1), (0, -9)], 4), PINK),
          Sh(crs([(0, -6), (14, -12), (22, -30), (18, -50), (0, -60), (-18, -50), (-22, -30), (-14, -12)]), lt_, cel=1.0),
          oval(-9, -42, 4, 7.5, col=WHITE, rot=25, op=.8, tag="detail")]
    return transform(o, dx=cx, dy=cy + 10, s=1.5)


def milk():
    cx, cy, z = table_top()
    sx, sy = P(cx + 13, cy + 5, z)
    glass = "#DDEFF8"
    o = [oval(0, 0, 6, 2.2, col=glass), Sh([(-6, -17), (6, -17), (5.4, 0), (-5.4, 0)], glass),
         Sh([(-5.4, -13), (5.4, -13), (5, -1), (-5, -1)], WHITE), oval(0, -13, 5.4, 1.6, col="#F4F7FC"),
         oval(0, -17, 6, 2, col="#EEF7FB"), Sh([(-4, -15), (-2.6, -15), (-2.6, -3), (-4, -3)], "#F8FCFF", tag="detail")]
    return transform(o, dx=sx, dy=sy, s=1.4)


# ================================================================ lineup (哪一個不一樣？): a mug
def lineup_mug(col=RED, spoon=False):
    o = [oval(2, 0, 34, 6, col="#E9D9C2", op=.8)]
    o.append(Sh(tube(crs([(20, -40), (36, -38), (38, -22), (20, -14)], 8, closed=False), 7), kit.tone(col, .9)))
    o.append(Sh(crs([(-24, -52), (24, -52), (23, -8), (16, 0), (-16, 0), (-23, -8)], 6), col, cel=1.0))
    o.append(Sh(rect(-23.6, -34, 47.2, 9), WHITE))
    o.append(oval(0, -52, 24, 6, col=kit.tone(col, .62, 1.05)))
    o.append(oval(0, -52, 24, 6, col=mix(col, WHITE, .3)))
    o.append(oval(0, -51, 21, 4.6, col="#8A5A3C"))
    if spoon:
        o.append(Sh(tube([(4, -50), (16, -78)], 4.6, 4.6), "#B7C0D6"))
        o.append(oval(17.5, -81, 4.6, 6.4, col="#C9D1E4", rot=24))
    o.append(oval(-14, -42, 2.8, 6, col=WHITE, op=.6, tag="detail"))
    return transform(o, s=1.6)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("kitchen", "廚房", "kitchen")
    sa.background(background)
    C = kit

    def z(name, dz=0.0):
        x, y = PLACE[name]
        return int(x + y + dz)
    sa.thing("fridge", "冰箱", "fridge",
             {"fridge": fridge, "fridge_pink": lambda: fridge("#FFB3CC"), "fridge_magnets": lambda: fridge(magnets=1)},
             [C.color("fridge_pink", "冰箱變成粉紅色了！"), C.count("fridge_magnets", "冰箱上的磁鐵變少了！"), C.gone("冰箱不見了！")],
             big=True, z=z("fridge", 38))
    sa.thing("window", "窗戶", "window",
             {"window": window, "window_green": lambda: window(GREEN), "window_dots": lambda: window(dots=True)},
             [C.color("window_green", "窗簾變成綠色了！"), C.pattern("window_dots", "窗簾變成點點了！"), C.gone("窗戶不見了！")],
             big=True, z=10)
    sa.thing("pot", "鍋子", "pot", {"pot": pot, "pot_red": lambda: pot(RED)},
             [C.color("pot_red", "鍋子變紅色了！"), C.gone("鍋子不見了！"), C.size(1.3, "鍋子變大了！")],
             big=True, z=z("pot"))
    sa.thing("kettle", "水壺", "kettle", {"kettle": kettle, "kettle_blue": lambda: kettle(BLUE)},
             [C.flip("水壺轉向另一邊了！"), C.color("kettle_blue", "水壺變成藍色了！"), C.gone("水壺不見了！")],
             z=z("kettle"))
    sa.thing("ricecooker", "電鍋", "rice cooker", {"ricecooker": ricecooker, "ricecooker_green": lambda: ricecooker(GREEN)},
             [C.color("ricecooker_green", "電鍋變成綠色了！"), C.gone("電鍋不見了！")],
             big=True, z=z("ricecooker"))
    sa.thing("clock", "時鐘", "clock", {"clock": clock, "clock_purple": lambda: clock(PURPLE), "clock_wow": lambda: clock(face="wow")},
             [C.face_("clock_wow", "時鐘嚇了一跳！"), C.color("clock_purple", "時鐘變成紫色了！"), C.gone("時鐘不見了！")],
             big=True, z=12)
    sa.thing("mugs", "杯子", "mugs",
             {"mugs": mugs, "mugs_red": lambda: mugs(RED), "mugs_two": lambda: mugs(n_=2), "mugs_dots": lambda: mugs(dots=True)},
             [C.color("mugs_red", "杯子變成紅色了！"), C.count("mugs_two", "杯子少了一個！"), C.pattern("mugs_dots", "杯子變成點點了！")],
             big=True, z=14)
    sa.thing("board", "紅蘿蔔", "carrots",
             {"board": board, "board_two": lambda: board(2), "board_cucumber": lambda: board(veg="cucumber")},
             [C.count("board_two", "紅蘿蔔少了一根！"), C.swap("board_cucumber", "紅蘿蔔變成小黃瓜了！")],
             z=z("board"))
    sa.thing("apron", "圍裙", "apron", {"apron": apron, "apron_green": lambda: apron(GREEN), "apron_dots": lambda: apron(dots=True)},
             [C.pattern("apron_dots", "圍裙變成點點了！"), C.color("apron_green", "圍裙變成綠色了！"), C.gone("圍裙不見了！")],
             z=16)
    sa.thing("broom", "掃把", "broom", {"broom": broom, "broom_red": lambda: broom(RED)},
             [C.color("broom_red", "掃把變成紅色了！"), C.gone("掃把不見了！"), C.flip("掃把倒向另一邊了！")],
             z=z("broom"))
    sa.thing("table", "桌子", "table", {"table": table, "table_blue": lambda: table(BLUE)},
             [C.color("table_blue", "桌子變成藍色了！")],
             big=True, z=z("table", 20))
    sa.thing("fruit", "蘋果", "apples", {"fruit": fruit, "fruit_two": lambda: fruit(2), "fruit_orange": lambda: fruit(kind="orange")},
             [C.count("fruit_two", "蘋果少了一顆！"), C.swap("fruit_orange", "蘋果變成橘子了！")],
             z=z("table", 40))
    sa.thing("cat", "小貓", "cat", {"cat": lambda: critter("cat", cat_sprite(), 1.45), "cat_dog": lambda: critter("cat", dog_sprite(), 1.45)},
             [C.swap("cat_dog", "小貓變成小狗了！"), C.flip("小貓轉向另一邊了！"), C.gone("小貓不見了！")],
             big=True, z=z("cat"))
    sa.thing("stool", "小板凳", "stool", {"stool": stool, "stool_yellow": lambda: stool(YELLOW)},
             [C.color("stool_yellow", "小板凳變成黃色了！"), C.gone("小板凳不見了！"), C.size(1.3, "小板凳變大了！")],
             big=True, z=z("stool", 20))
    sa.thing("plant", "盆栽", "potted plant", {"plant": plant, "plant_purple": lambda: plant(PURPLE)},
             [C.color("plant_purple", "花盆變成紫色了！"), C.gone("盆栽不見了！"), C.size(1.25, "盆栽變大了！")],
             big=True, z=z("plant"))
    sa.extra("mouse", "小老鼠", "mouse", mouse, "多了一隻小老鼠！", z=z("mouse"))
    sa.extra("balloon", "氣球", "balloon", balloon, "多了一個氣球！", z=3, big=True)
    sa.extra("milk", "牛奶", "milk", milk, "桌上多了一杯牛奶！", z=z("table", 41))
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"mug": lineup_mug, "mug_blue": lambda: lineup_mug(BLUE), "mug_spoon": lambda: lineup_mug(spoon=True)}, "杯子",
              # the spoon is something added (「多了一個」, for 2-3 years too): an art change without a type
              [C.color("mug_blue", "這個杯子是藍色的！"), {"kind": "art", "art": "mug_spoon", "said": "這個杯子裡有湯匙！"},
               C.flip("這個杯子的把手在另一邊！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((118, 306), 46, "plant", "leaf"), ((484, 356), 44, "cat", "white"), ((321, 242), 44, "stool", "wood")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("pot", 0), ("clock", 0), ("fruit", 0), ("cat", 1), ("stool", 1), ("balloon", "extra:balloon")]


if __name__ == "__main__":
    scene().build()
