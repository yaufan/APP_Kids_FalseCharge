"""Writes the game's pictures (kit.py: one geometry, three styles) and checks them.

    python3 build.py chameleon                  # 小變: app/assets/art/<a|b|c>/chameleon_*.svg
    python3 build.py park                       # one scene (and 小變): art + app/assets/scenes/park.json
    python3 build.py all                        # 小變 and every scene_<name>.py in this folder
    python3 build.py check                      # only the checks (flutter_svg rules + docs/scenes.md)
    python3 build.py layout park                # boxes, overlaps and puzzle counts, without writing files
    python3 build.py preview park OUT.png       # contact sheet: the scene in a/b/c, a changed version,
                                                # 小變 hiding in it, 小變's poses and hides, the lineup;
                                                # also OUT_things.png: every thing and variant
    python3 build.py fluttercheck [park|chameleon|all]
                                                # draw every file with the real flutter_svg (a throw-away
                                                # Flutter project in /dev/shm, deleted afterwards) and with
                                                # Chromium, and compare them

A scene is a module scene_<name>.py with a function scene() that returns a kit.SceneArt and a list
PREVIEW_CHANGES [(thing id, change index or "extra:<id>")] used by `preview` for its changed version.
Previews and the comparison need Node.js with Playwright (Chromium); the comparison needs Flutter at
/home/user/flutter/bin (or $FLUTTER) and the pub cache that the sibling apps already filled.
"""
import sys

sys.dont_write_bytecode = True      # no __pycache__ in design/art

import html  # noqa: E402
import importlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

import kit  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
RENDER_JS = kit.ROOT / "docs" / "mockups" / "render.js"


def scene_names():
    return sorted(p.stem[len("scene_"):] for p in HERE.glob("scene_*.py"))


def scene_module(name):
    return importlib.import_module(f"scene_{name}")


def build_chameleon():
    import chameleon
    chameleon.build()


def build_scene(name):
    if not (kit.ART / "a" / "chameleon_wave.svg").exists():
        build_chameleon()
    scene_module(name).scene().build()


def check_all():
    """Re-check every file on disk and every scene JSON."""
    n_ = 0
    for st in kit.STYLES:
        for p in sorted((kit.ART / st).rglob("*.svg")):
            kit.check_svg(str(p.relative_to(kit.ROOT)), p.read_text())
            n_ += 1
    for p in sorted(kit.SCENES.glob("*.json")):
        kit.check_scene(p.stem)
    print(f"check: {n_} SVG files and {len(list(kit.SCENES.glob('*.json')))} scenes are fine")


# ================================================================ preview (HTML -> PNG with Chromium)
def _img(src, x, y, w, h, extra=""):
    return f'<img src="file://{src}" style="position:absolute;left:{x:.2f}px;top:{y:.2f}px;width:{w:.2f}px;height:{h:.2f}px;{extra}">'


def composite(sid, style, size, changes=(), extras=(), hides=False, rings=False):
    """The scene as the app composes it: bg, then every thing at its box in z order.
    changes: [(thing id, change dict)]; extras: [extra id]; hides: draw 小變 at every hide spot."""
    data = json.loads((kit.SCENES / f"{sid}.json").read_text())
    d = kit.ART / style / sid
    k = size
    items = []
    ch = dict(changes)
    for o in data["objects"]:
        c = ch.get(o["id"])
        if c and c["kind"] == "gone":
            continue
        art = c["art"] if c and c["kind"] == "art" else o["id"]
        w, h = o["w"] * k, o["h"] * k
        x, y = o["x"] * k - w / 2, o["y"] * k - h / 2
        extra = ""
        if c and c["kind"] == "flip":
            extra = "transform:scaleX(-1);"
        if c and c["kind"] == "size":
            extra = f"transform:scale({c['scale']});transform-origin:50% 100%;"
        items.append((o["z"], _img(d / f"{art}.svg", x, y, w, h, extra)))
    for e in data["extras"]:
        if e["id"] in extras:
            w, h = e["w"] * k, e["h"] * k
            items.append((e["z"], _img(d / f"{e['id']}.svg", e["x"] * k - w / 2, e["y"] * k - h / 2, w, h)))
    if hides:
        for hd in data["hides"]:
            w, h = hd["w"] * k, hd["h"] * k
            items.append((hd["z"], _img(kit.ART / style / f"chameleon_hide_{hd['tint']}.svg", hd["x"] * k - w / 2, hd["y"] * k - h / 2, w, h)))
    items.sort(key=lambda t: t[0])
    body = _img(d / "bg.svg", 0, 0, k, k) + "".join(t[1] for t in items)
    if rings:
        marks = [(o, c) for o in data["objects"] for (i, c) in changes if i == o["id"]]
        marks += [(e, None) for e in data["extras"] if e["id"] in extras]
        if hides:
            marks += [(hd, None) for hd in data["hides"]]
        for o, c in marks:
            s = c.get("scale", 1) if c and c["kind"] == "size" else 1
            w, h = o["w"] * k * s, o["h"] * k * s
            x = o["x"] * k - w / 2
            y = o["y"] * k + o["h"] * k / 2 - h
            body += (f'<div style="position:absolute;left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;height:{h:.1f}px;'
                     f'border:2px dashed #E0245E;border-radius:6px;box-sizing:border-box"></div>')
    return f'<div style="position:relative;width:{k}px;height:{k}px;overflow:hidden;border-radius:12px">{body}</div>'


def _cell(inner, label):
    return f'<div class="cell">{inner}<div class="lb">{html.escape(label)}</div></div>'


def _page(rows, width):
    css = ("body{margin:0;background:#E9EDF3;font:15px sans-serif;color:#334}"
           ".row{display:flex;flex-wrap:wrap;gap:14px;padding:10px 14px}"
           ".cell{background:#fff;border-radius:14px;padding:8px}.lb{text-align:center;padding-top:4px}"
           "h2{margin:10px 14px 0;font-size:18px}")
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body style="width:{width}px">{"".join(rows)}</body></html>'


def shoot(page_html, out, width, height=None):
    """HTML -> PNG with Playwright (full page)."""
    with tempfile.TemporaryDirectory(dir="/dev/shm") as tmp:
        hp = pathlib.Path(tmp) / "page.html"
        hp.write_text(page_html)
        js = pathlib.Path(tmp) / "shot.js"
        js.write_text("""const { chromium } = require('playwright');
(async () => { const [inp, out, w] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: 800 }, deviceScaleFactor: 1 });
  await p.goto('file://' + inp); await p.waitForTimeout(400); await p.screenshot({ path: out, fullPage: true }); await b.close(); })();""")
        pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["node", str(js), str(hp), str(out), str(width)], check=True, cwd=tmp)


def preview(sid, out):
    mod = scene_module(sid)
    data = json.loads((kit.SCENES / f"{sid}.json").read_text())
    objs = {o["id"]: o for o in data["objects"]}
    changes, extras = [], []
    for tid, which in mod.PREVIEW_CHANGES:
        if str(which).startswith("extra:"):
            extras.append(which[6:])
        else:
            changes.append((tid, objs[tid]["changes"][which]))
    boxes = [(tid, kit._diff_box(objs[tid], c)) for tid, c in changes]
    boxes += [(e["id"], (e["x"], e["y"], e["w"], e["h"])) for e in data["extras"] if e["id"] in extras]
    for i, (a, ba) in enumerate(boxes):
        for b, bb in boxes[i + 1:]:
            if kit._overlaps(ba, bb):
                print(f"preview: the changes of {a} and {b} overlap (the app would not pick them together)")
    S = 560
    rows = ["<h2>" + html.escape(f"{data['zh']} {sid}: a / b / c") + "</h2>"]
    rows.append('<div class="row">' + "".join(_cell(composite(sid, st, S), st) for st in kit.STYLES) + "</div>")
    said = "、".join(c["said"] for _, c in changes) + "、" + "、".join(e["said"] for e in data["extras"] if e["id"] in extras)
    rows.append("<h2>" + html.escape("changed: " + said) + "</h2>")
    rows.append('<div class="row">' + "".join(_cell(composite(sid, st, S, changes, extras, rings=(st == "a")), st + " changed")
                                              for st in kit.STYLES) + "</div>")
    rows.append("<h2>小變 hiding (" + ", ".join(h["tint"] for h in data["hides"]) + ")</h2>")
    rows.append('<div class="row">' + "".join(_cell(composite(sid, st, S, hides=True), st + " hides") for st in kit.STYLES) + "</div>")
    import chameleon
    rows.append("<h2>小變: poses and hides</h2>")
    for st in kit.STYLES:
        cells = "".join(_cell(f'<img src="file://{kit.ART / st / f"chameleon_{p}.svg"}" width="150" height="150">', f"{st} {p}")
                        for p in chameleon.POSES)
        cells += "".join(_cell(f'<img src="file://{kit.ART / st / f"chameleon_hide_{t}.svg"}" width="110" height="110" '
                               f'style="background:{kit.TINT[t]}33">', f"{st} {t}") for t in kit.TINT)
        rows.append(f'<div class="row">{cells}</div>')
    if "lineup" in data:
        lu = data["lineup"]
        names = [lu["art"]] + [c["art"] for c in lu["odd"] if c["kind"] == "art"]
        rows.append("<h2>" + html.escape(f"lineup: {lu['zh']} ({', '.join(c['said'] for c in lu['odd'])})") + "</h2>")
        cells = ""
        for st in kit.STYLES:
            for nm in names:
                cells += _cell(f'<img src="file://{kit.ART / st / sid / f"{nm}.svg"}" width="120" height="120">', f"{st} {nm}")
            cells += _cell(f'<img src="file://{kit.ART / st / sid / f"{lu["art"]}.svg"}" width="120" height="120" style="transform:scaleX(-1)">', f"{st} flip")
        rows.append(f'<div class="row">{cells}</div>')
    shoot(_page(rows, 3 * (S + 30) + 20), out, 3 * (S + 30) + 20)
    # every thing and its variants
    rows = []
    for st in kit.STYLES:
        cells = ""
        for o in data["objects"] + data["extras"]:
            arts = [o["id"]] + [c["art"] for c in o.get("changes", []) if c["kind"] == "art"]
            k = 130 / max(o["w"], o["h"])
            for a in arts:
                w, h = o["w"] * k, o["h"] * k
                cells += _cell(f'<div style="width:{w:.0f}px;height:{h:.0f}px;background:#F4F6F0">'
                               f'<img src="file://{kit.ART / st / sid / f"{a}.svg"}" width="{w:.0f}" height="{h:.0f}"></div>', f"{st} {a}")
        rows.append(f"<h2>{st}</h2><div class='row'>{cells}</div>")
    o2 = str(out).rsplit(".", 1)[0] + "_things.png"
    shoot(_page(rows, 1800), o2, 1800)
    print(out, o2)


# ================================================================ flutter_svg against Chromium
DART_TEST = r"""
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/widgets.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('render svgs', (tester) async {
    final lines = File('list.txt').readAsLinesSync().where((l) => l.trim().isNotEmpty);
    final failed = <String>[];
    for (final line in lines) {
      final p = line.split('|');
      final w = int.parse(p[2]), h = int.parse(p[3]);
      await tester.runAsync(() async {
        try {
          final info = await vg.loadPicture(SvgStringLoader(File(p[0]).readAsStringSync()), null);
          final rec = ui.PictureRecorder();
          final c = Canvas(rec);
          c.scale(w / info.size.width, h / info.size.height);
          c.drawPicture(info.picture);
          final img = await rec.endRecording().toImage(w, h);
          final bytes = await img.toByteData(format: ui.ImageByteFormat.png);
          File(p[1]).writeAsBytesSync(bytes!.buffer.asUint8List());
          info.picture.dispose();
        } catch (e) {
          failed.add('${p[0]}: $e');
        }
      });
    }
    File('failed.txt').writeAsStringSync(failed.join('\n'));
  });
}
"""

CHROME_JS = r"""
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const lines = fs.readFileSync(process.argv[2], 'utf8').split('\n').filter(l => l.trim());
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 400, height: 400 }, deviceScaleFactor: 1 });
  for (const line of lines) {
    const [inp, out, w, h] = line.split('|');
    const svg = fs.readFileSync(inp);
    await page.setViewportSize({ width: +w, height: +h });
    await page.setContent(`<html><body style="margin:0;background:transparent"><img style="display:block;width:${w}px;height:${h}px" src="data:image/svg+xml;base64,${svg.toString('base64')}"></body></html>`);
    await page.waitForFunction(() => document.images[0].complete);
    await page.screenshot({ path: out, omitBackground: true });
  }
  await browser.close();
})();
"""


def fluttercheck(which="all", keep=False, px=260):
    """Draw every SVG with flutter_svg (the app's renderer) and with Chromium; report the files whose
    pictures differ. A throw-away Flutter project in /dev/shm is made for it and deleted after."""
    import numpy as np
    from PIL import Image
    files = []
    for st in kit.STYLES:
        if which in ("all", "chameleon"):
            files += sorted((kit.ART / st).glob("chameleon_*.svg"))
        for sid in (scene_names() if which == "all" else [which]):
            if (kit.ART / st / sid).is_dir():
                files += sorted((kit.ART / st / sid).glob("*.svg"))
    flutter = pathlib.Path(os.environ.get("FLUTTER", "/home/user/flutter/bin")) / "flutter"
    work = pathlib.Path(tempfile.mkdtemp(prefix="svgcheck_", dir="/dev/shm"))
    try:
        (work / "lib").mkdir()
        (work / "test").mkdir()
        (work / "out").mkdir()
        (work / "pubspec.yaml").write_text("name: svgcheck\npublish_to: 'none'\nversion: 0.0.1\nenvironment:\n  sdk: ^3.13.7\n"
                                           "dependencies:\n  flutter:\n    sdk: flutter\n  flutter_svg: ^2.3.0\n"
                                           "dev_dependencies:\n  flutter_test:\n    sdk: flutter\n")
        (work / "lib" / "main.dart").write_text("void main() {}\n")
        (work / "test" / "render_test.dart").write_text(DART_TEST)
        (work / "shot.js").write_text(CHROME_JS)
        fl, cr = [], []
        for i, f in enumerate(files):
            vb = [float(v) for v in kit.ET.parse(f).getroot().get("viewBox").split()]
            s = px / max(vb[2], vb[3])
            w, h = max(8, round(vb[2] * s)), max(8, round(vb[3] * s))
            fl.append(f"{f}|{work / 'out' / f'{i}_f.png'}|{w}|{h}")
            cr.append(f"{f}|{work / 'out' / f'{i}_c.png'}|{w}|{h}")
        (work / "list.txt").write_text("\n".join(fl))
        (work / "crlist.txt").write_text("\n".join(cr))
        subprocess.run([str(flutter), "pub", "get", "--offline"], cwd=work, check=True, capture_output=True)
        r = subprocess.run([str(flutter), "test", "test/render_test.dart"], cwd=work, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit("flutter test failed")
        failed = (work / "failed.txt").read_text().strip()
        if failed:
            print("flutter_svg could not draw:\n" + failed)
        subprocess.run(["node", str(work / "shot.js"), str(work / "crlist.txt")], cwd=work, check=True)
        rows = []
        for i, f in enumerate(files):
            a = work / "out" / f"{i}_f.png"
            b = work / "out" / f"{i}_c.png"
            if not a.exists():
                rows.append((1.0, 1.0, f))
                continue
            A = np.asarray(Image.open(a).convert("RGBA")).astype(float)
            B = np.asarray(Image.open(b).convert("RGBA")).astype(float)

            def flat(X):   # over white
                al = X[..., 3:4] / 255
                return X[..., :3] * al + 255 * (1 - al)
            D = np.abs(flat(A) - flat(B)).max(axis=2)
            # differences in single pixels are anti-aliasing; count pixels whose 3x3 neighbourhood all differ
            big = D > 60
            core = big[1:-1, 1:-1] & big[:-2, 1:-1] & big[2:, 1:-1] & big[1:-1, :-2] & big[1:-1, 2:]
            rows.append((core.mean(), D.mean() / 255, f))
        rows.sort(key=lambda r: (-r[0], -r[1]))
        bad = [r for r in rows if r[0] > .004]
        print(f"fluttercheck: {len(files)} files; worst:")
        for frac, mean, f in rows[:8]:
            print(f"  {frac * 100:6.2f}% solid differences, mean {mean * 100:.2f}%  {f.relative_to(kit.ROOT)}")
        if keep:
            print("kept", work)
        if bad:
            raise SystemExit(f"{len(bad)} files draw differently in flutter_svg (more than 0.4% of the picture)")
        print("fluttercheck: flutter_svg draws every file like Chromium")
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def layout(sid):
    """Print each thing's box (scene px), the boxes that overlap, and how many differences the app's
    puzzle picking always finds (kit.pick_stats), without writing any file."""
    sa = scene_module(sid).scene()
    sa.boxes()
    data = sa.json()
    items = data["objects"] + data["extras"]
    for o in items:
        x0, y0 = (o["x"] - o["w"] / 2) * 600, (o["y"] - o["h"] / 2) * 600
        print(f"  {o['id']:10s} {'BIG' if o['big'] else '   '} x {x0:5.0f}..{x0 + o['w'] * 600:5.0f}  y {y0:5.0f}..{y0 + o['h'] * 600:5.0f}"
              f"  w {o['w']:.3f} h {o['h']:.3f} z {o['z']}")
    print("overlapping (with the app's gap):")
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if kit._overlaps((a["x"], a["y"], a["w"], a["h"]), (b["x"], b["y"], b["w"], b["h"])):
                tag = "BIG+BIG" if a["big"] and b["big"] else ""
                print(f"  {a['id']} / {b['id']} {tag}")
    print("fewest differences found:", kit.pick_stats(data))


def main(argv):
    if not argv:
        print(__doc__)
        return
    cmd = argv[0]
    if cmd == "chameleon":
        build_chameleon()
    elif cmd == "all":
        build_chameleon()
        for s in scene_names():
            build_scene(s)
        check_all()
    elif cmd == "check":
        check_all()
    elif cmd == "layout":
        layout(argv[1])
    elif cmd == "preview":
        preview(argv[1], argv[2])
    elif cmd == "fluttercheck":
        fluttercheck(argv[1] if len(argv) > 1 else "all", keep="--keep" in argv)
    elif cmd in scene_names():
        build_scene(cmd)
    else:
        raise SystemExit(f"unknown: {cmd} (scenes: {', '.join(scene_names())})")


if __name__ == "__main__":
    main(sys.argv[1:])
