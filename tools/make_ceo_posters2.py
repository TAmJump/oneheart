#!/usr/bin/env python3
"""ONE HEART — CHILDREN CEO PROJECT, five-panel narrative (v2)."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/ceo-posters-v2")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/ceobuild2")
BUILD.mkdir(exist_ok=True)

INTER = FONTS / "inter/files"
NOTO = FONTS / "noto-sans-jp/files"
QR = "file:///home/claude/qr_ks.png"

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
.num{flex:0 0 74px;height:74px;background:var(--fg);color:var(--bg);
     font-family:'Inter';font-weight:900;font-size:42px;display:flex;
     align-items:center;justify-content:center;line-height:1}
.brand{font-family:'Inter';font-weight:900;font-size:25px;line-height:1.05}
.brand small{display:block;font-size:12px;letter-spacing:.22em;font-weight:700;
             margin-top:7px;opacity:.8}

h1{font-weight:900;letter-spacing:-.025em;line-height:1.24;margin-top:30px}
.deck{font-weight:700;line-height:1.75;margin-top:18px;opacity:.94}

.card{background:#FFF8EC;color:#111111;padding:24px 26px;margin-top:18px}
.card p{font-weight:400;line-height:1.9}
.card p + p{margin-top:14px}
.card b{font-weight:900}
.accent{background:var(--fg);color:var(--bg);padding:24px 26px;margin-top:18px;
        font-weight:900;line-height:1.5}

.chain{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.link{background:#FFF8EC;color:#111;padding:12px 14px;font-weight:700;line-height:1.3}
.arrow{align-self:center;font-weight:900;opacity:.75}

.flow{display:flex;gap:10px;margin-top:20px}
.step{flex:1;background:#FFF8EC;color:#111;padding:18px 14px}
.step .n{font-family:'Inter';font-weight:900;font-size:20px;color:var(--bg);
         background:#111;width:32px;height:32px;display:flex;align-items:center;
         justify-content:center;line-height:1}
.step h4{font-weight:900;line-height:1.35;margin-top:12px}
.step p{font-weight:400;line-height:1.6;margin-top:7px}

.uses{display:flex;gap:10px;margin-top:18px}
.use{flex:1;background:#FFF8EC;color:#111;padding:16px 10px;text-align:center;
     font-weight:700;line-height:1.45}

.grid22{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin-top:16px}
.grid22 figure{border:2px solid #111;background:#111;line-height:0}

.note{font-weight:400;line-height:1.75;margin-top:16px;opacity:.9}

.spacer{flex:1;min-height:16px}
.foot{display:flex;align-items:flex-end;gap:22px;border-top:5px solid var(--fg);padding-top:20px}
.foot figure{flex:0 0 122px;border:4px solid var(--fg);background:#fff;line-height:0}
.foot .date{font-family:'Inter';font-weight:900;letter-spacing:.1em;font-size:17px;line-height:1}
.foot .k{font-weight:900;font-size:20px;margin-top:9px;line-height:1.35}
.foot .u{font-family:'Inter';font-weight:700;letter-spacing:.06em;font-size:14px;
         margin-top:9px;opacity:.82}
"""

W, H = 1080, 1350


def head(n, title, deck="", h_px=56, d_px=22):
    d = f'<div class="deck" style="font-size:{d_px}px">{deck}</div>' if deck else ""
    return f"""
<div class="top">
  <div class="num">{n}</div>
  <div class="brand">ONE HEART<small>CHILDREN CEO PROJECT</small></div>
</div>
<h1 style="font-size:{h_px}px">{title}</h1>{d}"""


FOOT = f"""
<div class="spacer"></div>
<div class="foot">
  <figure><img src="{QR}"></figure>
  <div>
    <div class="date">2026.09.08 TUE</div>
    <div class="k">Kickstarterで公開<br>WE ARE ALL ONE HEART</div>
    <div class="u">oneheart.tamjump.com</div>
  </div>
</div>"""


def chain(items, size=17):
    out = []
    for i, t in enumerate(items):
        if i:
            out.append('<div class="arrow" style="font-size:20px">→</div>')
        out.append(f'<div class="link" style="font-size:{size}px">{t}</div>')
    return '<div class="chain">' + "".join(out) + "</div>"


def p1():
    return head(1, "いまの道は、<br>間違っていない。",
                "病気が見つかってから治療が届くまでに、たくさんの人と仕組みが動いています。", 58) + f"""
{chain(["病気が見つかる", "家族が支える", "税と保険", "制度", "医療", "治療が届く"])}
<div class="card">
  <p>どの病気を助成の対象にするか。どこまで負担を軽くするか。専門家が検討し、
  行政が制度にし、医師が治療を組み立てる。この道があるから、治療が受けられます。</p>
  <p><b>これは守るべき仕組みです。ONE HEART は、ここを否定するために始めたものではありません。</b></p>
</div>
<div class="accent" style="font-size:27px">まず、この道に感謝から始めたい。</div>
""" + FOOT


def p2():
    return head(2, "決める場所に、<br>本人がいない。", "", 58) + """
<div class="card">
  <p>助成の対象になる病気を決めるのは、国の検討会です。負担の上限を決めるのは制度です。
  治療を決めるのは、医学的な根拠をもとにした医師と家族の話し合いです。
  年齢や理解の程度に応じて、本人が関わることもあります。</p>
  <p>どれも必要な手続きで、誰かが間違えているわけではありません。</p>
  <p><b>ただ、この一連の流れの中に、本人が自分の力で動かせる部分は、ほとんど残っていません。</b></p>
</div>
<div class="card">
  <p>そして、通院や付き添いで家族の働き方が変わることがあります。
  そのことを、周りの大人が思っているより、よく見ている子がいます。</p>
</div>
<div class="accent" style="font-size:25px">よかれと思って決めたことが、<br>
  その子の選べる範囲を、静かに形づくっていく。</div>
""" + FOOT


def p3():
    return head(3, "もう一本、<br>道をつくる。",
                "支える道はそのまま。生み出す道を1本、足します。", 58) + """
<div class="flow">
  <div class="step"><div class="n">1</div>
    <h4 style="font-size:18px">アイデアを出す</h4>
    <p style="font-size:14px">その子の考えが<br>キャラクターになる</p></div>
  <div class="step"><div class="n">2</div>
    <h4 style="font-size:18px">作品になる</h4>
    <p style="font-size:14px">アートやグッズなど<br>いろいろな形にする</p></div>
  <div class="step"><div class="n">3</div>
    <h4 style="font-size:18px">世界の人が参加する</h4>
    <p style="font-size:14px">共感した人が集まり<br>キャラクターに価値がつく</p></div>
  <div class="step"><div class="n">4</div>
    <h4 style="font-size:18px">本人の収益になる</h4>
    <p style="font-size:14px">生まれた利益が<br>発案した本人に戻る</p></div>
</div>
<div class="card">
  <p>22体のキャラクターは、病気と向き合う子どもたちのアイデアから生まれました。
  絵にしたのは私です。最初の商品はアートにしました。</p>
  <p>顔写真1枚が1ピースになり、2,500枚で1作品が完成します。作品は23点、全体で60,000ピース。</p>
</div>
<div class="accent" style="font-size:26px">支えられる側から、生み出す側へ。</div>
""" + FOOT


def p4():
    return head(4, "使い道は、<br>本人が決める。", "", 58) + """
<div class="uses">
  <div class="use" style="font-size:17px">治療に<br>使う</div>
  <div class="use" style="font-size:17px">好きな服を<br>買う</div>
  <div class="use" style="font-size:17px">家族と<br>出かける</div>
  <div class="use" style="font-size:17px">将来のために<br>貯める</div>
</div>
<div class="card">
  <p>自分で生み出した価値なら、何に使うかも自分で決められます。</p>
  <p>「病気なんだから治療に使いなさい」と大人が用途を決めた瞬間、
  また大人がその子の人生を決めることになります。それでは元の場所に戻ってしまう。</p>
  <p><b>使い道を決める経験そのものが、この仕組みでいちばん渡したいものです。</b></p>
</div>
<div class="accent" style="font-size:27px">自分で生み出した価値だから、<br>自分で使い道を決める。</div>
""" + FOOT


def p5():
    cells = "".join(f'<figure><img src="{art(i)}"></figure>' for i in range(1, 23))
    return head(5, "君は、支援されるだけの<br>存在じゃない。", "", 50) + f"""
<div class="accent" style="font-size:66px;letter-spacing:.04em;text-align:center;
     padding:30px 26px">君が社長だ。</div>
<div class="card">
  <div class="grid22">{cells}</div>
  <p style="font-size:17px;margin-top:14px"><b>22のアイデア。22人の発案者。</b>
  23番目の作品で、世界中の参加者と合流します。</p>
</div>
<div class="note" style="font-size:15px">未成年者の権利保護、保護者同意、著作権と収益分配、税務。
国ごとに設計しなければ成立しない部分が多く、確立された制度があるわけではありません。
まず1作品を成立させて、実務として何が必要かを洗い出す段階です。</div>
""" + FOOT


PANELS = [
    {"id": "01_road",  "bg": "#0B7A72", "fg": "#FFF8EC", "fn": p1},
    {"id": "02_who",   "bg": "#1F6FA5", "fg": "#FFF8EC", "fn": p2},
    {"id": "03_route", "bg": "#E8A020", "fg": "#111111", "fn": p3},
    {"id": "04_use",   "bg": "#D6402C", "fg": "#FFF8EC", "fn": p4},
    {"id": "05_ceo",   "bg": "#6E3159", "fg": "#FFF8EC", "fn": p5},
]


def page(p, scale):
    return f"""<html><head><meta charset="utf-8"><style>
{FACE}
:root{{--bg:{p['bg']};--fg:{p['fg']}}}
{CSS}
html,body{{width:{W}px;height:{H}px}}
.canvas{{zoom:{scale}}}
</style></head><body><div class="canvas">{p['fn']()}</div></body></html>"""


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for p in PANELS:
            # まず縮小して収め、余白が大きい場合は拡大して埋める
            scale, best = 1.0, None
            for _ in range(60):
                f = BUILD / f"{p['id']}.html"
                f.write_text(page(p, scale))
                pg = await b.new_page(viewport={"width": W, "height": H})
                await pg.goto("file://" + str(f))
                await pg.wait_for_timeout(600)
                h = await pg.evaluate(
                    "()=>Math.ceil(document.querySelector('.canvas').getBoundingClientRect().height)")
                await pg.close()
                if h <= H:
                    best = scale
                    break
                scale -= 0.02
            if best and best >= 0.999:
                s2 = best
                while s2 < 1.30:
                    trial = round(s2 + 0.02, 2)
                    f.write_text(page(p, trial))
                    pg = await b.new_page(viewport={"width": W, "height": H})
                    await pg.goto("file://" + str(f))
                    await pg.wait_for_timeout(500)
                    h = await pg.evaluate(
                        "()=>Math.ceil(document.querySelector('.canvas').getBoundingClientRect().height)")
                    await pg.close()
                    if h > H:
                        break
                    s2 = trial
                best = s2
            f.write_text(page(p, best))
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto("file://" + str(f))
            await pg.wait_for_timeout(900)
            out = OUT / f"oneheart_ceo2_{p['id']}_{W}x{H}.png"
            await pg.screenshot(path=str(out))
            await pg.close()
            print(f"{out.name}  scale={best:.2f}")
        await b.close()


asyncio.run(main())
