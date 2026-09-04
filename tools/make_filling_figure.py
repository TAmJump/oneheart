"""
How the artwork fills up.

The source artworks are already photomosaics: every tile is a portrait pushed
towards the colour that place needs. This figure reuses those real tiles, so
the 'taken' places are genuine portrait tiles from the artwork itself.

Open places are drawn as the flat colour of that position, which is what the
artwork ships with when a place has not been taken by the deadline.
"""
import random
from PIL import Image, ImageDraw, ImageFont

random.seed(23)

SRC   = "/home/claude/art/ONE EARTH.png"
FONT  = "/home/claude/interfont/extras/ttf/Inter-%s.ttf"
SRCN  = 36          # grid the source preview was rendered at
GRID  = 50          # 50 x 50 = 2,500 places
CELL  = 26
SIDE  = GRID * CELL

YELLOW = (255, 217, 0)
INK    = (17, 17, 17)

src = Image.open(SRC).convert("RGB")

# ---- harvest the real portrait tiles out of the source artwork -------------
step = src.width / SRCN
tiles = []
for gy in range(SRCN):
    for gx in range(SRCN):
        x0, y0 = round(gx * step), round(gy * step)
        t = src.crop((x0 + 3, y0 + 3, x0 + round(step) - 3, y0 + round(step) - 3))
        if min(t.size) < 8:
            continue
        # keep only tiles with real photographic detail
        ex = t.convert("L").resize((16, 16))
        px = list(ex.getdata())
        if max(px) - min(px) > 55:
            tt = t.resize((CELL, CELL), Image.LANCZOS)
            st = tt.resize((1, 1)).getpixel((0, 0))
            tiles.append((tt, st))
print("portrait tiles harvested:", len(tiles))

# normalise each tile so its own colour cast does not fight the target
import colorsys
def norm(t):
    im, mean = t
    lift = tuple(128 - v for v in mean)
    return Image.eval(im, lambda v: v)  # keep pixels, we correct at paste time


colours = src.resize((GRID, GRID), Image.LANCZOS)


def place(colour):
    """A taken place: a real portrait tile shifted onto the colour needed."""
    tl, mean = random.choice(tiles)
    # move the tile's own average onto the target colour, keeping its detail
    px = tl.split()
    out = []
    for ch, m, c in zip(px, mean, colour):
        d = c - m
        out.append(ch.point(lambda v, d=d: max(0, min(255, int(v * 0.80 + 0.20 * 128) + d - 26))))
    shifted = Image.merge("RGB", out)
    solid = Image.new("RGB", tl.size, colour)
    return Image.blend(shifted, solid, 0.10)


def render(taken):
    canvas = Image.new("RGB", (SIDE, SIDE))
    d = ImageDraw.Draw(canvas)
    cells = [(x, y) for y in range(GRID) for x in range(GRID)]
    random.shuffle(cells)
    filled = set(cells[:taken])

    for y in range(GRID):
        for x in range(GRID):
            c = colours.getpixel((x, y))
            box = (x * CELL, y * CELL)
            if (x, y) in filled:
                canvas.paste(place(c), box)
            else:
                canvas.paste(Image.new("RGB", (CELL, CELL), c), box)
                # a hairline so an open place still reads as a place
                d.rectangle([box[0], box[1], box[0] + CELL - 1, box[1] + CELL - 1],
                            outline=tuple(max(0, v - 8) for v in c), width=1)
    return canvas


# ---- sheet ----------------------------------------------------------------
steps = [(100, "100 places taken"),
         (600, "600 places taken"),
         (1500, "1,500 places taken"),
         (2500, "2,500 — every place taken")]

TH, PAD, GAP = 300, 40, 30          # thumb size, outer padding, gap
LBL = 92
W = PAD * 2 + TH * 4 + GAP * 3
H = PAD * 2 + TH + LBL

sheet = Image.new("RGB", (W, H), YELLOW)
d = ImageDraw.Draw(sheet)
f_lab = ImageFont.truetype(FONT % "Bold", 21)

for i, (n, label) in enumerate(steps):
    im = render(n).resize((TH, TH), Image.LANCZOS)
    x = PAD + i * (TH + GAP)
    sheet.paste(im, (x, PAD))
    d.rectangle([x - 3, PAD - 3, x + TH + 2, PAD + TH + 2], outline=INK, width=3)
    w = d.textlength(label, font=f_lab)
    d.text((x + (TH - w) / 2, PAD + TH + 24), label, font=f_lab, fill=INK)

sheet.save("/home/claude/oneheart/images/filling.jpg", quality=92,
           optimize=True, progressive=True)
print("saved", sheet.size)

# ---- 2 x 2 variant for narrow screens -------------------------------------
TH2, PAD2, GAP2 = 420, 34, 26
LBL2 = 78
W2 = PAD2 * 2 + TH2 * 2 + GAP2
H2 = PAD2 * 2 + (TH2 + LBL2) * 2
sheet2 = Image.new("RGB", (W2, H2), YELLOW)
d2 = ImageDraw.Draw(sheet2)
f2 = ImageFont.truetype(FONT % "Bold", 26)

for i, (n, label) in enumerate(steps):
    im = render(n).resize((TH2, TH2), Image.LANCZOS)
    x = PAD2 + (i % 2) * (TH2 + GAP2)
    y = PAD2 + (i // 2) * (TH2 + LBL2)
    sheet2.paste(im, (x, y))
    d2.rectangle([x - 3, y - 3, x + TH2 + 2, y + TH2 + 2], outline=INK, width=3)
    w = d2.textlength(label, font=f2)
    d2.text((x + (TH2 - w) / 2, y + TH2 + 22), label, font=f2, fill=INK)

sheet2.save("/home/claude/oneheart/images/filling-2x2.jpg", quality=92,
            optimize=True, progressive=True)
print("saved 2x2", sheet2.size)
