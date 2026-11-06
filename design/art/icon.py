"""眼尖尖大挑戰's app icon: 小變 the chameleon in the game's toy look (style a, 等角小模型風: flat
shading, light and dark crescents on round things, no outlines), drawn with kit.py and chameleon.py
like the rest of the art. Three candidates:

    glass  小變's face close up; a big red magnifying glass in front of one eye makes it huge.
           Bright sky blue.
    bush   小變 hiding in a leafy bush on a little grass tile: his body is the bush's colour, only
           his eyes and his curly tail show, and a sparkle says "here!". Lilac.
    cards  Two little picture cards, the same but for a red and a blue balloon, with 小變 peeking
           over them. Sunny yellow.

    python3 icon.py preview OUT.png              # the three side by side: big, as the phone cuts them
                                                 # (round, rounded square) at 96 and 48 px, and at 48 px
                                                 # on a light and a dark home screen next to the sibling
                                                 # apps' icons (when their repos are on this machine)
    python3 icon.py export [glass|bush|cards]    # writes the Android and iOS icons into app/ (default glass)

export writes
- Android, full square art: app/android/app/src/main/res/mipmap-{mdpi..xxxhdpi}/ic_launcher.png
  (48..192 px, opaque).
- Android adaptive icon (API 26+): mipmap-anydpi-v26/ic_launcher.xml, with
  drawable-{mdpi..xxxhdpi}/ic_launcher_foreground.png and ic_launcher_background.png (108 dp canvas;
  the whole subject stays inside the central 66 dp circle, the part every launcher mask shows).
- iOS: every PNG listed in app/ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json, at its
  size, opaque (no alpha).

Everything is drawn in 200 x 200 units (like 小變's own art), rendered at 1024 px by Chromium (Node.js
with Playwright; one browser for all the pictures) and scaled down with Pillow. No randomness: the same
script gives the same bytes. Scratch files go to /dev/shm and are deleted.
"""
import json
import math
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

import chameleon as CH
import kit
from kit import Iso, Sh, crs, line, mix, oval, rrect, sparkle, spiral, transform, tube

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
APP = ROOT / "app"
RES = APP / "android" / "app" / "src" / "main" / "res"
IOS = APP / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
FONT = APP / "assets" / "fonts" / "jf-openhuninn-2.1.ttf"

U = 200                              # drawing units across the icon
C = 1024                             # rendered size, scaled down from here
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
FULL_R = .44 * U                     # full square art (legacy Android, iOS): the subject's radius
SAFE_R = 33 / 108 * U * .97          # adaptive foreground: inside the central 66 dp circle of 108 dp
VIEW = 72 / 108                      # how much of the adaptive canvas a launcher shows

G, EYE, INK = CH.G, CH.EYE, CH.INK
LEAF = kit.TINT["leaf"]
LEAF_D = kit.tone(LEAF, .7, 1.05)    # the darker line on a hiding 小變 (as chameleon.hide does it)
RED, BLUE, YELLOW = "#FF5A5F", "#4C8DFF", "#FFD84A"
WHITE = "#FFFFFF"
GRASS, GRASS_RIM, SOIL, SKY = "#A3E487", "#7FD06E", "#EBB57E", "#D4F0FF"


# ================================================================ the three subjects (their own units)
def eye(x, y, r, look=(0.0, 0.0)):
    """A white eye of radius r with a dark pupil looking along `look` (-1..1) and two highlights
    (the shapes chameleon.head uses, at any size)."""
    k = r / 17.5
    px, py = x + look[0] * 7 * k, y + look[1] * 7 * k
    return [oval(x, y, r, col=EYE),
            oval(px, py, 10.2 * k, col=INK),
            oval(px - 3.6 * k, py - 4 * k, 3.7 * k, col=EYE, tag="detail"),
            oval(px + 3.6 * k, py + 3.4 * k, 1.6 * k, col=EYE, tag="detail")]


def glass():
    """小變's head (chameleon.head) with a big magnifying glass held in front of his right eye (the
    viewer's left): the glass shows his skin and his eye 1.6 times bigger, looking at you."""
    o = CH.head("wave", (-.35, .3))
    cx, cy, R, r = -33, -117, 45, 35.5          # the glass: centre, rim, glass
    a = math.radians(132)                       # the handle runs down to the left
    ux, uy = math.cos(a), math.sin(a)

    def along(t0, t1, k=10):
        return [(cx + ux * (t0 + (t1 - t0) * i / k), cy + uy * (t0 + (t1 - t0) * i / k)) for i in range(k + 1)]
    o.append(Sh(tube(along(R - 8, R + 32), 19, 22), YELLOW, cel=.8))
    o.append(Sh(tube(along(R - 8, R + 8, 4), 24, 24), RED, cel=.6))
    o.append(oval(cx, cy, R, col=RED, cel=1.0))
    o.append(oval(cx, cy, r + 2.6, col=kit.a_dark(RED)))
    o.append(oval(cx, cy, r, col=G, cel=.45))
    o += eye(cx + 1.5, cy + 1, 28, look=(.55, .45))
    o.append(oval(cx, cy, r, col="#CFEFFF", op=.16))
    rg = r - 7.5
    o.append(line([(cx + rg * math.cos(math.radians(d)), cy + rg * math.sin(math.radians(d))) for d in range(196, 254, 4)],
                  WHITE, 5.4, op=.85))
    o.append(oval(cx + rg * math.cos(math.radians(266)), cy + rg * math.sin(math.radians(266)), 2.9, col=WHITE, op=.85))
    return o


def bush():
    """A little grass tile with a round leafy bush; 小變, the bush's colour, hides in it: his eye turrets
    peek over the leaves, his curly tail sticks out at the side. Sparkles say where."""
    iso = Iso(k=1.0, ox=0, oy=-48)
    T = 96                                      # the tile, in world units (its middle is (0, 0) on screen)
    o = []
    o += iso.box(0, 0, -21, T, T, 14, SOIL)[:2]
    o += iso.box(0, 0, -7, T, T, 7, GRASS_RIM, top=GRASS)
    o.append(oval(4, 6, 74, 26, col="#3B5A7A", tag="shadow"))
    for x, y, col in ((74, 93, WHITE), (92, 78, YELLOW)):      # two little flowers at the front corner
        sx, sy = iso.P(x, y)
        o += [oval(sx + 4.4 * math.cos(math.radians(d)), sy - 4 + 4.4 * math.sin(math.radians(d)) * .7, 3.3, col=col, tag="detail")
              for d in range(0, 360, 72)]
        o.append(oval(sx, sy - 4, 2.4, col="#FFB13D", tag="detail"))

    def blob(x, y, r):
        return [oval(x, y, r, col=LEAF, cel=.8)]
    for x, y, r in ((-36, -26, 32), (36, -28, 32), (0, -40, 36)):
        o += blob(x, y, r)
    # 小變's tail, rolled up, coming out of the bush on the right
    tl = spiral((82, -42), 27, 1.6, 200, 90, shrink=.84)
    o.append(Sh(tube(tl, 19, 7), LEAF, cel=.7))
    o.append(line(spiral((82, -42), 21, 1.45, 212, 80, shrink=.88), LEAF_D, 3.2))
    # his crest and his eye turrets
    o.append(Sh(crs([(-13, -84), (-7, -106), (6, -110), (16, -99), (13, -82)]), LEAF, cel=.6))
    for ex, ey in ((-25, -74), (25, -76)):
        o.append(oval(ex, ey, 26, col=LEAF, cel=.75))
        o += eye(ex - 2, ey - 1, 19, look=(-.75, .15))
        o.append(line([(ex + 22 * math.cos(math.radians(d)), ey + 22 * math.sin(math.radians(d))) for d in range(200, 330, 10)],
                      LEAF_D, 3, op=.8))
    # leaves in front of him, then the front of the bush
    for x, y, r in ((-40, -38, 21), (34, -42, 19)):
        o += blob(x, y, r)
    for x, y, r in ((-48, -4, 28), (48, -6, 28), (0, -6, 36)):
        o += blob(x, y, r)
    for x, y, rr in ((-30, -14, 3.6), (10, 10, 3.2), (44, -16, 3.6), (-58, 4, 3), (60, 0, 2.8), (-12, -30, 2.8), (28, -44, 2.6)):
        o.append(oval(x, y, rr, col=LEAF_D, op=.55, tag="detail"))
    # sparkles: here he is!
    o.append(Sh(sparkle(64, -100, 18, 0), YELLOW))
    o.append(Sh(sparkle(84, -76, 8, 0), WHITE))
    o.append(Sh(sparkle(-66, -92, 9, 0), WHITE))
    return o


def bottom_round(x, y, w, h, r, k=5):
    """A rectangle with only its two bottom corners rounded."""
    pts = [(x, y), (x + w, y)]
    for cx, a0 in ((x + w - r, 0), (x + r, 90)):
        for j in range(k + 1):
            a = math.radians(a0 + 90 * j / k)
            pts.append((cx + r * math.cos(a), y + h - r + r * math.sin(a)))
    return pts


def card(col):
    """A little picture card (its middle at 0, 0): sky, grass and a balloon of colour col."""
    w, h, r = 80, 100, 12
    o = [Sh([(x + 5, y + 10) for x, y in rrect(-w / 2, -h / 2, w, h, r)], "#3B5A7A", tag="shadow"),
         Sh([(x, y + 5) for x, y in rrect(-w / 2, -h / 2, w, h, r)], "#C9D6EA"),
         Sh(rrect(-w / 2, -h / 2, w, h, r), WHITE),
         Sh(rrect(-31, -41, 62, 82, 7), SKY),
         Sh(bottom_round(-31, 16, 62, 25, 7), GRASS)]
    o.append(line(crs([(0, 2), (4, 12), (-2, 22), (1, 30)], 6, closed=False), "#7C86A8", 1.8))
    o.append(Sh(crs([(-4.5, 3), (4.5, 3), (0, -5)], 4), col))
    o.append(Sh(crs([(0, -1), (11, -6), (17, -20), (14, -35), (0, -42), (-14, -35), (-17, -20), (-11, -6)]), col, cel=1.0))
    o.append(oval(-7, -28, 3.4, 6.4, col=WHITE, rot=25, op=.8, tag="detail"))
    return o


def cards():
    """Two picture cards side by side, a red balloon on one and a blue one on the other; 小變 peeks
    over them from behind, holding their tops."""
    o = []
    s = 1.0
    hd = CH.head("wave", (0.0, .85))
    o += transform(hd, s=s, dx=0, dy=-50 + 119 * s)
    o += transform(card(RED), rot=-7, dx=-44, dy=16)
    o += transform(card(BLUE), rot=7, dx=44, dy=16)
    for x, y, a in ((-24, -34, 0), (24, -34, 0)):
        o += CH.mitten(x, y, a, 7.2)
    o.append(Sh(sparkle(78, -66, 12, 0), WHITE))
    o.append(Sh(sparkle(-80, -60, 8, 0), WHITE))
    return o


# ================================================================ backgrounds (full 200 x 200, opaque)
def gradient(top, bottom):
    return (f'<defs><linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="1" stop-color="{bottom}"/></linearGradient></defs>'
            f'<rect width="{U}" height="{U}" fill="url(#bgg)"/>')


def deco(view, items):
    """Background sparkles and dots, placed from the middle so the adaptive layer (of which a launcher
    shows only the middle `view`) keeps them in sight."""
    o = []
    for kind, dx, dy, r, col, op in items:
        x, y, rr = U / 2 + dx * view, U / 2 + dy * view, r * view
        if kind == "spark":
            o.append(Sh(sparkle(x, y, rr, 0), col, op=op))
        else:
            o.append(oval(x, y, rr, col=col, op=op))
    return o


def bg_glass(view):
    return gradient("#2FA8F2", "#8AD6FF"), deco(view, [
        ("spark", 70, -72, 11, WHITE, .95), ("spark", -78, 62, 7, WHITE, .85), ("dot", 80, -44, 3, WHITE, .7),
        ("dot", -60, 80, 3, WHITE, .6), ("dot", 84, 70, 4, WHITE, .5)])


def bg_bush(view):
    return gradient("#CDBDFF", "#9B86F2"), deco(view, [
        ("dot", -76, -70, 4, WHITE, .5), ("dot", 80, 74, 3, WHITE, .5), ("spark", -80, 64, 7, WHITE, .7)])


def bg_cards(view):
    return gradient("#FFE476", "#FFBE3B"), deco(view, [
        ("dot", -78, -76, 4, WHITE, .55), ("dot", 80, 78, 4, WHITE, .5), ("spark", 78, -78, 8, WHITE, .8),
        ("spark", -80, 72, 6, WHITE, .7)])


CANDIDATES = {
    "glass": (glass, bg_glass, "1 放大鏡"),
    "bush": (bush, bg_bush, "2 躲在草叢裡"),
    "cards": (cards, bg_cards, "3 兩張卡片"),
}
DEFAULT = "glass"


# ================================================================ placing and drawing
def enclosing(shapes):
    """The centre and radius of (nearly) the smallest circle around the shapes (ground shadows left
    out; strokes count with their width)."""
    pts, pad = [], 0.0
    for sh in shapes:
        if sh.tag == "shadow":
            continue
        pts += sh.pts
        if not sh.closed:
            pad = max(pad, sh.w / 2)
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    hull = []                                   # convex hull (monotone chain): fewer points to search
    for seq in (pts, pts[::-1]):
        part = []
        for p in seq:
            while len(part) >= 2 and ((part[-1][0] - part[-2][0]) * (p[1] - part[-2][1])
                                      - (part[-1][1] - part[-2][1]) * (p[0] - part[-2][0])) <= 0:
                part.pop()
            part.append(p)
        hull += part[:-1]
    x0, y0 = min(p[0] for p in hull), min(p[1] for p in hull)
    x1, y1 = max(p[0] for p in hull), max(p[1] for p in hull)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i in range(1, 3000):                    # Badoiu-Clarkson: step towards the farthest point
        fx, fy = max(hull, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        cx += (fx - cx) / (i + 1)
        cy += (fy - cy) / (i + 1)
    r = max(math.hypot(x - cx, y - cy) for x, y in hull) + pad
    return cx, cy, r


def placed(name, radius):
    """The candidate's subject moved and scaled so it sits in the middle and reaches `radius`."""
    shapes = CANDIDATES[name][0]()
    cx, cy, r = enclosing(shapes)
    s = radius / r
    return transform(shapes, dx=U / 2 - cx * s, dy=U / 2 - cy * s, s=s)


def inner(svg):
    """The inside of the <svg> element kit.render wrote."""
    return svg[svg.index(">") + 1:svg.rindex("</svg>")]


def doc(px, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {U} {U}" width="{px}" height="{px}">{body}</svg>'


def subject_svg(name, radius, px=C):
    return doc(px, inner(kit.render(placed(name, radius), "a", box=(0, 0, U, U))))


def background_svg(name, view, px=C):
    under, shapes = CANDIDATES[name][1](view)
    return doc(px, under + (inner(kit.render(shapes, "a", box=(0, 0, U, U))) if shapes else ""))


RENDER_JS = """
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  for (const [inp, out, px] of jobs) {
    const page = await browser.newPage({ viewport: { width: px, height: px }, deviceScaleFactor: 1 });
    await page.goto('file://' + inp);
    await page.screenshot({ path: out, omitBackground: true });
    await page.close();
  }
  await browser.close();
})();
"""


def render_all(svgs):
    """{key: svg text} -> {key: RGBA image}, all drawn by one Chromium."""
    shm = "/dev/shm" if pathlib.Path("/dev/shm").is_dir() else None
    with tempfile.TemporaryDirectory(dir=shm, prefix="icon_") as tmp:
        tmp = pathlib.Path(tmp)
        jobs = []
        for i, (key, text) in enumerate(svgs.items()):
            src, out = tmp / f"{i}.svg", tmp / f"{i}.png"
            src.write_text(text)
            jobs.append([str(src), str(out), C])
        (tmp / "jobs.json").write_text(json.dumps(jobs))
        (tmp / "r.js").write_text(RENDER_JS)
        subprocess.run(["node", str(tmp / "r.js"), str(tmp / "jobs.json")], check=True)
        return {key: Image.open(tmp / f"{i}.png").convert("RGBA").copy() for i, key in enumerate(svgs)}


def art(names):
    """{name: (full square art RGB, adaptive background RGB, adaptive foreground RGBA)}."""
    svgs = {}
    for nm in names:
        svgs[(nm, "bg")] = background_svg(nm, 1.0)
        svgs[(nm, "fg")] = subject_svg(nm, FULL_R)
        svgs[(nm, "abg")] = background_svg(nm, VIEW)
        svgs[(nm, "afg")] = subject_svg(nm, SAFE_R)
    im = render_all(svgs)
    out = {}
    for nm in names:
        full = Image.alpha_composite(im[(nm, "bg")], im[(nm, "fg")]).convert("RGB")
        out[nm] = (full, im[(nm, "abg")].convert("RGB"), im[(nm, "afg")])
    return out


def launcher_view(bg, fg):
    """The adaptive icon as a launcher shows it: both layers, the middle 72 dp of 108."""
    whole = Image.alpha_composite(bg.convert("RGBA"), fg).convert("RGB")
    k = C * 18 / 108
    return whole.crop((round(k), round(k), round(C - k), round(C - k)))


def resized(img, px):
    return img.resize((px, px), Image.LANCZOS)


def mask(kind, px):
    s = px * 4
    m = Image.new("L", (s, s), 0)
    dr = ImageDraw.Draw(m)
    if kind == "round":
        dr.ellipse((0, 0, s - 1, s - 1), fill=255)
    elif kind == "squircle":
        pts = []
        for i in range(720):
            t = 2 * math.pi * i / 720
            c, si = math.cos(t), math.sin(t)
            pts.append((s / 2 + s / 2 * math.copysign(abs(c) ** (2 / 5), c), s / 2 + s / 2 * math.copysign(abs(si) ** (2 / 5), si)))
        dr.polygon(pts, fill=255)
    else:                                       # iOS-like rounded square
        dr.rounded_rectangle((0, 0, s - 1, s - 1), radius=s * .225, fill=255)
    return m.resize((px, px), Image.LANCZOS)


# ================================================================ preview
SIBLINGS = (("畫畫小鎮", "APP_Kids_Paint"), ("字母寵物", "app_kids_paint_for_learning_writing"), ("動物小餐廳", "app_kids_cook"),
            ("小卡認天下", "app_kids_card_game"), ("想一想樂園", "app_kids_brainstorming"))


def font(size):
    try:
        return ImageFont.truetype(str(FONT), size)
    except OSError:
        return ImageFont.load_default()


def siblings():
    out = []
    for zh, repo in SIBLINGS:
        p = ROOT.parent / repo / "app" / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset" / "Icon-App-1024x1024@1x.png"
        if p.is_file():
            out.append((zh, Image.open(p).convert("RGB")))
    return out


def home_screen(icons, dark, W):
    """A strip of a phone's home screen: icons (label, image) at 48 px, round, with their names."""
    H = 104
    top, bottom = ("#3A3550", "#1E1B2B") if dark else ("#F6EFE6", "#E3EEF8")
    strip = Image.new("RGB", (W, H))
    dr = ImageDraw.Draw(strip)
    for y in range(H):
        dr.line([(0, y), (W, y)], fill=mix(top, bottom, y / (H - 1)))
    step = W / len(icons)
    f = font(13)
    for i, (label, im) in enumerate(icons):
        x = round(step * i + step / 2 - 24)
        strip.paste(resized(im, 48), (x, 18), mask("round", 48))
        tw = dr.textlength(label, font=f)
        dr.text((x + 24 - tw / 2, 74), label, font=f, fill="#FFFFFF" if dark else "#3B3550")
    return strip


def preview(out):
    names = list(CANDIDATES)
    arts = art(names)
    views = {nm: launcher_view(arts[nm][1], arts[nm][2]) for nm in names}
    col, pad, big = 400, 24, 300
    W = pad * 2 + col * len(names)
    H = 24 + big + 60 + 120 + 24 + 104 * 2 + 40
    sheet = Image.new("RGB", (W, H), "#FFFFFF")
    dr = ImageDraw.Draw(sheet)
    f = font(30)
    for i, nm in enumerate(names):
        x0 = pad + col * i
        v, full = views[nm], arts[nm][0]
        sheet.paste(resized(v, big), (x0 + (col - big) // 2, 24), mask("squircle", big))
        label = CANDIDATES[nm][2] + ("（建議）" if nm == DEFAULT else "")
        tw = dr.textlength(label, font=f)
        dr.text((x0 + col / 2 - tw / 2, 24 + big + 12), label, font=f, fill="#3B3550")
        y = 24 + big + 64
        x = x0 + 34
        for kind, im, s in (("round", v, 96), ("square", full, 96), ("round", v, 48), ("square", full, 48)):
            sheet.paste(resized(im, s), (x, y + 96 - s), mask(kind, s))
            x += s + 26
    y = 24 + big + 60 + 120 + 24
    icons = siblings() + [(CANDIDATES[nm][2], views[nm]) for nm in names]
    sheet.paste(home_screen(icons, False, W - 2 * pad), (pad, y))
    sheet.paste(home_screen(icons, True, W - 2 * pad), (pad, y + 104))
    sheet.save(out)
    print(out)


# ================================================================ export
ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""


def export(name):
    full, bg, fg = art([name])[name]
    written = []
    for d, k in DENSITIES.items():
        mip = RES / f"mipmap-{d}"
        mip.mkdir(parents=True, exist_ok=True)
        resized(full, round(48 * k)).save(mip / "ic_launcher.png")
        dr = RES / f"drawable-{d}"
        dr.mkdir(parents=True, exist_ok=True)
        resized(fg, round(108 * k)).save(dr / "ic_launcher_foreground.png")
        resized(bg, round(108 * k)).save(dr / "ic_launcher_background.png")
        written += [mip / "ic_launcher.png", dr / "ic_launcher_foreground.png", dr / "ic_launcher_background.png"]
    anydpi = RES / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    (anydpi / "ic_launcher.xml").write_text(ADAPTIVE_XML)
    written.append(anydpi / "ic_launcher.xml")
    contents = json.loads((IOS / "Contents.json").read_text())
    sizes = {}
    for image in contents["images"]:
        if image.get("filename"):
            px = round(float(image["size"].split("x")[0]) * float(image["scale"].rstrip("x")))
            if sizes.setdefault(image["filename"], px) != px:
                sys.exit(f"{image['filename']} is listed at two sizes in Contents.json")
    for fname, px in sizes.items():
        resized(full, px).convert("RGB").save(IOS / fname)
        written.append(IOS / fname)
    manifest = (APP / "android" / "app" / "src" / "main" / "AndroidManifest.xml").read_text()
    if 'android:icon="@mipmap/ic_launcher"' not in manifest:
        print("note: AndroidManifest.xml's android:icon is not @mipmap/ic_launcher")
    for p in written:
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "export":
        nm = sys.argv[2] if len(sys.argv) >= 3 else DEFAULT
        if nm not in CANDIDATES:
            sys.exit(f"unknown icon {nm!r}: one of {', '.join(CANDIDATES)}")
        export(nm)
    elif len(sys.argv) >= 3 and sys.argv[1] == "preview":
        preview(sys.argv[2])
    else:
        print(__doc__)
