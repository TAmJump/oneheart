"""Patch the completion-rule wording inside three Kickstarter story images.

The originals live outside the repo (story.zip). This script rewrites only the
text blocks that still describe the old rule ("an artwork is completed when its
2,500 places are filled") and leaves every other pixel untouched.

Usage: python3 patch_story_images.py SRC_DIR OUT_DIR
"""
import sys, pathlib
from PIL import Image, ImageDraw, ImageFont

FONTS = pathlib.Path("/home/claude/interfont/extras/ttf")
REG = str(FONTS / "Inter-Regular.ttf")
BOLD = str(FONTS / "Inter-Bold.ttf")


def fit_size(text, target_w, path=REG, lo=10, hi=48):
    """Find the point size whose rendered width matches the original line."""
    best, bestd = lo, 1e9
    for s in range(lo, hi):
        f = ImageFont.truetype(path, s)
        w = f.getbbox(text)[2] - f.getbbox(text)[0]
        d = abs(w - target_w)
        if d < bestd:
            best, bestd = s, d
    return best


def wrap(segments, font_reg, font_bold, max_w):
    """segments: list of (text, bold). Returns list of lines, each a segment list."""
    words = []
    for text, bold in segments:
        for i, w in enumerate(text.split(" ")):
            if w:
                words.append((w, bold))
    lines, cur, cur_w = [], [], 0
    space_w = font_reg.getlength(" ")
    for w, bold in words:
        f = font_bold if bold else font_reg
        ww = f.getlength(w)
        add = ww if not cur else space_w + ww
        if cur and cur_w + add > max_w:
            lines.append(cur)
            cur, cur_w = [(w, bold)], ww
        else:
            cur.append((w, bold))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines


def draw_line(d, x, y, line, font_reg, font_bold, colour):
    space_w = font_reg.getlength(" ")
    for i, (w, bold) in enumerate(line):
        f = font_bold if bold else font_reg
        if i:
            x += space_w
        d.text((x, y), w, font=f, fill=colour, anchor="la")
        x += f.getlength(w)


def patch(im, block):
    d = ImageDraw.Draw(im)
    d.rectangle(block["clear"], fill=block["bg"])

    size = fit_size(block["ref_text"], block["ref_w"])
    fr = ImageFont.truetype(REG, size)
    fb = ImageFont.truetype(BOLD, size)

    # calibrate: where does anchor="la" put the top of the reference line?
    top_off = fr.getbbox(block["ref_text"], anchor="la")[1]
    left_off = fr.getbbox(block["ref_text"], anchor="la")[0]
    x = block["x"] - left_off
    y = block["y"] - top_off

    lines = wrap(block["new"], fr, fb, block["max_w"])
    for i, line in enumerate(lines):
        draw_line(d, x, y + i * block["lh"], line, fr, fb, block["colour"])
    return len(lines)


GREY = (168, 170, 172)
LIGHT = (220, 222, 223)
DIM = (142, 144, 146)
DARK = (13, 13, 13)
CARD = (23, 24, 26)

JOBS = {
    "02_WHY_KICKSTARTER.png": [
        dict(clear=(1165, 726, 1530, 832), bg=DARK, x=1172, y=735, lh=33.5,
             max_w=310, colour=LIGHT,
             ref_text="Nothing is charged unless the", ref_w=308,
             new=[("Nothing is charged unless the project is actually funded.", False)]),
    ],
    "12_FUNDING.png": [
        dict(clear=(85, 200, 1210, 276), bg=DARK, x=89, y=209, lh=36,
             max_w=1015, colour=GREY,
             ref_text="The Kickstarter goal is the cost of completing the first artwork. It is not the cost of the",
             ref_w=1009,
             new=[("The Kickstarter goal is the minimum that lets the project start. It is not the cost of the whole project.", False)]),
        dict(clear=(130, 563, 772, 642), bg=CARD, x=134, y=572, lh=37,
             max_w=470, colour=LIGHT,
             ref_text="The cost of completing one artwork.", ref_w=410,
             new=[("The ", False), ("minimum", True),
                  (" that lets the project start. 2,500 places × ¥500.", False)]),
        dict(clear=(85, 762, 1530, 830), bg=DARK, x=89, y=769, lh=33,
             max_w=1395, colour=GREY,
             ref_text="Reaching ¥1,250,000 funds the first artwork and starts the project. It does not complete all 23. Each further artwork is completed",
             ref_w=1390,
             new=[("Reaching ¥1,250,000 starts the project. All 23 artworks are then produced and delivered as they stand on 30 June 2027, at whatever level of participation each one has reached.", False)]),
    ],
    "14_SCHEDULE.png": [
        dict(clear=(85, 200, 1210, 272), bg=DARK, x=89, y=209, lh=36,
             max_w=1065, colour=GREY,
             ref_text="An artwork is finalised only after its portraits have been collected and processed, so dates",
             ref_w=1060,
             new=[("Places stay open until 30 June 2027. On that date every artwork is closed and rendered as it stands.", False)]),
        dict(clear=(828, 412, 1180, 508), bg=DARK, x=832, y=419, lh=31,
             max_w=300, colour=DIM,
             ref_text="Each artwork is assembled", ref_w=252,
             new=[("Every artwork is rendered as it stands on 30 June 2027.", False)]),
    ],
}


def main(src, out):
    src, out = pathlib.Path(src), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, blocks in JOBS.items():
        im = Image.open(src / name).convert("RGB")
        for b in blocks:
            n = patch(im, b)
            print(f"{name}: {n} lines")
        im.save(out / name)
        print("wrote", out / name)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
