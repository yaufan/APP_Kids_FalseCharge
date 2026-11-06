"""生日派對 (birthday party): a pastel party room on the floating tile.

The same floating square as the park (an isometric tile, 200 x 200 world units, 1.5 px per unit),
here a little room: a pink-and-cream checked floor, two low mint walls at the back (bunting along
the back-right one; the star garland, a thing, on the back-left one), a wooden cupboard against the
back-left wall, and a butter-yellow base with sprinkles under the floor, on a pale pink backdrop.

Things: a round table with a long cloth, the birthday cake on it, juice and a plate of cookies,
a bunch of balloons floating against the back-right wall, the window (its curtains change), a wall
clock, a star garland, a lamp and party hats on the cupboard, a big red present, little presents
in front of it, a teddy bear, a sleeping cat on a cushion and a toy car. Extras: a balloon in the
sky, confetti, a puppy. The lineup is a cupcake.

    background()        backdrop, the tile, floor, walls, bunting, cupboard: never changes
    one function per thing and per variant, returning shapes in scene px (kit.SceneArt)
    PLACE               where things stand on the floor, in scene px (W: the same in world units);
    WIN, CLOCK, ...     the wall things and the cupboard, in world units on their wall

Colours that 小變 hides against come from kit.TINT: the cupboard (wood), the big present (red) and
the tablecloth (white). HIDES gives each hide spot as (centre, size, the thing drawn in front of
part of him, tint); his z is that thing's z minus one.
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, star_pts, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=186)
TILE = 200
H = 74            # wall height
WT = 5            # wall thickness
P = ISO.P

INK = "#2B3158"
WHITE = "#FFFFFF"
BACK = "#FFE4EE"          # backdrop
FLOOR_P = "#FFC8DC"       # floor checks
FLOOR_C = "#FFF6EA"
RIM = "#F79CC0"           # the floor slab's side
BASE = "#FFE19A"          # the base under the floor (a cake-like layer with sprinkles)
WALL = "#BDEDD8"          # mint walls
WALL_LOW = "#9FE0C4"      # the lower band of the walls
WOOD = TINT["wood"]
CLOTH = TINT["white"]
RED = TINT["red"]
PINK = "#FF8FB8"
LPINK = "#FFB3CF"
YELLOW = "#FFD84A"
MINT = "#5FD3A8"
BLUE = "#4C8DFF"
LBLUE = "#8FCBFF"
SKYBLUE = "#BFE6FF"
PURPLE = "#B48CFF"
ORANGE = "#FF9838"
GREEN = "#5BD08A"
CHOC = "#8C5A3C"
TEDDY = "#D99A5E"

# where things stand, in scene px on the floor (at() turns them into world units)
PLACE = {
    "table": (288, 286),        # the middle of the round table
    "balloons": (528, 266),     # the bow under the balloons (they float: BOW_Z up)
    "present": (166, 307),      # the back corner of the big present (in front of the cupboard)
    "gifts": (112, 352),        # the back corner of the little gifts
    "teddy": (416, 394),
    "cat": (306, 432),
    "car": (206, 420),
    "puppy": (508, 348),
}
CUP = (74, 128, 18, 26)         # the cupboard along the back-left wall: y from, y to, depth, height


def at(X, Y):
    """World (x, y) of a point on the floor given in scene px."""
    a = (X - ISO.ox) / (kit.C30 * ISO.k)
    b = (Y - ISO.oy) / (kit.S30 * ISO.k)
    return (a + b) / 2, (b - a) / 2


W = {k: at(*v) for k, v in PLACE.items()}
BOW_Z = 40
W["balloons"] = at(PLACE["balloons"][0], PLACE["balloons"][1] + BOW_Z * ISO.k)       # the floor point under the bow
W["cake"] = (W["table"][0] - 7, W["table"][1] - 7)
W["lamp"] = (WT + 9, CUP[0] + 12)
W["hats"] = (WT + 9, CUP[0] + 40)
WIN = (68, 108, 24, 50)         # the window on the back-right wall: x from, x to, z from, z to
CLOCK = (30, 62, 11)            # the clock on the back-left wall: y, z, radius
GARLAND = (96, 180, 70)         # the star garland on the back-left wall: y from, y to, z of the nails


def depth(name, dz=0.0):
    x, y = W[name]
    return x + y + dz


def RW(x, z, off=.3):
    """A point on the back-right wall (its face toward the room)."""
    return P(x, WT + off, z)


def LW(y, z, off=.3):
    """A point on the back-left wall (its face toward the room)."""
    return P(WT + off, y, z)


# ================================================================ background
def background():
    g = Group()
    g.add(Sh([(0, 0), (600, 0), (600, 600), (0, 600)], BACK, tag="screen", only="ab"), -9000)
    g.add(Sh([(0, 0), (600, 0), (600, 600), (0, 600)], "#FFF3F7", tag="screen", only="c"), -9000)    # C: a pale wash
    for (cx, cy), s in zip(((92, 150), (520, 104), (548, 494), (58, 470)), (1.0, .85, .9, .75)):
        c = tf(crs([(-34, 6), (-38, -4), (-26, -12), (-14, -22), (6, -22), (18, -12), (32, -10), (34, 6)]), s=s, dx=cx, dy=cy)
        g.add([Sh(tf(c, dy=3), "#F7CFDD", only="ab"), Sh(c, WHITE)], -8000)
    # the island's shadow on the air below
    cx, cy = P(TILE / 2, TILE / 2, -20)
    g.add(Sh(ellp(cx, cy + 44, 226, 24), "#3B5A7A", tag="shadow", op=.9), -7000)
    # the tile: a butter-yellow base with sprinkles, a pink floor slab
    g.add(ISO.box(0, 0, -21, TILE, TILE, 15, BASE)[:2], -6000)
    spr = []
    cols = (PINK, MINT, LBLUE, "#FFFFFF", PURPLE)
    for i in range(16):
        t = (i + .5) / 16
        if i % 2 == 0:
            x, y, z = 8 + t * (TILE - 16), TILE, -10 - (i * 7 % 9)
            rot = -30 + (i * 37 % 50)
        else:
            x, y, z = TILE, 8 + t * (TILE - 16), -10 - (i * 5 % 9)
            rot = 20 + (i * 41 % 50)
        sx, sy = P(x, y, z)
        spr.append(Sh(tf(rrect(-3.6, -1.2, 7.2, 2.4, 1.2), rot=rot, dx=sx, dy=sy), cols[i % len(cols)], tag="detail"))
    g.add(spr, -5950)
    g.add(ISO.box(0, 0, -6, TILE, TILE, 6, RIM, top=FLOOR_C), -5900)
    # floor checks: A and B draw the checks, C (a child's drawing) a pink floor with crayon lines
    n_ = 6
    s_ = TILE / n_
    for i in range(n_):
        for j in range(n_):
            if (i + j) % 2 == 0:
                q = [(i * s_, j * s_), ((i + 1) * s_, j * s_), ((i + 1) * s_, (j + 1) * s_), (i * s_, (j + 1) * s_)]
                g.add(ISO.flat(q, 0, FLOOR_P, only="ab"), -5800)
    g.add(ISO.flat([(0, 0), (TILE, 0), (TILE, TILE), (0, TILE)], 0, mix(FLOOR_P, WHITE, .35), only="c"), -5800)
    grid = []
    for i in range(1, n_):
        grid.append(line([P(i * s_, 0), P(i * s_, TILE)], "#FF9EC2", 2.2, only="c"))
        grid.append(line([P(0, i * s_), P(TILE, i * s_)], "#FF9EC2", 2.2, only="c"))
    g.add(grid, -5790)
    # the walls: back-right (along x) and back-left (along y)
    g.add(ISO.box(0, 0, 0, TILE, WT, H, WALL), -5000)
    g.add(ISO.box(0, WT, 0, WT, TILE - WT, H, WALL), -5000)
    _, ll, rl = kit.shades(WALL_LOW)
    g.add([Sh([RW(0, 0, .1), RW(TILE, 0, .1), RW(TILE, 24, .1), RW(0, 24, .1)], ll, face="left", base=WALL_LOW),
           Sh([LW(WT, 0, .1), LW(TILE, 0, .1), LW(TILE, 24, .1), LW(WT, 24, .1)], rl, face="right", base=WALL_LOW)], -4990)
    g.add([Sh([RW(0, 23, .2), RW(TILE, 23, .2), RW(TILE, 26, .2), RW(0, 26, .2)], WHITE, face="left", base=WHITE),
           Sh([LW(WT, 23, .2), LW(TILE, 23, .2), LW(TILE, 26, .2), LW(WT, 26, .2)], "#E4EAF6", face="right", base=WHITE)], -4980)
    # little hearts on the upper walls
    hearts = [_wall_heart(RW, u, z, 3.2, mix(WALL, WHITE, .55)) for u, z in ((22, 38), (110, 40), (150, 33), (190, 40), (130, 46))]
    hearts += [_wall_heart(LW, u, z, 3.2, mix(kit.shades(WALL)[2], WHITE, .45)) for u, z in ((44, 36), (56, 30), (196, 34), (110, 36))]
    g.add(hearts, -4970)
    # bunting along the tops of the walls
    g.add(_bunting(RW, 8, TILE - 4, 9), -4900)
    # the wooden cupboard along the back-left wall (小變 hides in front of it in wood)
    y0, y1, dpt, ht = CUP
    g.add(ISO.box(WT, y0, 0, dpt, y1 - y0, ht, WOOD), 0)
    door = mix(WOOD, WHITE, .14)
    for a, b in ((y0 + 4, (y0 + y1) / 2 - 1.5), ((y0 + y1) / 2 + 1.5, y1 - 4)):
        g.add(ISO.face([(WT + dpt + .2, a, 4), (WT + dpt + .2, b, 4), (WT + dpt + .2, b, ht - 4), (WT + dpt + .2, a, ht - 4)],
                       kit.shades(door)[2], "right", door), 1)
    for yy in ((y0 + y1) / 2 - 4.5, (y0 + y1) / 2 + 4.5):
        sx, sy = P(WT + dpt + .4, yy, ht / 2)
        g.add(oval(sx, sy, 2.2, col="#FFE27A", tag="detail"), 2)
    g.add(ISO.box(WT + dpt - 1, y0 - 1, ht, 2, y1 - y0 + 2, 1.6, mix(WOOD, WHITE, .2)), 3)
    return g.shapes()


def _wall_heart(fn, u, z, r, col):
    pts = []
    for i in range(24):
        t = 2 * math.pi * i / 24
        hx = 16 * math.sin(t) ** 3
        hz = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(fn(u + hx * r / 16, z + hz * r / 16, .2))
    return Sh(pts, col, tag="detail")


def _bunting(fn, u0, u1, k, z=H - 4, sag=4.0, cols=(PINK, YELLOW, MINT, LBLUE)):
    """A string along a wall with k triangle flags hanging from it, in swags."""
    out = []
    swags = 2

    def zz(u):
        t = (u - u0) / (u1 - u0) * swags
        f = t - math.floor(t)
        return z - sag * 4 * f * (1 - f)
    pts = [fn(u0 + (u1 - u0) * i / 40, zz(u0 + (u1 - u0) * i / 40), .6) for i in range(41)]
    out.append(line(pts, "#8E95B5", 1.2))
    step = (u1 - u0) / k
    for i in range(k):
        a = u0 + step * (i + .2)
        b = u0 + step * (i + .8)
        m = (a + b) / 2
        out.append(Sh([fn(a, zz(a) - .3, .7), fn(b, zz(b) - .3, .7), fn(m, zz(m) - 9.5, .7)], cols[i % len(cols)]))
    return out


# ================================================================ things
def shadow(x, y, r, op=1.0):
    return ISO.shadow(x, y, r, op=op)


# ---------------------------------------------------------------- the table (a round table with a long cloth)
TABLE_R = 36
TABLE_H = 30


def _cyl_band(cx, cy, R, z0, z1, a0, a1, col, k=8, **kw):
    """A band on the front of an upright cylinder between angles a0..a1 (degrees; 0 = +x, 90 = +y)."""
    lo, hi = [], []
    for i in range(k + 1):
        a = math.radians(a0 + (a1 - a0) * i / k)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        lo.append(P(x, y, z0))
        hi.append(P(x, y, z1))
    return Sh(lo + hi[::-1], col, **kw)


def _visible(a):
    """Whether an angle on a cylinder faces the viewer (the front half: -45..135 degrees)."""
    return -45 <= a <= 135


def table(cloth=CLOTH, deco=PINK, dots=False):
    x, y = W["table"]
    R, Ht = TABLE_R, TABLE_H
    g = Group()
    g.add(shadow(x + 2, y + 2, R - 1, .9), -1)
    g.add(ISO.cyl(x, y, 0, R, Ht, cloth), 0)
    band = []
    if dots:
        for a in range(-28, 118, 24):
            for zz, da in ((Ht * .62, 0), (Ht * .28, 13)):
                aa = math.radians(a + da)
                if not _visible(a + da):
                    continue
                sx, sy = P(x + (R + .2) * math.cos(aa), y + (R + .2) * math.sin(aa), zz)
                sq = abs(math.cos(aa - math.radians(45))) * .45 + .55      # dots squeeze toward the sides
                band.append(oval(sx, sy, 4.4 * sq, 4.6, col=deco if a + da > 45 else kit.a_dark(deco), tag="detail"))
    else:
        for a in range(-45, 135, 20):
            band.append(_cyl_band(x, y, R + .15, 5, Ht, a, a + 9, deco if a + 4.5 > 45 else kit.a_dark(deco), k=4))
    g.add(band, 1)
    # the scalloped hem
    hem = []
    for a in range(-21, 112, 12):
        aa = math.radians(a)
        sx, sy = P(x + (R + .3) * math.cos(aa), y + (R + .3) * math.sin(aa), 2.5)
        hem.append(oval(sx, sy + 1, 5.6, 3.6, col=deco))
    g.add([_cyl_band(x, y, R + .25, 2, 5.5, -45, 135, deco, k=24)] + hem, 2)
    return g.shapes()


# ---------------------------------------------------------------- the cake on the table
CAKE_R = 21
CAKE_H = 19
# candles stand in a row across the top of the cake (left to right on the screen): 3, or 4 when one is added
CANDLE_AT = {3: ((-9, 6.5), (-1.5, -1.5), (6.5, -9)), 4: ((-11.5, 9), (-5, 2.5), (2, -4.5), (8.5, -11))}


def cake(col=LPINK, candles=3):
    x, y = W["cake"]
    z0 = TABLE_H
    R, Hc = CAKE_R, CAKE_H
    g = Group()
    g.add(ISO.cyl(x, y, z0, R + 3, 2, WHITE), 0)                 # the cake board
    g.add(ISO.cyl(x, y, z0 + 2, R, Hc, col), 1)
    # white cream dripping over the top edge, on the front half
    top = z0 + 2 + Hc
    drip_up, drip_lo = [], []
    for i in range(37):
        a = -45 + 180 * i / 36
        aa = math.radians(a)
        px, py = x + (R + .3) * math.cos(aa), y + (R + .3) * math.sin(aa)
        drip_up.append(P(px, py, top + .2))
        d = 5.5 + 3.5 * math.cos(i * 1.1) + (3 if i % 6 == 3 else 0)
        drip_lo.append(P(px, py, top - d))
    g.add(Sh(drip_up + drip_lo[::-1], WHITE), 2)
    sx, sy = P(x, y, top)
    rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
    g.add(oval(sx, sy, rx - 1, ry - 1, col=WHITE), 3)
    g.add(oval(sx, sy + .8, rx - 6, ry - 4, col=mix(col, WHITE, .35)), 3.1)
    # cream dots around the rim and strawberries
    rim = []
    for a in range(0, 360, 40):
        aa = math.radians(a + 10)
        px, py = P(x + (R - 3) * math.cos(aa), y + (R - 3) * math.sin(aa), top)
        rim.append((a, px, py))
    for a, px, py in sorted(rim, key=lambda t: t[2]):
        g.add([oval(px, py - 2, 4.2, 3.4, col=WHITE, cel=.5)], 4 + py * .001)
    for dx, dy in ((12, 4), (2, 14), (-12, -1)):
        px, py = P(x + dx, y + dy, top)
        g.add([oval(px, py - 3, 4.6, 4.2, col=RED, cel=.6), Sh([(px - 3, py - 6.5), (px, py - 9), (px + 3, py - 6.5), (px, py - 5.5)], GREEN)],
              6 + py * .001)
    # candles
    stripes = (LBLUE, YELLOW, MINT, PINK)
    for k_, (dx, dy) in enumerate(CANDLE_AT[candles]):
        px, py = P(x + dx, y + dy, top)
        hgt = 19
        c = [Sh(rrect(px - 2.6, py - hgt, 5.2, hgt, 1.4), WHITE)]
        for s in range(3):
            yy = py - hgt + 3 + s * 7
            c.append(Sh([(px - 2.6, yy + 2.5), (px + 2.6, yy), (px + 2.6, yy + 2.6), (px - 2.6, yy + 5.1)], stripes[k_ % 4]))
        c.append(line([(px, py - hgt), (px, py - hgt - 2.5)], INK, 1))
        c.append(oval(px, py - hgt - 7, 5, 7, col="#FFF1A6", tag="glow"))
        c.append(Sh(crs([(px, py - hgt - 13), (px + 3.4, py - hgt - 5), (px, py - hgt - 1.5), (px - 3.4, py - hgt - 5)], 5), ORANGE))
        c.append(Sh(crs([(px, py - hgt - 9.5), (px + 1.8, py - hgt - 4.5), (px, py - hgt - 2.6), (px - 1.8, py - hgt - 4.5)], 4), YELLOW,
                    tag="detail"))
        g.add(c, 10 + dx + dy)
    return g.shapes()


# ---------------------------------------------------------------- juice and cookies on the table
def juice(col=ORANGE):
    x, y = W["table"]
    g = Group()
    for dx, dy in ((21, -13), (23.5, 3.5)):
        cx, cy = x + dx, y + dy
        z0 = TABLE_H
        R = 4.4
        sx, sy = P(cx, cy, z0)
        hh = 13 * ISO.k
        rx, ry = R * 1.2247 * ISO.k, R * .7071 * ISO.k
        glass = [Sh([(sx - rx, sy - hh)] + [(sx + rx * math.cos(math.pi - math.pi * i / 12), sy + ry * math.sin(math.pi - math.pi * i / 12))
                                                for i in range(13)] + [(sx + rx, sy - hh)], "#EAF6FF")]
        fill_top = sy - hh * .72
        glass.append(Sh([(sx - rx + 1.2, fill_top)] + [(sx + (rx - 1.2) * math.cos(math.pi - math.pi * i / 12),
                                                        sy - 1.5 + (ry - 1) * math.sin(math.pi - math.pi * i / 12)) for i in range(13)]
                        + [(sx + rx - 1.2, fill_top)], col))
        glass.append(oval(sx, fill_top, rx - 1.2, ry - 1, col=mix(col, WHITE, .3)))
        glass.append(oval(sx, sy - hh, rx, ry, col="#F6FBFF", op=.9))
        glass.append(line([(sx + 1, fill_top), (sx + 4, sy - hh - 9), (sx + 8, sy - hh - 11)], PINK, 2.2))
        glass.append(line([(sx - rx + 2.2, sy - hh + 4), (sx - rx + 2.2, sy - 5)], WHITE, 1.6, op=.9))
        g.add(glass, cx + cy)
    return g.shapes()


def cookies(n_=4):
    x, y = W["table"]
    cx, cy = x + 7.5, y + 21.5
    g = Group()
    g.add(ISO.cyl(cx, cy, TABLE_H, 10, 1.2, WHITE), 0)
    sx, sy = P(cx, cy, TABLE_H + 1.2)
    g.add(oval(sx, sy, 10 * 1.2247 * ISO.k - 4, 10 * .7071 * ISO.k - 2.5, col="#E9EEF7"), 1)
    spots = ((-7, -1, 0), (5, -3, 0), (-1, 4, 0), (1, -3, 3.4))[:n_]
    for k_, (dx, dy, dz) in enumerate(spots):
        px, py = sx + dx, sy + dy - dz
        c = [oval(px, py, 7.4, 4.6, col="#E3A15E", cel=.4)]
        for ex, ey in ((-2.6, -1), (2, .6), (-.2, 1.8), (3, -1.6)):
            c.append(oval(px + ex, py + ey, 1.1, .8, col=CHOC, tag="detail"))
        g.add(c, 2 + k_)
    return g.shapes()


# ---------------------------------------------------------------- balloons (helium: they float up against the wall)
def balloon_sprite(col, s=1.0):
    lt_ = mix(col, WHITE, .1)
    o = [Sh(crs([(-4, 1), (4, 1), (0, -7)], 4), col),
         Sh(crs([(0, -5), (13, -11), (20, -28), (16, -46), (0, -55), (-16, -46), (-20, -28), (-13, -11)]), lt_, cel=1.0),
         oval(-8, -39, 3.6, 6.6, col=WHITE, rot=25, op=.8, tag="detail")]
    return transform(o, s=s)


BALLOONS = (((-24, -112), PINK, -10), ((12, -126), YELLOW, 8), ((-4, -96), RED, 0))      # (top of string, colour, tilt)


def balloons(front=RED, n_=3):
    x, y = W["balloons"]
    bx, by = P(x, y, BOW_Z)       # the bow where the strings meet
    g = Group()
    out = []
    for i, ((dx, dy), col, rot) in enumerate(BALLOONS):
        if n_ == 2 and i == 0:
            continue
        if i == 2:
            col = front
        tx, ty = bx + dx, by + dy
        mid = ((bx + tx) / 2 + 6 - i * 4, (by + ty) / 2)
        out.append((i, [line(crs([(bx, by), mid, (tx, ty)], 8, closed=False), "#8E95B5", 1.3)]))
        out.append((i + .5, transform(balloon_sprite(col), dx=tx, dy=ty, rot=rot, s=1.45)))
    for i, s in out:
        g.add(s, i)
    # a bow and the ends of the ribbons
    g.add([line(crs([(bx, by), (bx - 3, by + 8), (bx + 2, by + 16), (bx - 1, by + 24)], 6, closed=False), PINK, 1.6),
           line(crs([(bx, by), (bx + 4, by + 9), (bx + 1, by + 18)], 6, closed=False), PINK, 1.6),
           Sh(crs([(bx, by), (bx - 8, by - 5), (bx - 8, by + 4)], 4), PINK),
           Sh(crs([(bx, by), (bx + 8, by - 5), (bx + 8, by + 4)], 4), PINK),
           oval(bx, by, 2.4, col=mix(PINK, "#C0306A", .3))], 10)
    return g.shapes()


# ---------------------------------------------------------------- the window on the back-right wall
def window(curtain=PINK):
    x0, x1, z0, z1 = WIN
    g = Group()
    g.add(Sh([RW(x0 - 2, z0 - 2), RW(x1 + 2, z0 - 2), RW(x1 + 2, z1 + 2), RW(x0 - 2, z1 + 2)], WHITE, face="left", base=WHITE), 0)
    g.add(Sh([RW(x0 + 1, z0 + 1, .4), RW(x1 - 1, z0 + 1, .4), RW(x1 - 1, z1 - 1, .4), RW(x0 + 1, z1 - 1, .4)], SKYBLUE), 1)
    # a cloud and the sun outside
    cl = [RW(x0 + 9 + 7 * math.cos(t), z1 - 11 + 3.2 * math.sin(t) + (2.5 if math.sin(t) > 0 else 0) * abs(math.cos(2 * t)), .5)
          for t in [2 * math.pi * i / 24 for i in range(24)]]
    g.add(Sh(cl, WHITE, tag="detail"), 2)
    sun = [RW(x1 - 9 + 4.6 * math.cos(t), z1 - 9 + 4.6 * math.sin(t), .5) for t in [2 * math.pi * i / 24 for i in range(24)]]
    g.add(Sh(sun, "#FFE27A", tag="detail"), 2)
    xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
    g.add([Sh([RW(xm - .9, z0, .6), RW(xm + .9, z0, .6), RW(xm + .9, z1, .6), RW(xm - .9, z1, .6)], WHITE),
           Sh([RW(x0, zm - .9, .6), RW(x1, zm - .9, .6), RW(x1, zm + .9, .6), RW(x0, zm + .9, .6)], WHITE)], 3)
    # the sill
    g.add(ISO.box(x0 - 4, WT, z0 - 4.5, x1 - x0 + 8, 4, 2.5, WHITE), 4)
    # curtains, gathered with a tie on each side, and a scalloped valance on top
    dark = kit.tone(curtain, .9, 1.05)
    for side in (0, 1):
        xa = x0 - 6 if side == 0 else x1 + 6
        sgn = 1 if side == 0 else -1
        pts = [(xa, z1 + 3), (xa + sgn * 13, z1 + 3), (xa + sgn * 6, zm + 2), (xa + sgn * 4, zm - 1), (xa + sgn * 8, z0 - 6),
               (xa, z0 - 6)]
        cur = crs(pts, 6)
        g.add(Sh([RW(u, z, 1.2) for u, z in cur], curtain), 5)
        g.add(line([RW(xa + sgn * 1.5, z1 + 1, 1.3), RW(xa + sgn * 3, zm, 1.3), RW(xa + sgn * 2.5, z0 - 4, 1.3)], dark, 1.6), 5.1)
        g.add(Sh([RW(u, z, 1.4) for u, z in crs([(xa - sgn * .5, zm + 1), (xa + sgn * 5.5, zm + 1.5), (xa + sgn * 5.5, zm - 2),
                                                 (xa - sgn * .5, zm - 2.5)], 4)], YELLOW), 5.2)
    val = []
    for i in range(8):
        a = x0 - 7 + (x1 - x0 + 14) * i / 8
        b = x0 - 7 + (x1 - x0 + 14) * (i + 1) / 8
        val += [(a, z1 + 7)] if i == 0 else []
        val += [(a + (b - a) * j / 6, z1 + 1.5 - 2.6 * math.sin(math.pi * j / 6)) for j in range(7)]
    val += [(x1 + 7, z1 + 7)]
    g.add(Sh([RW(u, z, 1.6) for u, z in val], curtain), 6)
    return g.shapes()


# ---------------------------------------------------------------- the clock on the back-left wall
def clock(frame=PINK, hands=(0, 90)):
    y, z, r = CLOCK
    def ring(rr, off):
        return [LW(y + rr * math.cos(t), z + rr * math.sin(t), off) for t in [2 * math.pi * i / 32 for i in range(32)]]
    o = [Sh(ring(r, .4), frame, cel=.6), Sh(ring(r - 2.6, .6), WHITE)]
    for a in range(0, 360, 90):
        aa = math.radians(a)
        px, py = LW(y + (r - 5) * math.cos(aa), z + (r - 5) * math.sin(aa), .7)
        o.append(oval(px, py, 1.5, col=frame, tag="detail"))
    for ang, ln in zip(hands, (6.5, 8.5)):           # degrees clockwise from 12 o'clock: hour hand, minute hand
        aa = math.radians(ang)
        o.append(line([LW(y, z, .8), LW(y - ln * math.sin(aa), z + ln * math.cos(aa), .8)], INK, 2.4))
    o.append(oval(*LW(y, z, .9), 1.8, col=INK))
    # a little bell on top
    bx, by = LW(y, z + r + 1.5, .5)
    o.append(Sh(crs([(bx - 6, by + 2), (bx - 5, by - 4), (bx, by - 7), (bx + 5, by - 4), (bx + 6, by + 2)], 5), YELLOW, cel=.4))
    return o


# ---------------------------------------------------------------- the star garland on the back-left wall
STARS = 5


def garland(col=YELLOW, k=STARS):
    y0, y1, zn = GARLAND
    o = []
    nails = [y0 + (y1 - y0) * i / 2 for i in range(3)]

    def zz(u):
        t = (u - y0) / (y1 - y0) * 2
        f = t - math.floor(t) if t < 2 else 1.0
        return zn - 5 * 4 * f * (1 - f)
    pts = [LW(y0 + (y1 - y0) * i / 40, zz(y0 + (y1 - y0) * i / 40), .8) for i in range(41)]
    o.append(line(pts, "#8E95B5", 1.4))
    for u in nails:
        px, py = LW(u, zn, .9)
        o.append(oval(px, py, 2.2, col=PINK))
    for i in range(k):
        u = y0 + (y1 - y0) * (i + .5) / STARS
        zc = zz(u) - 9
        st = [LW(u + yy, zc + zz_, 1.0) for yy, zz_ in star_pts(7.4, 3.4, 0, 0, rot=90)]
        o.append(line([LW(u, zz(u), 1.0), LW(u, zc + 6, 1.0)], "#8E95B5", 1.1))
        o.append(Sh(st, col, cel=.5))
    return o


# ---------------------------------------------------------------- lamp and party hats on the cupboard
def lamp(shade=YELLOW):
    x, y = W["lamp"]
    z0 = CUP[3] + 1.6
    g = Group()
    g.add(ISO.cyl(x, y, z0, 5, 2.4, WHITE), 0)
    g.add(ISO.cyl(x, y, z0 + 2.4, 1.2, 15, "#C9D2E6"), 1)
    sx, sy = P(x, y, z0 + 16)
    top, bot = sy - 22, sy
    g.add(oval(sx, sy - 10, 18, col="#FFF3B0", tag="glow"), 1.5)
    sh = [(sx - 9, top), (sx + 9, top), (sx + 16, bot)] + [(sx + 16 * math.cos(math.pi * i / 10), bot + 4 * math.sin(math.pi * i / 10))
                                                           for i in range(11)] + [(sx - 16, bot)]
    g.add(Sh(sh, shade, cel=.5), 2)
    g.add(oval(sx, top, 9, 2.4, col=mix(shade, WHITE, .4)), 3)
    g.add(line([(sx - 16, bot + 1), (sx - 7, bot + 4.6), (sx + 7, bot + 4.6), (sx + 16, bot + 1)], mix(shade, "#C0306A", .2), 2), 3.1)
    return g.shapes()


def hat_sprite(c1, c2, dots=False):
    """A party hat (a cone with a pompom), origin at its brim."""
    o = [Sh([(-11, 0), (11, 0), (0, -30)], c1, cel=.5)]
    if dots:
        for dx, dy, r in ((-4, -6, 2.2), (4, -10, 2.0), (-1, -17, 1.8), (5, -3, 1.6), (-6, -1.5, 1.4)):
            o.append(oval(dx, dy, r, col=c2, tag="detail"))
    else:
        for t0 in (.18, .5):
            ya, yb = -30 * t0, -30 * (t0 + .16)
            wa, wb = 11 * (1 - t0), 11 * (1 - t0 - .16)
            o.append(Sh([(-wa, ya), (wa, ya - 3), (wb, yb - 3), (-wb, yb)], c2))
    o.append(oval(0, 0, 11.5, 2.6, col=mix(c1, INK, .15)))
    o.append(oval(0, -31, 4.4, col=YELLOW, cel=.5))
    return o


def hats(c1=PINK, c2=WHITE, dots=False):
    x, y = W["hats"]
    z0 = CUP[3] + 1.6
    g = Group()
    for dx, dy, rot in ((0, -7, -8), (1, 7, 10)):
        sx, sy = P(x + dx, y + dy, z0)
        g.add(transform(hat_sprite(c1, c2, dots), dx=sx, dy=sy, rot=rot, s=.85), dx + dy)
    return g.shapes()


# ---------------------------------------------------------------- presents
def _present(x, y, z, w, d, h, col, rib, dots=False):
    """A present: a box with a ribbon across the top and down the sides, a bow on top."""
    out = ISO.box(x, y, z, w, d, h, col)
    t, l, r = kit.shades(col)
    if dots:
        for fx, fz in ((.25, .3), (.7, .25), (.5, .7), (.2, .78), (.82, .72)):
            out.append(ISO.face([(x + fx * w - 1.6, y + d + .2, z + fz * h - 1.6), (x + fx * w + 1.6, y + d + .2, z + fz * h - 1.6),
                                 (x + fx * w + 1.6, y + d + .2, z + fz * h + 1.6), (x + fx * w - 1.6, y + d + .2, z + fz * h + 1.6)],
                                WHITE, tag="detail"))
            out.append(ISO.face([(x + w + .2, y + fx * d - 1.6, z + fz * h - 1.6), (x + w + .2, y + fx * d + 1.6, z + fz * h - 1.6),
                                 (x + w + .2, y + fx * d + 1.6, z + fz * h + 1.6), (x + w + .2, y + fx * d - 1.6, z + fz * h + 1.6)],
                                "#E9EEF7", tag="detail"))
        for fx, fy in ((.25, .3), (.75, .7), (.3, .78), (.78, .22)):
            px, py = P(x + fx * w, y + fy * d, z + h + .1)
            out.append(oval(px, py, 2.4, 1.4, col=WHITE, tag="detail"))
    rw = 2.6
    rt, rl, rr = kit.shades(rib)
    xm, ym = x + w / 2, y + d / 2
    out += [ISO.face([(xm - rw, y + d + .25, z), (xm + rw, y + d + .25, z), (xm + rw, y + d + .25, z + h), (xm - rw, y + d + .25, z + h)], rl, "left", rib),
            ISO.face([(x + w + .25, ym - rw, z), (x + w + .25, ym + rw, z), (x + w + .25, ym + rw, z + h), (x + w + .25, ym - rw, z + h)], rr, "right", rib),
            ISO.face([(xm - rw, y, z + h + .2), (xm + rw, y, z + h + .2), (xm + rw, y + d, z + h + .2), (xm - rw, y + d, z + h + .2)], rt, "top", rib),
            ISO.face([(x, ym - rw, z + h + .2), (x + w, ym - rw, z + h + .2), (x + w, ym + rw, z + h + .2), (x, ym + rw, z + h + .2)], rt, "top", rib)]
    bx, by = P(xm, ym, z + h)
    s = min(w, d) / 22
    out += [Sh(crs([(bx, by - 2), (bx - 13 * s, by - 12 * s), (bx - 15 * s, by - 2), (bx - 6 * s, by + 1)], 5), rib, cel=.5),
            Sh(crs([(bx, by - 2), (bx + 13 * s, by - 12 * s), (bx + 15 * s, by - 2), (bx + 6 * s, by + 1)], 5), rib, cel=.5),
            oval(bx, by - 2, 3.4 * s + 1, col=rl)]
    return out


def present(col=RED, n_=2, dots=False):
    x, y = W["present"]
    g = Group()
    g.add(shadow(x + 13, y + 12, 18, .8), -1)
    g.add(_present(x, y, 0, 26, 24, 22, col, YELLOW, dots), 0)
    if n_ == 2:
        g.add(_present(x + 6, y + 5, 22, 14, 13, 11, MINT, PINK), 1)
    return g.shapes()


def gifts(col=YELLOW, n_=2):
    x, y = W["gifts"]
    g = Group()
    g.add(shadow(x + 9, y + 9, 13, .8), -1)
    g.add(_present(x, y, 0, 16, 15, 14, col, PINK), 0)
    if n_ == 2:
        g.add(_present(x + 17, y + 3, 0, 11, 11, 9, LPINK, MINT), 1)
    return g.shapes()


# ---------------------------------------------------------------- teddy bear (sitting, looking left)
def teddy_sprite(col=TEDDY, face="smile"):
    light = mix(col, WHITE, .45)
    dark = kit.tone(col, .78, 1.05)
    o = []
    o.append(oval(16, -36, 8, 11, col=dark, rot=-20, cel=.4))                    # the far arm
    o.append(oval(0, -27, 21, 23, col=col, cel=1.0))                             # body
    o.append(oval(-4, -24, 12, 14, col=light, tag="detail"))                     # belly
    o.append(oval(12, -6, 10, 8, col=dark, cel=.4))                              # far leg
    o.append(oval(-15, -7, 11, 9, col=col, cel=.6))                              # near leg
    o.append(oval(-20, -8, 5.6, 6.6, col=light, tag="detail"))                   # foot pad
    o.append(oval(-17, -30, 7.5, 11, col=col, rot=35, cel=.5))                   # near arm
    # head
    for ex, ey in ((-15, -78), (12, -80)):
        o.append(oval(ex, ey, 8, col=col, cel=.5))
        o.append(oval(ex, ey, 4.2, col=light, tag="detail"))
    o.append(oval(-1, -62, 21, 19, col=col, cel=1.0))
    o.append(oval(-13, -56, 9.5, 7.5, col=light))                                # snout
    o.append(oval(-19, -59, 3.6, 2.8, col=INK))                                  # nose
    if face == "smile":
        o.append(oval(-15, -67, 2.6, 3.2, col=INK))
        o.append(oval(-2, -68, 2.6, 3.2, col=INK))
        o.append(line(crs([(-19, -54), (-15, -51), (-11, -53)], 4, closed=False), INK, 1.6))
    else:
        for ex in (-15, -2):
            o.append(oval(ex, -68, 4, 4.4, col=WHITE))
            o.append(oval(ex - .8, -67.5, 2.4, 2.8, col=INK))
        o.append(oval(-14, -50.5, 3, 3.6, col=INK))
    o.append(oval(-4, -58, 3.8, 2.4, col="#FF9DB6", op=.8, tag="detail"))
    # a bow tie
    o.append(Sh([(-6, -43), (-16, -48), (-16, -37)], RED))
    o.append(Sh([(-6, -43), (4, -48), (4, -37)], RED))
    o.append(oval(-6, -43, 2.8, col=mix(RED, INK, .2)))
    return o


def teddy(col=TEDDY, face="smile"):
    x, y = W["teddy"]
    sx, sy = P(x, y)
    return shadow(x + 2, y + 2, 17, .8) + transform(teddy_sprite(col, face), dx=sx, dy=sy, s=1.32)


# ---------------------------------------------------------------- the sleeping cat (and the dog) on a cushion
CUSHION = "#C9B4FF"


def cushion(x, y):
    g = []
    g += shadow(x + 2, y + 2, 21, .8)
    g += ISO.cyl(x, y, 0, 20, 5, CUSHION)
    sx, sy = P(x, y, 5)
    g.append(oval(sx, sy, 20 * 1.2247 * ISO.k - 5, 20 * .7071 * ISO.k - 3, col=mix(CUSHION, WHITE, .3)))
    return g


def cat_sprite(col="#FFA552"):
    """A cat curled up asleep, head on the left."""
    dark = "#E8843A"
    o = [oval(4, -14, 27, 14, col=col, cel=1.0)]
    for k in range(3):
        o.append(line(crs([(6 + k * 7, -27), (9 + k * 7, -20), (7 + k * 7, -15)], 4, closed=False), dark, 2.2))
    o.append(Sh(tube(crs([(28, -10), (24, -2), (6, 1), (-12, -1)], 8, closed=False), 7.5, 5.5), col, cel=.5))
    o.append(oval(-13, -2, 4.2, 3.2, col="#FFE3BF"))                                     # tail tip
    o.append(Sh(crs([(-28, -24), (-30, -38), (-20, -30)], 4), col))                       # ears
    o.append(Sh(crs([(-14, -32), (-6, -40), (-8, -26)], 4), col))
    o.append(Sh(crs([(-27.5, -27), (-28.5, -34), (-23, -29.5)], 3), "#FFB3C6", tag="detail"))
    o.append(oval(-18, -19, 13, 11.5, col=col, cel=1.0))                                  # head
    o.append(oval(-20, -13, 6.5, 4.5, col="#FFE3BF"))
    for ex in (-24, -13):
        o.append(line([(ex - 3, -21), (ex, -19), (ex + 3, -21)], INK, 1.6))
    o.append(Sh(crs([(-21.5, -15), (-17.5, -15), (-19.5, -12.5)], 3), "#FF8FA8", tag="detail"))
    o.append(oval(-26, -14, 2.8, 1.8, col="#FF9DB6", op=.8, tag="detail"))
    return o


def dog_sprite(col="#F4EEE6"):
    """A puppy curled up asleep, head on the left, floppy ears."""
    spot = "#C98E5A"
    o = [oval(4, -14, 27, 14, col=col, cel=1.0)]
    o.append(oval(12, -19, 9, 7, col=spot, tag="detail"))
    o.append(Sh(tube(crs([(28, -12), (30, -4), (22, 1)], 6, closed=False), 7, 5), col, cel=.5))
    o.append(oval(-17, -19, 14, 12, col=col, cel=1.0))                                   # head
    o.append(Sh(crs([(-24, -29), (-33, -24), (-34, -10), (-28, -8), (-24, -20)], 5), spot, cel=.4))
    o.append(Sh(crs([(-8, -30), (0, -26), (2, -12), (-4, -10), (-8, -20)], 5), spot, cel=.4))
    o.append(oval(-22, -12, 7.5, 5, col=WHITE))
    o.append(oval(-27, -14, 3, 2.4, col=INK))
    for ex in (-20, -10):
        o.append(line([(ex - 3, -21), (ex, -19), (ex + 3, -21)], INK, 1.6))
    o.append(oval(-15, -13, 2.6, 1.6, col="#FF9DB6", op=.8, tag="detail"))
    return o


def cat(animal="cat"):
    x, y = W["cat"]
    sx, sy = P(x, y, 5)
    spr = cat_sprite() if animal == "cat" else dog_sprite()
    return cushion(x, y) + transform(spr, dx=sx + 4, dy=sy + 7, s=1.2)


# ---------------------------------------------------------------- toy car (side view, facing left)
def car_sprite(col=BLUE):
    dark = kit.tone(col, .8, 1.05)
    o = []
    o.append(Sh(rrect(-38, -34, 76, 24, 9), col, cel=.6))                    # body
    o.append(Sh(crs([(-12, -32), (-6, -52), (20, -54), (30, -36), (30, -32)], 6), col, cel=.6))     # cabin
    o.append(Sh(crs([(-6, -35), (-2, -48), (8, -49), (8, -35)], 4), SKYBLUE))
    o.append(Sh(crs([(12, -35), (12, -49), (19, -49), (25, -36)], 4), SKYBLUE))
    o.append(oval(-34, -24, 4.4, 3.6, col="#FFE27A"))                         # headlight at the front
    o.append(Sh(rrect(30, -27, 9, 5, 2.5), "#FF6B6B"))                         # tail light
    o.append(line([(-30, -18), (32, -18)], dark, 1.8))
    for wx in (-22, 22):
        o += [oval(wx, -10, 10.5, col="#3E4566"), oval(wx, -10, 4.4, col="#DDE3F0")]
    return o


def car(col=BLUE):
    x, y = W["car"]
    sx, sy = P(x, y)
    return shadow(x, y, 16, .7) + transform(car_sprite(col), dx=sx, dy=sy, s=1.0)


# ---------------------------------------------------------------- extras
def balloon2():
    cx, cy = 96, 66
    o = [line(crs([(0, 0), (5, 10), (-3, 20), (1, 30)], 6, closed=False), "#8E95B5", 1.3)]
    o += balloon_sprite(MINT)
    return transform(o, dx=cx, dy=cy + 26, rot=-8, s=1.55)


def confetti():
    cx, cy = 394, 46
    o = []
    bits = ((-28, -6, PINK, 20), (-14, -20, YELLOW, -30), (2, -8, LBLUE, 50), (16, -22, MINT, 10), (28, -4, PURPLE, -40),
            (-20, 10, ORANGE, 35), (-4, 14, PINK, -10), (14, 10, YELLOW, 60), (30, 18, LBLUE, -20), (-34, 22, MINT, 5),
            (6, 28, RED, 25))
    for dx, dy, col, rot in bits:
        o.append(Sh(tf(rrect(-4.5, -2.4, 9, 4.8, 1.4), rot=rot, dx=dx, dy=dy), col))
    for dx, dy, col in ((-8, -2, RED), (22, 4, PINK), (-26, -24, LBLUE), (8, -28, PURPLE)):
        o.append(oval(dx, dy, 3, col=col))
    o.append(line(crs([(-36, 34), (-26, 30), (-22, 38), (-12, 34)], 6, closed=False), PINK, 2.4))
    o.append(line(crs([(18, -36), (26, -32), (24, -26), (34, -26)], 6, closed=False), YELLOW, 2.4))
    return transform(o, dx=cx, dy=cy, s=1.15)


def puppy_sprite(col="#E8B47A"):
    """A puppy sitting, looking left."""
    light = mix(col, WHITE, .5)
    ear = kit.tone(col, .72, 1.1)
    o = [Sh(tube(crs([(12, -8), (20, -14), (22, -24)], 6, closed=False), 5, 3.4), col, cel=.4)]
    o.append(oval(4, -16, 13, 15, col=col, cel=1.0))
    o.append(oval(0, -14, 7, 9, col=light, tag="detail"))
    for lx in (-6, 4):
        o.append(Sh(rrect(lx - 3.4, -10, 6.8, 10, 3.2), col, cel=.3))
    o.append(oval(-4, -38, 13, 12, col=col, cel=1.0))
    o.append(oval(-13, -33, 7, 5.4, col=light))
    o.append(oval(-18.5, -35, 2.6, 2.2, col=INK))
    o.append(oval(-7, -41, 2.2, 2.6, col=INK))
    o.append(Sh(crs([(2, -48), (10, -44), (10, -30), (5, -27), (2, -38)], 5), ear, cel=.4))
    o.append(Sh(rrect(-12, -27, 16, 3.6, 1.8), RED))
    return o


def puppy():
    x, y = W["puppy"]
    sx, sy = P(x, y)
    return shadow(x + 1, y + 1, 10, .8) + transform(puppy_sprite(), dx=sx, dy=sy, s=1.15)


# ================================================================ lineup (哪一個不一樣？): a cupcake
def cupcake(frost=LPINK, cherry=False, sprinkles=False):
    cup = MINT
    o = [Sh([(-30, -40), (30, -40), (22, 0), (-22, 0)], cup, cel=.4)]
    for k in range(-2, 3):
        o.append(Sh([(k * 11 - 2.4, -40), (k * 11 + 2.4, -40), (k * 8.2 + 1.8, 0), (k * 8.2 - 1.8, 0)], mix(cup, WHITE, .45)))
    sw = [oval(0, -46, 36, 12, col=frost, cel=.6), oval(0, -60, 29, 11, col=frost, cel=.7), oval(0, -73, 20, 9, col=frost, cel=.8),
          Sh(crs([(-10, -78), (0, -94), (10, -78)], 5), frost, cel=.6)]
    o += sw
    if sprinkles:
        cols = (YELLOW, LBLUE, PURPLE, WHITE, MINT)
        for i, (dx, dy, rot) in enumerate(((-22, -48, 30), (-6, -44, -40), (12, -47, 10), (24, -50, -20), (-14, -60, -15), (4, -62, 45),
                                           (18, -60, -50), (-6, -74, 20), (8, -76, -30), (-24, -58, 60))):
            o.append(Sh(tf(rrect(-4.2, -1.5, 8.4, 3, 1.5), rot=rot, dx=dx, dy=dy), cols[i % len(cols)], tag="detail"))
    if cherry:
        o.append(line(crs([(2, -100), (6, -110), (13, -114)], 4, closed=False), "#4FAE5C", 2))
        o.append(oval(0, -96, 9, col=RED, cel=.8))
    o.append(oval(-12, -66, 4, 2.4, col=WHITE, op=.7, rot=-20, tag="detail"))
    return transform(o, s=1.0)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("party", "生日派對", "birthday party")
    sa.background(background)
    C = kit
    zt = int(depth("table"))
    sa.thing("table", "桌子", "table",
             {"table": table, "table_blue": lambda: table(LBLUE), "table_dots": lambda: table(dots=True)},
             [C.color("table_blue", "桌巾變成藍色了！"), C.pattern("table_dots", "桌巾變成點點了！")],
             big=True, z=zt)
    sa.thing("cake", "生日蛋糕", "birthday cake",
             {"cake": cake, "cake_choc": lambda: cake(CHOC), "cake_four": lambda: cake(candles=4)},
             [C.color("cake_choc", "蛋糕變成巧克力蛋糕了！"), C.count("cake_four", "蛋糕的蠟燭多了一根！"), C.gone("蛋糕不見了！")],
             big=True, z=zt + 6)
    sa.thing("juice", "果汁", "juice", {"juice": juice, "juice_grape": lambda: juice(PURPLE)},
             [C.color("juice_grape", "果汁變成紫色了！"), C.gone("果汁不見了！")], z=zt + 10)
    sa.thing("cookies", "餅乾", "cookies", {"cookies": cookies, "cookies_two": lambda: cookies(2)},
             [C.count("cookies_two", "餅乾少了兩片！"), C.gone("餅乾不見了！")], z=zt + 11)
    sa.thing("balloons", "氣球", "balloons",
             {"balloons": balloons, "balloons_blue": lambda: balloons(BLUE), "balloons_two": lambda: balloons(n_=2)},
             [C.color("balloons_blue", "紅氣球變成藍色了！"), C.count("balloons_two", "氣球少了一顆！"), C.gone("氣球不見了！")],
             big=True, z=int(depth("balloons")))
    sa.thing("window", "窗戶", "window", {"window": window, "window_blue": lambda: window(LBLUE)},
             [C.color("window_blue", "窗簾變成藍色了！")], big=True, z=3)
    sa.thing("clock", "時鐘", "clock",
             {"clock": clock, "clock_yellow": lambda: clock(YELLOW), "clock_late": lambda: clock(hands=(240, 180))},
             [C.color("clock_yellow", "時鐘變成黃色了！"), C.face_("clock_late", "時鐘的指針轉了！"), C.gone("時鐘不見了！")], z=4)
    sa.thing("garland", "星星吊飾", "star garland",
             {"garland": garland, "garland_pink": lambda: garland(PINK), "garland_fewer": lambda: garland(k=3)},
             [C.color("garland_pink", "星星變成粉紅色了！"), C.count("garland_fewer", "星星少了兩顆！"), C.gone("星星不見了！")],
             big=True, z=5)
    sa.thing("lamp", "檯燈", "lamp", {"lamp": lamp, "lamp_blue": lambda: lamp(LBLUE)},
             [C.color("lamp_blue", "檯燈變成藍色了！"), C.gone("檯燈不見了！"), C.size(1.35, "檯燈變大了！")],
             z=int(depth("lamp")))
    sa.thing("hats", "派對帽", "party hats",
             {"hats": hats, "hats_blue": lambda: hats(LBLUE), "hats_dots": lambda: hats(dots=True)},
             [C.color("hats_blue", "派對帽變成藍色了！"), C.pattern("hats_dots", "派對帽變成點點了！"), C.gone("派對帽不見了！")],
             z=int(depth("hats")))
    sa.thing("present", "大禮物", "big present",
             {"present": present, "present_blue": lambda: present(BLUE), "present_one": lambda: present(n_=1),
              "present_dots": lambda: present(dots=True)},
             [C.color("present_blue", "紅色的禮物變成藍色了！"), C.count("present_one", "禮物少了一個！"),
              C.pattern("present_dots", "禮物變成點點了！")],
             big=True, z=int(depth("present")) + 10)
    sa.thing("gifts", "小禮物", "little presents",
             {"gifts": gifts, "gifts_purple": lambda: gifts(PURPLE), "gifts_one": lambda: gifts(n_=1)},
             [C.color("gifts_purple", "黃色的小禮物變成紫色了！"), C.count("gifts_one", "小禮物少了一個！"), C.gone("小禮物不見了！")],
             z=int(depth("gifts")) + 10)
    sa.thing("teddy", "小熊", "teddy bear",
             {"teddy": teddy, "teddy_pink": lambda: teddy(LPINK), "teddy_wow": lambda: teddy(face="wow")},
             [C.color("teddy_pink", "小熊變成粉紅色了！"), C.flip("小熊轉向另一邊了！"), C.face_("teddy_wow", "小熊嚇了一跳！"),
              C.gone("小熊不見了！")],
             big=True, z=int(depth("teddy")))
    sa.thing("cat", "小貓", "cat", {"cat": cat, "cat_dog": lambda: cat("dog")},
             [C.swap("cat_dog", "小貓變成小狗了！"), C.flip("小貓轉向另一邊了！"), C.gone("小貓不見了！")],
             big=True, z=int(depth("cat")))
    sa.thing("car", "小汽車", "toy car", {"car": car, "car_yellow": lambda: car(YELLOW)},
             [C.color("car_yellow", "小汽車變成黃色了！"), C.flip("小汽車轉向另一邊了！"), C.gone("小汽車不見了！")],
             big=True, z=int(depth("car")))
    sa.extra("balloon2", "綠氣球", "green balloon", balloon2, "天上多了一顆氣球！", z=1, big=True)
    sa.extra("confetti", "彩色紙花", "confetti", confetti, "多了好多彩色紙花！", z=2, big=True)
    sa.extra("puppy", "小狗", "puppy", puppy, "多了一隻小狗！", z=int(depth("puppy")))
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"cupcake": cupcake, "cupcake_blue": lambda: cupcake(LBLUE), "cupcake_cherry": lambda: cupcake(cherry=True),
               "cupcake_sprinkles": lambda: cupcake(sprinkles=True)}, "杯子蛋糕",
              [C.color("cupcake_blue", "這個杯子蛋糕是藍色的！"),
               {"kind": "art", "art": "cupcake_cherry", "said": "這個杯子蛋糕多了一顆櫻桃！"},
               C.pattern("cupcake_sprinkles", "這個杯子蛋糕有彩色糖粒！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((200, 262), 40, "present", "wood"), ((150, 338), 40, "gifts", "red"), ((238, 232), 38, "cake", "white")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("cake", 1), ("balloons", 0), ("teddy", 1), ("present", 0), ("car", 0), ("confetti", "extra:confetti")]


if __name__ == "__main__":
    scene().build()
