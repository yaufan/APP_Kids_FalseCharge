"""Art kit for 眼尖尖大挑戰: ONE geometry, THREE styles.

Every picture of the game (scene backgrounds, the things in a scene and their variants, 小變 the
chameleon) is described once as a list of shapes (`Sh`) with plain colours, and then drawn by three
renderers. Switching style therefore never moves, resizes or recolours anything that matters for a
puzzle: only the way it is painted changes.

    a  等角小模型風  isometric toy diorama: flat-shaded faces (top lightest, left = the colour,
                     right darker), soft round corners, round things get a light crescent on top
                     and a dark one on the right; no outlines.
    b  孔版印刷風    risograph print: every colour is snapped to the nearest mix of four inks
                     (fluorescent pink, blue, yellow, teal; up to two inks overprinted, three for
                     dark colours). The mixed colours are computed here (flutter_svg has no blend
                     modes). A second ink peeks out 1-2 units to one side (misregistration),
                     shadows are halftone dots, and inked areas carry sparse paper-coloured grain.
    c  粗蠟筆童畫風  thick crayon on white paper: back-and-forth hatch fills (clipped to a slightly
                     bigger copy of the shape, so they overshoot), tiny wax gaps in the strokes,
                     wobbly doubled outlines in a darker crayon. Small details are solid.

THE CONTRACT with the app is docs/scenes.md: where files go, the scene JSON, viewBoxes. `SceneArt`
below writes all of it; `check_svg()` and `check_scene()` enforce it.

flutter_svg limits (hard rules, enforced by check_svg): no <filter>, <mask>, <style>, style=, CSS,
<text>, <image>, <foreignObject>, <pattern>, blend modes; every drawing element carries its own
fill/stroke attribute; under ~70 KB and fewer than 800 <use> per file. Clip paths are used only one
level deep and contain plain paths/ellipses or an untransformed <use> (nested clips with a
transformed <use> were found NOT to work in flutter_svg).

------------------------------------------------------------------------------------------------
HOW TO DRAW (see scene_park.py for a full scene, chameleon.py for a character)

Coordinates are output units: for scene art, the scene's 600 x 600 pixels; for 小變, 200 x 200.

    iso = Iso(k=1.5, ox=300, oy=186)           # world (x right-front, y left-front, z up) -> scene px
    g = Group()
    g.add(iso.shadow(50, 50, 20))              # each primitive returns a list of Sh
    g.add(iso.box(40, 40, 0, 20, 20, 30, "#FF7A7A"), depth=iso.depth(50, 50))
    g.add(iso.ball(50, 50, 30, 12, "#5BC46A"), depth=iso.depth(50, 50) + 1)
    g.add(iso.sprite(dog_shapes, 80, 60, 0, s=.5))   # a 2D sprite (origin at its feet) stood on the ground
    shapes = g.shapes()                        # sorted back to front (depth, then insertion order)
    svg = render(shapes, "b", box=(x0, y0, w, h))   # viewBox 0 0 w h; SceneArt does this for you

Shapes (`Sh`): a closed polygon (filled) or an open polyline (a stroke of width `w`), one colour
(the style-A colour; b and c derive theirs from it), and hints for the renderers:
    cel=1.0        style A crescent shading strength (round things); 0 = flat
    face="top"     an iso face ("top"/"left"/"right"): A gives it soft corners, C hatches it at
                   that face's angle
    tag="shadow"   a ground shadow (A: soft dark, B: halftone dots, C: left out)
    tag="glow"     a soft light (A/B: pale and see-through, C: left out)
    tag="detail"   no crayon outline in C (highlights, spots)
    tag="screen"   a big light area (a sky): B prints it as a halftone dot screen on the paper
    op=0.8         opacity
    only="ab"      drawn only in these styles (e.g. scenery a child would draw more simply in C:
                   give the C version only="c" at the same place). Never use it for a thing's
                   look that matters to a puzzle.
Ellipses keep their exact form (`ell`), so A and B write compact <ellipse> elements.

Colours: pass plain hex colours. Things that a hiding 小變 must blend with use TINT[...] colours
(bush = TINT["leaf"], sand path = TINT["sand"], tree trunk/bench wood = TINT["wood"]...), so his
hide art matches them in all three styles automatically. B and C colours are computed from the A
colour (riso_snap(), crayon()); override a single colour with RISO_OVERRIDE / CRAYON_OVERRIDE.

Determinism: all randomness (crayon wobble and hatch, riso grain) is seeded from a hash of each
shape's geometry, so the same drawing gives the same bytes on every run, and a colour variant or a
"one duck fewer" variant keeps exactly the same strokes for everything that did not change.

------------------------------------------------------------------------------------------------
HOW TO ADD A SCENE: copy scene_park.py. It makes a SceneArt, gives it a background function, one
function per thing and per variant (each returns shapes in scene px), changes with their `said`
lines, extras, hide spots and the lineup, and calls `.build()`. Then
    python3 build.py layout <scene>            # boxes, which boxes overlap, puzzle counts (no files)
    python3 build.py <scene>                   # writes art + JSON, runs the checks
    python3 build.py preview <scene> out.png   # look at it (bg + things in z order, a, b, c)
    python3 build.py fluttercheck <scene>      # draws every file with the real flutter_svg and
                                               # compares with Chromium (throw-away project in /dev/shm)

What check_scene() enforces (besides the files and fields of docs/scenes.md):
  - every art file exists in a, b and c, with the viewBox aspect of its box (the app draws each
    thing with BoxFit.fill into its box, in z order; `size` scales about the bottom edge, `flip`
    mirrors left-right); a `size` change must stay inside the picture;
  - `big` things are at least 0.12 wide; at least 7 big things have a colour or gone change;
  - the app's own puzzle picking (pick(), ported from lib/core/puzzles.dart: only big things below
    4-5 years, one difference per thing, boxes kept GAP apart) always finds 1 / 3 / 5 differences
    for 小小 / 中 / 大 in thousands of random tries: spread the big things apart until it does;
  - every hide spot is square (the hide art is 200 x 200) and some thing with a higher z overlaps it
    (older children find him partly hidden; for 2-3 years the app draws him on top).

Lessons for a good scene: put tall things at the back and in a band of sky above the tile (sky
things never overlap ground things); keep front things low; give 2-year-old changes to things that
are big and plain (colour, gone); keep the background under about 60 KB in every style (big crayon
areas and riso grain cost the most: use tag="screen" for the sky, one geometry for paths, and
only="c" simplifications for fences and other fiddly scenery).
"""
import colorsys
import hashlib
import json
import math
import pathlib
import random
import re
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ART = ROOT / "app" / "assets" / "art"
SCENES = ROOT / "app" / "assets" / "scenes"
STYLES = ("a", "b", "c")
SCENE = 600            # scene art is 600 x 600 units
CHAR = 200             # 小變 art is 200 x 200 units
PAD = 3                # units around a thing's drawing (crayon wobble, ink misregistration)

# The colours 小變 can take when he hides (docs/scenes.md `tint`). Scenery he hides against must
# use the same colour so he blends in in every style.
TINT = {
    "leaf": "#5BC46A",
    "sand": "#F3D69A",
    "wood": "#B98356",
    "red": "#FF5A5F",
    "blue": "#4C8DFF",
    "white": "#F2F5FA",
}


# ================================================================ numbers and colours
def n(v):
    """A number, short: one decimal, no trailing .0, no -0."""
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("-0") and s.strip("-0.") == "":
        s = "0"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _hexrgb(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def mix(a, b, t):
    """a moved t of the way to b."""
    return _hexrgb(*[x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b))])


def lt(c, t):
    return mix(c, "#FFFFFF", t)


def dk(c, t):
    return mix(c, "#1E2238", t)


def _hls(c):
    return colorsys.rgb_to_hls(*[x / 255 for x in _rgb(c)])


def _hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s)))
    return _hexrgb(r * 255, g * 255, b * 255)


def tone(c, l=1.0, s=1.0, dh=0.0):
    """Scale lightness and saturation, shift hue."""
    h, L, S = _hls(c)
    return _hex(h + dh, L * l, S * s)


def shades(col):
    """Style A iso faces: (top, left, right). The top is the lightest, the left face is the colour
    itself, the right face darker (greys get a cool blue shade)."""
    h, L, S = _hls(col)
    if S < .1:
        return mix(col, "#FFFFFF", .55), col, mix(col, "#AFC0E6", .5)
    return mix(col, "#FFFFFF", .3), col, _hex(h + .006, L * .82, min(1, S * 1.05))


def a_light(c):
    return mix(c, "#FFFFFF", .42)


def a_dark(c):
    h, L, S = _hls(c)
    if S < .1:
        return mix(c, "#B8C6E6", .55)
    return _hex(h + .005, L * .84, min(1, S * 1.04))


# ================================================================ geometry (point lists)
C30, S30 = math.cos(math.radians(30)), .5


def ellp(cx, cy, rx, ry=None, n=40, rot=0.0):
    """Points of an ellipse (rot in degrees)."""
    ry = rx if ry is None else ry
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def crs(ctrl, k=10, closed=True):
    """Catmull-Rom spline through the control points, as a dense point list."""
    m = len(ctrl)
    out = []
    segs = m if closed else m - 1
    for i in range(segs):
        p0 = ctrl[(i - 1) % m] if closed else ctrl[max(i - 1, 0)]
        p1, p2 = ctrl[i], ctrl[(i + 1) % m]
        p3 = ctrl[(i + 2) % m] if closed else ctrl[min(i + 2, m - 1)]
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * (2 * p1[q] + (-p0[q] + p2[q]) * t + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * t2
                                   + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * t3) for q in (0, 1)))
    if not closed:
        out.append(tuple(ctrl[-1]))
    return out


def rrect(x, y, w, h, r, k=5):
    """Rounded rectangle points."""
    r = min(r, w / 2, h / 2)
    out = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for j in range(k + 1):
            a = math.radians(a0 + 90 * j / k)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def tube(c, w0, w1=None, caps=True):
    """A closed outline around the centre line c (dense points): width w0 at the start, w1 at the end."""
    w1 = w0 if w1 is None else w1
    m = len(c)
    L, R, dirs = [], [], []
    for i, (x, y) in enumerate(c):
        x0, y0 = c[max(i - 1, 0)]
        x1, y1 = c[min(i + 1, m - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        dx, dy = dx / ln_, dy / ln_
        dirs.append((dx, dy))
        w = (w0 + (w1 - w0) * i / max(1, m - 1)) / 2
        L.append((x - dy * w, y + dx * w))
        R.append((x + dy * w, y - dx * w))
    if not caps:
        return L + R[::-1]

    def cap(p, d, w, start):
        out = []
        sgn = -1 if start else 1
        for j in range(1, 6):
            ph = math.pi * j / 6
            nx, ny = -d[1], d[0]
            out.append((p[0] + w * (math.cos(ph) * nx * (-1 if start else 1) + math.sin(ph) * d[0] * sgn),
                        p[1] + w * (math.cos(ph) * ny * (-1 if start else 1) + math.sin(ph) * d[1] * sgn)))
        return out
    return L + cap(c[-1], dirs[-1], w1 / 2, False) + R[::-1] + cap(c[0], dirs[0], w0 / 2, True)


def tf(pts, dx=0.0, dy=0.0, rot=0.0, s=1.0, about=(0.0, 0.0), sx=None):
    """Scale (sx, s) and rotate about `about`, then move by (dx, dy)."""
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    sx = s if sx is None else sx
    out = []
    for x, y in pts:
        x, y = (x - about[0]) * sx, (y - about[1]) * s
        out.append((about[0] + x * ca - y * sa + dx, about[1] + x * sa + y * ca + dy))
    return out


def star_pts(R, r, cx=0.0, cy=0.0, k=5, rot=-90.0):
    out = []
    for i in range(2 * k):
        a = math.radians(rot + 180 * i / k)
        rr_ = R if i % 2 == 0 else r
        out.append((cx + rr_ * math.cos(a), cy + rr_ * math.sin(a)))
    return out


def sparkle(cx, cy, R, rot=0.0):
    """A four-pointed twinkle (curved sides)."""
    out = []
    for i in range(4):
        a = math.radians(rot + 90 * i)
        tip = (cx + R * math.cos(a), cy + R * math.sin(a))
        b = math.radians(rot + 90 * i + 45)
        mid = (cx + R * .18 * math.cos(b), cy + R * .18 * math.sin(b))
        out += [tip, mid]
    return crs(out, 4)


def spiral(c, r0, turns, th0, k=80, shrink=.82):
    out = []
    for i in range(k + 1):
        t = i / k
        th = math.radians(th0 + t * turns * 360)
        r = r0 * (1 - shrink * t)
        out.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
    return out


def resample(pts, step, closed=True):
    seq = list(pts) + ([pts[0]] if closed else [])
    out = [seq[0]]
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        t = step - acc
        while t <= seg:
            out.append((x0 + (x1 - x0) * t / seg, y0 + (y1 - y0) * t / seg))
            t += step
        acc = (acc + seg) % step if seg else acc
    if not closed and out[-1] != seq[-1]:
        out.append(seq[-1])
    return out


def wobble(pts, amp, rnd, closed=True, step=3.0):
    """A hand-drawn copy of the line: resampled every `step`, pushed in and out by smooth noise."""
    p = resample(pts, step, closed)
    m = len(p)
    ph = [rnd.uniform(0, 6.3) for _ in range(3)]
    fr = [rnd.uniform(.08, .14), rnd.uniform(.25, .4), rnd.uniform(.6, .9)]
    out = []
    for i, (x, y) in enumerate(p):
        x0, y0 = p[max(i - 1, 0)]
        x1, y1 = p[min(i + 1, m - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln_ = math.hypot(dx, dy) or 1
        off = amp * (math.sin(i * fr[0] + ph[0]) * .6 + math.sin(i * fr[1] + ph[1]) * .3 + math.sin(i * fr[2] + ph[2]) * .15)
        out.append((x - dy / ln_ * off, y + dx / ln_ * off))
    return out


def area(pts):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2


def perimeter(pts, closed=True):
    seq = list(pts) + ([pts[0]] if closed else [])
    return sum(math.hypot(x1 - x0, y1 - y0) for (x0, y0), (x1, y1) in zip(seq, seq[1:]))


def thickness(pts):
    """How thick a shape is (4 x area / perimeter): the diameter of a disc, about twice the width
    of a long thin strip; a bounding box would call a thin diagonal rail big."""
    p = perimeter(pts)
    return 4 * area(pts) / p if p else 0.0


def long_axis(pts):
    """(angle in degrees of a shape's long axis, how much longer than wide it is)."""
    m = len(pts)
    mx = sum(p[0] for p in pts) / m
    my = sum(p[1] for p in pts) / m
    sxx = sum((p[0] - mx) ** 2 for p in pts) / m
    syy = sum((p[1] - my) ** 2 for p in pts) / m
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / m
    ang = .5 * math.atan2(2 * sxy, sxx - syy)
    tr, det = sxx + syy, sxx * syy - sxy * sxy
    disc = math.sqrt(max(0.0, tr * tr / 4 - det))
    l1, l2 = tr / 2 + disc, max(1e-9, tr / 2 - disc)
    return math.degrees(ang), math.sqrt(l1 / l2)


def inside(pt, pts):
    """Point in polygon (even-odd)."""
    x, y = pt
    c = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            c = not c
        j = i
    return c


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def pd(pts, closed=True, whole=False):
    """SVG path data of a point list (whole=True: whole numbers, for wobbly crayon lines)."""
    if not pts:
        return ""
    f = (lambda v: str(round(v))) if whole else n
    s = f"M{f(pts[0][0])},{f(pts[0][1])}L" + " ".join(f"{f(x)},{f(y)}" for x, y in pts[1:])
    return s + ("Z" if closed else "")


# ================================================================ shapes
class Sh:
    """One shape in output units: a filled polygon (closed) or a stroked polyline of width w.
    col is the style A colour. See the module docstring for cel / face / tag / op."""
    __slots__ = ("pts", "col", "closed", "w", "cel", "face", "op", "tag", "ell", "base", "only")

    def __init__(self, pts, col, closed=True, w=0.0, cel=0.0, face=None, op=1.0, tag=None, ell=None, base=None, only=None):
        self.pts, self.col, self.closed, self.w = list(pts), col, closed, w
        self.cel, self.face, self.op, self.tag, self.ell = cel, face, op, tag, ell
        self.base, self.only = base, only

    def copy(self, **kw):
        s = Sh(self.pts, self.col, self.closed, self.w, self.cel, self.face, self.op, self.tag, self.ell, self.base, self.only)
        for k, v in kw.items():
            setattr(s, k, v)
        return s

    def bbox(self):
        x0, y0, x1, y1 = bbox(self.pts)
        if not self.closed:
            h = self.w / 2
            return x0 - h, y0 - h, x1 + h, y1 + h
        return x0, y0, x1, y1

    def size(self):
        x0, y0, x1, y1 = bbox(self.pts)
        return min(x1 - x0, y1 - y0)

    def affine(self, a, b, c, d, e, f):
        """Apply the SVG matrix(a b c d e f) to the points (and to the ellipse, when it stays one)."""
        pts = [(a * x + c * y + e, b * x + d * y + f) for x, y in self.pts]
        ell = None
        det = a * d - b * c
        if self.ell is not None:
            sim = abs(a - d) < 1e-9 and abs(b + c) < 1e-9
            refl = abs(a + d) < 1e-9 and abs(b - c) < 1e-9
            if sim or refl:
                cx, cy, rx, ry, rot = self.ell
                s = math.sqrt(abs(det))
                base = math.degrees(math.atan2(b, a))
                ell = (a * cx + c * cy + e, b * cx + d * cy + f, rx * s, ry * s, base + (rot if det > 0 else -rot))
        sc = math.sqrt(abs(det))
        return Sh(pts, self.col, self.closed, self.w * sc, self.cel, self.face, self.op, self.tag, ell, self.base, self.only)

    def key(self):
        """A stable hash of the geometry (not the colour): seeds the crayon and grain noise."""
        x0, y0, x1, y1 = bbox(self.pts)
        h = hashlib.md5(f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f},{len(self.pts)},{self.closed}".encode())
        return int(h.hexdigest()[:8], 16)


def shape(pts, col, **kw):
    return Sh(pts, col, **kw)


def oval(cx, cy, rx, ry=None, col="#000000", rot=0.0, k=40, **kw):
    """An ellipse shape (keeps its exact form for A and B)."""
    ry = rx if ry is None else ry
    return Sh(ellp(cx, cy, rx, ry, k, rot), col, ell=(cx, cy, rx, ry, rot), **kw)


def line(pts, col, w, **kw):
    """An open stroke."""
    return Sh(pts, col, closed=False, w=w, **kw)


def transform(shapes, dx=0.0, dy=0.0, s=1.0, rot=0.0, flip=False, about=(0.0, 0.0)):
    """Scale (and mirror) about `about`, rotate, then move. Returns new shapes."""
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    sx = -s if flip else s
    # p' = R * S * (p - about) + about + d
    A, B, C, D = ca * sx, sa * sx, -sa * s, ca * s
    E = about[0] + dx - (A * about[0] + C * about[1])
    F = about[1] + dy - (B * about[0] + D * about[1])
    return [sh.affine(A, B, C, D, E, F) for sh in shapes]


def recolor(shapes, cmap):
    """Swap colours: cmap {old hex: new hex} (exact, case-insensitive)."""
    m = {k.upper(): v for k, v in cmap.items()}
    out = []
    for sh in shapes:
        if sh.base and sh.base.upper() in m:
            nb = m[sh.base.upper()]
            t, l, r = shades(nb)
            out.append(sh.copy(base=nb, col={"top": t, "left": l, "right": r}.get(sh.face, nb)))
        else:
            out.append(sh.copy(col=m.get(sh.col.upper(), sh.col)))
    return out


def shapes_bbox(shapes):
    bs = [sh.bbox() for sh in shapes]
    return min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)


class Group:
    """Shapes painted back to front: by depth, then in the order they were added."""

    def __init__(self):
        self.items = []

    def add(self, shapes, depth=0.0):
        if isinstance(shapes, Sh):
            shapes = [shapes]
        self.items.append((depth, len(self.items), list(shapes)))
        return self

    def shapes(self):
        out = []
        for _, _, s in sorted(self.items, key=lambda t: t[:2]):
            out += s
        return out


# ================================================================ isometric projection
class Iso:
    """World units to output units, 30 degrees from above: x runs to the right-front, y to the
    left-front, z up. Primitives return lists of Sh with the A-style face shading built in."""

    def __init__(self, k=1.0, ox=0.0, oy=0.0):
        self.k, self.ox, self.oy = k, ox, oy

    def P(self, x, y, z=0.0):
        return (self.ox + (x - y) * C30 * self.k, self.oy + (x + y) * S30 * self.k - z * self.k)

    @staticmethod
    def depth(x, y, z=0.0):
        """Painter's depth of a world point: bigger = nearer the viewer (drawn later)."""
        return x + y + z * .01

    def face(self, pts3, col, face=None, base=None, **kw):
        return Sh([self.P(*p) for p in pts3], col, face=face, base=base, **kw)

    def box(self, x, y, z, w, d, h, col, top=None, left=None, right=None, **kw):
        """A box from (x, y, z) to (x+w, y+d, z+h): its three visible faces."""
        t, l, r = shades(col)
        bt, bl, br = (None if top else col), (None if left else col), (None if right else col)   # overridden faces print their own colour
        t, l, r = top or t, left or l, right or r
        return [self.face([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], l, "left", bl, **kw),
                self.face([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], r, "right", br, **kw),
                self.face([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], t, "top", bt, **kw)]

    def flat(self, pts_xy, z, col, **kw):
        """A flat polygon lying on the plane at height z (a path, a rug, water)."""
        return Sh([self.P(x, y, z) for x, y in pts_xy], col, **kw)

    def disc(self, cx, cy, z, R, col, **kw):
        sx, sy = self.P(cx, cy, z)
        return oval(sx, sy, R * 1.2247 * self.k, R * .7071 * self.k, col, **kw)

    def shadow(self, cx, cy, R, z=0.0, op=1.0):
        return [self.disc(cx, cy, z, R, "#3B5A7A", tag="shadow", op=op)]

    def cyl(self, cx, cy, z, R, h, col, top=None, k=28):
        """An upright cylinder: left half of the side, right half (darker), top."""
        t, l, r = shades(col)
        t = top or t
        rx, ry = R * 1.2247 * self.k, R * .7071 * self.k
        sx, sy = self.P(cx, cy, z)
        hh = h * self.k
        lower = [(sx + rx * math.cos(math.pi - math.pi * i / k), sy + ry * math.sin(math.pi - math.pi * i / k)) for i in range(k + 1)]
        mid = k // 2
        left = lower[:mid + 1] + [(lower[mid][0], lower[mid][1] - hh), (lower[0][0], lower[0][1] - hh)]
        right = lower[mid:] + [(lower[-1][0], lower[-1][1] - hh), (lower[mid][0], lower[mid][1] - hh)]
        return [Sh(left, l, face="left", base=col), Sh(right, r, face="right", base=col), oval(sx, sy - hh, rx, ry, t, face="top", base=col)]

    def ball(self, cx, cy, z, R, col, cel=1.0, sq=1.0):
        """A ball resting on height z (drawn as a round sprite with crescent shading in A)."""
        sx, sy = self.P(cx, cy, z)
        Rk = R * self.k
        return [oval(sx, sy - Rk * sq, Rk, Rk * sq, col, cel=cel)]

    def pyramid(self, x, y, z, w, d, h, col):
        t, l, r = shades(col)
        apex = (x + w / 2, y + d / 2, z + h)
        return [self.face([(x, y + d, z), (x + w, y + d, z), apex], l, "left", col),
                self.face([(x + w, y, z), (x + w, y + d, z), apex], r, "right", col)]

    def ramp(self, x, y0, y1, z0, z1, w, th, col):
        """A slope running along +y (a slide chute): right side, front end, top."""
        t, l, r = shades(col)
        return [self.face([(x + w, y0, z0), (x + w, y1, z1), (x + w, y1, z1 - th), (x + w, y0, z0 - th)], r, "right", col),
                self.face([(x, y1, z1), (x + w, y1, z1), (x + w, y1, z1 - th), (x, y1, z1 - th)], l, "left", col),
                self.face([(x, y0, z0), (x + w, y0, z0), (x + w, y1, z1), (x, y1, z1)], t, "top", col)]

    def line3(self, pts3, col, w, **kw):
        return line([self.P(*p) for p in pts3], col, w * self.k, **kw)

    def sprite(self, shapes, x, y, z=0.0, s=1.0, flip=False):
        """Stand a 2D sprite (drawn with its origin at its feet) on a world point; s in world units."""
        sx, sy = self.P(x, y, z)
        return transform(shapes, dx=sx, dy=sy, s=s * self.k, flip=flip)


# ================================================================ SVG output
class Out:
    """One SVG file being written: <defs> and body."""

    def __init__(self):
        self.defs, self.body, self.nid = [], [], 0

    def id(self, p):
        self.nid += 1
        return f"{p}{self.nid}"

    def stroke(self, d, col, w, op=1.0):
        """A stroked line; joined into the previous one when it is painted the same way (fully
        opaque only, so overlaps look the same): one element instead of many."""
        ws = n(w) if w >= .95 else f"{max(w, .2):.2f}".lstrip("0")
        key = (col, ws)
        if op >= .999 and self.body and getattr(self, "_last", None) == (key, len(self.body)):
            self.body[-1] = self.body[-1].replace('" fill="none"', d + '" fill="none"', 1)
        else:
            self.body.append(_stroke(d, col, w, op))
        self._last = (key, len(self.body)) if op >= .999 else None

    def svg(self, w, h):
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" width="{n(w)}" height="{n(h)}">'
                f"{defs}{''.join(self.body)}</svg>\n")


def _geom(sh, dx=0.0, dy=0.0):
    """The bare element (no paint) for a shape, moved by (dx, dy)."""
    if sh.ell is not None and sh.closed:
        cx, cy, rx, ry, rot = sh.ell
        cx, cy = cx + dx, cy + dy
        r = f' transform="rotate({n(rot)} {n(cx)} {n(cy)})"' if abs(rot) % 180 > .05 else ""
        return f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}"{r}'
    pts = sh.pts if not (dx or dy) else [(x + dx, y + dy) for x, y in sh.pts]
    return f'<path d="{pd(pts, sh.closed)}"'


def _ell_d(sh, dx=0.0, dy=0.0):
    """Path data of a shape (ellipses as two arcs), moved by (dx, dy)."""
    if sh.ell is not None:
        cx, cy, rx, ry, rot = sh.ell
        cx, cy = cx + dx, cy + dy
        a = math.radians(rot)
        p0 = (cx - rx * math.cos(a), cy - rx * math.sin(a))
        p1 = (cx + rx * math.cos(a), cy + rx * math.sin(a))
        return (f"M{n(p0[0])},{n(p0[1])}A{n(rx)},{n(ry)} {n(rot)} 1 0 {n(p1[0])},{n(p1[1])}"
                f"A{n(rx)},{n(ry)} {n(rot)} 1 0 {n(p0[0])},{n(p0[1])}Z")
    return pd([(x + dx, y + dy) for x, y in sh.pts], True)


def _op(op, attr="opacity"):
    return f' {attr}="{op:.2f}"'.replace("0.", ".") if op < .999 else ""


def _stroke(d, col, w, op=1.0, extra=""):
    ws = n(w) if w >= .95 else f"{max(w, .2):.2f}".lstrip("0")
    return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{ws}" '
            f'stroke-linecap="round" stroke-linejoin="round"{_op(op)}{extra}/>')


# ---------------------------------------------------------------- style A
SHADOW_A = "#3B5A7A"


def _render_a(o, shapes):
    for sh in shapes:
        col = sh.col
        if sh.tag == "shadow":
            o.body.append(f'{_geom(sh)} fill="{SHADOW_A}"{_op(.16 * sh.op, "fill-opacity")}/>')
            continue
        if sh.tag == "glow":
            o.body.append(f'{_geom(sh)} fill="{col}"{_op(.5 * sh.op, "fill-opacity")}/>')
            continue
        if not sh.closed:
            o.stroke(pd(sh.pts, False), col, sh.w, sh.op)
            continue
        x0, y0, x1, y1 = bbox(sh.pts)
        size = min(x1 - x0, y1 - y0)
        if sh.cel and size > 4:
            t = sh.cel * max(1.6, min(9.0, size * .16))
            vl, vd = (t * .3, t), (-t, -t * .25)
            k = o.id("k")
            if sh.ell is not None:
                o.defs.append(f'<clipPath id="{k}">{_geom(sh)}/></clipPath>')
                light = f'{_geom(sh)} fill="{a_light(col)}"/>'
                base = f'{_geom(sh, *vl)} fill="{col}"/>'
            else:
                p = o.id("p")
                o.defs.append(f'<path id="{p}" d="{pd(sh.pts)}"/><clipPath id="{k}"><use href="#{p}"/></clipPath>')
                light = f'<use href="#{p}" fill="{a_light(col)}"/>'
                base = f'<use href="#{p}" transform="translate({n(vl[0])} {n(vl[1])})" fill="{col}"/>'
            m = 2
            rect = f"M{n(x0 - m)},{n(y0 - m)}L{n(x1 + m)},{n(y0 - m)} {n(x1 + m)},{n(y1 + m)} {n(x0 - m)},{n(y1 + m)}Z"
            dark = f'<path d="{rect}{_ell_d(sh, *vd)}" fill-rule="evenodd" fill="{a_dark(col)}"/>'
            o.body.append(f'<g clip-path="url(#{k})"{_op(sh.op)}>{light}{base}{dark}</g>')
            continue
        if sh.face:
            o.body.append(f'{_geom(sh)} fill="{col}" stroke="{col}" stroke-width="1.2" stroke-linejoin="round"{_op(sh.op)}/>')
            continue
        o.body.append(f'{_geom(sh)} fill="{col}"{_op(sh.op)}/>')


# ---------------------------------------------------------------- style B (risograph)
INKS = {"Y": "#FFE800", "P": "#FF48B0", "T": "#00838A", "B": "#0078BF"}   # yellow, fluorescent pink, teal, blue
INK_ORDER = "YPTB"                     # the anchor of a mix is its first ink in this order
INK_OFF = {"Y": (0.0, 0.0), "P": (1.5, -1.1), "T": (-1.3, -.9), "B": (-1.3, 1.2)}   # misregistration
PAPER_B = "#FBF6EC"
PAPER_C = "#FFFFFF"
DENS = (.1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0)
# {A colour: {ink: density}}: force the mix for a colour (and the faces drawn from it). The game's
# blue leans to violet, which the nearest mix would print with pink; it is meant to read as blue.
RISO_OVERRIDE = {"#4C8DFF": {"B": .85}, "#5E9BFF": {"B": .75}, "#7FA8FF": {"B": .6}, "#7FC4FF": {"B": .5},
                 # lawn greens print as a fresh yellow-green (the nearest mix is a dull sage)
                 "#A3E487": {"Y": .7, "T": .3}, "#7FD06E": {"Y": .85, "T": .5}}
FACE_DENS = {"top": .55, "left": 1.0, "right": 1.35}   # riso iso faces: the same inks, lighter or heavier
GRAIN_AREA = 75.0                      # one grain speck per this many square units of full ink


def ink_tint(ink, dens):
    return mix("#FFFFFF", INKS[ink], dens)


def ink_mix(combo):
    """The colour of inks printed over each other (multiply), combo {ink: density}; {} = paper."""
    out = [255.0, 255.0, 255.0]
    for ink, d in combo.items():
        t = _rgb(ink_tint(ink, d))
        out = [a * b / 255 for a, b in zip(out, t)]
    if not combo:
        return PAPER_B
    return _hexrgb(*out)


def _lab(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in _rgb(c))
    X = (.4124 * r + .3576 * g + .1805 * b) / .95047
    Y = .2126 * r + .7152 * g + .0722 * b
    Z = (.0193 * r + .1192 * g + .9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


_PALETTE = []


def _palette():
    if _PALETTE:
        return _PALETTE
    combos = [{}]
    inks = INK_ORDER
    for a in inks:
        for d in DENS:
            combos.append({a: d})
    for i, a in enumerate(inks):
        for b in inks[i + 1:]:
            for da in DENS:
                for db in DENS:
                    combos.append({a: da, b: db})
    for i, a in enumerate(inks):
        for j, b in enumerate(inks[i + 1:], i + 1):
            for c in inks[j + 1:]:
                for da in DENS[4::2]:
                    for db in DENS[4::2]:
                        for dc in DENS[4::2]:
                            combos.append({a: da, b: db, c: dc})
    for c in combos:
        col = ink_mix(c)
        _PALETTE.append((c, col, _lab(col)))
    return _PALETTE


_SNAP = {}


def riso_snap(col):
    """(combo, colour): the ink mix nearest to an A colour (CIELAB, hue weighted over lightness)."""
    key = col.upper()
    if key in _SNAP:
        return _SNAP[key]
    if key in RISO_OVERRIDE:
        c = RISO_OVERRIDE[key]
        _SNAP[key] = (c, ink_mix(c))
        return _SNAP[key]
    L, a, b = _lab(col)
    if L > 96 and abs(a) < 3 and abs(b) < 5:
        _SNAP[key] = ({}, PAPER_B)
        return _SNAP[key]
    best = None
    for combo, c, (L2, a2, b2) in _palette():
        if not combo:
            continue
        dist = (L - L2) ** 2 + (a - a2) ** 2 + (b - b2) ** 2 + 40 * (len(combo) - 1)
        if best is None or dist < best[0]:
            best = (dist, combo, c)
    _SNAP[key] = (best[1], best[2])
    return _SNAP[key]


def riso_of(sh):
    """(combo, colour) for a shape: iso faces print their base colour's inks lighter (top) or
    heavier (right side); everything else snaps its own colour."""
    if sh.face and sh.base:
        combo, _ = riso_snap(sh.base)
        f = FACE_DENS[sh.face]
        combo = {i: min(1.0, round(d * f * 20) / 20) for i, d in combo.items()}
        combo = {i: d for i, d in combo.items() if d > .04}
        return combo, ink_mix(combo)
    return riso_snap(sh.col)


def _anchor(combo):
    for i in INK_ORDER:
        if i in combo:
            return i
    return None


def _halftone(o, sh, ink, dens, step=3.2):
    """Halftone dots of one ink inside a shape (riso shadows); big shapes get a coarser screen."""
    x0, y0, x1, y1 = bbox(sh.pts)
    step = max(step, math.sqrt(area(sh.pts)) / 34)
    pts = []
    yy, row = y0 + step / 2, 0
    while yy < y1:
        xx = x0 + (step / 2 if row % 2 else 0) + step / 4
        while xx < x1:
            if inside((xx, yy), sh.pts):
                pts.append((xx, yy))
            xx += step
        yy += step * .87
        row += 1
    if not pts:
        return
    o.body.append(f'<path d="{_dots(pts, .5)}" fill="none" stroke="{INKS[ink]}" stroke-width="{n(1.1 + 1.1 * dens)}" '
                  f'stroke-linecap="round"{_op(.9)}/>')


def _dots(pts, seg):
    """Path data of many short horizontal dashes (dots, specks): relative moves on a 0.1 grid, so
    the positions do not drift."""
    d, (px, py) = [], (0, 0)
    for i, (x, y) in enumerate(pts):
        x10, y10 = round(x * 10), round(y * 10)
        if i == 0:
            d.append(f"M{n(x10 / 10)},{n(y10 / 10)}h{n(seg)}")
        else:
            d.append(f"m{n((x10 - px) / 10)},{n((y10 - py) / 10)}h{n(seg)}")
        px, py = x10 + round(seg * 10), y10
    return "".join(d)


def _screen(o, sh, combo, step=5.0):
    """A big light area as a riso halftone: the paper, then rows of dots (tiny squares) of its main
    ink; two rows (even, odd) are drawn once and repeated with <use>, all clipped to the shape."""
    ink = max(combo, key=combo.get) if combo else "B"
    dens = combo.get(ink, .2)
    x0, y0, x1, y1 = bbox(sh.pts)
    side = .8 + 3.0 * dens
    k = o.id("k")
    o.defs.append(f'<clipPath id="{k}">{_geom(sh)}/></clipPath>')
    rows = []
    for j in (0, 1):
        r = o.id("r")
        sq = f"h{n(side)}v{n(side)}h-{n(side)}z"
        xs = [x0 + step * i + (step / 2 if j else 0) for i in range(int((x1 - x0) / step) + 2)]
        d = f"M{n(xs[0])},{n(y0)}{sq}" + "".join(f"m{n(step)},0{sq}" for _ in xs[1:])
        o.defs.append(f'<path id="{r}" d="{d}"/>')
        rows.append(r)
    o.body.append(f'{_geom(sh)} fill="{PAPER_B}"/>')
    uses = []
    j, yy = 0, 0.0
    while y0 + yy <= y1 + step:
        uses.append(f'<use href="#{rows[j % 2]}" y="{n(yy)}" fill="{INKS[ink]}"/>')
        yy += step * .87
        j += 1
    o.body.append(f'<g clip-path="url(#{k})">{"".join(uses)}</g>')


def _render_b(o, shapes, grain=True):
    specks = []
    for sh in shapes:
        if sh.tag == "screen":
            _screen(o, sh, riso_of(sh)[0])
            continue
        if sh.tag == "shadow":
            _halftone(o, sh, "B", .55 * sh.op)
            continue
        if sh.tag == "glow":
            combo, mc = riso_snap(sh.col)
            o.body.append(f'{_geom(sh)} fill="{mc}"{_op(.45 * sh.op, "fill-opacity")}/>')
            continue
        combo, mc = riso_of(sh)
        if not sh.closed:
            a = _anchor(combo)
            dx, dy = INK_OFF.get(a, (0, 0)) if len(combo) == 1 else (0, 0)
            o.stroke(pd([(x + dx, y + dy) for x, y in sh.pts], False), mc, sh.w, sh.op)
            continue
        x0, y0, x1, y1 = bbox(sh.pts)
        size = min(x1 - x0, y1 - y0)
        anc = _anchor(combo)
        fringes = [(i, combo[i]) for i in INK_ORDER if i in combo and i != anc] if size >= 3 else []
        if fringes and sh.ell is None:
            p = o.id("p")
            o.defs.append(f'<path id="{p}" d="{pd(sh.pts)}"/>')
            for i, d in fringes:
                dx, dy = INK_OFF[i]
                o.body.append(f'<use href="#{p}" transform="translate({n(dx)} {n(dy)})" fill="{ink_tint(i, d)}"{_op(sh.op)}/>')
            o.body.append(f'<use href="#{p}" fill="{mc}"{_op(sh.op)}/>')
        else:
            for i, d in fringes:
                o.body.append(f'{_geom(sh, *INK_OFF[i])} fill="{ink_tint(i, d)}"{_op(sh.op)}/>')
            o.body.append(f'{_geom(sh)} fill="{mc}"{_op(sh.op)}/>')
        cover = min(1.0, sum(combo.values()))      # light tints show little grain
        if grain and cover > .25 and size >= 2.5 and sh.op > .5:
            a_ = area(sh.pts)
            rnd = random.Random(sh.key() ^ 0x5EED)
            cnt = int(a_ * cover / GRAIN_AREA + rnd.random())
            tries = 0
            while cnt > 0 and tries < cnt * 4 + 8:
                tries += 1
                p_ = (rnd.uniform(x0, x1), rnd.uniform(y0, y1))
                if inside(p_, sh.pts):
                    specks.append(p_)
                    cnt -= 1
    if specks:
        specks.sort(key=lambda p: (round(p[1] / 40), p[0]))
        o.body.append(f'<path d="{_dots(specks, .8)}" fill="none" stroke="{PAPER_B}" stroke-width=".9"{_op(.85)}/>')


# ---------------------------------------------------------------- style C (crayon)
CRAYON_OVERRIDE = {}                   # {A colour: crayon colour}
HATCH = 3.1                            # hatch spacing (units)
HATCH_W = 3.0                          # hatch stroke width
WAX = "17 1.1 7 .9 25 1.3 11 .8"       # tiny gaps along each crayon stroke (wax on paper)
FACE_ANGLE = {"top": 18.0, "left": -58.0, "right": 58.0}


def crayon(c):
    """The crayon for an A colour: a bit more saturated; greys and whites stay."""
    if c.upper() in CRAYON_OVERRIDE:
        return CRAYON_OVERRIDE[c.upper()]
    h, L, S = _hls(c)
    if S < .12 or L > .95:
        return c
    return _hex(h, L * .97, min(1, S * 1.22))


def crayon_dark(c):
    h, L, S = _hls(c)
    if L > .95 or S < .12:
        return mix(c, "#4A5068", .62)
    return _hex(h, L * .6, min(1, S * 1.05))


def _render_c(o, shapes):
    for sh in shapes:
        if sh.tag in ("shadow", "glow"):
            continue
        rnd = random.Random(sh.key())
        col = crayon(sh.col)
        if not sh.closed:
            wp = wobble(sh.pts, .7, rnd, False, max(3, perimeter(sh.pts, False) / 60))
            o.stroke(pd(wp, False), col, max(sh.w, 2.2), sh.op)
            continue
        x0, y0, x1, y1 = bbox(sh.pts)
        bw, bh = x1 - x0, y1 - y0
        size = thickness(sh.pts)
        per = perimeter(sh.pts)
        light = _hls(col)[1]
        if size < 6.5 or light > .93 or light < .3:
            # small details, white and very dark parts: solid wax, a little wobbly
            if sh.ell is not None and size < 14:
                o.body.append(f'{_geom(sh)} fill="{col}"{_op(sh.op)}/>')
            elif len(sh.pts) <= 12:
                jp = [(x + rnd.uniform(-.35, .35), y + rnd.uniform(-.35, .35)) for x, y in sh.pts]
                o.body.append(f'<path d="{pd(jp)}" fill="{col}"{_op(sh.op)}/>')
            else:
                wp = wobble(sh.pts, min(.6, size * .06), rnd, True, max(2.2, per / 40))
                o.body.append(f'<path d="{pd(wp)}" fill="{col}"{_op(sh.op)}/>')
        else:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            ov = 1.7
            big = tf(sh.pts, s=1 + 2 * ov / bh, sx=1 + 2 * ov / bw, about=(cx, cy))
            k = o.id("k")
            if sh.ell is not None:
                ex, ey, rx, ry, rot = sh.ell
                clip_el = _geom(sh.copy(ell=(ex, ey, rx + ov, ry + ov, rot)))
            else:
                clip_el = _geom(sh.copy(pts=big, ell=None))
            o.defs.append(f'<clipPath id="{k}">{clip_el}/></clipPath>')
            ang = FACE_ANGLE.get(sh.face) if sh.face else rnd.choice([-1, 1]) * rnd.uniform(28, 62)
            la, elong = long_axis(resample(sh.pts, max(1.0, per / 80)))
            if elong > 1.8:              # long shapes: strokes run along them, as a child would colour
                ang = la + rnd.uniform(-14, 14)
            ang = math.radians(ang + rnd.uniform(-6, 6))
            ca, sa = math.cos(ang), math.sin(ang)
            cs = [((px - cx) * ca + (py - cy) * sa, -(px - cx) * sa + (py - cy) * ca) for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
            umin, umax = min(c[0] for c in cs) - 3, max(c[0] for c in cs) + 3
            vmin, vmax = min(c[1] for c in cs) - 2, max(c[1] for c in cs) + 2
            grow = 1 + min(.45, size / 260)       # big areas: a fatter crayon, wider strokes
            pts, v, side = [], vmin, 0
            while v <= vmax + HATCH * grow:
                u = (umin if side == 0 else umax) + rnd.uniform(-2, 2)
                pts.append((cx + u * ca - v * sa, cy + u * sa + v * ca))
                v += HATCH * grow * rnd.uniform(.8, 1.2)
                side ^= 1
            dash = f' stroke-dasharray="{WAX}" stroke-dashoffset="{rnd.randint(0, 40)}"' if size > 10 else ""
            o.body.append(f'<g clip-path="url(#{k})"><path d="{pd(pts, False, True)}" fill="none" stroke="{col}" stroke-width="{n(HATCH_W * grow)}" '
                          f'stroke-linecap="round" stroke-linejoin="round"{_op(.9 * sh.op, "stroke-opacity")}{dash}/></g>')
        if size < 4 or sh.tag in ("detail", "screen"):
            continue
        oc = crayon_dark(col) if light > .22 else col
        step = max(3.0, per / 64)
        for j in range(2 if 14 < size < 120 else 1):
            wp = wobble(sh.pts, .8 + .5 * j, rnd, True, step * (1 + .3 * j))
            o.stroke(pd(wp, True, size > 9), oc, (2.3 if size > 9 else 1.6) * (1 - .3 * j), (.95 - .3 * j) * sh.op)


# ---------------------------------------------------------------- render
def render(shapes, style, box=None, paper=False, grain=True):
    """One SVG file. box = (x0, y0, w, h) in the shapes' units: the viewBox becomes 0 0 w h and
    the shapes are moved by (-x0, -y0). paper=True paints the style's paper under everything (a
    whole background); objects stay see-through."""
    if box is None:
        x0, y0, x1, y1 = shapes_bbox(shapes)
        box = (x0 - PAD, y0 - PAD, x1 - x0 + 2 * PAD, y1 - y0 + 2 * PAD)
    shapes = [sh for sh in shapes if sh.only is None or style in sh.only]
    bx, by, bw, bh = box
    if bx or by:
        shapes = transform(shapes, dx=-bx, dy=-by)
    o = Out()
    if paper and style in ("b", "c"):
        o.body.append(f'<rect x="0" y="0" width="{n(bw)}" height="{n(bh)}" fill="{PAPER_B if style == "b" else PAPER_C}"/>')
    {"a": _render_a, "b": lambda o_, s_: _render_b(o_, s_, grain), "c": _render_c}[style](o, shapes)
    return o.svg(bw, bh)


# ================================================================ checks (flutter_svg rules + the contract)
FORBIDDEN = ("<filter", "<mask", "<style", "style=", "class=", "<text", "<image", "<foreignObject", "<pattern",
             "mix-blend-mode", "mask=", "filter=", "vector-effect", "<symbol", "<marker", "@import")
_TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_NARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
DRAWN = {"path", "ellipse", "circle", "rect", "polygon", "polyline", "line", "use"}
MAX_KB = 70
MAX_USE = 800


def check_path(d):
    """Raise ValueError unless d is path data flutter_svg reads (it drops the WHOLE picture over one
    bad path, where Chromium only skips that path)."""
    toks = _TOK.findall(d)
    if not toks or toks[0] not in "Mm":
        raise ValueError(f"path does not start with M: {d[:40]!r}")
    if len("".join(toks)) != len(re.sub(r"[\s,]", "", d)):
        raise ValueError(f"stray characters in path: {d[:60]!r}")
    i = 0
    while i < len(toks):
        c = toks[i]
        if not c.isalpha():
            raise ValueError(f"numbers without a command: {d[:60]!r}")
        i += 1
        k = _NARGS[c.upper()]
        j = i
        while j < len(toks) and not toks[j].isalpha():
            j += 1
        cnt = j - i
        if (k == 0 and cnt) or (k and (cnt == 0 or cnt % k)):
            raise ValueError(f"command {c} has {cnt} numbers: {d[:60]!r}")
        if c in "Aa":
            for q in range(i, j, 7):
                if toks[q + 3] not in ("0", "1") or toks[q + 4] not in ("0", "1"):
                    raise ValueError(f"arc flags must be 0 or 1: {d[:60]!r}")
        i = j


def check_svg(name, text, aspect=None):
    """flutter_svg rules: forbidden features, explicit paint on every drawn element (except paths
    in <defs> that a <use> paints), size, <use> count, parseable XML and path data, viewBox aspect.
    Returns the size in KB; raises SystemExit on a problem."""
    bad = [f for f in FORBIDDEN if f in text]
    if bad:
        raise SystemExit(f"{name}: uses {bad} (flutter_svg cannot draw these)")
    if text.count("<use") >= MAX_USE:
        raise SystemExit(f"{name}: {text.count('<use')} <use> (keep under {MAX_USE})")
    kb = len(text.encode()) / 1024
    if kb > MAX_KB:
        raise SystemExit(f"{name}: {kb:.0f} KB (keep under {MAX_KB} KB)")
    if not text.rstrip().endswith("</svg>"):
        raise SystemExit(f"{name}: cut short")
    root = ET.fromstring(text)
    ns = "{http://www.w3.org/2000/svg}"
    vb = [float(v) for v in root.get("viewBox").split()]
    if vb[0] or vb[1]:
        raise SystemExit(f"{name}: viewBox must start at 0 0")
    if aspect and abs(vb[2] / vb[3] - aspect) > .006 * aspect:
        raise SystemExit(f"{name}: viewBox aspect {vb[2] / vb[3]:.4f}, box needs {aspect:.4f}")
    defs = root.find(f"{ns}defs")
    in_defs = set()
    if defs is not None:
        for el in defs.iter():
            in_defs.add(id(el))
    for el in root.iter():
        tag = el.tag.replace(ns, "")
        d = el.get("d")
        if d is not None:
            try:
                check_path(d)
            except ValueError as e:
                raise SystemExit(f"{name}: {e}")
        if tag in DRAWN and id(el) not in in_defs and el.get("fill") is None and el.get("stroke") is None:
            raise SystemExit(f"{name}: a <{tag}> without fill/stroke")
    return kb


def write_svg(path, text, aspect=None):
    kb = check_svg(str(path), text, aspect)
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return kb


# ================================================================ a scene: things, variants, JSON
CHANGE_KINDS = {"art", "gone", "flip", "size"}
ART_TYPES = {"color", "swap", "count", "pattern", "face"}
HIDE_TINTS = tuple(TINT)


class Thing:
    def __init__(self, tid, zh, en, art, changes, big, z):
        self.id, self.zh, self.en, self.art, self.changes, self.big, self.z = tid, zh, en, art, changes, big, z
        self.box = None


class SceneArt:
    """Collects one scene and writes app/assets/art/<style>/<scene>/*.svg and
    app/assets/scenes/<scene>.json (docs/scenes.md).

        sa = SceneArt("park", "公園", "park")
        sa.background(lambda: shapes)                         # 600 x 600, never changes
        sa.thing("balloon", "氣球", "balloon",
                 art={"balloon": fn, "balloon_blue": fn_blue},  # first = the thing itself
                 changes=[color("balloon_blue", "氣球變藍色了！"), gone("氣球不見了！")],
                 big=True, z=320)
        sa.extra("butterfly", "蝴蝶", "butterfly", fn, "多了一隻蝴蝶！", z=400)
        sa.hide(cx, cy, size, z, "leaf")                       # a square spot (scene px)
        sa.lineup({"duck": fn, "duck_hat": fn2}, "小鴨子", odd=[...])
        sa.build()

    Art functions return shapes in scene px. A thing's box is the bounding box of ALL its
    variants plus PAD, so every variant fits the same box; each SVG's viewBox is that box."""

    def __init__(self, sid, zh, en):
        self.id, self.zh, self.en = sid, zh, en
        self.bg = None
        self.things, self.extras, self.hides = [], [], []
        self.line = None

    def background(self, fn):
        self.bg = fn

    def thing(self, tid, zh, en, art, changes, big=False, z=0):
        self.things.append(Thing(tid, zh, en, art, changes, big, z))

    def extra(self, tid, zh, en, fn, said, z=0, big=False):
        t = Thing(tid, zh, en, {tid: fn}, [], big, z)
        t.said = said
        self.extras.append(t)

    def hide(self, cx, cy, size, z, tint):
        assert tint in TINT, tint
        self.hides.append({"x": round(cx / SCENE, 4), "y": round(cy / SCENE, 4), "w": round(size / SCENE, 4),
                           "h": round(size / SCENE, 4), "z": z, "tint": tint})

    def lineup(self, art, zh, odd, w=.2, h=.2):
        self.line = {"art_fns": art, "zh": zh, "odd": odd, "w": w, "h": h}

    # ------------------------------------------------------------ geometry
    @staticmethod
    def _box(art):
        """Integer box (x0, y0, w, h) around all variants, padded."""
        bs = [shapes_bbox(fn()) for fn in art.values()]
        x0 = math.floor(min(b[0] for b in bs) - PAD)
        y0 = math.floor(min(b[1] for b in bs) - PAD)
        x1 = math.ceil(max(b[2] for b in bs) + PAD)
        y1 = math.ceil(max(b[3] for b in bs) + PAD)
        return x0, y0, x1 - x0, y1 - y0

    def boxes(self):
        """{id: (x0, y0, w, h)} of every thing and extra (scene px)."""
        out = {}
        for t in self.things + self.extras:
            if t.box is None:
                t.box = self._box(t.art)
            out[t.id] = t.box
        return out

    def json(self):
        self.boxes()

        def rel(t):
            x0, y0, w, h = t.box
            return {"x": round((x0 + w / 2) / SCENE, 5), "y": round((y0 + h / 2) / SCENE, 5),
                    "w": round(w / SCENE, 5), "h": round(h / SCENE, 5)}
        objs = []
        for t in self.things:
            o = {"id": t.id, "zh": t.zh, "en": t.en, **rel(t), "z": t.z, "big": t.big, "changes": t.changes}
            objs.append(o)
        extras = [{"id": t.id, "zh": t.zh, "en": t.en, **rel(t), "z": t.z, "big": t.big, "said": t.said} for t in self.extras]
        out = {"id": self.id, "zh": self.zh, "en": self.en, "objects": objs, "extras": extras, "hides": self.hides}
        if self.line:
            out["lineup"] = {"art": next(iter(self.line["art_fns"])), "zh": self.line["zh"],
                             "w": self.line["w"], "h": self.line["h"], "odd": self.line["odd"]}
        return out

    # ------------------------------------------------------------ writing
    def build(self, styles=STYLES, verbose=True):
        self.boxes()
        sizes = []
        for st in styles:
            d = ART / st / self.id
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob("*.svg"):
                old.unlink()
            if self.bg:
                sizes.append(("bg", st, write_svg(d / "bg.svg", render(self.bg(), st, (0, 0, SCENE, SCENE), paper=True), 1.0)))
            for t in self.things + self.extras:
                x0, y0, w, h = t.box
                for name, fn in t.art.items():
                    sizes.append((name, st, write_svg(d / f"{name}.svg", render(fn(), st, t.box), w / h)))
            if self.line:
                lb = self._square_box(self.line["art_fns"])
                for name, fn in self.line["art_fns"].items():
                    sizes.append((name, st, write_svg(d / f"{name}.svg", render(fn(), st, lb), 1.0)))
        SCENES.mkdir(parents=True, exist_ok=True)
        data = self.json()
        (SCENES / f"{self.id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        check_scene(self.id)
        if verbose:
            big = max(sizes, key=lambda s: s[2])
            print(f"{self.id}: {len(sizes)} files, largest {big[1]}/{big[0]} {big[2]:.1f} KB")
        return sizes

    @staticmethod
    def _square_box(art):
        x0, y0, w, h = SceneArt._box(art)
        s = max(w, h)
        return (x0 - (s - w) / 2, y0 - (s - h), s, s)


# change helpers (docs/scenes.md `changes`)
def color(art, said):
    return {"kind": "art", "type": "color", "art": art, "said": said}


def swap(art, said):
    return {"kind": "art", "type": "swap", "art": art, "said": said}


def count(art, said):
    return {"kind": "art", "type": "count", "art": art, "said": said}


def pattern(art, said):
    return {"kind": "art", "type": "pattern", "art": art, "said": said}


def face_(art, said):
    return {"kind": "art", "type": "face", "art": art, "said": said}


def gone(said):
    return {"kind": "gone", "said": said}


def flip(said):
    return {"kind": "flip", "said": said}


def size(scale, said):
    return {"kind": "size", "scale": scale, "said": said}


def _boxes_overlap(a, b):
    return a["x"] - a["w"] / 2 < b["x"] + b["w"] / 2 and b["x"] - b["w"] / 2 < a["x"] + a["w"] / 2 and \
        a["y"] - a["h"] / 2 < b["y"] + b["h"] / 2 and b["y"] - b["h"] / 2 < a["y"] + a["h"] / 2


def overlap_frac(a, b):
    """Overlap area / the smaller box's area."""
    ix = min(a["x"] + a["w"] / 2, b["x"] + b["w"] / 2) - max(a["x"] - a["w"] / 2, b["x"] - b["w"] / 2)
    iy = min(a["y"] + a["h"] / 2, b["y"] + b["h"] / 2) - max(a["y"] - a["h"] / 2, b["y"] - b["h"] / 2)
    if ix <= 0 or iy <= 0:
        return 0.0
    return ix * iy / min(a["w"] * a["h"], b["w"] * b["h"])


# ---------------------------------------------------------------- the app's puzzle picking (lib/core/puzzles.dart)
GAP = .015                              # Puzzles.gap: room between two differences of one puzzle
LEVELS = ("small", "mid", "big")        # 2-3, 3-4, 4-5 years
NEED = {"small": 1, "mid": 3, "big": 5}  # differences a puzzle must always find (TwoRound: 3 at mid, 5 at big)


def _from(c):
    """Change.from in scenes.dart: the youngest level a change is used for (0 small, 1 mid, 2 big)."""
    k = c["kind"]
    if k in ("gone", "extra"):
        return 0
    if k in ("flip", "size"):
        return 1
    return {"color": 0, "swap": 1}.get(c.get("type"), 2)


def _diff_box(t, c):
    b = (t["x"], t["y"], t["w"], t["h"])
    if c["kind"] != "size":
        return b
    s = c["scale"]
    bottom = t["y"] + t["h"] / 2
    l, r = min(t["x"] - t["w"] / 2, t["x"] - t["w"] * s / 2), max(t["x"] + t["w"] / 2, t["x"] + t["w"] * s / 2)
    top = min(t["y"] - t["h"] / 2, bottom - t["h"] * s)
    return ((l + r) / 2, (top + bottom) / 2, r - l, bottom - top)


def _overlaps(a, b, gap=GAP):
    return (a[0] - a[2] / 2 - gap < b[0] + b[2] / 2 and b[0] - b[2] / 2 - gap < a[0] + a[2] / 2 and
            a[1] - a[3] / 2 - gap < b[1] + b[3] / 2 and b[1] - b[3] / 2 - gap < a[1] + a[3] / 2)


def choices(data, level):
    """Puzzles.choices: (thing id, box, kind) of every difference a level may use."""
    li = LEVELS.index(level)
    out = []
    for t in data["objects"]:
        if t["big"] or level == "big":
            for c in t["changes"]:
                if _from(c) <= li:
                    out.append((t["id"], _diff_box(t, c), c["kind"] + "." + c.get("type", "")))
    for e in data["extras"]:
        if e.get("big") or level == "big":
            out.append((e["id"], _diff_box(e, {"kind": "extra"}), "extra"))
    return out


def pick(data, level, n_, rnd):
    """Puzzles.pick: n differences, one per thing, apart from each other, different kinds first."""
    alls = choices(data, level)
    rnd.shuffle(alls)
    picked = []
    for any_kind in (False, True):
        for d in alls:
            if len(picked) == n_:
                return picked
            if d in picked or any(p[0] == d[0] or _overlaps(p[1], d[1]) for p in picked):
                continue
            if not any_kind and any(p[2] == d[2] for p in picked):
                continue
            picked.append(d)
    return picked


def pick_stats(data, runs=4000):
    """{level: fewest differences found in `runs` random puzzles}."""
    out = {}
    for level in LEVELS:
        rnd = random.Random(7)
        out[level] = min(len(pick(data, level, 5, rnd)) for _ in range(runs))
    return out


def check_scene(sid):
    """The contract (docs/scenes.md) for one scene: JSON fields, every art file in all three styles,
    viewBox aspects equal to the boxes, `big` things wide enough, enough big colour/gone changes,
    hide tints that 小變 has art for. Raises SystemExit on a problem; returns the JSON."""
    p = SCENES / f"{sid}.json"
    data = json.loads(p.read_text())

    def fail(msg):
        raise SystemExit(f"{sid}.json: {msg}")
    for k in ("id", "zh", "en", "objects", "extras", "hides"):
        if k not in data:
            fail(f"missing {k}")
    ids = set()

    def need_art(name, aspect):
        for st in STYLES:
            f = ART / st / sid / f"{name}.svg"
            if not f.exists():
                fail(f"missing {f.relative_to(ROOT)}")
            vb = [float(v) for v in ET.parse(f).getroot().get("viewBox").split()]
            if abs(vb[2] / vb[3] - aspect) > .006 * aspect:
                fail(f"{st}/{name}.svg aspect {vb[2] / vb[3]:.4f} != box {aspect:.4f}")

    def need_box(o):
        for k in ("x", "y", "w", "h", "z"):
            if not isinstance(o.get(k), (int, float)):
                fail(f"{o.get('id')}: {k} missing")
        if not (0 <= o["x"] - o["w"] / 2 + 1e-6 and o["x"] + o["w"] / 2 <= 1 + 1e-6 and
                0 <= o["y"] - o["h"] / 2 + 1e-6 and o["y"] + o["h"] / 2 <= 1 + 1e-6):
            fail(f"{o.get('id', 'hide')}: box outside the scene")
    for st in STYLES:
        if not (ART / st / sid / "bg.svg").exists():
            fail(f"missing {st}/{sid}/bg.svg")
    big_easy = 0
    for o in data["objects"]:
        for k in ("id", "zh", "en", "big", "changes"):
            if k not in o:
                fail(f"object without {k}")
        if o["id"] in ids:
            fail(f"duplicate id {o['id']}")
        ids.add(o["id"])
        need_box(o)
        asp = o["w"] / o["h"]
        need_art(o["id"], asp)
        if o["big"] and o["w"] < .12:
            fail(f"{o['id']} is big but only {o['w']:.3f} wide (needs 0.12)")
        if not o["changes"]:
            fail(f"{o['id']} has no changes")
        for c in o["changes"]:
            if c.get("kind") not in CHANGE_KINDS:
                fail(f"{o['id']}: change kind {c.get('kind')}")
            if not c.get("said"):
                fail(f"{o['id']}: a change without `said`")
            if c["kind"] == "art":
                if c.get("type") not in ART_TYPES:
                    fail(f"{o['id']}: art change type {c.get('type')}")
                need_art(c["art"], asp)
            if c["kind"] == "size":
                if not isinstance(c.get("scale"), (int, float)) or c["scale"] <= 0:
                    fail(f"{o['id']}: size change without scale")
                bx = _diff_box(o, c)
                if bx[0] - bx[2] / 2 < -1e-6 or bx[0] + bx[2] / 2 > 1 + 1e-6 or bx[1] - bx[3] / 2 < -1e-6:
                    fail(f"{o['id']}: scaled by {c['scale']} it leaves the picture")
        if o["big"] and any(c["kind"] == "gone" or c.get("type") == "color" for c in o["changes"]):
            big_easy += 1
    if big_easy < 7:
        fail(f"only {big_easy} big things with a colour or gone change (need 7)")
    for e in data["extras"]:
        if e["id"] in ids:
            fail(f"duplicate id {e['id']}")
        ids.add(e["id"])
        need_box(e)
        need_art(e["id"], e["w"] / e["h"])
        if not e.get("said"):
            fail(f"extra {e['id']} without said")
    for h in data["hides"]:
        need_box(h)
        if h["tint"] not in HIDE_TINTS:
            fail(f"hide tint {h['tint']}")
        if abs(h["w"] - h["h"]) > 1e-6:
            fail("hide spots are square (小變's hide art is 200 x 200)")
        for st in STYLES:
            if not (ART / st / f"chameleon_hide_{h['tint']}.svg").exists():
                fail(f"missing {st}/chameleon_hide_{h['tint']}.svg")
    stats = pick_stats(data)
    for level, k in NEED.items():
        if stats[level] < k:
            fail(f"a {level} puzzle can end up with only {stats[level]} differences (needs {k}): spread the boxes apart")
    for h in data["hides"]:
        hb = (h["x"], h["y"], h["w"], h["h"])
        if not any(o["z"] > h["z"] and _overlaps(hb, (o["x"], o["y"], o["w"], o["h"]), 0) for o in data["objects"]):
            fail(f"hide {h['tint']} at z {h['z']}: nothing is drawn in front of any part of it")
    if "lineup" in data:
        lu = data["lineup"]
        need_art(lu["art"], lu["w"] / lu["h"])
        for c in lu["odd"]:
            if c["kind"] == "art":
                need_art(c["art"], lu["w"] / lu["h"])
            if not c.get("said"):
                fail("lineup odd without said")
    return data
