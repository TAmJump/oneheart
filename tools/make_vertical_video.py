from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
YELLOW = (255, 217, 0)
INK = (17, 17, 17)
CORAL = (229, 57, 53)

VW = 1000                      # video width
VH = 562
VX = (W - VW) // 2             # 40
VY = 600
B = 5                          # border

F = "/home/claude/interfont/extras/ttf/Inter-%s.ttf"


def f(w, s):
    return ImageFont.truetype(F % w, s)


def center(d, y, txt, font, fill, tracking=0):
    if tracking:
        widths = [d.textlength(c, font=font) + tracking for c in txt]
        x = (W - (sum(widths) - tracking)) / 2
        for c, cw in zip(txt, widths):
            d.text((x, y), c, font=font, fill=fill)
            x += cw
    else:
        w = d.textlength(txt, font=font)
        d.text(((W - w) / 2, y), txt, font=font, fill=fill)


def build(phase, out):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # ---- top band ----
    center(d, 176, "TAMJ INC.  /  TOKYO", f("Bold", 26), INK, 6)
    center(d, 244, "WE ARE ALL", f("Black", 108), INK)
    center(d, 352, "ONE HEART", f("Black", 108), CORAL)
    center(d, 486, "23 PIECES,  ONE WORLD", f("Bold", 34), INK, 3)

    # ---- video frame border ----
    d.rectangle([VX - B, VY - B, VX + VW + B - 1, VY + VH + B - 1], outline=INK, width=B)

    # ---- bottom band ----
    y = VY + VH + 96

    center(d, y, "ONE PORTRAIT.  ONE PLACE.  \u00a5500.", f("Black", 46), INK)
    y += 96

    if phase == "pre":
        line1, line2 = "LAUNCHING", "8 SEPTEMBER"
    else:
        line1, line2 = "LIVE NOW", "ON KICKSTARTER"

    center(d, y, line1, f("Bold", 40), INK, 4)
    y += 58
    center(d, y, line2, f("Black", 92), CORAL)
    y += 128

    if phase == "pre":
        center(d, y, "ON KICKSTARTER", f("Bold", 38), INK, 4)
        y += 76

    # pill with the site URL
    txt = "oneheart.tamjump.com"
    fo = f("Black", 42)
    tw = d.textlength(txt, font=fo)
    pw, ph = tw + 96, 96
    px, py = (W - pw) / 2, y
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=48, fill=INK)
    d.text(((W - tw) / 2, py + 22), txt, font=fo, fill=YELLOW)

    im.save(out)
    print(out, "ok")


build("pre", "/home/claude/frame_pre.png")
build("live", "/home/claude/frame_live.png")

# --- encode (run after this script) -------------------------------------
# for p in pre live; do
#   ffmpeg -i ../media/one-heart.mp4 -i frame_$p.png \
#     -f lavfi -i color=c=0xFFD900:s=1080x1920:r=30 \
#     -filter_complex "[0:v]scale=1000:562,setsar=1[v];\
# [2:v][v]overlay=40:600:shortest=1[b];[b][1:v]overlay=0:0,format=yuv420p[out]" \
#     -map "[out]" -map 0:a -c:v libx264 -preset medium -crf 21 \
#     -c:a aac -b:a 192k -movflags +faststart -shortest one-heart-vertical-$p.mp4 -y
# done
