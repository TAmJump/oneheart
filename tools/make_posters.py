#!/usr/bin/env python3
"""ONE HEART — Japanese announcement posters, one colour per pattern."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/posters")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/posterbuild")
BUILD.mkdir(exist_ok=True)

INTER = FONTS / "inter/files"
NOTO = FONTS / "noto-sans-jp/files"
GRID = f"file://{ROOT}/images/23grid.jpg"
QR = "file:///home/claude/qr_ks.png"

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
        display:flex;flex-direction:column;padding:64px 62px 58px}
img{display:block;width:100%;height:auto}
.eyebrow{font-family:'Inter';font-weight:900;letter-spacing:.2em;text-transform:uppercase;
         color:var(--fg);opacity:.72;line-height:1}
.head{font-weight:900;letter-spacing:-.02em;line-height:1.28;margin-top:20px}
.rule{height:5px;background:var(--fg);margin:26px 0 0;opacity:.9}
.body{font-weight:400;line-height:1.95;margin-top:26px;white-space:pre-line}
.body b{font-weight:700}
.shot{margin-top:26px;position:relative}
.shot figure{border:5px solid var(--fg);background:#111;line-height:0}
.spacer{flex:1;min-height:22px}
.foot{display:flex;align-items:flex-end;gap:26px;border-top:5px solid var(--fg);padding-top:24px}
.foot figure{flex:0 0 var(--qr);border:5px solid var(--fg);background:#fff;line-height:0}
.foot .txt{flex:1}
.foot .date{font-family:'Inter';font-weight:900;letter-spacing:.1em;line-height:1}
.foot .k{font-weight:900;margin-top:10px;line-height:1.35}
.foot .u{font-family:'Inter';font-weight:700;letter-spacing:.06em;margin-top:12px;opacity:.82}
"""

W, H = 1080, 1350

# bg / fg / whether the grid image is shown
PATTERNS = [
    {
        "id": "A_child",
        "bg": "#FFD900", "fg": "#111111", "grid": False,
        "eyebrow": "One Heart Project",
        "head": "支えられる側から、<br>生み出す側へ。",
        "body": (
            "「私のために、そんなに頑張らないで」\n\n"
            "病気と向き合う子どもの中には、周りの大人がどれだけのものを差し出しているかを、"
            "正確に理解している子がいます。そして、自分のせいで誰かが無理をすることを、静かに嫌がっています。\n\n"
            "支えられる側に置かれ続けるかぎり、その気持ちには行き場がありません。\n\n"
            "ONE HEART は、その関係を組み替えられないかという試みです。子どもが出したアイデアを"
            "キャラクターにする。そのキャラクターに作品としての価値を持たせる。生まれた価値を、"
            "アイデアを出した本人の未来に向ける。\n\n"
            "22体のキャラクターは、2024年から2025年にかけて出会った子どもたちのアイデアから"
            "生まれました。絵にしたのは私です。\n\n"
            "最初の商品は、アートです。"
        ),
    },
    {
        "id": "B_system",
        "bg": "#0B7A72", "fg": "#FFF8EC", "grid": False,
        "eyebrow": "One Heart Project",
        "head": "その子のアイデアは、<br>その子の資産になる。",
        "body": (
            "病気と向き合う子どもは、家族と医療と公的制度に支えられる側に固定されます。"
            "制度としては正しくても、本人の側から見ると、自分の存在が誰かの負担として"
            "計上され続ける構造です。\n\n"
            "ONE HEART が試すのは、そこに別の経路を1本通せるかどうかです。\n\n"
            "子どものアイデアをキャラクターにし、知的財産として価値を持たせ、商品化や"
            "ライセンスで生まれた利益を、アイデアを出した本人に帰属させる。受け取る側から、"
            "生み出す側へ移す設計です。\n\n"
            "未成年者の権利保護、保護者同意、著作権と収益分配、税務。国ごとに設計しなければ"
            "成立しない部分が多く、確立された制度があるわけではありません。まず1作品を"
            "成立させて、実務として何が必要かを洗い出す段階です。"
        ),
    },
    {
        "id": "C_short",
        "bg": "#D6402C", "fg": "#FFF8EC", "grid": True,
        "eyebrow": "One Heart Project",
        "head": "顔写真1枚が、<br>1ピースになる。",
        "body": (
            "2,500枚で1作品。23作品で60,000ピース。\n\n"
            "参加した人は、作品を見る側ではなく、作品の中身になります。\n\n"
            "1枠500円。23作品から好きな作品を選べます。"
        ),
    },
    {
        "id": "D_call",
        "bg": "#F2A81D", "fg": "#111111", "grid": True,
        "eyebrow": "One Heart Project",
        "head": "あなたが、<br>この作品の一部になる。",
        "body": (
            "世界中から顔写真を集めて、1枚を1ピースとして2,500枚で1作品をつくります。"
            "作品は23点。\n\n"
            "いま公開前のページが出ています。「ローンチ通知を受け取る」を押すと、"
            "公開と同時に通知が届きます。課金は発生しません。\n\n"
            "フォローが10人集まるまで、このページはKickstarterの検索に出ません。"
        ),
    },
    {
        "id": "E_press",
        "bg": "#6E3159", "fg": "#FFF8EC", "grid": False,
        "eyebrow": "News Release · 2026.09.03",
        "head": "参加型モザイクアート<br>「WE ARE ALL ONE HEART」<br>9月8日 Kickstarterで公開",
        "body": (
            "タムジ株式会社（東京都、代表取締役 大下甚）は、2026年9月8日より、Kickstarterにて"
            "参加型アートプロジェクト「WE ARE ALL ONE HEART — 23 Pieces, One World」を"
            "公開します。会期は10月8日まで、目標額は1,250,000円です。\n\n"
            "世界中から集めた顔写真1枚を1ピースとして、2,500枚で1点のモザイク作品を構成します。"
            "作品は全23点、総ピース数は60,000。参加は1枠500円で、完成作品のデジタル版と、"
            "作品名・ピース番号・座標を記載した参加証明書が発行されます。発送物はありません。\n\n"
            "23点のうち22点のキャラクターは、2024年から2025年にかけて、病気と向き合う"
            "子どもたちから寄せられたアイデアをもとに制作されました。同社は、そこから生じた"
            "価値を発案者本人に帰属させる仕組みの構築を目指しており、本プロジェクトはその"
            "第一段階にあたります。\n\n"
            "お問い合わせ：タムジ株式会社　info@tamjump.com"
        ),
    },
]


def html(p, head_px, body_px):
    grid = (f'<div class="shot"><figure><img src="{GRID}"></figure></div>'
            if p["grid"] else "")
    return f"""<html><head><meta charset="utf-8"><style>
{FACE}
:root{{--bg:{p['bg']};--fg:{p['fg']};--qr:160px}}
{CSS}
html,body{{width:{W}px;height:{H}px}}
</style></head><body>
<div class="canvas">
  <div class="eyebrow" style="font-size:19px">{p['eyebrow']}</div>
  <div class="head" style="font-size:{head_px}px">{p['head']}</div>
  <div class="rule"></div>
  {grid}
  <div class="body" style="font-size:{body_px}px">{p['body']}</div>
  <div class="spacer"></div>
  <div class="foot">
    <figure><img src="{QR}"></figure>
    <div class="txt">
      <div class="date" style="font-size:20px">2026.09.08 TUE</div>
      <div class="k" style="font-size:25px">Kickstarterで公開<br>1枠 500円・23作品</div>
      <div class="u" style="font-size:16px">oneheart.tamjump.com</div>
    </div>
  </div>
</div></body></html>"""


async def render(b, p):
    head_px, body_px = 52, 25
    for _ in range(28):
        f = BUILD / f"{p['id']}.html"
        f.write_text(html(p, head_px, body_px))
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.goto("file://" + str(f))
        await pg.wait_for_timeout(700)
        h = await pg.evaluate("()=>document.querySelector('.canvas').scrollHeight")
        if h <= H:
            out = OUT / f"oneheart_jp_{p['id']}_{W}x{H}.png"
            await pg.screenshot(path=str(out))
            await pg.close()
            print(f"{out.name}  head={head_px} body={body_px}  {h}/{H}")
            return
        await pg.close()
        body_px -= 1
        if body_px % 3 == 0 and head_px > 36:
            head_px -= 2
    print("could not fit", p["id"])


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        for p in PATTERNS:
            await render(b, p)
        await b.close()


asyncio.run(main())
