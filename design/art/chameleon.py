"""小變 the chameleon, in the three styles (kit.py draws them).

    app/assets/art/<a|b|c>/chameleon_<pose>.svg        pose: wave, think, cheer, magic, sleep (200 x 200)
    app/assets/art/<a|b|c>/chameleon_hide_<tint>.svg   tint: leaf, sand, wood, red, blue, white (200 x 200)

He is drawn in his own units with the origin between his feet (y up is negative), at the same size
and place in every pose (feet at the bottom middle-left, room at the top right for his magic), so the
app can swap poses without him jumping. The hiding versions are a crouched 小變 whose body, crest and
tail take the tint colour (kit.TINT, the same colours the scenes use for leaves, sand, wood...);
only his eyes and the dark line of his curly tail stand out.
"""
import math

import kit
from kit import Sh, crs, line, oval, spiral, sparkle, star_pts, transform, tube

G = "#5ACB6C"        # body
GL = "#D2F28C"       # belly and spots
GD = "#3BAA5A"       # darker green lines
EYE = "#FFFFFF"
INK = "#2B3158"
CHEEK = "#FF9DB6"
TONGUE = "#FF7598"
POSES = ("wave", "think", "cheer", "magic", "sleep")
ORIGIN = (86.0, 196.0)     # where his feet are in the 200 x 200 picture
SCALE = .98


def mitten(x, y, a=0.0, r=6.6, col=G):
    dx, dy = math.cos(math.radians(a)) * r * .62, math.sin(math.radians(a)) * r * .62
    return [oval(x - dx, y - dy, r, col=col), oval(x + dx, y + dy, r, col=col)]


def arm(pts, col=G, w=11.5):
    return Sh(tube(crs(pts, 8, closed=False), w, w * .9), col, cel=.6)


def head(pose, look=(0.0, 0.0)):
    """His head (crest, face, eye turrets), neck at about (0, -74)."""
    hd = []
    hd.append(Sh(crs([(-14, -144), (-6, -162), (8, -165), (18, -152), (16, -140)]), G, cel=.7))
    hd.append(Sh(crs([(-52, -108), (-46, -86), (-24, -74), (0, -71), (26, -74), (48, -86), (54, -108), (44, -134),
                      (20, -148), (-20, -148), (-44, -134)]), G, cel=1.0))
    hd.append(oval(2, -153, 3, col=GL, tag="detail"))
    hd.append(oval(-10, -138, 3.6, col=GL, tag="detail"))
    hd.append(oval(13, -141, 2.6, col=GL, tag="detail"))
    lx, ly = look
    for ex in (-30, 30):
        hd.append(oval(ex, -119, 24.5, col=G, cel=.75))
        hd.append(line([(ex + 21 * math.cos(math.radians(a)), -119 + 21 * math.sin(math.radians(a))) for a in range(200, 300, 8)],
                       GD, 2.2, op=.55))
        if pose == "cheer":
            hd.append(oval(ex, -118, 17.5, col=EYE))
            hd.append(line([(ex - 9, -114), (ex - 4.5, -123), (ex, -125.5), (ex + 4.5, -123), (ex + 9, -114)], INK, 4))
        elif pose == "sleep":
            # closed eyes: the lid (a lighter green) and a soft curved line of lashes
            hd.append(oval(ex, -117, 17.5, col=GL, cel=.4))
            hd.append(line([(ex - 11, -116), (ex - 5, -111), (ex, -110), (ex + 5, -111), (ex + 11, -116)], INK, 3.6))
        else:
            hd.append(oval(ex + lx * 2.6, -118 + ly * 2.6, 17.5, col=EYE))
            px, py = ex + lx * 7, -118 + ly * 7
            hd.append(oval(px, py, 10.2, col=INK))
            hd.append(oval(px - 3.6, py - 4, 3.7, col=EYE, tag="detail"))
            hd.append(oval(px + 3.6, py + 3.4, 1.6, col=EYE, tag="detail"))
    hd.append(oval(-6, -101, 1.8, col=GD, tag="detail"))
    hd.append(oval(6, -101, 1.8, col=GD, tag="detail"))
    if pose in ("cheer", "magic"):
        hd.append(Sh(crs([(-19, -93), (-10, -88), (0, -87), (10, -88), (19, -93), (12, -80), (0, -76), (-12, -80)]), INK))
        hd.append(Sh(crs([(-9, -80.5), (0, -86), (9, -80.5), (0, -77)]), TONGUE, tag="detail"))
    elif pose == "think":
        hd.append(line(crs([(-14, -88), (-6, -91), (2, -89), (10, -92)], 6, closed=False), INK, 3.2))
    elif pose == "sleep":
        hd.append(line(crs([(-9, -89), (0, -85), (9, -89)], 6, closed=False), INK, 3.0))
    else:
        hd.append(Sh(crs([(17, -91), (24, -85.5), (22, -79), (16, -82.5)]), TONGUE, tag="detail"))
        hd.append(line(crs([(-25, -95), (-10, -86), (6, -85), (20, -90), (27, -97)], 8, closed=False), INK, 3.4))
    hd.append(oval(-41, -97, 7.5, 4.6, col=CHEEK, op=.85, tag="detail"))
    hd.append(oval(41, -97, 7.5, 4.6, col=CHEEK, op=.85, tag="detail"))
    return hd


def sleeping():
    """Curled up on the ground, chin on his hands, tail wrapped round, eyes closed."""
    o = []
    tl = spiral((70, -26), 24, 1.4, 150, 70)
    o.append(Sh(tube(tl, 16, 6), G, cel=.7))
    for t in (.15, .35, .55):
        x, y = tl[int(t * (len(tl) - 1))]
        o.append(oval(x, y, 3 - t * 2, col=GL, tag="detail"))
    o.append(Sh(crs([(-40, -2), (-50, -26), (-36, -52), (-4, -64), (34, -60), (62, -42), (70, -18), (58, -2), (10, 2)]), G, cel=1.0))
    for x, y, r in ((10, -48, 4), (34, -40, 3.4), (-14, -30, 3), (48, -22, 3)):
        o.append(oval(x, y, r, col=GL, tag="detail"))
    o.append(Sh(crs([(30, -4), (52, -10), (74, -6), (80, 2), (52, 4)]), G, cel=.5))
    hd = transform(head("sleep"), s=.78, rot=-8, about=(0, -74), dx=-46, dy=58)
    o += hd
    o += mitten(-62, -6, 0, 7.2) + mitten(-30, -5, 0, 7.2)
    return o


def body(pose):
    """The standing 小變 (in his own units). Returns shapes, back to front."""
    if pose == "sleep":
        return sleeping()
    o = []
    # tail: from the back of the body, up, round and curling in underneath
    tl = spiral((64, -32), 25, 1.45, 205, 70)
    o.append(Sh(tube(tl, 15, 5.5), G, cel=.7))
    for t in (.12, .3, .48, .66):
        x, y = tl[int(t * (len(tl) - 1))]
        o.append(oval(x, y, 3.2 - t * 2.2, col=GL, tag="detail"))
    o += [oval(-17, -5, 13, 7, col=G, cel=.5), oval(17, -5, 13, 7, col=G, cel=.5)]
    o.append(Sh(crs([(-30, -12), (-15, -3), (0, -1), (15, -3), (30, -12), (36, -36), (30, -62), (14, -77),
                     (-14, -77), (-30, -62), (-36, -36)]), G, cel=1.0))
    o.append(oval(0, -36, 18.5, 24, col=GL, cel=.5))
    for y in (-42, -32, -22):
        o.append(line(crs([(-14, y), (0, y + 3), (14, y)], 6, closed=False), GD, 1.6, op=.5))
    o.append(oval(-28, -44, 4, col=GL, tag="detail"))
    o.append(oval(28, -30, 3.4, col=GL, tag="detail"))
    front = []
    if pose == "wave":
        o.append(arm([(-25, -60), (-38, -48), (-36, -34)]))
        o += mitten(-36, -31, 0)
        o.append(arm([(24, -62), (44, -76), (52, -100)]))
        o += mitten(53, -104, 90)
        for k in (0, 1):
            r = 14 + k * 8
            o.append(line([(70 + r * math.cos(math.radians(a)) * .6, -104 + r * math.sin(math.radians(a))) for a in range(-50, 40, 6)],
                          GD, 2.6, op=.7))
    elif pose == "cheer":
        o.append(arm([(-24, -62), (-44, -82), (-50, -108)]))
        o += mitten(-51, -112, 90)
        o.append(arm([(24, -62), (44, -82), (50, -108)]))
        o += mitten(51, -112, 90)
    elif pose == "magic":
        o.append(arm([(-25, -60), (-38, -48), (-36, -34)]))
        o += mitten(-36, -31, 0)
        o.append(arm([(24, -62), (46, -72), (68, -88)]))
        o += mitten(71, -91, 40)
    elif pose == "think":
        o.append(arm([(-25, -60), (-34, -46), (-22, -36)]))
        o += mitten(-19, -34, 20)
        front.append(arm([(26, -60), (40, -66), (30, -84)], w=10.5))
        front += mitten(26, -87, 60, 6.4)
    look = {"wave": (.15, .1), "think": (.55, -.7), "magic": (.7, -.35), "cheer": (0, 0)}[pose]
    hd = head(pose, look)
    if pose == "think":
        hd = transform(hd, rot=-6, about=(0, -78))
    o += hd + front
    # what is around him
    if pose == "think":
        for (x, y, r) in ((52, -150, 4.2), (64, -166, 6.2), (82, -184, 8.6)):
            o.append(oval(x, y, r, col="#EAF4FF", cel=.6))
    if pose == "magic":
        burst = crs(star_pts(27, 17, 76, -158, 11, -80), 3)
        o.append(Sh(burst, "#FFE27A", cel=.4))
        o.append(Sh(crs(star_pts(17, 11, 76, -158, 9, -70), 3), "#FFFFFF", tag="detail"))
        for (x, y, r, c) in ((84, -112, 8.5, "#FFC93C"), (100, -100, 6, "#FF8FB8"), (60, -124, 5.5, "#7FC4FF"),
                             (104, -128, 5, "#B48CFF"), (52, -102, 4, "#FFC93C")):
            o.append(Sh(sparkle(x, y, r, 8), c, tag="detail"))
    if pose == "cheer":
        for (x, y, r, c) in ((-72, -128, 7, "#FFC93C"), (72, -132, 7, "#FF8FB8"), (-64, -150, 4.5, "#7FC4FF"), (66, -154, 4.5, "#FFC93C")):
            o.append(Sh(sparkle(x, y, r, 0), c, tag="detail"))
    return o


def hide(tint):
    """小變 crouched and coloured like `tint`: a round body with the eye turrets on top and the curly
    tail rolled up at his side; eyes (white, dark pupils) and the tail's darker spiral are what shows."""
    T = kit.TINT[tint]
    h, L, S = kit._hls(T)
    Td = kit.tone(T, .7, 1.05) if L < .9 else kit.mix(T, "#8C96B0", .5)
    o = []
    o.append(Sh(crs([(-64, -4), (-70, -34), (-58, -70), (-30, -92), (0, -98), (30, -92), (56, -72), (66, -36), (62, -4), (0, 0)]), T, cel=1.0))
    o.append(Sh(crs([(-16, -96), (-8, -116), (6, -120), (16, -108), (14, -94)]), T, cel=.6))
    for x, y, r in ((-36, -40, 4.2), (-6, -24, 3.4), (26, -50, 4.6), (34, -20, 3.2), (-46, -70, 3)):
        o.append(oval(x, y, r, col=Td, op=.6, tag="detail"))
    o += [oval(-34, -6, 12, 6.5, col=T, cel=.5), oval(18, -6, 12, 6.5, col=T, cel=.5)]
    for x in (-42, -34, -26, 10, 18, 26):
        o.append(line([(x, -4), (x, 0)], Td, 1.6, op=.7))
    # the tail: out of his right side, rolled up into a big curl in front
    tl = spiral((78, -40), 28, 1.7, 205, 90, shrink=.86)
    o.append(Sh(tube(tl, 19, 6), T, cel=.7))
    o.append(line(spiral((78, -40), 22, 1.55, 215, 80, shrink=.9), Td, 2.8))
    for ex, ey in ((-26, -96), (26, -98)):
        o.append(oval(ex, ey, 23, col=T, cel=.75))
        o.append(oval(ex - 2, ey - 1, 16.5, col=EYE))
        o.append(oval(ex - 6, ey + 1, 9.6, col=INK))
        o.append(oval(ex - 9.4, ey - 3, 3.5, col=EYE, tag="detail"))
        o.append(oval(ex - 2.6, ey + 4.4, 1.5, col=EYE, tag="detail"))
        o.append(line([(ex + 19 * math.cos(math.radians(a)), ey + 19 * math.sin(math.radians(a))) for a in range(200, 330, 10)], Td, 2.4, op=.8))
    return o


def place(shapes, pose=""):
    """His units -> the 200 x 200 picture (same place and size for every standing pose; the
    sleeping one is centred)."""
    if pose == "sleep":
        x0, y0, x1, y1 = kit.shapes_bbox(shapes)
        s = min(SCALE * 1.15, 190 / (x1 - x0))
        return transform(shapes, dx=100 - (x0 + x1) / 2 * s, dy=ORIGIN[1] - y1 * s, s=s)
    return transform(shapes, dx=ORIGIN[0], dy=ORIGIN[1], s=SCALE)


def place_hide(shapes):
    x0, y0, x1, y1 = kit.shapes_bbox(shapes)
    s = 188 / max(x1 - x0, y1 - y0)
    return transform(shapes, dx=100 - (x0 + x1) / 2 * s, dy=196 - y1 * s, s=s)


def build(styles=kit.STYLES, verbose=True):
    sizes = []
    for st in styles:
        d = kit.ART / st
        for p in POSES:
            sizes.append(kit.write_svg(d / f"chameleon_{p}.svg", kit.render(place(body(p), p), st, (0, 0, kit.CHAR, kit.CHAR)), 1.0))
        for t in kit.TINT:
            sizes.append(kit.write_svg(d / f"chameleon_hide_{t}.svg", kit.render(place_hide(hide(t)), st, (0, 0, kit.CHAR, kit.CHAR)), 1.0))
    if verbose:
        print(f"chameleon: {len(sizes)} files, largest {max(sizes):.1f} KB")
    return sizes


if __name__ == "__main__":
    build()
