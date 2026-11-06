"""夜市 (night market): the same floating isometric tile as the park, at night.

A navy sky with the moon, stars and two strings of coloured lights hung from a festive pole at the
back corner; red paper lanterns hang from the left string. The tile is a sand-coloured paved street
(kit.TINT["sand"], so 小變 can hide on it) on a brick base. Two rows of stalls stand along the two
back edges and face the street: a grill stall (烤肉串) and a cotton-candy stall on the left, a drink
stall (珍珠奶茶, wooden counter: 小變 hides on it) and a balloon stall on the right. In the street: a
standing sign with a big shape on it (no text), a goldfish tub (撈金魚), a scooter, a cat, a red
plastic stool and a rubbish bin.

    background()        sky, stars, light strings, the pole, the tile, the lamps (bg.svg)
    Stall               one stall along a back edge (orient "L": the left row, facing +x;
                        "R": the right row, facing +y), drawn in its own (u along the edge,
                        v towards the street) coordinates
    PLACE               where the street things stand (scene px), and the sky things' centres

Hide spots (HIDES): red among the lanterns, wood on the drink stall's counter behind the cup, sand
on the street behind the stool.
"""
import math

import kit
from kit import TINT, Group, Iso, Sh, crs, ellp, line, mix, oval, rrect, sparkle, star_pts, tf, transform, tube

ISO = Iso(k=1.5, ox=300, oy=186)
TILE = 200
P = ISO.P
INK = "#2B3158"
WHITE = "#FFFFFF"
CREAM = "#FFF4E2"
METAL = "#7C86A8"
STEEL = "#C9D2E3"
DARK = "#3E4566"
NIGHT = "#1E2858"          # the sky (A, B)
NIGHT_C = "#2E3C7E"        # the sky in crayon: light enough to be hatched, not filled solid
NIGHT_CB = "#232D66"       # ... over a darker solid wax, so the gaps between strokes are not white
HALO = "#3B4C96"           # the soft light the market throws on the sky (A, B)
STAR = "#FFF1A8"
WIRE = "#6A6F98"
GOLD = "#FFC23D"
MOON = "#FFE9A0"
SAND = TINT["sand"]
WOOD = TINT["wood"]
RED = TINT["red"]
BLUE = TINT["blue"]
BRICK = "#C9785B"
CURB = "#E4D6C8"
PAVE = mix(SAND, "#C99A50", .28)
YELLOW = "#FFD84A"
AMBER = "#FFC83D"
ORANGE = "#FF9838"
PINK = "#FF8FB8"
PURPLE = "#B48CFF"
SKY = "#5EC8F0"
GREEN = "#5BD08A"
TEA = "#D9A066"
BULBS = ("#FFE27A", "#FF9DB6", "#8FE3FF", "#FFB35C", "#B6F07A")

# Where things are, in scene px: for things in the street, the point they stand on; for things in
# the sky, their centre.
PLACE = {
    "sign": (300, 350),
    "tub": (294, 444),         # the tub's centre on the ground
    "scooter": (400, 408),
    "cat": (186, 398),
    "stool": (452, 360),
    "bin": (86, 346),
    "moon": (556, 56),
    "balloon2": (226, 62),     # the knot under the balloon
    "firefly": (54, 262),
    "firework": (78, 500),
}
# the stalls: (orient, u0): along the left back edge (x = 0) or the right one (y = 0)
STALLS = {"grill": ("L", 35), "cotton": ("L", 115), "tea": ("R", 35), "balloon": ("R", 115)}
POLE = (2.5, 2.5)          # world: the light pole at the back corner
POLE_H = 90
POLE_TOP = P(POLE[0] + 1.2, POLE[1] + 1.2, POLE_H)
# the light strings (scene px), from the pole top out to the sky's edges
WIRE_L = crs([(-14, 30), (52, 60), (112, 76), (176, 74), (236, 62), POLE_TOP], 10, closed=False)
WIRE_R = crs([POLE_TOP, (368, 76), (436, 98), (502, 112), (556, 116), (614, 108)], 10, closed=False)
LANTERNS_AT = (58, 104, 150)   # x of the three lanterns on the left string


def at(name_or_xy):
    """World (x, y) of a ground point given in scene px (a PLACE name or a point)."""
    X, Y = PLACE[name_or_xy] if isinstance(name_or_xy, str) else name_or_xy
    a = (X - ISO.ox) / (kit.C30 * ISO.k)
    b = (Y - ISO.oy) / (kit.S30 * ISO.k)
    return (a + b) / 2, (b - a) / 2


def depth(name, dz=0.0):
    x, y = at(name)
    return x + y + dz


def on_wire(wire, x):
    """The point of a light string nearest to x."""
    return min(wire, key=lambda p: abs(p[0] - x))


def paper(shapes):
    """Crayon (C) fills let what is behind them show through their strokes; over this scene's dark
    sky that would stripe them navy. Under every shape that crayon hatches, put a solid white copy
    (crayon only), as if it were drawn on clean paper."""
    out = []
    for sh in shapes:
        if sh.closed and sh.tag is None and sh.only in (None, "c") and kit.thickness(sh.pts) >= 6.5 \
                and .3 <= kit._hls(kit.crayon(sh.col))[1] <= .93:
            out.append(sh.copy(col=WHITE, tag="detail", only="c", cel=0.0, face=None, base=None, op=1.0))
        out.append(sh)
    return out


# ================================================================ background
STARS = [(28, 150, 6), (196, 22, 7), (300, 18, 4), (372, 34, 6), (436, 150, 4), (590, 196, 5), (14, 268, 4),
         (560, 470, 6), (474, 540, 4), (586, 560, 3.5), (120, 560, 6), (36, 470, 4), (206, 586, 3.5), (402, 586, 4.5),
         (446, 22, 4), (590, 26, 4)]
DOTS = [(88, 14), (150, 40), (262, 120), (330, 140), (420, 12), (468, 128), (16, 96), (584, 300), (20, 330), (110, 430),
        (70, 520), (160, 500), (440, 500), (520, 420), (580, 380), (500, 580), (300, 576), (250, 540), (360, 520)]
CLOUDS = [((92, 470), .9), ((520, 520), 1.0), ((420, 590), .7)]


def background():
    g = Group()
    sky = [(0, 0), (600, 0), (600, 600), (0, 600)]
    # A: flat navy; B: one wide stroke (a flood of ink without the paper grain a 600 x 600 fill would
    # carry); C: a lighter navy, hatched like a child colours a night sky
    g.add([Sh(sky, NIGHT, only="a"), line([(300, -10), (300, 610)], NIGHT, 640, only="b"),
           Sh(sky, NIGHT_CB, tag="detail", only="c"), Sh(sky, NIGHT_C, tag="screen", only="c")], -9000)
    g.add(oval(300, 318, 320, 240, col=HALO, tag="glow", op=.6), -8900)
    for (cx, cy), s in CLOUDS:
        c = tf(crs([(-34, 6), (-38, -4), (-26, -12), (-14, -22), (6, -22), (18, -12), (32, -10), (34, 6)]), s=s, dx=cx, dy=cy)
        g.add(Sh(c, "#33407A", only="ab"), -8800)
    for x, y, r in STARS:
        g.add(Sh(sparkle(x, y, r), STAR, tag="detail"), -8700)
    for x, y in DOTS:
        g.add(oval(x, y, 1.6, col=STAR, tag="detail", op=.85), -8700)
    # the tile: a brick base, a slab of sand-coloured paving with a pale curb
    g.add(paper(ISO.box(0, 0, -22, TILE, TILE, 16, BRICK)[:2]), -6000)
    g.add(paper(ISO.box(0, 0, -6, TILE, TILE, 6, CURB, top=SAND)), -5900)
    mortar = "#E9B39A"
    br = []
    for side in ("x", "y"):
        def S(a, z):
            return P(a, TILE, z) if side == "x" else P(TILE, a, z)
        br.append(line([S(1, -14), S(199, -14)], mortar, 1.3))
        for i in range(10):          # crayon: half the joints
            a = 10 + i * 20
            br.append(line([S(a, -14), S(a, -6.5)], mortar, 1.3, only=None if i % 2 == 0 else "ab"))
            if a + 10 < TILE:
                br.append(line([S(a + 10, -21.5), S(a + 10, -14)], mortar, 1.3, only=None if i % 2 == 1 else "ab"))
    g.add(br, -5800)
    # paving: a few lines of big flagstones
    pv = []
    for a in range(40, TILE, 40):
        pv.append(ISO.line3([(a, 1, 0), (a, TILE - 1, 0)], PAVE, .8, only="ab"))
        pv.append(ISO.line3([(1, a, 0), (TILE - 1, a, 0)], PAVE, .8, only="ab"))
    g.add(pv, -5000)
    # pools of lamp light on the street (A, B)
    for wx, wy in ((22, 176), (176, 22)):
        sx, sy = P(wx, wy)
        g.add(oval(sx, sy, 50, 24, col="#FFF0B8", tag="glow", op=.6), -4900)
    # the light pole at the back corner, with a pennant
    px, py = POLE
    g.add(ISO.box(px, py, 0, 2.4, 2.4, POLE_H, "#9A8FC0"), px + py)
    tx, ty = POLE_TOP
    g.add([Sh([(tx, ty - 2), (tx + 22, ty + 4), (tx, ty + 10)], YELLOW), oval(tx, ty - 3, 3.4, col=GOLD)], px + py + .1)
    # light strings
    for w in (WIRE_L, WIRE_R):
        g.add(line(w, WIRE, 1.4), -100)
        bulbs = []
        for i, k in enumerate(range(5, len(w) - 3, 9)):
            x, y = w[k]
            if w is WIRE_L and any(abs(x - lx) < 16 for lx in LANTERNS_AT):
                continue
            col = BULBS[i % len(BULBS)]
            bulbs.append(oval(x, y + 4.5, 6.5, col=col, tag="glow", op=.6))
            bulbs.append(oval(x, y + 4.5, 3.2, 3.8, col=col))
        g.add(bulbs, -99)
    # lamp posts at the left and right corners
    for wx, wy in ((8, 192), (192, 8)):
        g.add(lamp(wx, wy), wx + wy)
    return g.shapes()


def lamp(x, y):
    o = ISO.shadow(x + 2, y + 2, 6, .8) + ISO.cyl(x, y, 0, 4, 3, METAL) + ISO.cyl(x, y, 3, 1.7, 52, METAL)
    o += ISO.box(x - 4, y - 4, 54, 8, 8, 2, "#5A6488")
    sx, sy = P(x, y, 60.5)
    o += [oval(sx, sy, 15, col="#FFD36A", tag="glow", op=.6), oval(sx, sy, 6, col="#FFE58A", cel=.6)]
    return o + ISO.pyramid(x - 5, y - 5, 66, 10, 10, 6, "#5A6488")


# ================================================================ stalls
SL, SD, OV, HC, HF, HB = 36, 22, 4, 18, 54, 66     # length, depth, roof overhang, counter, roof front, roof back


class Stall:
    """One stall in its own coordinates: u along the back edge from u0, v from the edge (0) towards
    the street (the counter's front at SD), z up."""

    def __init__(self, name):
        self.o, self.u0 = STALLS[name]

    def W(self, u, v, z=0.0):
        return P(v, u, z) if self.o == "L" else P(u, v, z)

    def box(self, u, v, z, lu, lv, h, col, **kw):
        return ISO.box(v, u, z, lv, lu, h, col, **kw) if self.o == "L" else ISO.box(u, v, z, lu, lv, h, col, **kw)

    def cyl(self, u, v, z, R, h, col):
        return ISO.cyl(v, u, z, R, h, col) if self.o == "L" else ISO.cyl(u, v, z, R, h, col)

    def world(self, u, v):
        return (v, u) if self.o == "L" else (u, v)

    @property
    def front(self):
        """The iso face the street side shows (the left row faces +x: the darker right face)."""
        return "right" if self.o == "L" else "left"

    @property
    def side(self):
        return "left" if self.o == "L" else "right"

    def face(self, pts3, col, face):
        t, l, r = kit.shades(col)
        return Sh([self.W(*p) for p in pts3], {"top": t, "left": l, "right": r}[face], face=face, base=col)

    def depth(self, dv=0.0):
        """Painter's depth of the stall's front corner on the near side."""
        x, y = self.world(self.u0 + SL, SD + dv)
        return x + y

    def sprite(self, shapes, u, v, z, s=1.0, flip=False):
        sx, sy = self.W(u, v, z)
        return transform(shapes, dx=sx, dy=sy, s=s, flip=flip)


def awning(st, c1, c2=CREAM, dots=False, n=6):
    """The sloping striped roof (or one colour with white dots) and its scalloped valance."""
    u0, u1 = st.u0 - 2, st.u0 + SL + 2
    vf = SD + OV
    o = []

    def zr(v):
        return HB + (HF - HB) * (v + 1) / (vf + 1)
    for i in range(n):
        ua, ub = u0 + (u1 - u0) * i / n, u0 + (u1 - u0) * (i + 1) / n
        col = c1 if (dots or i % 2 == 0) else c2
        o.append(st.face([(ua, -1, HB), (ub, -1, HB), (ub, vf, HF), (ua, vf, HF)], col, "top"))
    # the side of the roof on the near end
    o.append(st.face([(u1, -1, HB), (u1, vf, HF), (u1, vf, HF - 6), (u1, -1, HB - 6)], c1, st.side))
    for i in range(n):
        ua, ub = u0 + (u1 - u0) * i / n, u0 + (u1 - u0) * (i + 1) / n
        col = c1 if (dots or i % 2 == 0) else c2
        bot = [(ub - (ub - ua) * j / 8, vf, HF - 6 - 3.6 * math.sin(math.pi * j / 8)) for j in range(9)]
        o.append(st.face([(ua, vf, HF), (ub, vf, HF)] + bot, col, st.front))
    if dots:
        for i in range(4):
            for j in range(3):
                u = u0 + 5 + i * 10 + (5 if j % 2 else 0)
                if u > u1 - 4:
                    continue
                v = 4 + j * 9.5
                sx, sy = st.W(u, v, zr(v))
                o.append(oval(sx, sy, 4.6, 3.1, col=WHITE, tag="detail"))
        for i in range(6):
            u = u0 + 3.8 + i * 7.6
            sx, sy = st.W(u, vf, HF - 4)
            o.append(oval(sx, sy, 2, col=WHITE, tag="detail"))
    return o


def stall_body(st, front, wall, c1, c2=CREAM, dots=False, goods=(), roof_top=(), bulb="#FFE58A"):
    """A whole stall: back wall, side panels, counter, posts, roof. goods: shapes on the counter
    (drawn before the roof), roof_top: shapes standing on the roof."""
    u0 = st.u0
    g = Group()
    g.add(Sh([st.W(u0, SD, 0), st.W(u0 + SL, SD, 0), st.W(u0 + SL + 1, SD + 3, 0), st.W(u0 + 1, SD + 3, 0)], "#3B5A7A", tag="shadow"), 0)
    g.add(st.box(u0, 0, 0, SL, 2, HB - 1, wall), 1)
    g.add(st.box(u0, 2, 0, 2, SD - 12, HF - 1, wall), 2)
    g.add(st.box(u0 + SL - 2, 2, 0, 2, SD - 12, HF - 1, wall), 3)
    g.add(st.box(u0, SD - 10, 0, SL, 10, HC, front), 4)
    g.add(st.box(u0 - 1, SD - 11, HC, SL + 2, 12, 2, WOOD), 5)
    g.add(list(goods), 6)
    for uu in (u0, u0 + SL - 2):
        g.add(st.box(uu, SD - 1.5, HC + 2, 2, 2, HF - HC - 4, METAL), 7)
    # a bulb under the roof
    sx, sy = st.W(u0 + SL / 2, SD + 1, HF - 9)
    g.add([line([(sx, sy - 5), (sx, sy)], WIRE, 1), oval(sx, sy + 3, 10, col=bulb, tag="glow"), oval(sx, sy + 3, 3.4, 4, col=bulb)], 7.5)
    g.add(awning(st, c1, c2, dots), 8)
    g.add(list(roof_top), 9)
    return paper(g.shapes())


# ---------------------------------------------------------------- the grill stall (烤肉串): the grill is part of it, the skewers a thing
GRILL_U = (8, 14, 20, 26)        # where the skewers stand along the grill (u from u0)


def grill_parts(st):
    u0 = st.u0
    o = st.box(u0 + 5, SD - 8.5, HC + 2, 25, 6, 6, DARK)
    sx, sy = st.W(u0 + 17.5, SD - 5.5, HC + 8)
    o.append(oval(sx, sy, 16, 5, col="#FF8A3D", tag="glow"))
    for u in GRILL_U:
        cx, cy = st.W(u0 + u, SD - 5.5, HC + 8)
        o.append(oval(cx, cy, 2.6, 1.5, col="#FF7A3D", tag="detail"))
    return o


def stall_grill(c1=RED, dots=False):
    st = Stall("grill")
    return stall_body(st, CREAM, "#E9DCCB", c1, dots=dots, goods=grill_parts(st))


def skewer_sprite():
    """A skewer standing up (origin at its foot): a stick with meat, pepper and meat."""
    o = [line([(0, 0), (0, -32)], "#E8C08A", 2)]
    for i, (col, r) in enumerate((("#B5552E", 5.4), (GREEN, 4.6), ("#C4623A", 5.4))):
        o.append(oval(0, -8 - i * 8.6, r, r * .92, col=col, cel=.6))
    return o


def skewers(n_=4):
    st = Stall("grill")
    o = []
    for k, u in enumerate(GRILL_U):
        if n_ == 3 and k == 2:
            continue
        o += st.sprite(skewer_sprite(), st.u0 + u, SD - 5.5, HC + 8, s=.78)
    return o


# ---------------------------------------------------------------- the drink stall (珍珠奶茶): wooden counter, a big cup on the roof
def cup_sprite(drink=TEA, straw=PINK, lean=22, two=False):
    """A cup of bubble milk tea (origin at the cup's foot): clear cup, drink, pearls, dome lid and a
    fat straw leaning to the right (about 34 x 92 units)."""
    o = []
    if two:
        o.append(Sh(tube([(-3, -50), (-3 - 22 * .9, -88)], 6.4), GREEN))
    o.append(Sh(tube([(2, -50), (2 + lean * .9, -90)], 6.4), straw))
    o.append(Sh(crs([(-12, -2), (0, 0), (12, -2), (16, -50), (0, -51), (-16, -50)], 6), "#EAF4FF"))
    o.append(Sh(crs([(-11, -4), (0, -2.5), (11, -4), (14.4, -44), (0, -45), (-14.4, -44)], 6), drink, cel=.4))
    for px_, py_ in ((-7, -7.5), (0, -6.5), (7, -7.5), (-4, -13.5), (4, -13.5), (-9, -14), (9, -14)):
        o.append(oval(px_, py_, 3.3, col="#3A2626"))
    o.append(oval(-2.4, -8.6, 1, col=WHITE, tag="detail", op=.8))
    o.append(Sh(rrect(-9, -40, 3.6, 26, 1.8), WHITE, op=.55, tag="detail"))
    o.append(Sh([(-17, -49)] + [(17 * math.cos(math.radians(a)), -50 - 12 * math.sin(math.radians(a))) for a in range(0, 181, 15)], "#F4F9FF", cel=.5))
    o.append(Sh(rrect(-18, -52.5, 36, 5, 2.5), "#DDE7F5"))
    return o


def stall_tea(c1=AMBER, dots=False):
    st = Stall("tea")
    big = st.sprite(cup_sprite(), st.u0 + SL / 2 - 4, 3, HB - 3, s=.66)
    return stall_body(st, WOOD, WOOD, c1, dots=dots, roof_top=big)


def tea(drink=TEA):
    st = Stall("tea")
    return st.sprite(cup_sprite(drink), st.u0 + 11, SD - 5, HC + 2, s=.42)


# ---------------------------------------------------------------- the cotton-candy stall (棉花糖)
def fluff(cx, cy, r, col):
    """A cotton-candy cloud."""
    pts = []
    for i in range(36):
        a = math.radians(i * 10)
        rr = r * (1 + .09 * math.cos(9 * a))
        pts.append((cx + rr * math.cos(a), cy + rr * .92 * math.sin(a)))
    return Sh(pts, col, cel=.8)


def stall_cotton(c1=SKY, dots=False):
    st = Stall("cotton")
    goods = st.cyl(st.u0 + 26, SD - 5.5, HC + 2, 6, 7, STEEL)
    sx, sy = st.W(st.u0 + 26, SD - 5.5, HC + 9)
    goods.append(fluff(sx, sy - 3, 7, "#FFD3E6"))
    return stall_body(st, "#FFC6DD", "#F2E6F4", c1, dots=dots, goods=goods)


def cotton(col=PINK):
    st = Stall("cotton")
    o = st.box(st.u0 + 8, SD - 7, HC + 2, 5, 5, 4, METAL)
    sx, sy = st.W(st.u0 + 10.5, SD - 4.5, HC + 6)
    o.append(line([(sx, sy), (sx, sy - 18)], "#F4E6C8", 2))
    o.append(fluff(sx, sy - 27, 11, col))
    o.append(oval(sx - 4, sy - 31, 3.4, 2.4, col=WHITE, op=.7, tag="detail"))
    return o


# ---------------------------------------------------------------- the balloon stall (氣球攤): a bunch of balloons over the roof
def balloon_sprite(col):
    """A balloon (origin at the knot)."""
    lt_ = mix(col, WHITE, .1)
    return [Sh(crs([(-4, 1), (4, 1), (0, -7)], 4), col),
            Sh(crs([(0, -5), (11, -10), (17, -24), (14, -39), (0, -47), (-14, -39), (-17, -24), (-11, -10)]), lt_, cel=1.0),
            oval(-7, -33, 3.2, 6, col=WHITE, rot=25, op=.8, tag="detail")]


BUNCH = ((-24, -60, RED), (-9, -74, YELLOW), (8, -68, BLUE), (21, -56, PURPLE), (-3, -50, ORANGE))


def stall_balloon(c1=GREEN, dots=False, n_=5):
    st = Stall("balloon")
    bx, by = st.W(st.u0 + SL / 2 - 3, 4, HB - 1)
    top = []
    for i, (dx, dy, col) in enumerate(BUNCH):
        if n_ == 4 and i == 2:
            continue
        top.append(line(crs([(bx, by), (bx + dx * .5 + 3, by + dy * .5), (bx + dx, by + dy)], 6, closed=False), METAL, 1))
    for i, (dx, dy, col) in enumerate(BUNCH):
        if n_ == 4 and i == 2:
            continue
        top += transform(balloon_sprite(col), dx=bx + dx, dy=by + dy, s=.62)
    goods = []
    for k, col in enumerate((PINK, YELLOW, "#8FE3FF")):
        goods += st.sprite(balloon_sprite(col), st.u0 + 8 + k * 10, SD - 6, HC + 2, s=.4)
    return stall_body(st, "#FFE9A0", "#E6EEF9", c1, dots=dots, goods=goods, roof_top=top)


# ================================================================ things in the street
def sign_sprite(col=ORANGE, shape="star"):
    """A standing sign (origin at its feet): two legs, a framed board with one big shape."""
    o = [line([(-26, 0), (-22, -26)], "#8A6A4A", 3.4), line([(26, 0), (22, -26)], "#8A6A4A", 3.4)]
    o.append(Sh(rrect(-38, -74, 76, 52, 9), col, cel=.25))
    o.append(Sh(rrect(-32, -68, 64, 40, 6), CREAM))
    if shape == "star":
        o.append(Sh(star_pts(17, 8, 0, -47), col, cel=.4))
    else:
        o.append(Sh(crs([(0, -32), (-14, -42), (-17, -52), (-11, -59), (-4, -58), (0, -52), (4, -58), (11, -59), (17, -52), (14, -42)], 6),
                    col, cel=.4))
    for dx in (-30, 30):
        o.append(oval(dx, -72, 3, col=GOLD))
    return o


def foot_shadow(sx, sy, rx, ry=5.0):
    return [oval(sx, sy, rx, ry, col="#3B5A7A", tag="shadow")]


def sign(col=ORANGE, shape="star"):
    sx, sy = PLACE["sign"]
    return foot_shadow(sx, sy, 34) + transform(sign_sprite(col, shape), dx=sx, dy=sy, s=1.0)


FISH = ((-11, 2, 30), (9, -6, 200), (2, 11, 140))    # world offsets from the tub centre, heading (deg)


def fish_shapes(cx, cy, head):
    """A goldfish seen from above (flattened for the iso view)."""
    a = math.radians(head)
    o = []
    tail = [(-7, 0), (-13, -5), (-12, 0), (-13, 5)]
    body = ellp(0, 0, 7.5, 4, 20)
    for pts, col in ((tail, "#FF7A2E"), (body, "#FF9A3C")):
        q = [(px_ * math.cos(a) - py_ * math.sin(a), (px_ * math.sin(a) + py_ * math.cos(a)) * .62) for px_, py_ in pts]
        o.append(Sh([(cx + px_, cy + py_) for px_, py_ in q], col))
    ex, ey = 4 * math.cos(a), 4 * math.sin(a) * .62
    o.append(oval(cx + ex, cy + ey - 1, 1.3, col=INK))
    return o


def tub(col=BLUE, n_=3):
    x, y = at("tub")
    R = 23
    o = ISO.shadow(x + 2, y + 2, R + 2, .8)
    o += ISO.cyl(x, y, 0, R, 8, col)
    o.append(ISO.disc(x, y, 8, R - 2.5, kit.tone(col, .8, 1.05)))
    o.append(ISO.disc(x + 1, y + 1, 7, R - 4, "#9FE6FF"))
    for dx, dy, l_ in ((-12, 4, 8), (10, -10, 7)):
        sx, sy = P(x + dx, y + dy, 7)
        o.append(line([(sx - l_, sy), (sx, sy - 2), (sx + l_, sy)], WHITE, 1.5, op=.85))
    for i, (dx, dy, hd) in enumerate(FISH):
        if n_ == 2 and i == 1:
            continue
        sx, sy = P(x + dx, y + dy, 7)
        o += fish_shapes(sx, sy, hd)
    # a paper scoop floating at the back
    sx, sy = P(x - 6, y - 14, 7.2)
    o.append(line([(sx + 4, sy), (sx + 16, sy - 3)], "#FFB35C", 2.2))
    o.append(oval(sx, sy + 1, 5.6, 3.4, col=WHITE))
    o.append(oval(sx, sy + 1, 4, 2.2, col="#DDF5FF", tag="detail"))
    return o


def scooter_sprite(body=RED):
    """A scooter facing left (origin under the middle, on the ground; about 92 x 64 units)."""
    dark = kit.tone(body, .82, 1.05)
    o = []
    for wx in (-30, 30):
        o += [oval(wx, -10, 10, col="#3E4566"), oval(wx, -10, 5, col="#DDE3F0"), oval(wx, -10, 2, col=METAL)]
    o.append(Sh(crs([(4, -12), (14, -26), (34, -32), (46, -26), (46, -16), (38, -14), (30, -22), (20, -14)], 6), body, cel=.9))
    o.append(Sh(rrect(-20, -16, 28, 6, 2.5), "#5A6488"))
    o.append(Sh(crs([(-38, -14), (-30, -22), (-24, -54), (-16, -56), (-14, -46), (-18, -16)], 6), body, cel=.9))
    o.append(Sh(crs([(-42, -12), (-38, -22), (-24, -24), (-20, -16), (-28, -18)], 5), dark))
    o.append(Sh(rrect(4, -40, 34, 8, 4), "#3E4566"))
    o.append(line([(-28, -58), (-12, -62)], "#3E4566", 3.2))
    o.append(line([(-14, -62), (-10, -72)], METAL, 1.6))
    o.append(oval(-9, -74, 3.4, 2.4, col="#3E4566"))
    o.append(oval(-30, -50, 5, col="#FFF6C8", tag="glow"))
    o.append(oval(-29, -50, 3.6, 3, col="#FFF6C8"))
    o.append(oval(46, -24, 2.6, col=RED))
    return o


def scooter(body=RED):
    sx, sy = PLACE["scooter"]
    return foot_shadow(sx, sy, 42, 6) + transform(scooter_sprite(body), dx=sx, dy=sy, s=.95)


def stool(col=RED):
    x, y = at("stool")
    o = ISO.shadow(x + 1, y + 1, 8, .8)
    for dx, dy in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
        o += ISO.box(x + dx - 1, y + dy - 1, 0, 2.2, 2.2, 12, kit.tone(col, .9))
    o += ISO.cyl(x, y, 12, 8, 3, col)
    sx, sy = P(x, y, 15)
    o.append(oval(sx + .5, sy, 4, 2.2, col=kit.tone(col, .7), tag="detail"))
    return o


def rubbish_bin(col="#3FAF6B"):
    x, y = at("bin")
    o = ISO.shadow(x + 1, y + 1, 9, .8)
    o += ISO.cyl(x, y, 0, 8, 20, col)
    o += ISO.cyl(x, y, 20, 8.8, 3, kit.tone(col, .8))
    sx, sy = P(x, y, 23)
    o.append(Sh(rrect(sx - 4, sy - 4, 8, 3, 1.5), kit.tone(col, .7)))
    sx, sy = P(x - 1, y + 8, 11)
    o.append(Sh(star_pts(4.4, 2, sx, sy), WHITE, tag="detail"))
    return o


# ---------------------------------------------------------------- cat and dog (sprites facing left)
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
    o = [Sh(tube(crs([(20, -24), (28, -34), (32, -46)], 6, closed=False), 6, 4), col, cel=.5)]
    for lx in (-14, -6, 8, 16):
        o.append(Sh(rrect(lx - 3.4, -16, 6.8, 16, 3.2), col if lx in (-6, 16) else kit.tone(col, .9), cel=.3))
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


def critter(name, sprite, s=1.0):
    sx, sy = PLACE[name]
    return foot_shadow(sx + 2, sy, 24) + transform(sprite, dx=sx, dy=sy, s=s)


# ================================================================ sky things
def lantern_sprite(col=RED):
    """A paper lantern (origin where its cord meets the string): about 30 x 58 units."""
    dark = kit.tone(col, .78, 1.05)
    o = [line([(0, 0), (0, 6)], WIRE, 1.2)]
    o.append(oval(0, 25, 20, col=mix(col, "#FFC27A", .45), tag="glow", op=.75))
    o.append(Sh(rrect(-7, 4.5, 14, 5, 1.6), GOLD))
    o.append(oval(0, 25, 15, 16.5, col=col, cel=1.0))
    for dx in (-8, 0, 8):
        c = [(dx * .7, 10), (dx * 1.2, 25), (dx * .7, 40)] if dx else [(0, 9), (0, 41)]
        o.append(line(crs(c, 4, closed=False) if dx else c, dark, 1.2, op=.8))
    o.append(Sh(rrect(-6, 39.5, 12, 4.5, 1.6), GOLD))
    o.append(line([(0, 44), (0, 56)], GOLD, 2.4))
    o.append(oval(0, 57, 2.4, col=GOLD))
    return o


def lanterns(col=RED, n_=3):
    o = []
    for i, x in enumerate(LANTERNS_AT):
        if n_ == 2 and i == 1:
            continue
        wx, wy = on_wire(WIRE_L, x)
        o += transform(lantern_sprite(col), dx=wx, dy=wy, s=1.12)
    return paper(o)


def moon(face="smile"):
    cx, cy = PLACE["moon"]
    o = [oval(cx, cy, 38, col="#6575B4", tag="glow"), oval(cx, cy, 34, col="#8E9AD0", tag="glow"), oval(cx, cy, 30, col=MOON, cel=.8)]
    for dx, dy, r in ((13, -15, 4.6), (19, 5, 3.2), (-16, 15, 3.6)):
        o.append(oval(cx + dx, cy + dy, r, col="#F6D987", tag="detail"))
    o.append(oval(cx - 15, cy + 7, 5, 3, col="#FFAFC0", op=.85, tag="detail"))
    o.append(oval(cx + 15, cy + 7, 5, 3, col="#FFAFC0", op=.85, tag="detail"))
    if face == "smile":
        for ex in (-10, 10):
            o.append(oval(cx + ex, cy - 4, 3.2, 4.2, col=INK))
            o.append(oval(cx + ex - 1, cy - 5.6, 1.2, col=WHITE, tag="detail"))
        o.append(line(crs([(cx - 7, cy + 7), (cx, cy + 12), (cx + 7, cy + 7)], 6, closed=False), INK, 2.4))
    else:   # asleep
        for ex in (-10, 10):
            o.append(line([(cx + ex - 5, cy - 4), (cx + ex, cy), (cx + ex + 5, cy - 4)], INK, 2.4))
        o.append(oval(cx, cy + 10, 3, 2.4, col=INK))
    return paper(o)


def balloon2():
    cx, cy = PLACE["balloon2"]
    o = [line(crs([(0, 0), (4, 8), (-2, 16), (1, 24)], 6, closed=False), METAL, 1.2)]
    o += balloon_sprite("#8FE3FF")
    return paper(transform(o, dx=cx, dy=cy, s=1.2))


def firefly():
    """A firefly flying to the left: a big glowing tail, a little dark head, white wings."""
    cx, cy = PLACE["firefly"]
    o = [oval(cx + 6, cy + 2, 16, col="#E8FF8A", tag="glow"),
         line([(cx - 10, cy - 4), (cx - 15, cy - 12), (cx - 19, cy - 13)], INK, 1.3),
         line([(cx - 8, cy - 5), (cx - 10, cy - 14), (cx - 14, cy - 17)], INK, 1.3),
         oval(cx + 7, cy + 2, 8.5, 7.5, col="#EEFF6A", cel=.6),
         oval(cx - 3, cy - 1, 6.5, 6, col="#4A5070", cel=.5),
         oval(cx - 9, cy - 2, 4.6, col="#3E4566"),
         oval(cx - 10.4, cy - 3, 1.3, col=WHITE, tag="detail"),
         oval(cx - 1, cy - 11, 8, 4.6, col=WHITE, rot=-35, op=.9),
         oval(cx + 6, cy - 11, 8, 4.6, col="#E6F0FF", rot=25, op=.9)]
    return o


def firework():
    """A firework bursting in the sky: rays of dots in three colours around a bright middle."""
    cx, cy = PLACE["firework"]
    o = [oval(cx, cy, 40, col="#7A6AB8", tag="glow", op=.6)]
    for i in range(12):
        a = math.radians(i * 30 + 8)
        col = (PINK, YELLOW, "#8FE3FF")[i % 3]
        ca, sa = math.cos(a), math.sin(a)
        o.append(line([(cx + 10 * ca, cy + 10 * sa), (cx + 34 * ca, cy + 34 * sa)], col, 3))
        o.append(oval(cx + 42 * ca, cy + 42 * sa, 4.2, col=col))
    o.append(Sh(sparkle(cx, cy, 13), WHITE))
    return o


# ================================================================ lineup (哪一個不一樣？): bubble milk tea
def lineup_cup(drink=TEA, two=False):
    return transform([oval(0, 0, 22, 5, col="#86D8F7", op=.5)] + cup_sprite(drink, two=two), s=1.0)


# ================================================================ the scene
def scene():
    sa = kit.SceneArt("market", "夜市", "night market")
    sa.background(background)
    C = kit
    zg = int(Stall("grill").depth())
    zt = int(Stall("tea").depth())
    zc = int(Stall("cotton").depth())
    zb = int(Stall("balloon").depth())
    sa.thing("lanterns", "燈籠", "lanterns",
             {"lanterns": lanterns, "lanterns_blue": lambda: lanterns(BLUE), "lanterns_two": lambda: lanterns(n_=2)},
             [C.color("lanterns_blue", "燈籠變藍色了！"), C.count("lanterns_two", "燈籠少了一個！"), C.gone("燈籠不見了！")],
             big=True, z=3)
    sa.thing("moon", "月亮", "moon", {"moon": moon, "moon_sleep": lambda: moon("sleep")},
             [C.face_("moon_sleep", "月亮睡著了！"), C.gone("月亮不見了！")], big=True, z=1)
    sa.thing("stall_grill", "烤肉攤", "grill stall",
             {"stall_grill": stall_grill, "stall_grill_blue": lambda: stall_grill(BLUE), "stall_grill_dots": lambda: stall_grill(dots=True)},
             [C.color("stall_grill_blue", "烤肉攤變成藍色了！"), C.pattern("stall_grill_dots", "烤肉攤的棚子變成點點了！"), C.gone("烤肉攤不見了！")],
             big=True, z=zg)
    sa.thing("skewers", "烤肉串", "skewers", {"skewers": skewers, "skewers_three": lambda: skewers(3)},
             [C.count("skewers_three", "烤肉串少了一串！"), C.gone("烤肉串不見了！")], z=zg + 2)
    sa.thing("stall_tea", "飲料攤", "drink stall",
             {"stall_tea": stall_tea, "stall_tea_pink": lambda: stall_tea(PINK)},
             [C.color("stall_tea_pink", "飲料攤變成粉紅色了！"), C.gone("飲料攤不見了！")],
             big=True, z=zt)
    sa.thing("tea", "珍珠奶茶", "bubble tea", {"tea": tea, "tea_pink": lambda: tea("#FF9EC7")},
             [C.color("tea_pink", "珍珠奶茶變成粉紅色了！"), C.gone("珍珠奶茶不見了！"), C.size(1.5, "珍珠奶茶變大了！")], z=zt + 2)
    sa.thing("stall_cotton", "棉花糖攤", "cotton-candy stall",
             {"stall_cotton": stall_cotton, "stall_cotton_purple": lambda: stall_cotton(PURPLE)},
             [C.color("stall_cotton_purple", "棉花糖攤變成紫色了！"), C.gone("棉花糖攤不見了！")],
             big=True, z=zc)
    sa.thing("cotton", "棉花糖", "cotton candy", {"cotton": cotton, "cotton_blue": lambda: cotton("#8FC8FF")},
             [C.color("cotton_blue", "棉花糖變成藍色了！"), C.gone("棉花糖不見了！"), C.size(1.5, "棉花糖變大了！")], z=zc + 2)
    sa.thing("stall_balloon", "氣球攤", "balloon stall",
             {"stall_balloon": stall_balloon, "stall_balloon_orange": lambda: stall_balloon(ORANGE),
              "stall_balloon_four": lambda: stall_balloon(n_=4)},
             [C.color("stall_balloon_orange", "氣球攤變成橘色了！"), C.count("stall_balloon_four", "氣球少了一顆！"), C.gone("氣球攤不見了！")],
             big=True, z=zb)
    sa.thing("sign", "招牌", "sign", {"sign": sign, "sign_green": lambda: sign(GREEN), "sign_heart": lambda: sign(shape="heart")},
             [C.color("sign_green", "招牌變成綠色了！"), C.pattern("sign_heart", "招牌上的星星變成愛心了！"), C.gone("招牌不見了！")],
             big=True, z=int(depth("sign")))
    sa.thing("tub", "金魚池", "goldfish tub", {"tub": tub, "tub_red": lambda: tub(RED), "tub_two": lambda: tub(n_=2)},
             [C.color("tub_red", "金魚池變成紅色了！"), C.count("tub_two", "金魚少了一隻！"), C.gone("金魚池不見了！")],
             big=True, z=int(depth("tub")))
    sa.thing("scooter", "機車", "scooter", {"scooter": scooter, "scooter_blue": lambda: scooter(BLUE)},
             [C.color("scooter_blue", "機車變成藍色了！"), C.flip("機車轉向另一邊了！"), C.gone("機車不見了！")],
             big=True, z=int(depth("scooter")))
    sa.thing("cat", "小貓", "cat", {"cat": lambda: critter("cat", cat_sprite(), 1.2), "cat_dog": lambda: critter("cat", dog_sprite(), 1.2)},
             [C.swap("cat_dog", "小貓變成小狗了！"), C.flip("小貓轉向另一邊了！"), C.gone("小貓不見了！")], z=int(depth("cat")))
    sa.thing("stool", "椅子", "stool", {"stool": stool, "stool_blue": lambda: stool(BLUE)},
             [C.color("stool_blue", "椅子變成藍色了！"), C.gone("椅子不見了！")], z=int(depth("stool")))
    sa.thing("bin", "垃圾桶", "rubbish bin", {"bin": rubbish_bin, "bin_orange": lambda: rubbish_bin(ORANGE)},
             [C.color("bin_orange", "垃圾桶變成橘色了！"), C.gone("垃圾桶不見了！")], z=int(depth("bin")))
    sa.extra("balloon2", "氣球", "balloon", balloon2, "多了一顆氣球！", z=2, big=True)
    sa.extra("firework", "煙火", "firework", firework, "多了一朵煙火！", z=4, big=True)
    sa.extra("firefly", "螢火蟲", "firefly", firefly, "多了一隻螢火蟲！", z=900)
    zs = {t.id: t.z for t in sa.things}
    for (cx, cy), size_, front, tint in HIDES:
        sa.hide(cx, cy, size_, zs[front] - 1, tint)
    sa.lineup({"cup": lineup_cup, "cup_pink": lambda: lineup_cup("#FF9EC7"), "cup_two": lambda: lineup_cup(two=True)}, "珍珠奶茶",
              # the second straw is something added (「多了一個」, for 2-3 years too): an art change without a type
              [C.color("cup_pink", "這杯是粉紅色的！"), {"kind": "art", "art": "cup_two", "said": "這杯多了一根吸管！"},
               C.flip("這杯的吸管歪向另一邊！")])
    return sa


# hide spots: (centre in scene px, size in scene px, the thing drawn in front of part of him, tint)
HIDES = [((127, 84), 40, "lanterns", "red"), ((349, 194), 36, "tea", "wood"), ((474, 344), 38, "stool", "sand")]

# for `build.py preview`: the changed version shows these
PREVIEW_CHANGES = [("lanterns", 0), ("stall_grill", 1), ("tub", 1), ("scooter", 1), ("moon", 0), ("balloon2", "extra:balloon2")]


if __name__ == "__main__":
    scene().build()
