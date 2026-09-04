#!/usr/bin/env python3
"""ONE HEART — five-panel message set addressed to everyone."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/world-posters")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/worldbuild")
BUILD.mkdir(exist_ok=True)

INTER = FONTS / "inter/files"
NOTO = FONTS / "noto-sans-jp/files"
QR = "file:///home/claude/qr_ks.png"
GRID = f"file://{ROOT}/images/23grid.jpg"
CERT = f"file://{ROOT}/images/certificate.jpg"

def art(n):
    return f"file://{ROOT}/images/artworks/{n:02d}.jpg"

FACE = f"""
@font-face{{font-family:'Inter';font-weight:700;src:url('file://{INTER}/inter-latin-700-normal.woff2')format('woff2')}}
@font-face{{font-family:'Inter';font-weight:900;src:url('file://{INTER}/inter-latin-900-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:400;src:url('file://{NOTO}/noto-sans-jp-japanese-400-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:700;src:url('file://{NOTO}/noto-sans-jp-japanese-700-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:900;src:url('file://{NOTO}/noto-sans-jp-japanese-900-normal.woff2')format('woff2')}}
"""

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:'NotoJP','Inter',sans-serif;
     -webkit-font-smoothing:antialiased}
.canvas{position:relative;width:100%;min-height:100%;background:var(--bg);
        display:flex;flex-direction:column;padding:58px 56px 52px}
img{display:block;width:100%;height:auto}

.top{display:flex;align-items:center;gap:22px}
.num{flex:0 0 72px;height:72px;background:var(--fg);color:var(--bg);
     font-family:'Inter';font-weight:900;font-size:40px;display:flex;
     align-items:center;justify-content:center;line-height:1}
.brand{font-family:'Inter';font-weight:900;font-size:24px;line-height:1.05}
.brand small{display:block;font-size:12px;letter-spacing:.2em;font-weight:700;
             margin-top:7px;opacity:.8}

h1{font-weight:900;letter-spacing:-.025em;line-height:1.24;margin-top:30px}
.en{font-family:'Inter';font-weight:900;letter-spacing:-.01em;line-height:1.3;
    margin-top:14px;opacity:.86}

.card{background:#FFF8EC;color:#111111;padding:24px 26px;margin-top:18px}
.card p{font-weight:400;line-height:1.9}
.card p + p{margin-top:14px}
.card b{font-weight:900}
.card .enp{font-family:'Inter';font-weight:700;line-height:1.65;margin-top:14px;
           padding-top:14px;border-top:2px solid #111;opacity:.78}
.accent{background:var(--fg);color:var(--bg);padding:24px 26px;margin-top:18px;
        font-weight:900;line-height:1.5}
.accent .ens{display:block;font-family:'Inter';font-weight:700;margin-top:10px;opacity:.9}

.shot{margin-top:20px}
.shot figure{border:5px solid var(--fg);background:#111;line-height:0}

.stats{display:flex;margin-top:18px;border-top:5px solid var(--fg);border-bottom:5px solid var(--fg)}
.stat{flex:1;padding:16px 14px;border-right:3px solid var(--fg)}
.stat:last-child{border-right:0}
.stat .n{font-family:'Inter';font-weight:900;font-size:34px;line-height:1}
.stat .l{font-family:'Inter';font-weight:700;font-size:12px;letter-spacing:.14em;
         text-transform:uppercase;margin-top:8px;opacity:.85}

.grid22{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin-top:16px}
.grid22 figure{border:2px solid #111;background:#111;line-height:0}

.spacer{flex:1;min-height:16px}
.foot{display:flex;align-items:flex-end;gap:22px;border-top:5px solid var(--fg);padding-top:20px}
.foot figure{flex:0 0 120px;border:4px solid var(--fg);background:#fff;line-height:0}
.foot .date{font-family:'Inter';font-weight:900;letter-spacing:.1em;font-size:16px;line-height:1}
.foot .k{font-weight:900;font-size:19px;margin-top:9px;line-height:1.35}
.foot .u{font-family:'Inter';font-weight:700;letter-spacing:.06em;font-size:13px;
         margin-top:9px;opacity:.82}
"""

W, H = 1080, 1350


def head(n, jp, en, h_px=56, e_px=23):
    return f"""
<div class="top">
  <div class="num">{n}</div>
  <div class="brand">ONE HEART<small>23 PIECES, ONE WORLD</small></div>
</div>
<h1 style="font-size:{h_px}px">{jp}</h1>
<div class="en" style="font-size:{e_px}px">{en}</div>"""


FOOT = f"""
<div class="spacer"></div>
<div class="foot">
  <figure><img src="{QR}"></figure>
  <div>
    <div class="date">2026.09.08 TUE — 10.08 THU</div>
    <div class="k">Kickstarterで公開<br>WE ARE ALL ONE HEART</div>
    <div class="u">oneheart.tamjump.com</div>
  </div>
</div>"""


def p1():
    return head(1, "選んでいないことの<br>ほうが、多い。",
                "Most of it, you never chose.") + """
<div class="card">
  <p>生まれた国。育った家。体のこと。時代のこと。
  自分で選んだものより、選ばずに決まっていたもののほうが、たぶん多い。</p>
  <p><b>これは不公平の話ではありません。誰にでも当てはまる、ただの事実です。</b></p>
  <p>それでも人は、そこから何かを始めます。</p>
  <div class="enp" style="font-size:16px">Where you were born. The house you grew up in.
  Your body. Your era. Almost none of it was your decision — and that is true for everyone.
  We still begin from there.</div>
</div>
<div class="accent" style="font-size:26px">始まりは選べなくても、<br>そこから先はつくれる。
  <span class="ens" style="font-size:17px">You cannot choose the beginning. You can still build what follows.</span></div>
""" + FOOT


def p2():
    return head(2, "支える側と、<br>支えられる側。",
                "Two sides, and the line between them moves.") + """
<div class="card">
  <p>世の中はその2つに分かれているように見えます。
  けれど、その線は思ったより曖昧です。</p>
  <p>誰でも、いつでも、どちらの側にもなります。
  仕事も、国も、年齢も、そこには関係がありません。</p>
  <p><b>問題は、どちら側にいるかではなく、片側に置かれたまま動けなくなることです。</b></p>
  <div class="enp" style="font-size:16px">Everyone ends up on both sides of that line at some point.
  What hurts is not which side you are on. It is being fixed there, with no way across.</div>
</div>
<div class="accent" style="font-size:26px">立場は、固定されるものじゃない。
  <span class="ens" style="font-size:17px">No one should be fixed on one side of it.</span></div>
""" + FOOT


def p3():
    cells = "".join(f'<figure><img src="{art(i)}"></figure>' for i in range(1, 23))
    return head(3, "生み出す側に、<br>立てるようにする。",
                "From being supported, to creating value.", 54) + f"""
<div class="card">
  <p>ONE HEART は、誰かのアイデアが作品になり、価値になり、
  その価値が本人に戻る道をつくる試みです。</p>
  <p>最初の22体のキャラクターは、病気と向き合う子どもたちのアイデアから生まれました。
  絵にしたのは私です。</p>
  <div class="grid22">{cells}</div>
</div>
<div class="accent" style="font-size:23px">支える道はそのまま。生み出す道を1本、足す。
  <span class="ens" style="font-size:16px">Not replacing support. Adding a second route beside it.</span></div>
""" + FOOT


def p4():
    return head(4, "あなたの1枚が、<br>1ピースになる。",
                "One portrait becomes one piece.", 54) + f"""
<div class="shot"><figure><img src="{GRID}"></figure></div>
<div class="stats">
  <div class="stat"><div class="n">23</div><div class="l">Artworks</div></div>
  <div class="stat"><div class="n">60,000</div><div class="l">Pieces</div></div>
  <div class="stat"><div class="n">&yen;500</div><div class="l">One place</div></div>
</div>
<div class="card">
  <p>顔写真1枚が1ピースになり、2,500枚で1作品が完成します。
  受け取るのは作品のデジタル版と、ピース番号と座標が入った参加証明書です。</p>
  <p><b>国も、年齢も、職業も問いません。顔が1つあれば参加できます。</b></p>
  <div class="enp" style="font-size:16px">2,500 portraits complete one artwork.
  No country, age or occupation is asked for. One face is enough.</div>
</div>
""" + FOOT


def p5():
    return head(5, "作品を見る人ではなく、<br>作品の中身になる。",
                "Not looking at the artwork. Being inside it.", 50) + """
<div class="accent" style="font-size:56px;text-align:center;padding:34px 26px;
     letter-spacing:.01em">WE ARE ALL<br>ONE HEART
  <span class="ens" style="font-size:22px">60,000人で、ひとつ。</span></div>
<div class="card">
  <p>23番目の作品「ONE HEART」は、22の物語と、世界中の参加者が合流する場所です。
  ここだけ5,000ピースでできています。</p>
  <p>2026年9月8日、Kickstarterで公開します。会期は10月8日まで。</p>
  <div class="enp" style="font-size:16px">The 23rd artwork is where the other 22 and everyone
  taking part come together. Live on Kickstarter from 8 September 2026.</div>
</div>
""" + FOOT


PANELS = [
    {"id": "01_chose",  "bg": "#1F6FA5", "fg": "#FFF8EC", "fn": p1},
    {"id": "02_sides",  "bg": "#6E3159", "fg": "#FFF8EC", "fn": p2},
    {"id": "03_create", "bg": "#0B7A72", "fg": "#FFF8EC", "fn": p3},
    {"id": "04_piece",  "bg": "#E8A020", "fg": "#111111", "fn": p4},
    {"id": "05_one",    "bg": "#D6402C", "fg": "#FFF8EC", "fn": p5},
]


def page(p, scale):
    return f"""<html><head><meta charset="utf-8"><style>
{FACE}
:root{{--bg:{p['bg']};--fg:{p['fg']}}}
{CSS}
html,body{{width:{W}px;height:{H}px}}
.canvas{{zoom:{scale}}}
</style></head><body><div class="canvas">{p['fn']()}</div></body></html>"""


async def measure(b, p, scale, f):
    f.write_text(page(p, scale))
    pg = await b.new_page(viewport={"width": W, "height": H})
    await pg.goto("file://" + str(f))
    await pg.wait_for_timeout(650)
    h = await pg.evaluate(
        "()=>Math.ceil(document.querySelector('.canvas').getBoundingClientRect().height)")
    await pg.close()
    return h


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for p in PANELS:
            f = BUILD / f"{p['id']}.html"
            scale, fit = 1.0, None
            for _ in range(60):
                if await measure(b, p, scale, f) <= H:
                    fit = scale
                    break
                scale = round(scale - 0.02, 2)
            if fit and fit >= 0.999:
                while fit < 1.30:
                    trial = round(fit + 0.02, 2)
                    if await measure(b, p, trial, f) > H:
                        break
                    fit = trial
            f.write_text(page(p, fit))
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto("file://" + str(f))
            await pg.wait_for_timeout(900)
            out = OUT / f"oneheart_world_{p['id']}_{W}x{H}.png"
            await pg.screenshot(path=str(out))
            await pg.close()
            print(f"{out.name}  scale={fit:.2f}")
        await b.close()


asyncio.run(main())
