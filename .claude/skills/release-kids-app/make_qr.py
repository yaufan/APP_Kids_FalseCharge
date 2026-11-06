"""A QR code with a title and the link printed under it (the download QR codes).

    python3 tools/make_qr.py URL OUT.png "標題" "說明" "印在下面的網址（| 換行）"

Needs `pip install segno pillow` and a Chinese font (WenQuanYi Zen Hei on the
cloud machine; set QR_FONT to another .ttc/.ttf). Check the result decodes,
e.g. with OpenCV's cv2.QRCodeDetector, before sending it.
"""
import os
import sys

import segno
from PIL import Image, ImageDraw, ImageFont

url, out, title, sub, shown = sys.argv[1:6]
m = [list(r) for r in segno.make(url, error="q", micro=False).matrix]
box, quiet = 12, 4
qs = (len(m) + 2 * quiet) * box
W, top, bottom = max(qs, 640), 110, 130
img = Image.new("RGB", (W, top + qs + bottom), "white")
d = ImageDraw.Draw(img)
ox = (W - qs) // 2
for y, row in enumerate(m):
    for x, v in enumerate(row):
        if v:
            x0, y0 = ox + (x + quiet) * box, top + (y + quiet) * box
            d.rectangle([x0, y0, x0 + box - 1, y0 + box - 1], fill="#2b2b2b")
font = os.environ.get("QR_FONT", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
big, small, tiny = (ImageFont.truetype(font, s) for s in (48, 26, 19))


def center(text, y, f, fill):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


center(title, 28, big, "#e0594a")
center(sub, top + qs - 6, small, "#555555")
for i, line in enumerate(shown.split("|")):
    center(line, top + qs + 36 + i * 26, tiny, "#777777")
img.save(out, optimize=True)
