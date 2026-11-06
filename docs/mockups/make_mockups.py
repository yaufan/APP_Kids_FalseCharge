"""Design-stage sketches for the spot-the-difference game 「咦！哪裡不一樣？」 (working name, not final).

    python3 make_mockups.py          # writes docs/mockups/*.png (needs Node.js and Playwright)
    python3 make_mockups.py items    # one sheet of the characters in the three styles (written to the temp folder)
    python3 make_mockups.py 4        # only one page: 0 = style page, 1..7 = a screen, c = contact sheet

Every picture is drawn here as SVG shapes by code (no outside pictures, no emoji). render.js turns
each page into a PNG with Playwright's Chromium. The font is jf open-huninn from the sibling
字母寵物 checkout.

    0_畫風選擇.png      the same park corner (slide, tree, red balloon, duck pond, 小變 peeking
                        from behind the tree) in three styles: A 等角小模型風, B 孔版印刷風, C 粗蠟筆童畫風
    1_首頁.png          home: title, 小變 waving, six scene cards (isometric dioramas) with stars,
                        the grey parents' lock and the 相簿 (album) button
    2_找出不一樣的.png  2-3 years: 哪一個不一樣？ four rubber ducks, one wears a red hat
    3_哪裡變了.png      小變變了什麼？ one park picture, 小變 says 變！, the red balloon is now blue
    4_兩張找不同.png    3-5 years: two night-market pictures, 5 differences, 3 found (green rings on both)
    5_躲貓貓.png        小變躲在哪裡？ a busy beach, 小變 coloured like a sand rock (eyes and tail show)
    6_找到了.png        reward: the scene card fills with colour, gets a stamp and flies into the album
    7_家長模式.png      parents' settings: age, play time, hints, sound, English, progress
    contact_sheet.png  screens 1-7 in two rows

Style A 「等角小模型風」 (used for screens 1-7): little toy dioramas in isometric projection
(`P(x, y, z)`: 30 degrees from above). Boxes, cylinders and roofs are flat-shaded: the top face is
the lightest, the left face the base colour, the right face darker; every face carries a stroke of its
own colour so corners come out soft and round; no outlines anywhere. Round things (小變, ducks,
balloons, tree crowns) are sprites standing in the scene with a light crescent on top and a darker
crescent on the right, the same light as the boxes. Each scene sits on a floating tile.
Style B 「孔版印刷風」: three riso inks (fluorescent pink, blue, yellow). Every shape says how much of
each ink it takes; each ink is its own layer, painted in order (no ink = a white knock-out), then the
layers are multiplied together, so overlapping inks mix (yellow + blue = green, pink + yellow = red,
pink + blue = deep navy). Each layer is a little out of register and has fine grain (tiny white dots).
Style C 「粗蠟筆童畫風」: the same shapes drawn by a child with thick crayons: wobbly double outlines,
back-and-forth scribble fill that goes a little over the lines, waxy texture, white paper.
"""
import colorsys
import hashlib
import math
import pathlib
import random
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
FONT = pathlib.Path("/home/user/app_kids_paint_for_learning_writing/app/assets/fonts/jf-openhuninn-2.1.ttf")
if not FONT.exists():
    FONT = HERE.parents[2] / "app_kids_paint_for_learning_writing" / "app" / "assets" / "fonts" / "jf-openhuninn-2.1.ttf"
SCRATCH = pathlib.Path(tempfile.gettempdir())
W, H = 390, 844

# ---------------------------------------------------------------- colours
INK = "#33406B"        # words: deep blue slate
SOFT = "#8C95B8"
GREEN = "#4CC46A"      # 小變 green, "found" rings
GOLD = "#FFC93C"


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def mix(a, b, t):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(x + (y - x) * t))) for x, y in zip(_rgb(a), _rgb(b)))


def lt(c, t):
    return mix(c, "#FFFFFF", t)


def _hls(c):
    return colorsys.rgb_to_hls(*[x / 255 for x in _rgb(c)])


def _hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def tone(c, l=1.0, s=1.0, dh=0.0):
    h, L, S = _hls(c)
    return _hex(h + dh, L * l, S * s)


def multiply(*cols):
    out = [255, 255, 255]
    for c in cols:
        out = [a * b / 255 for a, b in zip(out, _rgb(c))]
    return "#%02X%02X%02X" % tuple(round(x) for x in out)


# ---------------------------------------------------------------- defs registry
class Defs:
    def __init__(self):
        self.d = {}

    def add(self, key, svg):
        self.d.setdefault(key, svg)
        return key

    def svg(self):
        return "<defs>" + "".join(self.d.values()) + "</defs>"


D = Defs()


def _h(*parts):
    return hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:10]


def _stops(stops):
    return "".join(f'<stop offset="{s[0]}" stop-color="{s[1]}"' + (f' stop-opacity="{s[2]}"' if len(s) > 2 else "") + "/>" for s in stops)


def lg(stops, x1=0, y1=0, x2=0, y2=1, user=False):
    k = "lg" + _h(stops, x1, y1, x2, y2, user)
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    D.add(k, f'<linearGradient id="{k}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{u}>{_stops(stops)}</linearGradient>')
    return f"url(#{k})"


def rg(stops, cx=.5, cy=.5, r=.5, user=False):
    k = "rg" + _h(stops, cx, cy, r, user)
    u = ' gradientUnits="userSpaceOnUse"' if user else ""
    D.add(k, f'<radialGradient id="{k}" cx="{cx}" cy="{cy}" r="{r}"{u}>{_stops(stops)}</radialGradient>')
    return f"url(#{k})"


def clip(d):
    k = "cp" + _h(d)
    D.add(k, f'<clipPath id="{k}"><path d="{d}"/></clipPath>')
    return f"url(#{k})"


def cel_mask(d, s):
    """The shape minus a copy of itself moved by s: a crescent on the opposite side."""
    k = "cm" + _h(d, s)
    D.add(k, f'<mask id="{k}" maskUnits="userSpaceOnUse" x="-4000" y="-4000" width="8000" height="8000">'
             f'<path d="{d}" fill="#fff"/><path d="{d}" fill="#000" transform="translate({s[0]:.2f} {s[1]:.2f})"/></mask>')
    return f"url(#{k})"


def blur(sd):
    k = "bl" + str(sd).replace(".", "_")
    D.add(k, f'<filter id="{k}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="{sd}"/></filter>')
    return f"url(#{k})"


def drop(op=.14, dy=5, sd=7, col="#4A5A8A"):
    k = "ds" + _h(op, dy, sd, col)
    D.add(k, f'<filter id="{k}" x="-20%" y="-20%" width="140%" height="150%">'
             f'<feDropShadow dx="0" dy="{dy}" stdDeviation="{sd}" flood-color="{col}" flood-opacity="{op}"/></filter>')
    return f"url(#{k})"


def grey_filter(sat=0.0, lift=.18):
    k = "gf" + _h(sat, lift)
    a = 1 - lift
    D.add(k, f'<filter id="{k}" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="{sat}"/>'
             f'<feComponentTransfer><feFuncR type="linear" slope="{a}" intercept="{lift}"/><feFuncG type="linear" slope="{a}" intercept="{lift}"/>'
             f'<feFuncB type="linear" slope="{a}" intercept="{lift}"/></feComponentTransfer></filter>')
    return f"url(#{k})"


# ================================================================ GEOMETRY (point lists, shared by the three styles)
def ellp(cx, cy, rx, ry=None, n=44, rot=0.0):
    ry = rx if ry is None else ry
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def crs(ctrl, n=10, closed=True):
    """Catmull-Rom spline through the control points, as a dense point list."""
    m = len(ctrl)
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        p0 = ctrl[(i - 1) % m] if closed else ctrl[max(i - 1, 0)]
        p1, p2 = ctrl[i], ctrl[(i + 1) % m]
        p3 = ctrl[(i + 2) % m] if closed else ctrl[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                   + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(tuple(ctrl[-1]))
    return out


def rrect(x, y, w, h, r, n=6):
    out = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def tube(c, w0, w1=None, caps=True):
    """A closed outline around the centre line c (dense points), width w0 at the start to w1 at the end."""
    w1 = w0 if w1 is None else w1
    n = len(c)
    L, R, dirs = [], [], []
    for i, (x, y) in enumerate(c):
        x0, y0 = c[max(i - 1, 0)]
        x1, y1 = c[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        dx, dy = dx / ln_, dy / ln_
        dirs.append((dx, dy))
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        L.append((x - dy * w, y + dx * w))
        R.append((x + dy * w, y - dx * w))

    def cap(p, d, w, start):
        out = []
        for k in range(1, 8):
            ph = math.pi * k / 8
            nx, ny = -d[1], d[0]
            sgn = -1 if start else 1
            out.append((p[0] + w * (math.cos(ph) * nx * (1 if not start else -1) + math.sin(ph) * d[0] * sgn),
                        p[1] + w * (math.cos(ph) * ny * (1 if not start else -1) + math.sin(ph) * d[1] * sgn)))
        return out
    if not caps:
        return L + R[::-1]
    return L + cap(c[-1], dirs[-1], w1 / 2, False) + R[::-1] + cap(c[0], dirs[0], w0 / 2, True)


def tf(pts, dx=0.0, dy=0.0, rot=0.0, s=1.0, about=(0.0, 0.0), sx=None):
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    sx = s if sx is None else sx
    out = []
    for x, y in pts:
        x, y = (x - about[0]) * sx, (y - about[1]) * s
        out.append((about[0] + x * ca - y * sa + dx, about[1] + x * sa + y * ca + dy))
    return out


def star_pts(R, r, cx=0.0, cy=0.0, n=5, rot=-90.0):
    out = []
    for i in range(2 * n):
        a = math.radians(rot + 180 * i / n)
        rr_ = R if i % 2 == 0 else r
        out.append((cx + rr_ * math.cos(a), cy + rr_ * math.sin(a)))
    return out


def star_round(R, r, cx=0.0, cy=0.0, n=5, rot=-90.0):
    return crs(star_pts(R, r, cx, cy, n, rot), 6)


class Sh:
    """One shape: dense points, a colour role, closed (filled) or open (a stroke of width w)."""
    __slots__ = ("pts", "role", "closed", "w", "shade", "op")

    def __init__(self, pts, role, closed=True, w=0.0, shade=None, op=1.0):
        self.pts, self.role, self.closed, self.w, self.shade, self.op = pts, role, closed, w, shade, op

    def d(self):
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in self.pts) + ("Z" if self.closed else "")

    def bbox(self):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)

    def moved(self, **kw):
        return Sh(tf(self.pts, **kw), self.role, self.closed, self.w * kw.get("s", 1.0), self.shade, self.op)


def moved(shapes, **kw):
    return [s.moved(**kw) for s in shapes]


def recolor(shapes, rolemap):
    return [Sh(s.pts, rolemap.get(s.role, s.role), s.closed, s.w, s.shade, s.op) for s in shapes]


# colour roles: (style A colour, style B inks {Y, P, B: density}, style C crayon)
ROLE = {
    "skyb": ("#CDEFFF", {"B": .3, "ht": True}, "#9FD8FF"),
    "cg": ("#5ACB6C", {"Y": 1, "B": .5}, "#22B04A"),        # 小變
    "cgl": ("#D2F28C", {"Y": 1, "B": .14}, "#A8DC3C"),       # 小變 belly and spots
    "cgd": ("#3BAA5A", {"Y": 1, "B": .8}, "#12853A"),
    "eyew": ("#FFFFFF", {}, "#FFFFFF"),
    "ink": ("#2B3158", {"B": 1, "P": .85}, "#1C1C2C"),
    "cheek": ("#FF9DB6", {"P": .45}, "#FF6FA8"),
    "tongue": ("#FF7598", {"P": .9, "Y": .15}, "#FF4F86"),
    "red": ("#FF5A5F", {"P": 1, "Y": 1}, "#EE2A2A"),
    "blue": ("#4C8DFF", {"B": 1}, "#1F5FE0"),
    "yellow": ("#FFD84A", {"Y": 1}, "#FFD000"),
    "yellowd": ("#F6B92E", {"Y": 1, "P": .2}, "#F2A300"),
    "orange": ("#FF9838", {"Y": 1, "P": .6}, "#FF7A00"),
    "brown": ("#B98356", {"Y": .8, "P": .5, "B": .45}, "#8E5124"),
    "brownd": ("#946542", {"Y": .9, "P": .6, "B": .6}, "#6E3A14"),
    "water": ("#7DD3F5", {"B": .45}, "#3DB4F0"),
    "waterd": ("#4FB6E8", {"B": .7}, "#1E8FD8"),
    "grass": ("#8EDB78", {"Y": 1, "B": .4}, "#5CCB3A"),
    "leaf": ("#5BC46A", {"Y": 1, "B": .75}, "#1F9E3A"),
    "leafl": ("#86DB72", {"Y": 1, "B": .45}, "#43BF34"),
    "white": ("#FFFFFF", {}, "#FFFFFF"),
    "cloud": ("#FFFFFF", {}, "#FFFFFF"),
    "sky": ("#CDEFFF", {"B": .14}, "#9FD8FF"),
    "sun": ("#FFD84A", {"Y": 1, "P": .25}, "#FFC400"),
    "sand": ("#F3D69A", {"Y": .55, "P": .12}, "#F2C060"),
    "sandd": ("#DDB574", {"Y": .7, "P": .25, "B": .1}, "#D59A3A"),
    "skin": ("#FFD2B3", {"Y": .3, "P": .25}, "#FFB98A"),
    "skind": ("#F0AE88", {"Y": .4, "P": .4}, "#E08A5A"),
    "sleeve": ("#7FA8FF", {"B": .6}, "#3F7BF0"),
    "pink": ("#FF9EC7", {"P": .7}, "#FF5FB0"),
    "grey": ("#BAC4DA", {"B": .3, "P": .1}, "#8890A0"),
    "purple": ("#B48CFF", {"B": .7, "P": .6}, "#8A4FE8"),
    "metal": ("#9AA6C2", {"B": .5, "P": .2}, "#6A7488"),
}


def rc(role, style="a"):
    if role.startswith("#"):
        return role
    return ROLE[role][{"a": 0, "b": 1, "c": 2}[style]]


# ================================================================ STYLE A SPRITES (flat shading, no outlines)
def a_light(c):
    return mix(c, "#FFFFFF", .42)


def a_dark(c):
    h, L, S = _hls(c)
    if S < .1:
        return mix(c, "#B8C6E6", .55)
    return _hex(h + .005, L * .84, min(1, S * 1.04))


def draw_a(shapes, overrides=None):
    o = []
    for sh in shapes:
        col = (overrides or {}).get(sh.role) or rc(sh.role)
        d = sh.d()
        op = f' opacity="{sh.op}"' if sh.op != 1 else ""
        if not sh.closed:
            o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sh.w:.2f}" stroke-linecap="round" stroke-linejoin="round"{op}/>')
            continue
        o.append(f'<path d="{d}" fill="{col}"{op}/>')
        x0, y0, x1, y1 = sh.bbox()
        size = min(x1 - x0, y1 - y0)
        shade = sh.shade if sh.shade is not None else size > 9
        if shade:
            t = (shade if isinstance(shade, float) else 1.0) * max(1.6, min(9.0, size * .16))
            o.append(f'<path d="{d}" fill="{a_light(col)}" mask="{cel_mask(d, (t * .3, t))}"{op}/>')
            o.append(f'<path d="{d}" fill="{a_dark(col)}" mask="{cel_mask(d, (-t, -t * .25))}"{op}/>')
    return "".join(o)


# ---------------------------------------------------------------- 小變 the chameleon
def spiral(c, r0, turns, th0, n=80, shrink=.82):
    out = []
    for i in range(n + 1):
        t = i / n
        th = math.radians(th0 + t * turns * 360)
        r = r0 * (1 - shrink * t)
        out.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
    return out


def mitten(x, y, a=0.0, r=6.6, role="cg"):
    dx, dy = math.cos(math.radians(a)) * r * .62, math.sin(math.radians(a)) * r * .62
    return [Sh(ellp(x - dx, y - dy, r), role, shade=False), Sh(ellp(x + dx, y + dy, r), role, shade=False)]


def arm(pts, role="cg", w=11.5):
    return Sh(tube(crs(pts, 8, closed=False), w, w * .9), role, shade=.6)


def chameleon(pose="wave", look=(0.0, 0.0), tilt=0.0):
    """小變: big round eyes in green turrets, a curly tail, a cheeky smile. Origin between the feet.
    Returns (back, front): `front` is drawn over whatever he hides behind (his gripping hand)."""
    back, front = [], []
    # tail: from the back of the body, up, round and curling in underneath
    tl = spiral((64, -32), 25, 1.45, 205, 70)
    back.append(Sh(tube(tl, 15, 5.5), "cg", shade=.7))
    for t in (.12, .3, .48, .66):
        x, y = tl[int(t * (len(tl) - 1))]
        back.append(Sh(ellp(x, y, 3.2 - t * 2.2), "cgl", shade=False))
    # feet and body
    back += [Sh(ellp(-17, -5, 13, 7), "cg", shade=.5), Sh(ellp(17, -5, 13, 7), "cg", shade=.5)]
    back.append(Sh(crs([(-30, -12), (-15, -3), (0, -1), (15, -3), (30, -12), (36, -36), (30, -62), (14, -77),
                        (-14, -77), (-30, -62), (-36, -36)]), "cg"))
    back.append(Sh(ellp(0, -36, 18.5, 24), "cgl", shade=.5))
    for y in (-42, -32, -22):
        back.append(Sh(crs([(-14, y), (0, y + 3), (14, y)], 6, closed=False), "cg", closed=False, w=1.6, op=.45))
    back.append(Sh(ellp(-28, -44, 4), "cgl", shade=False))
    back.append(Sh(ellp(28, -30, 3.4), "cgl", shade=False))
    # arms
    if pose == "wave":
        back.append(arm([(-25, -60), (-38, -48), (-36, -34)]))
        back += mitten(-36, -31, 0)
        back.append(arm([(24, -62), (44, -76), (52, -100)]))
        back += mitten(53, -104, 90)
        for k in (0, 1):
            r = 14 + k * 8
            back.append(Sh([(70 + r * math.cos(math.radians(a)) * .6, -104 + r * math.sin(math.radians(a)))
                            for a in range(-50, 40, 6)], "cgd", closed=False, w=2.6, op=.7))
    elif pose == "cheer":
        back.append(arm([(-24, -62), (-44, -82), (-50, -108)]))
        back += mitten(-51, -112, 90)
        back.append(arm([(24, -62), (44, -82), (50, -108)]))
        back += mitten(51, -112, 90)
    elif pose == "magic":
        back.append(arm([(-25, -60), (-38, -48), (-36, -34)]))
        back += mitten(-36, -31, 0)
        back.append(arm([(24, -62), (46, -70), (66, -84)]))
        back += mitten(69, -87, 40)
    elif pose == "peek":
        front.append(arm([(-22, -70), (-40, -84), (-50, -96)], w=10.5))
        front += mitten(-53, -99, 75, 6.2)
    # head (can tilt about the neck)
    hd = []
    hd.append(Sh(crs([(-14, -144), (-6, -162), (8, -165), (18, -152), (16, -140)]), "cg", shade=.7))
    hd.append(Sh(crs([(-52, -108), (-46, -86), (-24, -74), (0, -71), (26, -74), (48, -86), (54, -108), (44, -134),
                      (20, -148), (-20, -148), (-44, -134)]), "cg"))
    hd.append(Sh(ellp(2, -153, 3), "cgl", shade=False))
    hd.append(Sh(ellp(-10, -138, 3.6), "cgl", shade=False))
    hd.append(Sh(ellp(13, -141, 2.6), "cgl", shade=False))
    lx, ly = look
    for ex in (-30, 30):
        hd.append(Sh(ellp(ex, -119, 24.5), "cg", shade=.75))
        hd.append(Sh([(ex + 21 * math.cos(math.radians(a)), -119 + 21 * math.sin(math.radians(a))) for a in range(200, 300, 8)],
                     "cgd", closed=False, w=2.2, op=.55))
        if pose == "cheer":
            hd.append(Sh(ellp(ex, -118, 17.5), "eyew", shade=False))
            hd.append(Sh([(ex - 9, -114), (ex - 4.5, -123), (ex, -125.5), (ex + 4.5, -123), (ex + 9, -114)], "ink", closed=False, w=4))
        else:
            hd.append(Sh(ellp(ex + lx * 2.6, -118 + ly * 2.6, 17.5), "eyew", shade=False))
            px, py = ex + lx * 7, -118 + ly * 7
            hd.append(Sh(ellp(px, py, 10.2), "ink", shade=False))
            hd.append(Sh(ellp(px - 3.6, py - 4, 3.7), "eyew", shade=False))
            hd.append(Sh(ellp(px + 3.6, py + 3.4, 1.6), "eyew", shade=False))
    hd.append(Sh(ellp(-6, -101, 1.8), "cgd", shade=False))
    hd.append(Sh(ellp(6, -101, 1.8), "cgd", shade=False))
    if pose in ("cheer", "magic"):
        mouth = crs([(-19, -93), (-10, -88), (0, -87), (10, -88), (19, -93), (12, -80), (0, -76), (-12, -80)])
        hd.append(Sh(mouth, "ink", shade=False))
        hd.append(Sh(crs([(-9, -80.5), (0, -86), (9, -80.5), (0, -77)]), "tongue", shade=False))
    else:
        hd.append(Sh(crs([(17, -91), (24, -85.5), (22, -79), (16, -82.5)]), "tongue", shade=False))
        hd.append(Sh(crs([(-25, -95), (-10, -86), (6, -85), (20, -90), (27, -97)], 8, closed=False), "ink", closed=False, w=3.4))
    hd.append(Sh(ellp(-41, -97, 7.5, 4.6), "cheek", shade=False, op=.85))
    hd.append(Sh(ellp(41, -97, 7.5, 4.6), "cheek", shade=False, op=.85))
    if tilt:
        hd = moved(hd, rot=tilt, about=(0, -78))
    back += hd
    return back, front


def hide_rock():
    """The sand-coloured rock with 小變 on it, coloured like the rock: only his eyes and curly tail show."""
    R_, Rd = "#E6C283", "#C9A060"
    o = []
    for ex, ey in ((-13, -35), (10, -38)):
        o.append(Sh(ellp(ex, ey, 10), R_, shade=.8))
        o.append(Sh(ellp(ex - 1.6, ey - .5, 7.2), "eyew", shade=False))
        o.append(Sh(ellp(ex - 4, ey, 4.2), "ink", shade=False))
        o.append(Sh(ellp(ex - 5.4, ey - 1.6, 1.5), "eyew", shade=False))
    o.append(Sh(crs([(-34, 0), (-38, -14), (-28, -28), (-8, -32), (14, -33), (32, -22), (36, 0)]), R_, shade=1.1))
    tl = spiral((42, -12), 11, 1.5, 200, 60)
    o.append(Sh(tube(tl, 7, 3), R_, shade=False))
    o.append(Sh(tl[:-6], Rd, closed=False, w=1.3))
    for x, y in ((-20, -14), (4, -20), (20, -10)):
        o.append(Sh(ellp(x, y, 2.2, 1.4), Rd, shade=False, op=.6))
    return o


# ---------------------------------------------------------------- other sprites
def duck(hat=False):
    """Yellow rubber duck facing left, origin on the water line."""
    o = [Sh(crs([(-36, -16), (-28, -3), (-6, 2), (22, 0), (40, -10), (50, -31), (44, -34), (34, -27), (12, -29),
                 (-14, -31), (-30, -27)]), "yellow")]
    o.append(Sh(crs([(0, -19), (14, -26), (27, -22), (21, -11), (5, -10)]), "yellowd", shade=False))
    o.append(Sh(ellp(-18, -48, 19.5), "yellow"))
    o.append(Sh(crs([(-33, -47), (-49, -46), (-56, -40), (-49, -34), (-33, -37)]), "orange", shade=.6))
    o.append(Sh(ellp(-24, -53, 3.7, 4.7), "ink", shade=False))
    o.append(Sh(ellp(-25.3, -54.8, 1.5), "white", shade=False))
    o.append(Sh(ellp(-12, -41, 4.6, 2.8), "cheek", shade=False, op=.75))
    if hat:
        o.append(Sh(crs([(-32, -64), (-30, -80), (-18, -88), (-5, -81), (-4, -64)]), "red"))
        o.append(Sh([(-31.4, -66.5), (-31, -73), (-4.6, -73), (-4.2, -66.5)], "white", shade=False))
        o.append(Sh(ellp(-18, -64, 23, 6.2, rot=-6), "red", shade=.6))
    return o


def balloon(role="red"):
    """Origin at the knot."""
    return [Sh(crs([(-5, 1), (5, 1), (0, -9)], 4), role, shade=False),
            Sh(crs([(0, -6), (14, -12), (22, -30), (18, -50), (0, -60), (-18, -50), (-22, -30), (-14, -12)]), role),
            Sh(ellp(-9, -42, 4, 7.5, rot=25), "white", shade=False, op=.75)]


def pointing_hand():
    """A child's hand pointing up-left; origin at the fingertip."""
    o = [Sh(tube(crs([(38, 60), (52, 78), (64, 96)], 6, closed=False), 30, 32, caps=False), "skin", shade=.6)]
    o.append(Sh(tf(rrect(-25, -15, 50, 30, 11), rot=-38, dx=70, dy=104), "sleeve", shade=.6))
    o.append(Sh(crs([(14, 36), (34, 30), (50, 40), (56, 60), (46, 76), (26, 78), (12, 64)]), "skin", shade=.7))
    o.append(Sh(tube(crs([(0, 4), (10, 22), (20, 42)], 8, closed=False), 15, 16), "skin", shade=.6))
    o.append(Sh(tube(crs([(16, 56), (6, 58), (2, 66)], 6, closed=False), 12, 11), "skin", shade=False))
    for y in (48, 58, 68):
        o.append(Sh([(32, y), (44, y + 2)], "skind", closed=False, w=2))
    o.append(Sh(ellp(3, 7, 4, 5, rot=-30), "white", shade=False, op=.55))
    return o


# ================================================================ STYLE B (riso print) AND C (crayon) RENDERERS
RISO = {"Y": "#FFE800", "P": "#FF48B0", "B": "#0078BF"}
RISO_OFF = {"Y": (0.0, 0.0), "P": (1.5, -1.0), "B": (-1.2, 1.3)}
PAPER_B = "#FBF6EC"
PAPER_C = "#FFFFFF"


def part_tr(tx_, ty_, s, flip=False):
    return f"translate({tx_:.2f} {ty_:.2f}) scale({-s if flip else s:.4f} {s:.4f})"


def riso_grain(L):
    seed = {"Y": 3, "P": 17, "B": 29}[L]
    k = "rg_" + L
    D.add(k, f'<filter id="{k}" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB">'
             f'<feTurbulence type="fractalNoise" baseFrequency="1.25" numOctaves="1" seed="{seed}" result="n1"/>'
             '<feColorMatrix in="n1" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  30 0 0 0 -20.4" result="sp"/>'
             f'<feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="{seed + 5}" result="n2"/>'
             '<feColorMatrix in="n2" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.8 0 0 0 -0.37" result="mo"/>'
             '<feMerge result="wh"><feMergeNode in="mo"/><feMergeNode in="sp"/></feMerge>'
             '<feComposite in="wh" in2="SourceGraphic" operator="atop"/></filter>')
    return f"url(#{k})"


def riso_dots(L, dens):
    """Halftone for light tints: dots of full ink."""
    k = f"ht_{L}_{int(dens * 100)}"
    r = 1.1 * math.sqrt(dens / .3)
    D.add(k, f'<pattern id="{k}" width="4.4" height="4.4" patternUnits="userSpaceOnUse" patternTransform="rotate(28)">'
             f'<circle cx="2.2" cy="2.2" r="{min(r, 2.3):.2f}" fill="{RISO[L]}"/></pattern>')
    return f"url(#{k})"


def b_layer(shapes, L):
    o = []
    for sh in shapes:
        inks = rc(sh.role, "b")
        dens = inks.get(L, 0)
        op = f' opacity="{sh.op}"' if sh.op != 1 and dens > 0 else ""
        if dens <= 0:
            col = "#FFFFFF"
        elif inks.get("ht"):
            col = None
        else:
            col = mix("#FFFFFF", RISO[L], dens)
        if not sh.closed:
            o.append(f'<path d="{sh.d()}" fill="none" stroke="{col or RISO[L]}" stroke-width="{sh.w:.2f}" stroke-linecap="round" stroke-linejoin="round"{op}/>')
        elif col is None:
            o.append(f'<path d="{sh.d()}" fill="#FFFFFF"/><path d="{sh.d()}" fill="{riso_dots(L, dens)}"/>')
        else:
            o.append(f'<path d="{sh.d()}" fill="{col}"{op}/>')
    return "".join(o)


def riso(parts, x, y, w, h, r=18):
    """parts: [(shapes, tx, ty, s, flip)]. Three ink layers, multiplied, a little out of register."""
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER_B}"/>']
    for L in "YPB":
        dx, dy = RISO_OFF[L]
        inner = "".join(f'<g transform="{part_tr(a, b, s, f)}">{b_layer(shs, L)}</g>' for shs, a, b, s, f in parts)
        o.append(f'<g style="mix-blend-mode:multiply" filter="{riso_grain(L)}"><g transform="translate({dx} {dy})">{inner}</g></g>')
    cp = clip(f"M{x + r},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h - r} A{r},{r} 0 0 1 {x + w - r},{y + h} "
              f"H{x + r} A{r},{r} 0 0 1 {x},{y + h - r} V{y + r} A{r},{r} 0 0 1 {x + r},{y}Z")
    return f'<g clip-path="{cp}" style="isolation:isolate">{"".join(o)}</g>'


def resample(pts, step, closed=True):
    seq = pts + ([pts[0]] if closed else [])
    out = [seq[0]]
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        t = step - acc
        while t <= seg:
            out.append((x0 + (x1 - x0) * t / seg, y0 + (y1 - y0) * t / seg))
            t += step
        acc = (acc + seg) % step if seg else acc
    return out


def wobble(pts, amp, rnd, closed=True, step=3.0):
    p = resample(pts, step, closed)
    n = len(p)
    ph = [rnd.uniform(0, 6.3) for _ in range(3)]
    fr = [rnd.uniform(.08, .14), rnd.uniform(.25, .4), rnd.uniform(.6, .9)]
    out = []
    for i, (x, y) in enumerate(p):
        x0, y0 = p[max(i - 1, 0)]
        x1, y1 = p[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        off = amp * (math.sin(i * fr[0] + ph[0]) * .6 + math.sin(i * fr[1] + ph[1]) * .3 + math.sin(i * fr[2] + ph[2]) * .15)
        out.append((x - dy / ln_ * off, y + dx / ln_ * off))
    return out


def polyd(pts, closed=False):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + ("Z" if closed else "")


def crayon_dark(c):
    if c.upper() == "#FFFFFF":
        return "#5A5A66"
    h, L, S = _hls(c)
    return _hex(h, L * .62, min(1, S * 1.05))


def c_shapes(shapes, s, rnd):
    """Crayon: scribble fill clipped to a slightly bigger copy of the shape, then a wobbly double outline."""
    o = []
    lw = 2.7 / s
    for sh in shapes:
        col = rc(sh.role, "c")
        if not sh.closed:
            o.append(f'<path d="{polyd(wobble(sh.pts, .7 / s, rnd, False, 3 / s))}" fill="none" stroke="{col}" '
                     f'stroke-width="{max(sh.w, lw):.2f}" stroke-linecap="round" stroke-linejoin="round" opacity="{sh.op}"/>')
            continue
        x0, y0, x1, y1 = sh.bbox()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        size = min(x1 - x0, y1 - y0)
        if col.upper() != "#FFFFFF":
            big = tf(sh.pts, s=1 + 1.8 / s / max(size, 1), about=(cx, cy))
            ang = math.radians(rnd.choice([-1, 1]) * rnd.uniform(25, 60))
            ca, sa = math.cos(ang), math.sin(ang)
            corners = [((px - cx) * ca + (py - cy) * sa, -(px - cx) * sa + (py - cy) * ca) for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
            umin, umax = min(c[0] for c in corners) - 3, max(c[0] for c in corners) + 3
            vmin, vmax = min(c[1] for c in corners) - 2, max(c[1] for c in corners) + 2
            sp = 3.3 / s
            pts = []
            v, side = vmin, 0
            while v <= vmax + sp:
                u = (umin if side == 0 else umax) + rnd.uniform(-2, 2) / s
                pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
                v += sp * rnd.uniform(.8, 1.2)
                side ^= 1
            o.append(f'<g clip-path="{clip(polyd(big, True))}"><path d="{polyd(pts)}" fill="none" stroke="{col}" stroke-width="{3.1 / s:.2f}" '
                     f'stroke-linecap="round" stroke-linejoin="round" stroke-opacity=".88"/></g>')
        else:
            o.append(f'<path d="{sh.d()}" fill="#FFFFFF"/>')
        if size < 4 / s:
            continue
        oc = crayon_dark(col) if sh.role not in ("ink",) else col
        if sh.role in ("cheek", "tongue", "sky", "cloud"):
            oc = col
        for k in range(2 if size > 14 / s else 1):
            wp = wobble(sh.pts, (.9 + .4 * k) / s, rnd, True, 3 / s)
            o.append(f'<path d="{polyd(wp, True)}" fill="none" stroke="{oc}" stroke-width="{lw * (1 - .25 * k):.2f}" '
                     f'stroke-linecap="round" stroke-linejoin="round" opacity="{.95 - .3 * k}"/>')
    return "".join(o)


def crayon_filter():
    k = "crayon"
    D.add(k, f'<filter id="{k}" x="-3%" y="-3%" width="106%" height="106%" color-interpolation-filters="sRGB">'
             '<feTurbulence type="fractalNoise" baseFrequency="0.9 0.45" numOctaves="2" seed="4" result="n"/>'
             '<feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  10 0 0 0 -5.9" result="sp"/>'
             '<feComposite in="sp" in2="SourceGraphic" operator="atop" result="t"/>'
             '<feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="9" result="w"/>'
             '<feDisplacementMap in="t" in2="w" scale="2.2" xChannelSelector="R" yChannelSelector="G"/></filter>')
    return f"url(#{k})"


def crayon(parts, x, y, w, h, r=18, seed=1):
    rnd = random.Random(seed)
    inner = "".join(f'<g transform="{part_tr(a, b, s, f)}">{c_shapes(shs, s, rnd)}</g>' for shs, a, b, s, f in parts)
    cp = clip(f"M{x + r},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h - r} A{r},{r} 0 0 1 {x + w - r},{y + h} "
              f"H{x + r} A{r},{r} 0 0 1 {x},{y + h - r} V{y + r} A{r},{r} 0 0 1 {x + r},{y}Z")
    return (f'<g clip-path="{cp}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER_C}"/>'
            f'<g filter="{crayon_filter()}">{inner}</g></g>')


def a_parts(parts):
    return "".join(f'<g transform="{part_tr(a, b, s, f)}">{draw_a(shs)}</g>' for shs, a, b, s, f in parts)


# ================================================================ STYLE A: THE ISOMETRIC TOY WORLD
C30, S30 = .8660254, .5


def P(x, y, z=0.0):
    """World (x to the right-front, y to the left-front, z up) to the picture: 30 degrees from above."""
    return ((x - y) * C30, (x + y) * S30 - z)


def ptsd(ps, closed=True):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in ps) + ("Z" if closed else "")


def shades(col):
    """Flat shading: the top is the lightest, the left face the colour itself, the right face darker."""
    h, L, S = _hls(col)
    if S < .1:
        return mix(col, "#FFFFFF", .55), col, mix(col, "#AFC0E6", .5)
    return mix(col, "#FFFFFF", .3), col, _hex(h + .006, L * .82, min(1, S * 1.05))


class Scene:
    def __init__(self):
        self.items = []

    def add(self, depth, svg, layer=1):
        self.items.append((layer, depth, len(self.items), svg))

    def svg(self):
        return "".join(t[3] for t in sorted(self.items, key=lambda t: t[:3]))


def face(points, col, r=.8, extra=""):
    d = ptsd([P(*p) for p in points])
    if r:
        return f'<path d="{d}" fill="{col}" stroke="{col}" stroke-width="{2 * r:.2f}" stroke-linejoin="round"{extra}/>'
    return f'<path d="{d}" fill="{col}"{extra}/>'


def box_svg(x, y, z, w, d, h, col, r=.8, top=None, left=None, right=None):
    t, l, rr_ = shades(col)
    t, l, rr_ = top or t, left or l, right or rr_
    return (face([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], l, r)
            + face([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], rr_, r)
            + face([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], t, r))


def box(sc, x, y, z, w, d, h, col, r=.8, depth=None, layer=1, **kw):
    sc.add(x + w / 2 + y + d / 2 if depth is None else depth, box_svg(x, y, z, w, d, h, col, r, **kw), layer)


def cyl_svg(cx, cy, z, R, h, col, top=None):
    rx, ry = R * 1.2247, R * .7071
    sx, sy = P(cx, cy, z)
    t, l, rr_ = shades(col)
    t = top or t
    return (f'<path d="M{sx - rx:.1f},{sy - h:.1f} L{sx - rx:.1f},{sy:.1f} A{rx:.1f},{ry:.1f} 0 0 0 {sx + rx:.1f},{sy:.1f} L{sx + rx:.1f},{sy - h:.1f}Z" fill="{l}"/>'
            f'<path d="M{sx:.1f},{sy + ry:.1f} A{rx:.1f},{ry:.1f} 0 0 0 {sx + rx:.1f},{sy:.1f} L{sx + rx:.1f},{sy - h:.1f} L{sx:.1f},{sy - h:.1f}Z" fill="{rr_}"/>'
            f'<ellipse cx="{sx:.1f}" cy="{sy - h:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{t}"/>')


def cyl(sc, cx, cy, z, R, h, col, depth=None, layer=1, top=None):
    sc.add(cx + cy if depth is None else depth, cyl_svg(cx, cy, z, R, h, col, top), layer)


def disc_svg(cx, cy, z, R, col, op=1.0, extra=""):
    sx, sy = P(cx, cy, z)
    o = f' opacity="{op}"' if op != 1 else ""
    return f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{R * 1.2247:.1f}" ry="{R * .7071:.1f}" fill="{col}"{o}{extra}/>'


def shadow(sc, cx, cy, R, op=.16, z=0.0, depth=None):
    sc.add(-500 + (cx + cy) * .01 if depth is None else depth, disc_svg(cx, cy, z, R, "#3B5A7A", op), 0)


def ball_svg(cx, cy, z, R, col):
    sx, sy = P(cx, cy, z + R)
    return draw_a([Sh(ellp(sx, sy, R, n=40), col)])


def ball(sc, cx, cy, z, R, col, depth=None):
    sc.add(cx + cy if depth is None else depth, ball_svg(cx, cy, z, R, col))


def sprite(sc, shapes, x, y, z, s, flip=False, depth=None, layer=1, extra=""):
    sx, sy = P(x, y, z)
    sc.add(x + y if depth is None else depth, f'<g transform="{part_tr(sx, sy, s, flip)}"{extra}>{draw_a(shapes)}</g>', layer)


def tile(sc, x, y, w, d, top, rim, side, thick=26, rimh=7, r=2.2, shadow_=True):
    if shadow_:
        cx, cy = P(x + w / 2, y + d / 2, -thick)
        sc.add(-2000, f'<ellipse cx="{cx:.1f}" cy="{cy + (w + d) * .14:.1f}" rx="{(w + d) * .4:.1f}" ry="{(w + d) * .05:.1f}" '
                      f'fill="#5C74A8" opacity=".2" filter="{blur(9)}"/>', -1)
    t, l, rr_ = shades(side)
    s_ = box_svg(x, y, -thick, w, d, thick - rimh, side, r)
    s_ += box_svg(x, y, -rimh, w, d, rimh, rim, r, top=top)
    # pebbles in the soil
    rnd = random.Random(int(w * 7 + d))
    for _ in range(int((w + d) / 22)):
        if rnd.random() < .5:
            px, py = x + rnd.uniform(8, w - 8), y + d
        else:
            px, py = x + w, y + rnd.uniform(8, d - 8)
        pz = -rnd.uniform(rimh + 6, thick - 5)
        sx, sy = P(px, py, pz)
        s_ += f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{rnd.uniform(2.6, 4.2):.1f}" ry="{rnd.uniform(1.6, 2.4):.1f}" fill="{mix(side, "#FFFFFF", .32)}"/>'
    sc.add(-1000, s_, -1)


def decal(sc, pts_xy, z, col, depth=-400, extra=""):
    sc.add(depth, f'<path d="{ptsd([P(x, y, z) for x, y in pts_xy])}" fill="{col}"{extra}/>', 0)


def ramp(sc, x, y0, y1, z0, z1, w, th, col, depth=None, rail=None):
    """A slope going along +y (a slide chute): top, right side and front end."""
    t, l, rr_ = shades(col)
    s_ = face([(x + w, y0, z0), (x + w, y1, z1), (x + w, y1, z1 - th), (x + w, y0, z0 - th)], rr_, .6)
    s_ += face([(x, y1, z1), (x + w, y1, z1), (x + w, y1, z1 - th), (x, y1, z1 - th)], l, .6)
    s_ += face([(x, y0, z0), (x + w, y0, z0), (x + w, y1, z1), (x, y1, z1)], t, .6)
    if rail:
        for xx in (x, x + w - 2.4):
            s_ += face([(xx + 2.4, y0, z0 + 4), (xx + 2.4, y1, z1 + 4), (xx + 2.4, y1, z1), (xx + 2.4, y0, z0)], shades(rail)[2], .5)
            s_ += face([(xx, y1, z1 + 4), (xx + 2.4, y1, z1 + 4), (xx + 2.4, y1, z1), (xx, y1, z1)], rail, .5)
            s_ += face([(xx, y0, z0 + 4), (xx + 2.4, y0, z0 + 4), (xx + 2.4, y1, z1 + 4), (xx, y1, z1 + 4)], shades(rail)[0], .5)
    sc.add((x + w / 2) + (y0 + y1) / 2 if depth is None else depth, s_)


def pyramid_svg(x, y, z, w, d, h, col):
    t, l, rr_ = shades(col)
    apex = (x + w / 2, y + d / 2, z + h)
    return (face([(x, y + d, z), (x + w, y + d, z), apex], l, .8)
            + face([(x + w, y, z), (x + w, y + d, z), apex], rr_, .8))


def string_svg(p0, p1, col="#7C86A8", w=1.2, bow=6):
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2 + bow, (y0 + y1) / 2
    return f'<path d="M{x0:.1f},{y0:.1f} Q{mx:.1f},{my:.1f} {x1:.1f},{y1:.1f}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'


def flower_svg(x, y, col, s=1.0):
    sx, sy = P(x, y, 0)
    o = f'<path d="M{sx:.1f},{sy:.1f} L{sx:.1f},{sy - 7 * s:.1f}" stroke="#4FAE5C" stroke-width="{1.6 * s:.1f}" stroke-linecap="round"/>'
    for a in range(0, 360, 72):
        o += f'<circle cx="{sx + 3 * s * math.cos(math.radians(a)):.1f}" cy="{sy - 8 * s + 3 * s * math.sin(math.radians(a)):.1f}" r="{2.3 * s:.1f}" fill="{col}"/>'
    o += f'<circle cx="{sx:.1f}" cy="{sy - 8 * s:.1f}" r="{1.7 * s:.1f}" fill="#FFE27A"/>'
    return o


def flowers(sc, pts, cols):
    for i, (x, y) in enumerate(pts):
        sc.add(x + y, flower_svg(x, y, cols[i % len(cols)]))


def tuft(sc, x, y, col="#6CC66A"):
    sx, sy = P(x, y, 0)
    sc.add(-300 + (x + y) * .01, f'<path d="M{sx - 4:.1f},{sy - 5:.1f} L{sx - 1.5:.1f},{sy:.1f} L{sx:.1f},{sy - 7:.1f} L{sx + 1.5:.1f},{sy:.1f} L{sx + 4:.1f},{sy - 5:.1f}" '
                                  f'fill="none" stroke="{col}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>', 0)


def tree(sc, x, y, s=1.0, col="#5BC46A", trunk="#B98356", fruit=None):
    cyl(sc, x, y, 0, 6 * s, 26 * s, trunk, depth=x + y)
    shadow(sc, x + 6, y + 6, 22 * s)
    blobs = [(x - 12 * s, y + 6 * s, 30 * s, 17 * s), (x + 8 * s, y - 12 * s, 32 * s, 17 * s), (x, y, 40 * s, 25 * s),
             (x + 10 * s, y + 10 * s, 26 * s, 15 * s)]
    for bx, by, bz, br in sorted(blobs, key=lambda b: b[0] + b[1] + b[2] * .01):
        ball(sc, bx, by, bz - br, br, col, depth=x + y + .5 + (bx + by - (x + y)) * .01)
    if fruit:
        for fx, fy, fz in ((x + 6, y + 14, 44), (x + 16, y - 2, 40), (x - 6, y + 20, 30)):
            sx, sy = P(fx * 1.0, fy * 1.0, fz * s)
            sc.add(x + y + .9, f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{3 * s:.1f}" fill="{fruit}"/>')


def fence(sc, along, fixed, a0, a1, step=16, col="#FFFFFF", h=15):
    """A little picket fence along x (along='x', y=fixed) or along y (x=fixed)."""
    n = int((a1 - a0) / step)
    for i in range(n + 1):
        a = a0 + i * step
        x, y = (a, fixed) if along == "x" else (fixed, a)
        box(sc, x - 1.5, y - 1.5, 0, 3, 3, h, col, r=.6, depth=x + y - 2)
    for zz in (5, 10.5):
        if along == "x":
            box(sc, a0, fixed - .7, zz, a1 - a0, 1.4, 2.2, col, r=.4, depth=a0 + fixed - 3)
        else:
            box(sc, fixed - .7, a0, zz, 1.4, a1 - a0, 2.2, col, r=.4, depth=a0 + fixed - 3)


def bench(sc, x, y, col="#F2A35E"):
    for lx in (x + 3, x + 37):
        box(sc, lx, y + 3, 0, 3, 9, 9, "#7C86A8", r=.5, depth=x + y + 10)
    box(sc, x, y, 9, 42, 14, 3, col, r=.7, depth=x + y + 21)
    box(sc, x, y - 2, 12, 42, 3, 12, col, r=.7, depth=x + y + 18)


def lamp(sc, x, y, h=50):
    cyl(sc, x, y, 0, 2.2, h, "#7C86A8")
    cyl(sc, x, y, 0, 4.5, 3, "#7C86A8", depth=x + y - .1)
    sx, sy = P(x, y, h + 5)
    sc.add(x + y + .1, f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="13" fill="#FFF2B0" opacity=".45"/>'
                       + draw_a([Sh(ellp(sx, sy, 6.2), "#FFE58A")]))


def pond(sc, cx, cy, R, ducks=1, lily=True):
    cyl(sc, cx, cy, 0, R + 6, 4, "#E2E7F1", depth=-350, layer=0)
    wall = disc_svg(cx, cy, 4, R, "#56B3E2")
    sx, sy = P(cx, cy, 4)
    rx, ry = R * 1.2247, R * .7071
    cp = clip(f"M{sx - rx:.1f},{sy:.1f} A{rx:.1f},{ry:.1f} 0 1 0 {sx + rx:.1f},{sy:.1f} A{rx:.1f},{ry:.1f} 0 1 0 {sx - rx:.1f},{sy:.1f}Z")
    water = f'<g clip-path="{cp}">{disc_svg(cx, cy, 1.2, R, "#86D8F7")}</g>'
    rip = ""
    for dx, dy, l_ in ((-R * .4, -R * .2, 9), (R * .3, R * .25, 7), (R * .1, -R * .55, 6)):
        px, py = P(cx + dx, cy + dy, 1.2)
        rip += f'<path d="M{px - l_:.1f},{py:.1f} Q{px:.1f},{py - 2.5:.1f} {px + l_:.1f},{py:.1f}" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" opacity=".85"/>'
    sc.add(-340, wall + water + rip, 0)
    if lily:
        for dx, dy in ((-R * .5, R * .35), (R * .45, -R * .3)):
            px, py = P(cx + dx, cy + dy, 1.4)
            sc.add(-330, f'<path d="M{px:.1f},{py:.1f} L{px + 8:.1f},{py - 2:.1f} A8.5,4.6 0 1 1 {px + 7:.1f},{py + 2.6:.1f}Z" fill="#6CCB6E"/>'
                         f'<circle cx="{px - 2:.1f}" cy="{py - 1.5:.1f}" r="2.2" fill="#FFB3D0"/>', 0)


def cloud_svg(cx, cy, s=1.0, op=1.0):
    d = ("M-34,6 C-42,6 -44,-6 -34,-8 C-34,-20 -16,-24 -10,-14 C-6,-28 18,-28 20,-12 C30,-16 40,-6 34,6 Z")
    return (f'<g transform="translate({cx} {cy}) scale({s})" opacity="{op}"><path d="{d}" fill="#DCEBFA" transform="translate(0 3)"/>'
            f'<path d="{d}" fill="#FFFFFF"/></g>')


# ---------------------------------------------------------------- scene: the park corner
def park(balloon_role="red", hero=True, balloon_s=.72):
    sc = Scene()
    tile(sc, 0, 0, 220, 220, "#A3E487", "#7FD06E", "#EBB57E")
    fence(sc, "x", 5, 10, 214)
    fence(sc, "y", 5, 10, 214)
    # stepping stones
    for i, (x, y) in enumerate([(118, 214), (124, 196), (126, 178), (136, 162), (150, 150), (168, 140), (186, 130)]):
        cyl(sc, x, y, 0, 7.5, 1.8, "#F6E7C8", depth=-200 + i)
    pond(sc, 160, 62, 38)
    sprite(sc, duck(), 168, 60, 1.5, .3, depth=160)
    # reeds behind the pond
    for i, (x, y) in enumerate([(122, 30), (128, 24), (196, 34)]):
        sx, sy = P(x, y, 0)
        sc.add(x + y, f'<path d="M{sx:.1f},{sy:.1f} Q{sx - 2:.1f},{sy - 14:.1f} {sx + 1:.1f},{sy - 24:.1f}" stroke="#4FAE5C" stroke-width="2" fill="none" stroke-linecap="round"/>'
                      f'<rect x="{sx - 1:.1f}" y="{sy - 30:.1f}" width="4.4" height="10" rx="2.2" fill="#B98356"/>')
    # tree, with 小變 peeking from behind it
    if hero:
        back, front = chameleon("peek", (-.9, .15), tilt=-10)
        sprite(sc, back, 80, 12, 0, .4, depth=90)
        sprite(sc, front, 80, 12, 0, .4, depth=131)
    tree(sc, 62, 64, 1.35)
    ball(sc, 92, 28, 0, 15, "#6CCB6E", depth=118)
    # slide: a little tower with a roof, a ladder at the back and a chute down to the front
    sx0, sy0 = 24, 118
    for px, py in ((sx0, sy0), (sx0 + 22, sy0), (sx0, sy0 + 22), (sx0 + 22, sy0 + 22)):
        box(sc, px, py, 0, 3, 3, 66, "#5E9BFF", r=.5, depth=px + py)
    for k in range(5):
        box(sc, sx0 + 2, sy0 - 16 + k * 3.4, k * 9 + 4, 20, 2, 2, "#5E9BFF", r=.4, depth=sx0 + sy0 - 10 - k)
    box(sc, sx0, sy0, 42, 25, 25, 4, "#FF7A7A", r=.6, depth=sx0 + sy0 + 24)
    for zz in (50, 56):
        box(sc, sx0 + 24, sy0 + 1, zz, 1.4, 23, 1.6, "#5E9BFF", r=.3, depth=sx0 + sy0 + 26)
    sc.add(sx0 + sy0 + 50, pyramid_svg(sx0 - 3, sy0 - 3, 66, 31, 31, 18, "#FF7A7A"))
    ramp(sc, sx0 + 3, sy0 + 25, sy0 + 84, 45, 3, 19, 4, "#FFD54F", depth=sx0 + sy0 + 60, rail="#FFC23A")
    # bench and the balloon tied to it
    bench(sc, 128, 160)
    shadow(sc, 150, 168, 14)
    tie = P(169, 165, 15)
    bx, by = P(178, 178, 78)
    sc.add(410, string_svg(tie, (bx, by), bow=5) + f'<g transform="{part_tr(bx, by, balloon_s)}">{draw_a(balloon(balloon_role))}</g>')
    lamp(sc, 210, 142)
    # bushes and flowers
    for x, y, r in ((200, 196, 11), (186, 206, 8), (12, 200, 10), (96, 18, 9)):
        ball(sc, x, y, 0, r, "#6CCB6E")
    flowers(sc, [(70, 196), (78, 204), (88, 200), (204, 168), (210, 156), (100, 120), (108, 112), (40, 20), (20, 46)],
            ["#FF8FB8", "#FFD84A", "#FFFFFF", "#B48CFF"])
    for x, y in ((90, 150), (60, 112), (150, 112), (180, 196), (110, 70), (30, 170)):
        tuft(sc, x, y)
    return sc.svg()


# ---------------------------------------------------------------- more sprites (style A only)
def cat():
    o = [Sh(tube(crs([(12, -4), (28, -8), (34, -24), (27, -34)], 8, closed=False), 7.5, 5), "#FFA552", shade=.6)]
    o.append(Sh(crs([(-16, -2), (0, 0), (16, -2), (18, -22), (10, -38), (-10, -38), (-18, -22)]), "#FFA552"))
    o.append(Sh(ellp(0, -15, 8, 11), "#FFE3BF", shade=False))
    for sx_ in (-1, 1):
        o.append(Sh(crs([(-15 * sx_, -50), (-12 * sx_, -67), (-3 * sx_, -57)], 4), "#FFA552", shade=False))
        o.append(Sh(crs([(-12.5 * sx_, -53), (-11 * sx_, -62), (-6 * sx_, -57)], 4), "#FFB3C6", shade=False))
    o.append(Sh(ellp(0, -47, 15.5, 13), "#FFA552"))
    for x in (-5, 0, 5):
        o.append(Sh([(x, -59), (x, -54)], "#E8843A", closed=False, w=1.8))
    o.append(Sh(ellp(-6, -47, 2.3, 3.1), "ink", shade=False))
    o.append(Sh(ellp(6, -47, 2.3, 3.1), "ink", shade=False))
    o.append(Sh(crs([(-2, -42.5), (2, -42.5), (0, -40)], 3), "#FF8FA8", shade=False))
    o.append(Sh(ellp(-9, -42, 3, 1.8), "cheek", shade=False, op=.8))
    o.append(Sh(ellp(9, -42, 3, 1.8), "cheek", shade=False, op=.8))
    return o


def bubble_tea():
    o = [Sh([(-12, 0), (12, 0), (15.5, -34), (-15.5, -34)], "#EEF6FF", shade=.7)]
    o.append(Sh([(-11, -1.5), (11, -1.5), (13.6, -27), (-13.6, -27)], "#E2A86E", shade=.6))
    for i, (x, y) in enumerate([(-7, -5), (-1, -4.5), (5, -5), (-4, -9.5), (2.5, -9.5), (8, -9), (-9, -10)]):
        o.append(Sh(ellp(x, y, 2.5), "#4A3428", shade=False))
    o.append(Sh(ellp(0, -34, 16.5, 4.6), "#FFFFFF", shade=False))
    o.append(Sh(tube([(4, -34), (7, -42), (10, -50)], 4.5), "#FF6FA0", shade=False))
    return o


def lantern(role="#FF5A5F"):
    o = [Sh([(0, 0), (0, 5)], "#7C86A8", closed=False, w=1.2)]
    o.append(Sh(rrect(-5, 4, 10, 4, 1.4), "#FFC93C", shade=False))
    o.append(Sh(ellp(0, 17, 11.5, 10.5), role, shade=.8))
    o.append(Sh([(-4, 8), (-6, 17), (-4, 26)], tone(role, .8), closed=False, w=1.2, op=.7))
    o.append(Sh([(4, 8), (6, 17), (4, 26)], tone(role, .8), closed=False, w=1.2, op=.7))
    o.append(Sh(rrect(-5, 26, 10, 4, 1.4), "#FFC93C", shade=False))
    o.append(Sh([(0, 30), (0, 37)], "#FFC93C", closed=False, w=2))
    return o


def skewers():
    o = []
    for dx, rot in ((-7, -8), (0, 0), (7, 8)):
        st = tf([(0, 0), (0, -40)], rot=rot, dx=dx)
        o.append(Sh(st, "#C98E5A", closed=False, w=1.6))
        for k in range(4):
            x, y = tf([(0, -15 - k * 7.4)], rot=rot, dx=dx)[0]
            o.append(Sh(ellp(x, y, 4.4), "#FF4F5E", shade=False))
            o.append(Sh(ellp(x - 1.4, y - 1.6, 1.3), "#FFFFFF", shade=False, op=.8))
    o.append(Sh([(-9, 0), (9, 0), (10, -12), (-10, -12)], "#5E9BFF", shade=.6))
    return o


def fish(col="#FF8A3D"):
    return [Sh(crs([(6, 0), (9, -3.5), (9, 3.5)], 3), col, shade=False), Sh(ellp(0, 0, 6.5, 3.6), col, shade=False),
            Sh(ellp(-3, -.8, 1, 1), "ink", shade=False)]


def crab():
    o = []
    for sgn in (-1, 1):
        for k in range(3):
            o.append(Sh([(sgn * 8, -6 + k * 3), (sgn * 16, -4 + k * 4), (sgn * 18, 1 + k * 3)], "#E8454A", closed=False, w=2.4))
        o.append(Sh(tube([(sgn * 10, -12), (sgn * 16, -20), (sgn * 20, -24)], 3.4), "#FF5A5F", shade=False))
        o.append(Sh(ellp(sgn * 21, -27, 6, 5), "#FF5A5F", shade=.6))
        o.append(Sh([(sgn * 4, -16), (sgn * 5, -24)], "#E8454A", closed=False, w=2))
        o.append(Sh(ellp(sgn * 5, -25, 3.3), "#FFFFFF", shade=False))
        o.append(Sh(ellp(sgn * 5, -25, 1.8), "ink", shade=False))
    o.append(Sh(ellp(0, -10, 14, 9.5), "#FF5A5F"))
    o.append(Sh(crs([(-5, -8), (0, -5.5), (5, -8)], 4, closed=False), "ink", closed=False, w=1.5))
    return o


def rock(col="#B9C3D9", s=1.0):
    return [Sh(tf(crs([(-30, 0), (-34, -14), (-24, -30), (-4, -38), (18, -34), (32, -20), (30, 0)]), s=s), col, shade=1.1)]


def palm():
    o = []
    seg = [(0, 0), (4, -20), (10, -40), (18, -58), (28, -74)]
    tr = crs(seg, 10, closed=False)
    o.append(Sh(tube(tr, 13, 9), "#C98E5A", shade=.7))
    for i in range(1, len(tr) - 1, 5):
        x, y = tr[i]
        o.append(Sh([(x - 6, y + 1), (x + 6, y - 1)], "#A87148", closed=False, w=1.6))
    tip = (28, -76)
    for ang, ln_, dr in ((-170, 40, 18), (-140, 36, 14), (-95, 30, 8), (-40, 38, 14), (-10, 40, 18), (20, 32, 16)):
        a = math.radians(ang)
        ex, ey = tip[0] + ln_ * math.cos(a), tip[1] + ln_ * math.sin(a) + dr
        mx, my = tip[0] + ln_ * .5 * math.cos(a), tip[1] + ln_ * .5 * math.sin(a) - 8
        o.append(Sh(tube(crs([tip, (mx, my), (ex, ey)], 8, closed=False), 10, 2.5), "#4FBF63", shade=.7))
    for dx, dy in ((-4, 2), (4, 4), (0, -2)):
        o.append(Sh(ellp(tip[0] + dx, tip[1] + dy + 4, 5), "#946542", shade=False))
    return o


def umbrella(c1="#FF6B6B", c2="#FFFFFF"):
    o = [Sh([(0, 0), (0, -66)], "#9AA6C2", closed=False, w=2.6)]
    n = 6
    apex = (0, -84)
    for i in range(n):
        a0, a1 = -44 + 88 * i / n, -44 + 88 * (i + 1) / n
        pa, pb = (a0, -58 + abs(a0) * .05), (a1, -58 + abs(a1) * .05)
        mid = ((a0 + a1) / 2, -54 + abs(a0 + a1) * .03)
        base = c1 if i % 2 == 0 else c2
        k = i / (n - 1)
        col = mix(base, "#FFFFFF", .22 * (1 - k)) if k < .5 else tone(base, 1 - .14 * (k - .4), 1.02)
        if base == "#FFFFFF" and k >= .5:
            col = mix("#FFFFFF", "#C9D4EC", .5 * k)
        o.append(Sh(crs([apex, pb, mid, pa], 6), col, shade=False))
    o.append(Sh(ellp(0, -85, 2.8), "#9AA6C2", shade=False))
    return o


def beach_ball():
    o = [Sh(ellp(0, -14, 14), "#FFFFFF", shade=False)]
    for dx, col in ((-7, "#FF5A5F"), (1, "#FFD84A"), (9, "#4C8DFF")):
        o.append(Sh(crs([(0, -28), (dx + 3, -14), (0, 0), (dx - 1, -14)], 6), col, shade=False))
    o.append(Sh(ellp(-5, -21, 3.2, 2.2, rot=-30), "#FFFFFF", shade=False, op=.8))
    return o


def sailboat():
    return [Sh([(-26, -8), (26, -8), (18, 2), (-18, 2)], "#FF6B6B", shade=.6),
            Sh([(0, -8), (0, -58)], "#9AA6C2", closed=False, w=2),
            Sh(crs([(2, -56), (24, -14), (2, -12)], 4), "#FFFFFF", shade=.6),
            Sh(crs([(-2, -48), (-2, -12), (-20, -14)], 4), "#FFD84A", shade=.6),
            Sh([(0, -58), (9, -55), (0, -52)], "#4C8DFF", shade=False)]


def gull():
    return [Sh(crs([(-16, -6), (-8, -12), (0, -6), (8, -12), (16, -6), (8, -8), (0, -2), (-8, -8)], 4), "#FFFFFF", shade=False),
            Sh(ellp(0, -4, 3.4, 2.6), "#FFFFFF", shade=False), Sh([(2, -4), (6, -3), (2, -2)], "#FFC93C", shade=False)]


def spade():
    return [Sh([(0, 0), (0, -26)], "#FF8A3D", closed=False, w=3),
            Sh(crs([(-6, -24), (6, -24), (5, -34), (0, -38), (-5, -34)], 4), "#FFD84A", shade=.6)]


def giraffe():
    G, S_ = "#FFD36B", "#D9944A"
    o = []
    for x0, x1 in ((-22, -25), (-11, -12), (16, 16), (26, 29)):
        o.append(Sh(tube([(x0, -48), (x1, -2)], 7), G, shade=.5))
        o.append(Sh(ellp(x1, -2, 4, 2.4), "#8A5A3A", shade=False))
    o.append(Sh([(32, -58), (40, -36)], S_, closed=False, w=2))
    o.append(Sh(ellp(2, -55, 32, 17), G))
    o.append(Sh(tube(crs([(-18, -64), (-28, -90), (-36, -116)], 8, closed=False), 14, 10), G, shade=.6))
    for x, y in ((-10, -60), (8, -62), (20, -52), (-4, -48), (-24, -84), (-30, -100), (26, -64), (-20, -72)):
        o.append(Sh(crs([(x - 4, y - 2), (x, y - 4.5), (x + 4.5, y - 1), (x + 2, y + 3.5), (x - 3, y + 3)], 4), S_, shade=False))
    for dx in (-3, 5):
        o.append(Sh([(-36 + dx, -126), (-35 + dx, -138)], "#C98E5A", closed=False, w=2.4))
        o.append(Sh(ellp(-35 + dx, -139, 2.8), "#8A5A3A", shade=False))
    o.append(Sh(crs([(-26, -126), (-18, -132), (-22, -124)], 3), G, shade=False))
    o.append(Sh(ellp(-38, -121, 12.5, 9.5), G))
    o.append(Sh(ellp(-48, -116, 8.5, 6.5), "#FFE6A6", shade=False))
    o.append(Sh(ellp(-40, -124, 2, 2.4), "ink", shade=False))
    return o


def elephant():
    E = "#A9B8DA"
    o = []
    for x in (-18, -4, 18, 30):
        o.append(Sh(tube([(x, -30), (x, -4)], 13), E, shade=.5))
    o.append(Sh(ellp(8, -36, 36, 25), E))
    o.append(Sh([(42, -40), (48, -24)], E, closed=False, w=2.4))
    o.append(Sh(tube(crs([(-40, -40), (-50, -24), (-50, -10), (-44, -6)], 8, closed=False), 10, 6), E, shade=.5))
    o.append(Sh(ellp(-30, -44, 20, 19), E))
    o.append(Sh(crs([(-22, -60), (-6, -64), (2, -48), (-4, -30), (-18, -30)]), mix(E, "#FFFFFF", .15), shade=.7))
    o.append(Sh(crs([(-18, -56), (-8, -58), (-3, -46), (-7, -35), (-16, -36)]), "#FFC6D6", shade=False))
    o.append(Sh(ellp(-36, -48, 2.2, 2.8), "ink", shade=False))
    o.append(Sh(crs([(-42, -34), (-50, -30), (-44, -30)], 3), "#FFFFFF", shade=False))
    return o


def flame():
    return [Sh(crs([(0, 0), (3, -4), (0, -10), (-3, -4)], 4), "#FFB020", shade=False), Sh(ellp(0, -3.5, 1.4, 2.2), "#FFF2A0", shade=False)]


def apple(col="#FF5A5F"):
    return [Sh(ellp(0, -6, 6.5, 6), col), Sh([(0, -11), (1, -15)], "#946542", closed=False, w=1.4),
            Sh(crs([(1, -13), (6, -16), (3, -12)], 3), "#5BC46A", shade=False)]


# ---------------------------------------------------------------- iso helpers for the other scenes
def awning(sc, x, y, w, d, z0, z1, c1, c2, stripes=6, depth=None):
    """A striped shop awning sloping from the back (z0) to the front (z1), with a scalloped front edge."""
    s_ = ""
    sw = w / stripes
    for i in range(stripes):
        col = c1 if i % 2 == 0 else c2
        xa, xb = x + i * sw, x + (i + 1) * sw
        t, l, r_ = shades(col)
        s_ += face([(xa, y, z0), (xb, y, z0), (xb, y + d, z1), (xa, y + d, z1)], t, .5)
        pts = [(xa, y + d, z1), (xb, y + d, z1)]
        for k in range(7):
            a = math.pi * k / 6
            pts.append((xb - sw / 2 + sw / 2 * math.cos(a), y + d, z1 - 6 - 4.5 * math.sin(a)))
        s_ += face(pts, l, .5)
    s_ += face([(x + w, y, z0), (x + w, y + d, z1), (x + w, y + d, z1 - 6), (x + w, y, z0 - 2)], shades(c1)[2], .5)
    sc.add(x + w / 2 + y + d if depth is None else depth, s_)


def present(sc, x, y, w, d, h, col, rib="#FFFFFF", depth=None):
    s_ = box_svg(x, y, 0, w, d, h, col, .6)
    t, l, r_ = shades(rib)
    b = min(w, d) * .18
    s_ += face([(x + w / 2 - b / 2, y + d, 0), (x + w / 2 + b / 2, y + d, 0), (x + w / 2 + b / 2, y + d, h), (x + w / 2 - b / 2, y + d, h)], l, 0)
    s_ += face([(x + w, y + d / 2 - b / 2, 0), (x + w, y + d / 2 + b / 2, 0), (x + w, y + d / 2 + b / 2, h), (x + w, y + d / 2 - b / 2, h)], r_, 0)
    s_ += face([(x + w / 2 - b / 2, y, h), (x + w / 2 + b / 2, y, h), (x + w / 2 + b / 2, y + d, h), (x + w / 2 - b / 2, y + d, h)], t, 0)
    s_ += face([(x, y + d / 2 - b / 2, h), (x + w, y + d / 2 - b / 2, h), (x + w, y + d / 2 + b / 2, h), (x, y + d / 2 + b / 2, h)], t, 0)
    cx, cy = P(x + w / 2, y + d / 2, h)
    s_ += draw_a([Sh(ellp(cx - 4.5, cy - 2.5, 5, 3.2, rot=-25), rib, shade=False), Sh(ellp(cx + 4.5, cy - 2.5, 5, 3.2, rot=25), rib, shade=False),
                  Sh(ellp(cx, cy - 1.5, 2.2), tone(rib, .9), shade=False)])
    sc.add(x + w / 2 + y + d / 2 if depth is None else depth, s_)


def bunting(sc, p0, p1, cols, n=8, depth=-10):
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    a, b = P(x0, y0, z0), P(x1, y1, z1)
    s_ = string_svg(a, b, "#9AA6C2", 1.1, 0)
    for i in range(n):
        t = (i + .5) / n
        sag = 4 * t * (1 - t) * 6
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + sag
        s_ += f'<path d="M{x - 4.5:.1f},{y - 1:.1f} L{x + 4.5:.1f},{y + 1:.1f} L{x:.1f},{y + 10:.1f}Z" fill="{cols[i % len(cols)]}"/>'
    sc.add(depth, s_)


def glow(sx, sy, r, col="#FFE07A", op=.55):
    return f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="{rg([(0, col, op), (1, col, 0)])}"/>'


# ---------------------------------------------------------------- scene: the night market (5 differences)
NIGHT_DIFFS = [  # (world x, y, z) of each difference, and whether it is found in screen 4
    ((42, 28, 66), True),     # 1 the first awning: red stripes -> blue
    ((118, 20, 86), True),    # 2 the cat on the second roof is gone
    ((214, 22, 106), True),   # 3 the red balloon is gone
    ((178, 52, 40), False),   # 4 a lantern turns green
    ((48, 88, 36), False),    # 5 the bubble tea on the table is gone
]


def night_market(changed=False):
    sc = Scene()
    tile(sc, 0, 0, 236, 122, "#B9B4DD", "#A39DD0", "#7E78B6", thick=22, rimh=6)
    for i in range(1, 5):
        decal(sc, [(0, i * 25), (236, i * 25), (236, i * 25 + 1), (0, i * 25 + 1)], .1, "#A9A3D3", depth=-450 + i)
    for i in range(1, 9):
        decal(sc, [(i * 26, 52), (i * 26 + 1, 52), (i * 26 + 1, 122), (i * 26, 122)], .1, "#A9A3D3", depth=-440 + i)
    stalls = [(10, "#FF6B6B" if not changed else "#4C8DFF", "#FFFFFF"), (86, "#FFC93C", "#FFFFFF"), (162, "#55C98A", "#FFFFFF")]
    for k, (x, c1, c2) in enumerate(stalls):
        y, w = 6, 64
        for px, py in ((x + 1, y + 2), (x + w - 4, y + 2), (x + 1, y + 37), (x + w - 4, y + 37)):
            box(sc, px, py, 0, 3, 3, 64, "#8E7BC8", r=.4, depth=px + py)
        if k == 0:   # goldfish game: a long water basin
            box(sc, x + 3, y + 14, 0, w - 6, 24, 14, "#5E9BFF", r=.6, top="#9BE3FF", depth=x + y + 50)
            for fx, fy, fc in ((x + 14, y + 24, "#FF8A3D"), (x + 30, y + 30, "#FF5A5F"), (x + 44, y + 22, "#FF8A3D"), (x + 52, y + 32, "#FFB020")):
                sx_, sy_ = P(fx, fy, 14)
                sc.add(x + y + 51, f'<g transform="translate({sx_:.1f} {sy_:.1f}) scale(1.2)">{draw_a(fish(fc))}</g>')
        else:
            box(sc, x + 2, y + 16, 0, w - 4, 20, 22, "#F2B872", r=.6, left=lt(c1, .25), depth=x + y + 50)
        awning(sc, x - 2, y - 2, w + 4, 44, 72, 58, c1, c2, depth=x + y + 70)
        # two lanterns hanging from the front of each awning (difference 4: one turns green)
        s_ = ""
        for j, lx in enumerate((x + 10, x + w - 10)):
            col = "#5BD47A" if (changed and k == 2 and j == 0) else "#FF5A5F"
            hx, hy = P(lx, y + 42, 51)
            s_ += glow(hx, hy + 18, 24) + f'<g transform="translate({hx:.1f} {hy:.1f}) scale(.95)">{draw_a(lantern(col))}</g>'
        sc.add(x + y + 120, s_)
    # stall 2: skewers and a big bubble tea (difference 5: the tea is gone)
    sx_, sy_ = P(116, 32, 22)
    sc.add(200, f'<g transform="{part_tr(sx_, sy_, .9)}">{draw_a(skewers())}</g>')
    # stall 2 roof: the cat (difference 2: gone)
    if not changed:
        sx_, sy_ = P(118, 20, 68)
        sc.add(300, f'<g transform="{part_tr(sx_, sy_, .66)}">{draw_a(cat())}</g>')
    # stall 3: balloons (difference 3: the red one is gone)
    tie = P(196, 30, 22)
    bl = [("#4C8DFF", 182, 18, 104), ("#FFD84A", 200, 12, 112)] + ([] if changed else [("#FF5A5F", 214, 22, 100)])
    s_ = ""
    for col, bx, by, bz in bl:
        kx, ky = P(bx, by, bz)
        s_ += string_svg(tie, (kx, ky), bow=2) + f'<g transform="{part_tr(kx, ky, .58)}">{draw_a(balloon(col))}</g>'
    sx_, sy_ = P(196, 30, 22)
    s_ += f'<g transform="{part_tr(sx_, sy_ + 2, .5)}">{draw_a([Sh(ellp(-10, -4, 8, 6), "#FF9EC7"), Sh(ellp(8, -5, 7, 7), "#B48CFF")])}</g>'
    sc.add(260, s_)
    # string lights along the front edge of the tile
    a, b = P(4, 118, 30), P(232, 118, 30)
    cyl(sc, 4, 118, 0, 1.8, 30, "#8E7BC8", depth=122)
    cyl(sc, 232, 118, 0, 1.8, 30, "#8E7BC8", depth=350)
    s_ = f'<path d="M{a[0]:.1f},{a[1]:.1f} Q{(a[0] + b[0]) / 2:.1f},{(a[1] + b[1]) / 2 + 16:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="#6E64A8" stroke-width="1.2"/>'
    for i in range(1, 14):
        t = i / 14
        x = (1 - t) ** 2 * a[0] + 2 * t * (1 - t) * (a[0] + b[0]) / 2 + t * t * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * ((a[1] + b[1]) / 2 + 16) + t * t * b[1]
        c = ["#FFE27A", "#FF9EC7", "#9BE3FF"][i % 3]
        s_ += glow(x, y + 3, 7, c, .7) + f'<circle cx="{x:.1f}" cy="{y + 3:.1f}" r="2.4" fill="{c}"/>'
    sc.add(600, s_)
    # tables and stools in front
    for tx_, ty_ in ((48, 88), (150, 92)):
        shadow(sc, tx_ + 3, ty_ + 3, 14)
        cyl(sc, tx_, ty_, 0, 3, 16, "#8E7BC8", depth=tx_ + ty_)
        cyl(sc, tx_, ty_, 16, 13, 2.5, "#FFFFFF", depth=tx_ + ty_ + .1)
        for dx, dy in ((-20, 4), (6, 20), (18, -10)):
            cyl(sc, tx_ + dx, ty_ + dy, 0, 4.5, 9, "#FF9EC7", depth=tx_ + ty_ + dx + dy)
    cyl(sc, 150, 92, 18.5, 6, 4, "#FF9838", depth=242.5, top="#FFE0A0")
    if not changed:
        sx_, sy_ = P(48, 88, 18.5)
        sc.add(136.5, f'<g transform="{part_tr(sx_ + 1, sy_ + 3, .95)}">{draw_a(bubble_tea())}</g>')
    return sc.svg()


# ---------------------------------------------------------------- scene: the beach (小變 hides on a sand rock)
def beach(hidden=True):
    sc = Scene()
    tile(sc, 0, 0, 240, 240, "#F7DFA6", "#F0CF8A", "#E3B271")
    shore = [(0, 0), (240, 0), (240, 74)] + [(240 - i * 20, 74 + 7 * math.sin(i * 1.3)) for i in range(1, 12)] + [(0, 80)]
    wet = [(0, 0), (240, 0), (240, 84)] + [(240 - i * 20, 84 + 7 * math.sin(i * 1.3 + .6)) for i in range(1, 12)] + [(0, 90)]
    decal(sc, wet, .1, "#EBCB8E", depth=-480)
    decal(sc, shore, .3, "#7FD6F7", depth=-470)
    foam = [P(240 - i * 10, 74 + 7 * math.sin(i * .65), .4) for i in range(25)]
    sc.add(-460, f'<path d="{ptsd(foam, False)}" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>', 0)
    for wx, wy in ((60, 20), (150, 30), (110, 50), (200, 18), (30, 50)):
        px, py = P(wx, wy, .4)
        sc.add(-455, f'<path d="M{px - 8:.1f},{py:.1f} Q{px - 4:.1f},{py - 3:.1f} {px:.1f},{py:.1f} Q{px + 4:.1f},{py + 3:.1f} {px + 8:.1f},{py:.1f}" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" opacity=".9"/>', 0)
    # the sea side of the tile
    sc.add(-950, face([(240, 0, -6), (240, 74, -6), (240, 74, .3), (240, 0, .3)], "#5FBDEB", 0), -1)
    # in the water
    sprite(sc, sailboat(), 150, 12, 0, .62, depth=20)
    sx_, sy_ = P(70, 36, .5)
    sc.add(-440, f'<ellipse cx="{sx_:.1f}" cy="{sy_:.1f}" rx="13" ry="7" fill="#FF8FB8"/><ellipse cx="{sx_:.1f}" cy="{sy_:.1f}" rx="6" ry="3.2" fill="#7FD6F7"/>'
                 f'<path d="M{sx_ - 12:.1f},{sy_ - 2:.1f} L{sx_ - 6:.1f},{sy_ - 1:.1f} M{sx_ + 6:.1f},{sy_ + 1:.1f} L{sx_ + 12:.1f},{sy_ + 2:.1f}" stroke="#FFFFFF" stroke-width="2.4"/>', 0)
    for gx, gy, gs in ((-40, -40, .7), (60, -30, .55)):
        sc.add(900, f'<g transform="{part_tr(gx, gy, gs)}">{draw_a(gull())}</g>')
    # grey rocks along the shore, and the sand rock where 小變 hides
    for rx_, ry_, rs in ((214, 92, .55), (228, 108, .4), (24, 92, .45), (226, 230, .4)):
        sprite(sc, rock("#B9C3D9", rs), rx_, ry_, 0, 1, depth=rx_ + ry_)
    for rx_, ry_, rs in ((60, 104, .5), (110, 214, .45)):
        sprite(sc, rock("#E6C283", rs), rx_, ry_, 0, 1, depth=rx_ + ry_)
    shadow(sc, 66, 190, 16, .12)
    sprite(sc, umbrella("#4C8DFF"), 60, 184, 0, .8, depth=244)
    shadow(sc, 198, 152, 16, .12)
    if hidden:
        sprite(sc, hide_rock(), 196, 148, 0, .85, depth=344)
    else:
        sprite(sc, rock("#E6C283", .85), 196, 148, 0, 1, depth=344)
    # palm tree, umbrella, towel, ball
    shadow(sc, 30, 124, 16)
    sprite(sc, palm(), 20, 116, 0, 1.05, depth=136)
    decal(sc, [(52, 140), (96, 140), (96, 164), (52, 164)], .2, "#4C8DFF", depth=-300)
    for i in range(3):
        decal(sc, [(58 + i * 13, 140), (64 + i * 13, 140), (64 + i * 13, 164), (58 + i * 13, 164)], .25, "#FFFFFF", depth=-299)
    shadow(sc, 86, 120, 18, .12)
    sprite(sc, umbrella(), 78, 116, 0, .95, depth=194)
    sprite(sc, beach_ball(), 118, 184, 0, 1.0, depth=302)
    # sandcastle with a flag
    box(sc, 122, 96, 0, 34, 30, 10, "#F0CF8A", r=1)
    for cx_, cy_ in ((126, 100), (152, 100), (126, 122), (152, 122)):
        cyl(sc, cx_, cy_, 10, 5.5, 13, "#F0CF8A", depth=cx_ + cy_ + 10)
    cyl(sc, 139, 111, 10, 8, 22, "#F0CF8A", depth=252)
    sx_, sy_ = P(139, 111, 32)
    sc.add(253, f'<path d="M{sx_:.1f},{sy_:.1f} L{sx_:.1f},{sy_ - 18:.1f}" stroke="#9AA6C2" stroke-width="1.6"/><path d="M{sx_:.1f},{sy_ - 18:.1f} L{sx_ + 11:.1f},{sy_ - 14:.1f} L{sx_:.1f},{sy_ - 10:.1f}Z" fill="#FF6B9A"/>')
    cyl(sc, 150, 198, 0, 7, 11, "#4C8DFF", depth=348)
    sprite(sc, spade(), 164, 196, 0, .9, depth=360)
    sprite(sc, crab(), 72, 206, 0, .8, depth=278)
    for sx0, sy0, col in ((36, 186, "#FF9838"), (226, 200, "#FF6FA0"), (120, 226, "#FF9838")):
        px, py = P(sx0, sy0, .3)
        sc.add(-250, f'<path d="{ptsd(star_round(10, 4.6, px, py), True)}" fill="{col}" transform="translate({px:.1f} {py:.1f}) scale(1 .62) translate({-px:.1f} {-py:.1f})"/>', 0)
    for shx, shy in ((176, 226), (40, 222), (100, 110), (170, 140)):
        px, py = P(shx, shy, .3)
        sc.add(-240, f'<path d="M{px - 5:.1f},{py + 2:.1f} L{px:.1f},{py - 5:.1f} L{px + 5:.1f},{py + 2:.1f}Z" fill="#FFD1E0" stroke="#FFD1E0" stroke-width="2" stroke-linejoin="round"/>', 0)
    return sc.svg()


# ---------------------------------------------------------------- scene: four ducks on a pool (2-3 years)
def duck_pool(hat_at=2):
    sc = Scene()
    tile(sc, 0, 0, 220, 220, "#A3E487", "#7FD06E", "#EBB57E")
    inner = rrect(16, 16, 188, 188, 24)
    sc.add(-470, f'<path d="{ptsd([P(x, y, 0) for x, y in rrect(10, 10, 200, 200, 28)])}" fill="#E2E7F1"/>', 0)
    wall = ptsd([P(x, y, 0) for x, y in inner])
    cp = clip(wall)
    sc.add(-460, f'<path d="{wall}" fill="#4FAEE0"/><g clip-path="{cp}"><path d="{ptsd([P(x, y, -5) for x, y in inner])}" fill="#86D8F7"/></g>', 0)
    for wx, wy in ((50, 50), (160, 46), (56, 160), (176, 168), (110, 28), (28, 110)):
        px, py = P(wx, wy, -5)
        sc.add(-450, f'<path d="M{px - 9:.1f},{py:.1f} Q{px:.1f},{py - 3:.1f} {px + 9:.1f},{py:.1f}" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" opacity=".85"/>', 0)
    for dx, dy in ((34, 180), (184, 32)):
        px, py = P(dx, dy, -4.5)
        sc.add(-440, f'<path d="M{px:.1f},{py:.1f} L{px + 11:.1f},{py - 3:.1f} A12,6.5 0 1 1 {px + 10:.1f},{py + 3.6:.1f}Z" fill="#6CCB6E"/>', 0)
    for x, y in ((4, 184), (8, 204), (204, 6), (184, 4)):
        ball(sc, x, y, 0, 8, "#6CCB6E")
    for i, (x, y) in enumerate([(5, 150), (6, 130), (150, 5), (130, 6), (212, 212)]):
        sc.add(x + y, flower_svg(x, y, ["#FF8FB8", "#FFD84A", "#FFFFFF"][i % 3]))
    pos = []
    for k, sxw in enumerate((-123, -41, 41, 123)):
        dd = sxw / C30
        x, y = (220 + dd) / 2, (220 - dd) / 2
        sx_, sy_ = P(x, y, -5)
        pos.append((sx_, sy_))
        sc.add(500 + k, f'<ellipse cx="{sx_ - 2:.1f}" cy="{sy_ + 1:.1f}" rx="34" ry="6.5" fill="#FFFFFF" opacity=".45"/>'
                        f'<g transform="{part_tr(sx_, sy_, .72)}">{draw_a(duck(k == hat_at))}</g>')
    return sc.svg(), pos


# ---------------------------------------------------------------- small scenes for the home cards
def zoo():
    sc = Scene()
    tile(sc, 0, 0, 200, 200, "#A3E487", "#7FD06E", "#EBB57E")
    decal(sc, [(80, 0), (120, 0), (120, 200), (80, 200)], .2, "#F6E7C8", depth=-400)
    fence(sc, "y", 76, 10, 190, step=20, col="#C98E5A", h=14)
    fence(sc, "x", 8, 10, 70, step=20, col="#C98E5A", h=14)
    tree(sc, 30, 40, 1.0)
    shadow(sc, 40, 130, 18)
    sprite(sc, giraffe(), 38, 124, 0, .78, depth=170)
    pond(sc, 160, 60, 28, lily=False)
    shadow(sc, 160, 150, 20)
    sprite(sc, elephant(), 156, 146, 0, .78, flip=True, depth=310)
    for x, y in ((190, 110), (110, 190)):
        ball(sc, x, y, 0, 9, "#6CCB6E")
    return sc.svg()


def party():
    sc = Scene()
    tile(sc, 0, 0, 200, 200, "#FFE3EE", "#FFC4DA", "#F59AB8")
    for i in range(4):
        for j in range(4):
            if (i + j) % 2 == 0:
                decal(sc, [(i * 50, j * 50), (i * 50 + 50, j * 50), (i * 50 + 50, j * 50 + 50), (i * 50, j * 50 + 50)], .1, "#FFD3E3", depth=-450 + i * 4 + j)
    bunting(sc, (4, 4, 70), (196, 4, 70), ["#FF5A5F", "#FFD84A", "#4C8DFF", "#55C98A"], n=9, depth=-5)
    bunting(sc, (4, 4, 70), (4, 196, 70), ["#B48CFF", "#FF9838", "#FF5A5F", "#4C8DFF"], n=9, depth=-6)
    box(sc, 60, 60, 0, 80, 60, 26, "#FFFFFF", r=1)
    cyl(sc, 100, 90, 26, 6, 2, "#E2E7F1", depth=200)
    cyl(sc, 100, 90, 27, 20, 14, "#FF8FB8", depth=201, top="#FFF4F8")
    cyl(sc, 100, 90, 41, 12, 10, "#FFFFFF", depth=202, top="#FFD1E0")
    for k, (dx, dy) in enumerate(((-5, -3), (4, -4), (0, 5), (6, 4))):
        cx_, cy_ = 100 + dx, 90 + dy
        box(sc, cx_ - 1, cy_ - 1, 51, 2, 2, 8, ["#4C8DFF", "#FFD84A", "#55C98A", "#FF5A5F"][k], r=.2, depth=203 + k * .1)
        sx_, sy_ = P(cx_, cy_, 59)
        sc.add(204, f'<g transform="translate({sx_:.1f} {sy_:.1f}) scale(.8)">{draw_a(flame())}</g>')
    present(sc, 150, 140, 22, 22, 18, "#4C8DFF", "#FFD84A")
    present(sc, 30, 150, 18, 18, 14, "#55C98A", "#FF5A5F")
    present(sc, 160, 40, 16, 16, 14, "#FFD84A", "#B48CFF")
    tie = P(180, 30, 0)
    s_ = ""
    for col, bx, by, bz in (("#FF5A5F", 172, 26, 78), ("#B48CFF", 190, 40, 66)):
        kx, ky = P(bx, by, bz)
        s_ += string_svg(tie, (kx, ky), bow=3) + f'<g transform="{part_tr(kx, ky, .6)}">{draw_a(balloon(col))}</g>'
    sc.add(212, s_)
    for px_, py_ in ((4, 4), (196, 4), (4, 196)):
        cyl(sc, px_, py_, 0, 1.6, 72, "#9AA6C2", depth=px_ + py_ - 1)
    return sc.svg()


def kitchen():
    sc = Scene()
    tile(sc, 0, 0, 200, 200, "#FFF6E6", "#F3E3C8", "#D9B98E")
    for i in range(5):
        for j in range(5):
            if (i + j) % 2 == 0:
                decal(sc, [(i * 40, j * 40), (i * 40 + 40, j * 40), (i * 40 + 40, j * 40 + 40), (i * 40, j * 40 + 40)], .1, "#BFE6F7", depth=-450 + i * 5 + j)
    box(sc, 4, 4, 0, 130, 34, 34, "#FFFFFF", r=1, depth=40)
    for i in range(4):
        decal(sc, [(8 + i * 32, 38), (34 + i * 32, 38)], 0, "#000", depth=-999)
    for i in range(3):
        x0 = 10 + i * 42
        sc.add(41, face([(x0, 38, 4), (x0 + 36, 38, 4), (x0 + 36, 38, 28), (x0, 38, 28)], "#9ED3FF", .8)
               + f'<circle cx="{P(x0 + 30, 38, 18)[0]:.1f}" cy="{P(x0 + 30, 38, 18)[1]:.1f}" r="1.8" fill="#5E7FB8"/>')
    decal(sc, [(70, 8), (120, 8), (120, 34), (70, 34)], 34.2, "#4A4F6E", depth=-998)
    sc.items[-1] = (1, 41.5, sc.items[-1][2], sc.items[-1][3])
    for bx_ in (82, 106):
        sx_, sy_ = P(bx_, 21, 34.3)
        sc.add(41.6, f'<ellipse cx="{sx_:.1f}" cy="{sy_:.1f}" rx="10" ry="5.6" fill="none" stroke="#FF8A3D" stroke-width="1.6"/>')
    cyl(sc, 82, 21, 34.5, 10, 14, "#FF5A5F", depth=42)
    cyl(sc, 82, 21, 48.5, 10.5, 2, "#FF7A7A", depth=42.1)
    sx_, sy_ = P(82, 21, 52)
    sc.add(42.2, f'<circle cx="{sx_:.1f}" cy="{sy_ - 1:.1f}" r="2.6" fill="#FFFFFF"/>')
    box(sc, 150, 4, 0, 42, 36, 84, "#BDE7FF", r=1.2, depth=60)
    for zz in (30, 58):
        a, b = P(186, 40, zz), P(186, 40, zz + 16)
        sc.add(61, f'<path d="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}" stroke="#7FA8D8" stroke-width="2.4" stroke-linecap="round"/>')
    sc.add(61, face([(150, 40, 46), (192, 40, 46), (192, 40, 47), (150, 40, 47)], "#9CCDEB", 0))
    for lx, ly in ((76, 112), (124, 112), (76, 142), (124, 142)):
        box(sc, lx, ly, 0, 3, 3, 24, "#C98E5A", r=.4, depth=lx + ly)
    box(sc, 72, 108, 24, 58, 40, 4, "#E9A86C", r=.6, depth=260)
    cyl(sc, 101, 128, 28, 12, 6, "#FFFFFF", depth=262)
    for dx, dy, col in ((-4, -2, "#FF5A5F"), (4, 2, "#FF9838"), (0, 4, "#FF5A5F"), (5, -4, "#55C98A")):
        sx_, sy_ = P(101 + dx, 128 + dy, 33)
        sc.add(263 + dx * .01, f'<g transform="translate({sx_:.1f} {sy_:.1f}) scale(.9)">{draw_a(apple(col))}</g>')
    for cx_, cy_ in ((60, 128), (150, 128)):
        box(sc, cx_ - 8, cy_ - 8, 0, 16, 16, 14, "#FF9EC7", r=.8)
    return sc.svg()


def scene_bbox(name):
    """Local extents of each scene (for fitting into frames)."""
    return {"park": (-200, -50, 200, 252), "night": (-112, -74, 212, 206), "beach": (-212, -95, 212, 266),
            "pool": (-192, -14, 192, 262), "zoo": (-176, -112, 176, 226), "party": (-176, -84, 176, 226),
            "kitchen": (-176, -90, 176, 226)}[name]


def fit(svg, name, x, y, w, h, pad=0.0, dy=0.0, zoom=1.0):
    x0, y0, x1, y1 = scene_bbox(name)
    s = min((w - 2 * pad) / (x1 - x0), (h - 2 * pad) / (y1 - y0)) * zoom
    cx, cy = x + w / 2 - (x0 + x1) / 2 * s, y + h / 2 - (y0 + y1) / 2 * s + dy
    return f'<g transform="translate({cx:.2f} {cy:.2f}) scale({s:.4f})">{svg}</g>', (cx, cy, s)


# ================================================================ STYLES B AND C: THE SAME PARK, FLAT (330 x 240)
def bumpy(cx, cy, R, k=7, a=.12, ry=None, n=90):
    ry = ry or R
    return [(cx + R * (1 + a * abs(math.cos(k * t / 2))) * math.cos(t), cy + ry * (1 + a * abs(math.cos(k * t / 2))) * math.sin(t))
            for t in (2 * math.pi * i / n for i in range(n))]


def park_flat(style="b"):
    o = []
    if style == "b":
        o.append(Sh([(-10, -10), (340, -10), (340, 250), (-10, 250)], "skyb", shade=False))
    else:
        o.append(Sh(crs([(-10, -10), (340, -10), (340, 30), (250, 36), (160, 30), (80, 37), (-10, 31)], 8), "sky", shade=False))
        for a in range(0, 360, 40):
            r0, r1 = 27, 38
            o.append(Sh([(292 + r0 * math.cos(math.radians(a)), 44 + r0 * math.sin(math.radians(a))),
                         (292 + r1 * math.cos(math.radians(a)), 44 + r1 * math.sin(math.radians(a)))], "sun", closed=False, w=3.2))
    o.append(Sh(ellp(292, 44, 21), "sun", shade=False))
    for cx, cy, sc_ in ((52, 46, 1.0), (244, 108, .7)):
        o.append(Sh(tf(crs([(-30, 6), (-34, -4), (-22, -12), (-12, -20), (6, -20), (16, -10), (30, -8), (32, 6)]), s=sc_, dx=cx, dy=cy), "cloud", shade=False))
    o.append(Sh(crs([(-10, 176), (60, 166), (140, 172), (220, 164), (340, 172), (340, 250), (-10, 250)], 8), "grass", shade=False))
    o.append(Sh(ellp(290, 214, 40, 13), "water", shade=False))
    o.append(Sh([(266, 216), (278, 214)], "white", closed=False, w=2.2))
    o.append(Sh([(304, 220), (318, 218)], "white", closed=False, w=2.2))
    # slide
    o.append(Sh([(70, 108), (70, 210)], "blue", closed=False, w=4.5))
    for x in (28, 48):
        o.append(Sh([(x, 210), (x, 96)], "blue", closed=False, w=4.5))
    for y in range(196, 108, -16):
        o.append(Sh([(28, y), (48, y)], "blue", closed=False, w=3.6))
    o.append(Sh(crs([(28, 96), (38, 84), (48, 96)], 6, closed=False), "blue", closed=False, w=4))
    o.append(Sh(rrect(22, 100, 56, 9, 3), "yellow", shade=False))
    ch = crs([(74, 104), (98, 126), (118, 168), (136, 196), (158, 204)], 8, closed=False)
    o.append(Sh(tube(ch, 13), "pink" if style == "b" else "red", shade=False))
    o.append(Sh(tf(ch, dy=-9), "blue", closed=False, w=3))
    # the balloon tied to the slide
    o.append(Sh(crs([(40, 84), (52, 76), (68, 72), (100, 74)], 8, closed=False), "ink" if style == "c" else "blue", closed=False, w=1.4))
    o += moved(balloon("red"), s=.95, dx=100, dy=76)
    # 小變 behind the tree
    back, front = chameleon("peek", (-.9, .1), tilt=-10)
    o += moved(back, s=.44, dx=224, dy=200)
    tr = crs([(186, 214), (184, 170), (186, 130), (188, 108)], 6, closed=False)
    o.append(Sh(tube(tr, 32, 24), "brown", shade=False))
    o.append(Sh(tube(crs([(186, 136), (204, 122), (214, 112)], 6, closed=False), 9, 6), "brown", shade=False))
    o.append(Sh(bumpy(184, 78, 50, 7, .13, 46), "leaf", shade=False))
    for ax, ay in ((160, 62), (204, 52), (176, 98), (214, 90)):
        o.append(Sh(ellp(ax, ay, 6), "red", shade=False))
    o.append(Sh(bumpy(238, 198, 32, 5, .14, 20), "leaf", shade=False))
    for fx, fy in ((222, 190), (240, 184), (254, 196), (232, 204)):
        o.append(Sh(ellp(fx, fy, 3.6), "pink", shade=False))
    o += moved(front, s=.44, dx=224, dy=200)
    o += moved(duck(), s=.5, dx=296, dy=214)
    for fx, fy, col in ((16, 222, "pink"), (112, 226, "yellow"), (150, 232, "pink"), (60, 218, "purple")):
        o.append(Sh([(fx, fy + 10), (fx, fy)], "leaf", closed=False, w=2))
        for a in range(0, 360, 72):
            o.append(Sh(ellp(fx + 4 * math.cos(math.radians(a)), fy + 4 * math.sin(math.radians(a)), 3.4), col, shade=False))
        o.append(Sh(ellp(fx, fy, 2.4), "yellow" if col != "yellow" else "orange", shade=False))
    return o


# ================================================================ PAGE MACHINERY
def tx(x, y, s, size=16, color=INK, anchor="middle", extra="", weight=""):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}"{w} '
            f'font-family="Huninn, sans-serif" {extra}>{s}</text>')


def txo(x, y, s, size, color, ol="#FFFFFF", ow=6, anchor="middle"):
    """Words with a soft outline around them (titles on pictures)."""
    return tx(x, y, s, size, color, anchor, f'stroke="{ol}" stroke-width="{ow}" stroke-linejoin="round" paint-order="stroke"')


def page(body, bg, w=W, h=H):
    css = (f"@font-face {{ font-family: Huninn; src: url('file://{FONT}'); }}"
           f"* {{ margin: 0; padding: 0; }} body {{ width: {w}px; height: {h}px; overflow: hidden; background: {bg}; }}")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{D.svg()}{body}</svg>'
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{svg}</body></html>'


def render(html, out, w, h, scale):
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp) / "page.html"
        p.write_text(html)
        subprocess.run(["node", str(HERE / "render.js"), str(p), str(out), str(w), str(h), str(scale)], check=True)
    if pathlib.Path(out).stat().st_size > 1_000_000:
        # grain makes big PNGs: keep them small with a 256-colour palette (the grain hides the dithering)
        from PIL import Image
        im = Image.open(out).convert("RGB")
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(out, optimize=True)


# ================================================================ UI PIECES (style A: soft toy tiles, no outlines)
LIP = "#D5E0F2"


def bg(top, bottom, w=W, h=H):
    return f'<rect width="{w}" height="{h}" fill="{lg([(0, top), (1, bottom)])}"/>'


def lipbox(x, y, w, h, r, fill="#FFFFFF", lip=LIP, lipd=5, sh=True, extra=""):
    o = ""
    if sh:
        o += f'<rect x="{x}" y="{y + 4}" width="{w}" height="{h}" rx="{r}" fill="#5B6FA8" opacity=".13" filter="{blur(6)}"/>'
    o += f'<rect x="{x}" y="{y + lipd}" width="{w}" height="{h}" rx="{r}" fill="{lip}"/>'
    o += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{extra}/>'
    return o


def roundbtn(cx, cy, r, fill, lip, icon="", lipd=4):
    return (f'<circle cx="{cx}" cy="{cy + 3}" r="{r}" fill="#5B6FA8" opacity=".14" filter="{blur(4)}"/>'
            f'<circle cx="{cx}" cy="{cy + lipd}" r="{r}" fill="{lip}"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            f'<path d="M{cx - r * .62:.1f},{cy - r * .5:.1f} A{r * .8:.1f},{r * .8:.1f} 0 0 1 {cx + r * .1:.1f},{cy - r * .8:.1f}" fill="none" stroke="#FFFFFF" '
            f'stroke-width="{r * .14:.1f}" stroke-linecap="round" opacity=".45"/>' + icon)


def pill(cx, cy, w, h, text, fill, lip, size=19, color="#FFFFFF"):
    return (lipbox(cx - w / 2, cy - h / 2, w, h, h / 2, fill, lip, 4)
            + tx(cx, cy + size * .36, text, size, color))


def bubble_d(x, y, w, h, r, side=None, at=0, tl=15, tw=12):
    x1, y1 = x + w, y + h
    d = f"M{x + r},{y}"
    if side == "up":
        d += f" L{at - tw},{y} L{at - 3},{y - tl} L{at + tw},{y}"
    d += f" L{x1 - r},{y} A{r},{r} 0 0 1 {x1},{y + r}"
    if side == "right":
        d += f" L{x1},{at - tw} L{x1 + tl},{at + 3} L{x1},{at + tw}"
    d += f" L{x1},{y1 - r} A{r},{r} 0 0 1 {x1 - r},{y1}"
    if side == "down":
        d += f" L{at + tw},{y1} L{at - 4},{y1 + tl} L{at - tw},{y1}"
    d += f" L{x + r},{y1} A{r},{r} 0 0 1 {x},{y1 - r}"
    if side == "left":
        d += f" L{x},{at + tw} L{x - tl},{at + 3} L{x},{at - tw}"
    d += f" L{x},{y + r} A{r},{r} 0 0 1 {x + r},{y}Z"
    return d


def bubble(x, y, w, h, r=22, side=None, at=0, fill="#FFFFFF"):
    d = bubble_d(x, y, w, h, r, side, at)
    return (f'<path d="{d}" fill="#5B6FA8" opacity=".13" filter="{blur(6)}" transform="translate(0 4)"/>'
            f'<path d="{d}" fill="{LIP}" transform="translate(0 5)"/><path d="{d}" fill="{fill}"/>')


def ic(inner, cx, cy, s=1.0):
    return f'<g transform="translate({cx} {cy}) scale({s})">{inner}</g>'


def i_speaker(c="#FFFFFF"):
    return (f'<g transform="translate(-2 0)"><path d="M-12,-5 L-6,-5 L2,-12 L2,12 L-6,5 L-12,5Z" fill="{c}" stroke="{c}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M7.5,-6 A9,9 0 0 1 7.5,6 M11.5,-11 A15,15 0 0 1 11.5,11" stroke="{c}" stroke-width="2.8" fill="none" stroke-linecap="round"/></g>')


def i_home(c):
    return (f'<path d="M-13,-1 L0,-13 L13,-1" stroke="{c}" stroke-width="3.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M-9,-2 L-9,11 L-3,11 L-3,4 L3,4 L3,11 L9,11 L9,-2" fill="{c}" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>')


def i_lock(c):
    return (f'<path d="M-5.5,-2 V-6 A5.5,5.5 0 0 1 5.5,-6 V-2" stroke="{c}" stroke-width="2.6" fill="none"/>'
            f'<rect x="-8.5" y="-2.5" width="17" height="13" rx="3" fill="{c}"/>')


def i_check(c="#FFFFFF", w=4.5):
    return f'<path d="M-9,0 L-3,7 L10,-7" stroke="{c}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def i_arrow(c="#FFFFFF", w=4):
    return f'<path d="M-10,0 L9,0 M1,-9 L10,0 L1,9" stroke="{c}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def i_x(c, w=3):
    return f'<path d="M-8,-8 L8,8 M8,-8 L-8,8" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'


def i_magnifier(lens="#BDEBFF", rim="#FFB020", handle="#7C86A8"):
    return (f'<path d="M7,7 L17,17" stroke="{handle}" stroke-width="7.5" stroke-linecap="round"/>'
            f'<circle cx="-2" cy="-2" r="13" fill="{rim}"/><circle cx="-2" cy="-2" r="9" fill="{lens}"/>'
            f'<path d="M-8,-5 A7,7 0 0 1 -4,-9" stroke="#FFFFFF" stroke-width="2.6" fill="none" stroke-linecap="round"/>')


def i_album(c="#FFFFFF", c2="#FF7E6B"):
    return (f'<rect x="-14" y="-12" width="28" height="24" rx="4" fill="{c}"/>'
            f'<rect x="-10" y="-8" width="9" height="7" rx="1.6" fill="{c2}"/><rect x="1" y="-8" width="9" height="7" rx="1.6" fill="{c2}" opacity=".6"/>'
            f'<rect x="-10" y="1" width="9" height="7" rx="1.6" fill="{c2}" opacity=".6"/><rect x="1" y="1" width="9" height="7" rx="1.6" fill="{c2}"/>')


def star_ui(cx, cy, R, on=True):
    d = ptsd(star_round(R, R * .5, cx, cy), True)
    if not on:
        return f'<path d="{d}" fill="#DDE3EE" transform="translate(0 {R * .12:.1f})"/><path d="{d}" fill="#EEF2F8"/>'
    return (f'<path d="{d}" fill="#E5A51A" transform="translate(0 {R * .14:.1f})"/><path d="{d}" fill="{GOLD}"/>'
            f'<path d="{d}" fill="#FFE38A" mask="{cel_mask(d, (R * .1, R * .3))}"/>')


def sparkle(cx, cy, r, c=GOLD, op=1.0):
    return (f'<path d="M{cx},{cy - r} Q{cx + r * .16},{cy - r * .16} {cx + r},{cy} Q{cx + r * .16},{cy + r * .16} {cx},{cy + r} '
            f'Q{cx - r * .16},{cy + r * .16} {cx - r},{cy} Q{cx - r * .16},{cy - r * .16} {cx},{cy - r}Z" fill="{c}" opacity="{op}"/>')


def dots(cx, y, n, k, on=GREEN, r=6, gap=20):
    x0 = cx - (n - 1) * gap / 2
    o = []
    for i in range(n):
        x = x0 + i * gap
        if i < k:
            o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{on}"/>')
        elif i == k:
            o.append(f'<circle cx="{x}" cy="{y}" r="{r + 2}" fill="#FFFFFF"/><circle cx="{x}" cy="{y}" r="{r - 1}" fill="{on}" opacity=".35"/>')
        else:
            o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" opacity=".9"/>')
    return "".join(o)


def ring(cx, cy, r, col=GREEN, w=4.5):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="#FFFFFF" stroke-width="{w + 4}" opacity=".95"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{col}" stroke-width="{w}"/>')


def hero(pose, cx, base, s, look=(0, 0), flip=False, tilt=0.0):
    back, front = chameleon(pose, look, tilt)
    return f'<g transform="{part_tr(cx, base, s, flip)}">{draw_a(back + front)}</g>'


def topbar(title, fill, lip, right=""):
    return (roundbtn(40, 48, 22, "#FFFFFF", LIP, ic(i_home(INK), 40, 48, .9))
            + pill(195, 48, 196, 44, title, fill, lip, 20) + right)


def frame(x, y, w, h, r, inner, fill="#FFFFFF", pad=6):
    cp = clip(f"M{x + pad + r},{y + pad} H{x + w - pad - r} A{r},{r} 0 0 1 {x + w - pad},{y + pad + r} V{y + h - pad - r} "
              f"A{r},{r} 0 0 1 {x + w - pad - r},{y + h - pad} H{x + pad + r} A{r},{r} 0 0 1 {x + pad},{y + h - pad - r} V{y + pad + r} "
              f"A{r},{r} 0 0 1 {x + pad + r},{y + pad}Z")
    return lipbox(x, y, w, h, r + pad, fill) + f'<g clip-path="{cp}">{inner}</g>'


def to_screen(t, pt):
    cx, cy, s = t
    return cx + pt[0] * s, cy + pt[1] * s


# ================================================================ PAGE 0: three styles
def style_sheet():
    ph = 1226
    o = [bg("#F2F6FC", "#EEF2FA", W, ph)]
    o.append(tx(195, 58, "選一個畫風", 30, INK))
    o.append(tx(195, 90, "同一個公園角落，三種畫法", 16, SOFT))
    bands = [("A 等角小模型風（建議）", "從斜上方看的小小玩具世界，每樣東西都清楚。", "a"),
             ("B 孔版印刷風", "三種亮亮的油墨疊印，重疊的地方會變色。", "b"),
             ("C 粗蠟筆童畫風", "像小朋友用粗蠟筆畫的，線條歪歪、塗色一條條。", "c")]
    y = 116
    for title, desc, st in bands:
        h = 346
        if st == "a":
            o.append(f'<rect x="12" y="{y - 4}" width="366" height="{h + 8}" rx="28" fill="{GREEN}"/>')
            o.append(lipbox(16, y, 358, h, 24, "#FFFFFF", "#E3F4E8", 0, sh=False))
            o.append(f'<rect x="270" y="{y - 14}" width="92" height="30" rx="15" fill="{GREEN}"/>' + tx(316, y + 7, "我建議這個", 14, "#FFFFFF"))
        else:
            o.append(lipbox(16, y, 358, h, 24, "#FFFFFF", LIP, 4))
        o.append(tx(34, y + 40, title, 22, INK, "start"))
        o.append(tx(34, y + 68, desc, 14.5, "#5D6890", "start"))
        px, py, pw, phh = 30, y + 88, 330, 240
        if st == "a":
            inner = (f'<rect x="{px}" y="{py}" width="{pw}" height="{phh}" fill="{lg([(0, "#CFEFFF"), (1, "#F2FAFF")])}"/>'
                     + cloud_svg(px + 44, py + 30, .7) + cloud_svg(px + 290, py + 52, .55)
                     + fit(park(), "park", px, py, pw, phh, 4)[0])
            cp = clip(f"M{px + 18},{py} H{px + pw - 18} A18,18 0 0 1 {px + pw},{py + 18} V{py + phh - 18} A18,18 0 0 1 {px + pw - 18},{py + phh} "
                      f"H{px + 18} A18,18 0 0 1 {px},{py + phh - 18} V{py + 18} A18,18 0 0 1 {px + 18},{py}Z")
            o.append(f'<g clip-path="{cp}">{inner}</g>')
        elif st == "b":
            o.append(riso([(park_flat("b"), px, py, 1, False)], px, py, pw, phh))
        else:
            o.append(crayon([(park_flat("c"), px, py, 1, False)], px, py, pw, phh, seed=5))
        y += h + 22
    return page("".join(o), "#F2F6FC", W, ph), ph


# ================================================================ SCREEN 1: home
CARD_BG = {"park": ("#CDEFFF", "#EAF8FF"), "night": ("#2E3A7E", "#5A56A8"), "beach": ("#BDEFFF", "#E8FBFF"),
           "zoo": ("#D6F5D0", "#F0FFF0"), "party": ("#FFE0EC", "#FFF4F8"), "kitchen": ("#FFEBD0", "#FFF8EC")}


def scene_card(x, y, w, h, name, key, svg, stars):
    o = [lipbox(x, y, w, h, 22, "#FFFFFF")]
    top, bot = CARD_BG[key]
    px, py, pw, phh = x + 8, y + 8, w - 16, h - 52
    inner = f'<rect x="{px}" y="{py}" width="{pw}" height="{phh}" fill="{lg([(0, top), (1, bot)])}"/>'
    if key == "night":
        rnd = random.Random(3)
        inner += "".join(f'<circle cx="{px + rnd.uniform(4, pw - 4):.1f}" cy="{py + rnd.uniform(4, phh * .5):.1f}" r="{rnd.uniform(.6, 1.4):.1f}" fill="#FFFFFF" opacity=".8"/>' for _ in range(14))
    inner += fit(svg, key, px, py, pw, phh, 2, dy=3, zoom=1.12)[0]
    cp = clip(f"M{px + 15},{py} H{px + pw - 15} A15,15 0 0 1 {px + pw},{py + 15} V{py + phh - 15} A15,15 0 0 1 {px + pw - 15},{py + phh} "
              f"H{px + 15} A15,15 0 0 1 {px},{py + phh - 15} V{py + 15} A15,15 0 0 1 {px + 15},{py}Z")
    o.append(f'<g clip-path="{cp}">{inner}</g>')
    o.append(tx(x + 14, y + h - 16, name, 17, INK, "start"))
    for i in range(3):
        o.append(star_ui(x + w - 50 + i * 18, y + h - 22, 8, i < stars))
    return "".join(o)


def screen_home():
    o = [bg("#CFEFFF", "#FFF3E2")]
    o.append(cloud_svg(56, 168, .8, .9) + cloud_svg(352, 250, .6, .8))
    o.append(lipbox(296, 22, 78, 32, 16, "#E6EAF2", "#D2D8E4", 3, sh=False) + ic(i_lock("#8A93A8"), 316, 38, .8) + tx(350, 44, "家長", 14, "#7E879C"))
    cols = ["#FF6B6B", "#FFA23A", "#4CC46A", "#4C8DFF", "#A98BFF", "#FF7EB0", "#FFA23A", "#4CC46A"]
    title = "".join(f'<tspan fill="{c}">{ch}</tspan>' for ch, c in zip("咦！哪裡不一樣？", cols))
    o.append(f'<text x="195" y="103" font-size="35" text-anchor="middle" font-family="Huninn, sans-serif" fill="#C9D8EE">{"咦！哪裡不一樣？"}</text>'.replace('y="103"', 'y="107"'))
    o.append(f'<text x="195" y="103" font-size="35" text-anchor="middle" font-family="Huninn, sans-serif" stroke="#FFFFFF" stroke-width="8" stroke-linejoin="round" paint-order="stroke">{title}</text>')
    o.append(f'<ellipse cx="88" cy="252" rx="46" ry="8" fill="#5B6FA8" opacity=".14"/>')
    o.append(hero("wave", 80, 250, .76, (.5, .2)))
    o.append(bubble(170, 140, 202, 82, 24, "left", 182))
    o.append(tx(271, 175, "我偷偷變了魔法，", 17, INK) + tx(271, 203, "快來找一找！", 17, INK))
    cards = [("公園", "park", park(), 3), ("夜市", "night", night_market(), 2), ("海邊", "beach", beach(), 1),
             ("動物園", "zoo", zoo(), 0), ("生日派對", "party", party(), 0), ("廚房", "kitchen", kitchen(), 0)]
    for i, (n, k, svg, st) in enumerate(cards):
        x, y = 16 + (i % 2) * 187, 270 + (i // 2) * 166
        o.append(scene_card(x, y, 171, 154, n, k, svg, st))
    for i, c in enumerate(("#DDF0FF", "#FFF1C9")):
        x = 16 + i * 187
        o.append(lipbox(x, 768, 171, 154, 22, "#FFFFFF") + f'<rect x="{x + 8}" y="776" width="155" height="102" rx="15" fill="{c}"/>')
    o.append(f'<rect x="0" y="736" width="{W}" height="108" fill="{lg([(0, "#FFF3E2", 0), (.4, "#FFF3E2", .92), (1, "#FFF3E2", 1)])}"/>')
    o.append(lipbox(110, 774, 170, 54, 27, "#FF7E6B", "#E05F4E", 5) + ic(i_album(), 156, 801, 1) + tx(214, 809, "相簿", 21, "#FFFFFF"))
    return page("".join(o), "#FFF3E2")


# ================================================================ SCREEN 2: which one is different? (2-3 years)
def screen_odd():
    o = [bg("#D7F1FF", "#FFF4E2")]
    o.append(topbar("哪一個不一樣？", "#FF9A3D", "#E07B22",
                    lipbox(316, 32, 60, 30, 15, "#FFFFFF", LIP, 3, sh=False) + tx(346, 52, "2～3 歲", 13, "#E07B22")))
    o.append(bubble(16, 90, 358, 64, 26))
    o.append(roundbtn(52, 122, 21, GREEN, "#36A456", ic(i_speaker(), 52, 122, .82)))
    o.append(tx(84, 130, "哪一隻小鴨不一樣？", 22, INK, "start"))
    svg, pos = duck_pool(2)
    g, t = fit(svg, "pool", 0, 166, W, 440, 0, zoom=1.12, dy=-12)
    o.append(g)
    dx, dy = to_screen(t, pos[2])
    cx, cy = dx - 3 * t[2], dy - 30 * t[2]
    o.append(ring(cx, cy, 50))
    for sx_, sy_, r in ((cx + 46, cy - 46, 12), (cx - 50, cy - 34, 8), (cx + 54, cy + 16, 7)):
        o.append(sparkle(sx_, sy_, r))
    o.append(roundbtn(cx + 38, cy - 42, 14, GREEN, "#36A456", ic(i_check("#FFFFFF", 3.4), cx + 38, cy - 42, .85), 3))
    o.append(f'<ellipse cx="82" cy="780" rx="44" ry="8" fill="#5B6FA8" opacity=".14"/>')
    o.append(hero("cheer", 78, 778, .78))
    o.append(bubble(160, 628, 214, 104, 26, "left", 690))
    o.append(tx(267, 668, "對了！", 24, "#2FA552"))
    o.append(tx(267, 702, "這隻小鴨戴了紅帽子。", 16, INK))
    o.append(dots(195, 816, 5, 2, "#FF9A3D"))
    return page("".join(o), "#FFF4E2")


# ================================================================ SCREEN 3: what did 小變 change?
def screen_change():
    o = [bg("#DDF6E6", "#FFF6E4")]
    o.append(topbar("小變變了什麼？", GREEN, "#36A456"))
    px, py, pw, phh = 12, 86, 366, 330
    inner = (f'<rect x="{px}" y="{py}" width="{pw}" height="{phh}" fill="{lg([(0, "#CFEFFF"), (1, "#F2FAFF")])}"/>'
             + cloud_svg(px + 60, py + 42, .8) + cloud_svg(px + 300, py + 66, .6))
    g, t = fit(park("blue", hero=False, balloon_s=1.0), "park", px, py, pw, phh, 8, zoom=1.06, dy=6)
    o.append(frame(px, py, pw, phh, 18, inner + g, pad=0))
    bx, by = to_screen(t, P(178, 178, 78))
    bcx, bcy = bx, by - 30 * t[2]
    o.append(f'<circle cx="{bcx:.1f}" cy="{bcy:.1f}" r="44" fill="{GREEN}" opacity=".14"/>')
    o.append(ring(bcx, bcy, 36))
    o.append(f'<g transform="{part_tr(bcx + 17, bcy + 22, 1.0)}">{draw_a(pointing_hand())}</g>')
    for a in (-150, -110, -70):
        r1, r2 = 43, 53
        o.append(f'<path d="M{bcx + r1 * math.cos(math.radians(a)):.1f},{bcy + r1 * math.sin(math.radians(a)):.1f} L{bcx + r2 * math.cos(math.radians(a)):.1f},{bcy + r2 * math.sin(math.radians(a)):.1f}" stroke="{GREEN}" stroke-width="3.4" stroke-linecap="round"/>')
    # 小變 doing magic, with a burst saying 變！
    o.append(f'<ellipse cx="94" cy="628" rx="46" ry="8" fill="#5B6FA8" opacity=".14"/>')
    o.append(hero("magic", 84, 626, .82, (1, -.4)))
    hx, hy = 84 + 69 * .82, 626 - 87 * .82
    for i, (sx_, sy_, r) in enumerate(((hx + 14, hy - 12, 10), (hx + 34, hy - 30, 7), (hx + 22, hy - 46, 5), (hx + 50, hy - 52, 8), (hx + 6, hy - 30, 4))):
        o.append(sparkle(sx_, sy_, r, ["#FFC93C", "#FF7EB0", "#7FD3FF", "#FFC93C", "#A98BFF"][i]))
    burst = star_pts(52, 40, 0, 0, 12)
    o.append(f'<g transform="translate(236 470) rotate(-8)"><path d="{ptsd(crs(burst, 3), True)}" fill="{LIP}" transform="translate(0 5)"/>'
             f'<path d="{ptsd(crs(burst, 3), True)}" fill="#FFFFFF"/>' + tx(0, 14, "變！", 36, "#2FA552") + '</g>')
    o.append(bubble(16, 662, 358, 112, 28))
    o.append(roundbtn(56, 700, 21, GREEN, "#36A456", ic(i_speaker(), 56, 700, .82)))
    o.append(tx(88, 709, "氣球變顏色了！", 24, INK, "start"))
    o.append(f'<circle cx="114" cy="746" r="9" fill="#FF5A5F"/>' + tx(130, 752, "紅色", 16, "#5D6890", "start"))
    o.append(ic(i_arrow("#9AA6C2", 3.4), 190, 746, .8))
    o.append(f'<circle cx="222" cy="746" r="9" fill="#4C8DFF"/>' + tx(238, 752, "藍色", 16, "#5D6890", "start"))
    o.append(dots(195, 816, 5, 1, GREEN))
    return page("".join(o), "#FFF6E4")


# ================================================================ SCREEN 4: two pictures, five differences
def night_frame(x, y, w, h, changed, found):
    rnd = random.Random(7)
    inner = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{lg([(0, "#26326E"), (1, "#5050A0")])}"/>'
    inner += "".join(f'<circle cx="{x + rnd.uniform(6, w - 6):.1f}" cy="{y + rnd.uniform(6, h * .45):.1f}" r="{rnd.uniform(.7, 1.6):.1f}" fill="#FFFFFF" opacity="{rnd.uniform(.5, .95):.2f}"/>' for _ in range(26))
    inner += (f'<circle cx="{x + 40}" cy="{y + 36}" r="16" fill="#FFF2B0"/><circle cx="{x + 48}" cy="{y + 30}" r="14" fill="#33407A"/>')
    g, t = fit(night_market(changed), "night", x, y, w, h, 6, dy=-2, zoom=1.04)
    o = frame(x, y, w, h, 16, inner + g, pad=0)
    for (wx, wy, wz), f in NIGHT_DIFFS:
        if f and found:
            cx, cy = to_screen(t, P(wx, wy, wz))
            o += ring(cx, cy, 25)
    return o


def screen_two():
    o = [bg("#ECE8FF", "#FFF2E6")]
    o.append(roundbtn(40, 46, 22, "#FFFFFF", LIP, ic(i_home(INK), 40, 46, .9)))
    o.append(lipbox(104, 24, 182, 44, 22, "#FFFFFF", LIP, 4))
    for i in range(5):
        x = 132 + i * 31.5
        if i < 3:
            o.append(f'<circle cx="{x}" cy="46" r="11" fill="{GREEN}"/>' + ic(i_check("#FFFFFF", 3.2), x, 46, .62))
        else:
            o.append(f'<circle cx="{x}" cy="46" r="11" fill="#E8ECF4"/><circle cx="{x}" cy="46" r="4" fill="#C9D2E2"/>')
    o.append(lipbox(316, 31, 60, 30, 15, "#FFFFFF", LIP, 3, sh=False) + tx(346, 51, "3～5 歲", 13, "#6C63C9"))
    o.append(night_frame(10, 80, 370, 330, False, True))
    o.append(night_frame(10, 420, 370, 330, True, True))
    o.append(f'<ellipse cx="64" cy="832" rx="30" ry="5" fill="#5B6FA8" opacity=".14"/>')
    o.append(hero("wave", 58, 832, .44, (.6, -.2)))
    o.append(bubble(112, 774, 160, 50, 22, "left", 800))
    o.append(tx(192, 806, "還有 2 個喔！", 17, INK))
    o.append(roundbtn(338, 798, 30, "#FFFFFF", LIP, ic(i_magnifier(), 340, 796, 1.05)))
    o.append(tx(338, 840, "提示", 12, SOFT))
    return page("".join(o), "#FFF2E6")


# ================================================================ SCREEN 5: where is 小變 hiding?
def screen_hide():
    o = [bg("#D2F3FA", "#FFF4DE")]
    o.append(topbar("小變躲在哪裡？", "#A98BFF", "#8A6BE0"))
    o.append(bubble(16, 90, 358, 64, 26))
    o.append(roundbtn(52, 122, 21, GREEN, "#36A456", ic(i_speaker(), 52, 122, .82)))
    o.append(tx(84, 130, "小變躲起來了，找找看！", 20, INK, "start"))
    px, py, pw, phh = 8, 170, 374, 440
    inner = (f'<rect x="{px}" y="{py}" width="{pw}" height="{phh}" fill="{lg([(0, "#BDEFFF"), (1, "#EAFBFF")])}"/>'
             + cloud_svg(px + 70, py + 40, .8) + cloud_svg(px + 300, py + 70, .6))
    g, t = fit(beach(), "beach", px, py, pw, phh, 4, zoom=1.28, dy=-4)
    o.append(frame(px, py, pw, phh, 18, inner + g, pad=0))
    rx_, ry_ = to_screen(t, P(196, 148, 0))
    hx, hy = rx_ + 2 * t[2], ry_ - 30 * t[2]
    for sx_, sy_, r, op in ((hx - 32, hy - 22, 8, .95), (hx + 34, hy - 28, 10, .95), (hx + 40, hy + 8, 6, .85), (hx - 38, hy + 12, 5, .8)):
        o.append(sparkle(sx_, sy_, r + 2, "#FFC93C", op * .8) + sparkle(sx_, sy_, r, "#FFFFFF", op))
    o.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="40" fill="{rg([(0, "#FFF6C0", .55), (1, "#FFF6C0", 0)])}"/>')
    o.append(lipbox(16, 636, 358, 120, 26, "#FFFFFF"))
    o.append(f'<circle cx="74" cy="696" r="44" fill="#EAF8EE"/>')
    o.append(hero("wave", 70, 734, .46, (.6, 0)))
    o.append(tx(132, 684, "小變會變顏色，", 17, INK, "start") + tx(132, 712, "變得和石頭一樣！", 17, INK, "start"))
    o.append(f'<rect x="132" y="726" width="20" height="14" rx="4" fill="#5ACB6C"/>' + ic(i_arrow("#9AA6C2", 3), 166, 733, .6)
             + f'<rect x="180" y="726" width="20" height="14" rx="4" fill="#E6C283"/>')
    o.append(roundbtn(336, 696, 26, "#FFF6DA", "#F2D98A", ic(i_magnifier(), 338, 694, .9)))
    o.append(dots(195, 812, 5, 0, "#A98BFF"))
    return page("".join(o), "#FFF4DE")


# ================================================================ SCREEN 6: found it! (reward)
def album(cx, cy):
    o = [f'<ellipse cx="{cx}" cy="{cy + 62}" rx="78" ry="9" fill="#5B6FA8" opacity=".14"/>']
    o.append(f'<path d="M{cx - 82},{cy - 46} L{cx},{cy - 38} L{cx + 82},{cy - 46} L{cx + 82},{cy + 56} L{cx},{cy + 64} L{cx - 82},{cy + 56}Z" fill="#E05F4E"/>')
    o.append(f'<path d="M{cx - 76},{cy - 50} Q{cx - 38},{cy - 56} {cx},{cy - 44} L{cx},{cy + 54} Q{cx - 38},{cy + 44} {cx - 76},{cy + 50}Z" fill="#FFFFFF"/>')
    o.append(f'<path d="M{cx + 76},{cy - 50} Q{cx + 38},{cy - 56} {cx},{cy - 44} L{cx},{cy + 54} Q{cx + 38},{cy + 44} {cx + 76},{cy + 50}Z" fill="#F1F5FB"/>')
    slots = [(-66, -38, "#BFEFD0"), (-34, -36, "#2E3A7E"), (-66, -2, "#BDEFFF"), (-34, 0, None), (8, -36, None), (40, -38, None), (8, 0, None), (40, -2, None)]
    for i, (dx, dy, c) in enumerate(slots):
        if c:
            o.append(f'<rect x="{cx + dx}" y="{cy + dy}" width="26" height="30" rx="4" fill="{c}"/>')
            o.append(star_ui(cx + dx + 13, cy + dy + 22, 4.5))
        elif i == 3:
            o.append(f'<rect x="{cx + dx}" y="{cy + dy}" width="26" height="30" rx="4" fill="#FFF3C4" stroke="{GOLD}" stroke-width="2.4" stroke-dasharray="4 3"/>')
        else:
            o.append(f'<rect x="{cx + dx}" y="{cy + dy}" width="26" height="30" rx="4" fill="#E7ECF5"/>')
    o.append(tx(cx, cy + 92, "相簿", 17, "#C24E3E"))
    return "".join(o)


def screen_found():
    o = [bg("#FFF1D6", "#FFE3EE")]
    rnd = random.Random(11)
    for _ in range(46):
        x, y = rnd.uniform(8, 382), rnd.uniform(10, 560)
        if 50 < y < 200 and 70 < x < 320:
            continue
        c = rnd.choice(["#FF6B6B", "#FFC93C", "#4CC46A", "#4C8DFF", "#A98BFF", "#FF7EB0"])
        if rnd.random() < .55:
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="7" height="7" rx="1.5" fill="{c}" transform="rotate({rnd.uniform(0, 90):.0f} {x + 3.5:.1f} {y + 3.5:.1f})"/>')
        else:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{c}"/>')
    o.append(star_ui(135, 86, 26) + star_ui(255, 86, 26) + star_ui(195, 72, 36))
    o.append(txo(195, 160, "全部找到了！", 32, "#E0572E", ow=7))
    # the card fills with colour (from the middle out) and gets a stamp
    card = []
    cx_, cy_ = 195, 318
    cw, chh = 300, 250
    x0, y0 = cx_ - cw / 2, cy_ - chh / 2
    card.append(lipbox(x0, y0, cw, chh, 24, "#FFFFFF"))
    px, py, pw, phh = x0 + 10, y0 + 10, cw - 20, chh - 62
    pic = (f'<rect x="{px}" y="{py}" width="{pw}" height="{phh}" fill="{lg([(0, "#CFEFFF"), (1, "#F2FAFF")])}"/>'
           + fit(park(), "park", px, py, pw, phh, 4)[0])
    cpp = clip(f"M{px + 16},{py} H{px + pw - 16} A16,16 0 0 1 {px + pw},{py + 16} V{py + phh - 16} A16,16 0 0 1 {px + pw - 16},{py + phh} "
               f"H{px + 16} A16,16 0 0 1 {px},{py + phh - 16} V{py + 16} A16,16 0 0 1 {px + 16},{py}Z")
    rr_ = 112
    circ = clip(f"M{cx_ - rr_ - 20},{py + phh / 2} A{rr_},{rr_ * .82} 0 1 0 {cx_ + rr_ - 20},{py + phh / 2} A{rr_},{rr_ * .82} 0 1 0 {cx_ - rr_ - 20},{py + phh / 2}Z")
    card.append(f'<g clip-path="{cpp}"><g filter="{grey_filter(0, .25)}">{pic}</g><g clip-path="{circ}">{pic}</g></g>')
    for a in range(0, 360, 30):
        sx_ = cx_ - 20 + rr_ * math.cos(math.radians(a))
        sy_ = py + phh / 2 + rr_ * .82 * math.sin(math.radians(a))
        if px + 6 < sx_ < px + pw - 6 and py + 6 < sy_ < py + phh - 6:
            card.append(sparkle(sx_, sy_, 7 if a % 60 else 10, "#FFFFFF"))
    card.append(tx(x0 + 22, y0 + chh - 20, "公園", 20, INK, "start"))
    for i in range(3):
        card.append(star_ui(x0 + 96 + i * 22, y0 + chh - 26, 9.5))
    st = [f'<circle r="38" fill="#FFFFFF" opacity=".55"/><circle r="38" fill="none" stroke="#FF5A5F" stroke-width="4"/>',
          '<circle r="31" fill="none" stroke="#FF5A5F" stroke-width="1.8"/>', tx(0, 7, "找到了", 18, "#FF5A5F")]
    for a in (-60, -90, -120):
        st.append(sparkle(23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a)) - 2, 3.4, "#FF5A5F"))
    card.append(f'<g transform="translate({x0 + cw - 44} {y0 + chh - 48}) rotate(-14)" opacity=".92">{"".join(st)}</g>')
    o.append(f'<g transform="rotate(-4 {cx_} {cy_})">{"".join(card)}</g>')
    # flying into the album
    o.append(f'<path d="M{cx_ + 122},{cy_ + 118} Q{cx_ + 168},{cy_ + 220} {cx_ + 58},{cy_ + 290}" fill="none" stroke="{GOLD}" stroke-width="3.4" stroke-dasharray="2 9" stroke-linecap="round"/>')
    o.append(sparkle(cx_ + 142, cy_ + 168, 8) + sparkle(cx_ + 118, cy_ + 252, 6))
    o.append(album(272, 624))
    o.append(f'<ellipse cx="94" cy="740" rx="48" ry="8" fill="#5B6FA8" opacity=".14"/>')
    o.append(hero("cheer", 90, 738, .84))
    o.append(sparkle(40, 560, 9, "#FF7EB0") + sparkle(150, 556, 7, "#4CC46A"))
    o.append(lipbox(95, 768, 200, 56, 28, GREEN, "#36A456", 5) + tx(176, 805, "下一張", 22, "#FFFFFF") + ic(i_arrow(), 248, 796, .9))
    return page("".join(o), "#FFE3EE")


# ================================================================ SCREEN 7: parents
P_BG, P_TXT, P_SUB, P_ACC, P_LINE = "#F4F6FA", "#3A4256", "#8A93A8", "#3FAE76", "#E3E7EF"


def toggle(x, y, on=True):
    if on:
        return f'<rect x="{x}" y="{y}" width="46" height="26" rx="13" fill="{P_ACC}"/><circle cx="{x + 33}" cy="{y + 13}" r="10" fill="#FFFFFF"/>'
    return f'<rect x="{x}" y="{y}" width="46" height="26" rx="13" fill="#D5D9E2"/><circle cx="{x + 13}" cy="{y + 13}" r="10" fill="#FFFFFF"/>'


def section(y, h, title=None):
    o = f'<rect x="14" y="{y}" width="362" height="{h}" rx="16" fill="#FFFFFF" stroke="{P_LINE}" stroke-width="1.2"/>'
    if title:
        o += tx(30, y + 26, title, 15, P_SUB, "start")
    return o


def segmented(y, opts, sel, x0=30, w=330):
    o = f'<rect x="{x0}" y="{y}" width="{w}" height="36" rx="10" fill="#EEF0F4"/>'
    cw = (w - 4) / len(opts)
    for i, a in enumerate(opts):
        x = x0 + 2 + i * cw
        if i == sel:
            o += f'<rect x="{x}" y="{y + 2}" width="{cw}" height="32" rx="9" fill="{P_ACC}"/>'
        o += tx(x + cw / 2, y + 23, a, 15, "#FFFFFF" if i == sel else P_TXT)
    return o


def screen_parents():
    o = [f'<rect width="{W}" height="{H}" fill="{P_BG}"/>']
    o.append(tx(195, 50, "家長模式", 20, P_TXT))
    o.append(f'<circle cx="350" cy="44" r="18" fill="#E4E7EE"/>' + ic(i_x("#5C6474", 2.6), 350, 44, .85))
    o.append(section(76, 104, "年齡"))
    o.append(segmented(114, ("2～3 歲", "3～4 歲", "4～5 歲"), 1))
    o.append(tx(30, 168, "年紀越大，不一樣的地方越小、越多。", 12.5, P_SUB, "start"))
    o.append(section(190, 92, "每次玩多久"))
    for i, m in enumerate((5, 10, 15, 20, 30)):
        x = 30 + i * 67
        sel = m == 15
        o.append(f'<rect x="{x}" y="228" width="61" height="36" rx="18" fill="{P_ACC if sel else "#FFFFFF"}" stroke="{P_ACC if sel else "#D5D9E2"}" stroke-width="1.5"/>')
        o.append(tx(x + 30.5, 251, f"{m} 分鐘", 14, "#FFFFFF" if sel else P_TXT))
    o.append(section(292, 104, "提示"))
    o.append(segmented(330, ("多", "少"), 0))
    o.append(tx(30, 384, "找不到的時候，小變會發亮給一點提示。", 12.5, P_SUB, "start"))
    o.append(section(406, 108))
    o.append(tx(30, 440, "聲音", 16, P_TXT, "start"))
    o.append(f'<rect x="96" y="432" width="210" height="6" rx="3" fill="#E1E4EA"/><rect x="96" y="432" width="140" height="6" rx="3" fill="{P_ACC}"/>'
             f'<circle cx="236" cy="435" r="10" fill="#FFFFFF" stroke="{P_ACC}" stroke-width="2"/>')
    o.append(ic(i_speaker(P_SUB), 336, 435, .7))
    o.append(f'<path d="M30,460 L360,460" stroke="#EEF0F4" stroke-width="1.2"/>')
    o.append(tx(30, 486, "英文", 16, P_TXT, "start") + tx(30, 504, "說完國語，再說一次英文", 12.5, P_SUB, "start"))
    o.append(toggle(314, 474, True))
    o.append(section(524, 290, "進度"))
    o.append(tx(360, 550, "已經找完 9 張", 13, P_SUB, "end"))
    rows = [("公園", 5, "#7FD06E"), ("夜市", 3, "#6E64C8"), ("海邊", 1, "#4FB6E8"), ("動物園", 0, "#F0B44A"), ("生日派對", 0, "#FF8FB8"), ("廚房", 0, "#FF9838")]
    for i, (n, k, c) in enumerate(rows):
        y = 586 + i * 38
        if i:
            o.append(f'<path d="M30,{y - 21} L360,{y - 21}" stroke="#EEF0F4" stroke-width="1.2"/>')
        o.append(f'<rect x="30" y="{y - 13}" width="22" height="22" rx="6" fill="{c}"/>')
        o.append(tx(62, y + 4, n, 15, P_TXT, "start"))
        for j in range(5):
            o.append(f'<circle cx="{180 + j * 24}" cy="{y - 2}" r="8" fill="{c if j < k else "#EEF0F4"}"/>')
        o.append(tx(360, y + 4, f"{k}/5", 13, P_SUB, "end"))
    return page("".join(o), P_BG)


SCREENS = {"1_首頁": screen_home, "2_找出不一樣的": screen_odd, "3_哪裡變了": screen_change, "4_兩張找不同": screen_two,
           "5_躲貓貓": screen_hide, "6_找到了": screen_found, "7_家長模式": screen_parents}


def contact_sheet(names):
    cw_, ch_, gap, m = 232, 502, 24, 30
    per = 4
    w = per * cw_ + (per - 1) * gap + 2 * m
    rowh = ch_ + 64
    h = 2 * rowh + 40
    items = []
    for i, n in enumerate(names):
        r, c = divmod(i, per)
        x = m + c * (cw_ + gap) + (0 if r == 0 else (cw_ + gap) / 2)
        y = 28 + r * rowh
        items.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:{cw_}px;text-align:center">'
                     f'<img src="file://{HERE / (n + ".png")}" style="width:{cw_}px;height:{ch_}px;border-radius:18px;box-shadow:0 6px 16px rgba(60,80,130,.18)">'
                     f'<div style="font:19px Huninn, sans-serif;color:{INK};margin-top:10px">{n.replace("_", " ")}</div></div>')
    css = f"@font-face {{ font-family: Huninn; src: url('file://{FONT}'); }} * {{ margin:0; padding:0 }} body {{ width:{w}px; height:{h}px; background:#EEF3FA; position:relative }}"
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(items)}</body></html>', w, h


def items_sheet():
    cw, ch = 220, 230
    b0, f0 = chameleon("wave", (.3, .2))
    b1, f1 = chameleon("cheer")
    b2, f2 = chameleon("magic", (1, -.2))
    b3, f3 = chameleon("peek", (-.8, .1), tilt=-12)
    rows = [
        [("A wave", "a", b0 + f0, .95), ("A cheer", "a", b1 + f1, .95), ("A magic", "a", b2 + f2, .95), ("A peek", "a", b3 + f3, .95),
         ("A hidden", "a", hide_rock(), 2.2)],
        [("A duck", "a", duck(), 1.6), ("A duck hat", "a", duck(True), 1.6), ("A balloon", "a", balloon(), 1.8),
         ("A balloon blue", "a", balloon("blue"), 1.8), ("A hand", "a", pointing_hand(), 1.6)],
        [("B wave", "b", b0 + f0, .95), ("B duck", "b", duck(True), 1.6), ("C wave", "c", b0 + f0, .95), ("C duck", "c", duck(True), 1.6),
         ("C balloon", "c", balloon(), 1.8)],
    ]
    o = []
    for r_, row in enumerate(rows):
        for c_, (name, st, shs, s) in enumerate(row):
            x, y = 16 + c_ * (cw + 16), 16 + r_ * (ch + 16)
            xs = [p[0] for sh in shs for p in sh.pts]
            ys = [p[1] for sh in shs for p in sh.pts]
            cx_, cy_ = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            part = [(shs, x + cw / 2 - cx_ * s, y + ch / 2 - 10 - cy_ * s, s, False)]
            if st == "a":
                o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="18" fill="#EEF6FF"/>' + a_parts(part))
            elif st == "b":
                o.append(riso(part, x, y, cw, ch))
            else:
                o.append(crayon(part, x, y, cw, ch, seed=c_ + 3))
            o.append(tx(x + cw / 2, y + ch - 10, name, 14, SOFT))
    w, h = 16 + 5 * (cw + 16), 16 + 3 * (ch + 16)
    return page("".join(o), "#F7F8FC", w, h), w, h


def main(only=None):
    global D
    if only in (None, "0"):
        D = Defs()
        html, ph = style_sheet()
        render(html, HERE / "0_畫風選擇.png", W, ph, 2)
        print("0_畫風選擇")
    for name, make in SCREENS.items():
        if only not in (None, name.split("_")[0]):
            continue
        D = Defs()
        render(make(), HERE / f"{name}.png", W, H, 2)
        print(name)
    if only in (None, "c"):
        html, w, h = contact_sheet(list(SCREENS))
        render(html, HERE / "contact_sheet.png", w, h, 1.25)
        print("contact_sheet")
    if only and only.startswith("items"):
        D = Defs()
        html, w, h = items_sheet()
        out = SCRATCH / "findiff_items.png"
        render(html, out, w, h, 1)
        print(out)
        return


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
