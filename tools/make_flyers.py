#!/usr/bin/env python3
"""Generate ONE HEART social flyers (square / portrait / story / link card)."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/flyers")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/flyerbuild")
BUILD.mkdir(exist_ok=True)

INTER = FONTS / "inter/files"
NOTO = FONTS / "noto-sans-jp/files"

FACE = f"""
@font-face{{font-family:'Inter';font-weight:400;src:url('file://{INTER}/inter-latin-400-normal.woff2')format('woff2')}}
@font-face{{font-family:'Inter';font-weight:700;src:url('file://{INTER}/inter-latin-700-normal.woff2')format('woff2')}}
@font-face{{font-family:'Inter';font-weight:800;src:url('file://{INTER}/inter-latin-800-normal.woff2')format('woff2')}}
@font-face{{font-family:'Inter';font-weight:900;src:url('file://{INTER}/inter-latin-900-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:400;src:url('file://{NOTO}/noto-sans-jp-japanese-400-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:700;src:url('file://{NOTO}/noto-sans-jp-japanese-700-normal.woff2')format('woff2')}}
@font-face{{font-family:'NotoJP';font-weight:900;src:url('file://{NOTO}/noto-sans-jp-japanese-900-normal.woff2')format('woff2')}}
"""

GRID = f"file://{ROOT}/images/23grid.jpg"
CERT = f"file://{ROOT}/images/certificate.jpg"

def art(n):
    return f"file://{ROOT}/images/artworks/{n:02d}.jpg"


COPY = {
    "pre": {
        "eyebrow": "Kickstarter · Launching",
        "date": "2026.09.08 TUE",
        "lead": "One portrait becomes one piece.",
        "body": "2,500 portraits make one artwork. 23 artworks, 60,000 pieces.<br>The people who join are what the artwork is made of.",
        "cta_k": "Launching 8 September",
        "cta_v": "Follow the pre-launch page to be notified",
        "qr_note": "Scan to open on Kickstarter",
    },
    "live": {
        "eyebrow": "Now live on Kickstarter",
        "date": "ENDS 2026.10.08 THU",
        "lead": "One portrait becomes one piece.",
        "body": "Choose any of the 23 artworks. &yen;500 for one place.<br>You receive the artwork and your certificate.",
        "cta_k": "Now live",
        "cta_v": "Campaign ends 8 October 2026",
        "qr_note": "Scan to open on Kickstarter",
    },
}

QR = "file:///home/claude/qr_ks.png"


def footer(c, qr, k_size, v_size, note_size, url_size, gap=24):
    return f"""
<div style="display:flex;align-items:stretch;gap:{gap}px;">
  <figure style="flex:0 0 {qr}px;border:4px solid #111;background:#fff;line-height:0;
                 align-self:flex-end">
    <img src="{QR}" style="width:100%;height:auto">
  </figure>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end">
    <div style="font-family:'Inter';font-weight:700;font-size:{note_size}px;
                letter-spacing:.1em;text-transform:uppercase;color:#3a3527;margin-bottom:10px">
      {c['qr_note']}
    </div>
    <div class="bar" style="padding:{int(k_size*0.62)}px {int(k_size*0.85)}px">
      <div class="k" style="font-size:{k_size}px;font-family:'Inter'">{c['cta_k']}</div>
    </div>
    <div style="font-family:'Inter';font-weight:700;font-size:{v_size}px;color:#3a3527;
                margin-top:12px">{c['cta_v']}</div>
    <div class="url" style="font-size:{url_size}px;margin-top:10px">oneheart.tamjump.com</div>
  </div>
</div>"""


BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);font-family:'Inter','NotoJP',sans-serif;color:#111;
     -webkit-font-smoothing:antialiased}
.canvas{position:relative;width:100%;min-height:100%;background:var(--bg)}
.frame{position:absolute;border:4px solid #111}
img{display:block;width:100%;height:auto}
.eyebrow{font-weight:800;text-transform:uppercase;color:var(--ac);line-height:1}
.title{font-weight:900;letter-spacing:-.035em;line-height:.92;color:#111}
.sub{font-weight:700;letter-spacing:.02em;color:#111}
.jp{font-family:'NotoJP',sans-serif}
.lead{font-family:'NotoJP',sans-serif;font-weight:900;letter-spacing:-.01em;line-height:1.3}
.body{font-family:'NotoJP',sans-serif;font-weight:400;line-height:1.75;color:#3a3527}
.shot{position:relative}
.shot .block{position:absolute;background:var(--ac)}
.shot figure{position:relative;border:4px solid #111;background:#111;line-height:0}
.stats{display:flex;border-top:4px solid #111;border-bottom:4px solid #111}
.stat{flex:1;border-right:3px solid #111;padding:18px 20px}
.stat:last-child{border-right:0}
.stat .n{font-weight:900;letter-spacing:-.02em;color:var(--ac);line-height:1}
.stat .l{font-family:'NotoJP',sans-serif;font-weight:700;letter-spacing:.14em;
         text-transform:uppercase;color:#3a3527;margin-top:8px}
.bar{background:var(--ac);color:#fff;display:flex;align-items:center;gap:20px}
.bar .k{font-family:'NotoJP',sans-serif;font-weight:900;letter-spacing:.02em;white-space:nowrap}
.bar .v{font-family:'NotoJP',sans-serif;font-weight:700;opacity:.94}
.url{font-weight:700;letter-spacing:.08em;color:#111}
.strip{display:flex;gap:14px}
.strip figure{flex:1;border:3px solid #111;background:#111;line-height:0}
"""


def stats(n_size, l_size, pad):
    return f"""
<div class="stats">
  <div class="stat" style="padding:{pad}">
    <div class="n" style="font-size:{n_size}px">23</div>
    <div class="l" style="font-size:{l_size}px">Artworks</div></div>
  <div class="stat" style="padding:{pad}">
    <div class="n" style="font-size:{n_size}px">60,000</div>
    <div class="l" style="font-size:{l_size}px">Pieces</div></div>
  <div class="stat" style="padding:{pad}">
    <div class="n" style="font-size:{n_size}px">&yen;500</div>
    <div class="l" style="font-size:{l_size}px">One place</div></div>
</div>"""


def square(c):
    """1080 x 1080"""
    return f"""
<div class="canvas" style="padding:48px 56px 44px">
  <div class="eyebrow" style="font-size:19px;letter-spacing:.2em">{c['eyebrow']} &nbsp;{c['date']}</div>
  <div class="title" style="font-size:72px;margin-top:16px">WE ARE ALL<br>ONE HEART</div>
  <div class="sub" style="font-size:21px;margin-top:12px;color:#3a3527">23 Pieces, One World</div>

  <div class="shot" style="margin-top:24px;width:78%;margin-left:auto">
    <div class="block" style="left:-22px;top:22px;width:52%;height:100%"></div>
    <figure><img src="{GRID}"></figure>
  </div>

  <div style="margin-top:24px">{stats(32, 12, '13px 16px')}</div>

  <div style="margin-top:24px">{footer(c, 148, 23, 15, 12, 15)}</div>
</div>"""


def portrait(c):
    """1080 x 1350"""
    return f"""
<div class="canvas" style="padding:56px 58px 50px">
  <div class="eyebrow" style="font-size:21px;letter-spacing:.2em">{c['eyebrow']} &nbsp;{c['date']}</div>
  <div class="title" style="font-size:80px;margin-top:18px">WE ARE ALL<br>ONE HEART</div>
  <div class="sub" style="font-size:24px;margin-top:14px;color:#3a3527">23 Pieces, One World</div>

  <div class="shot" style="margin-top:30px;width:88%;margin-left:auto">
    <div class="block" style="left:-24px;top:24px;width:56%;height:100%"></div>
    <figure><img src="{GRID}"></figure>
  </div>

  <div class="lead" style="font-family:'Inter';font-size:34px;margin-top:34px">{c['lead']}</div>
  <div class="body" style="font-family:'Inter';font-size:19px;margin-top:12px">{c['body']}</div>

  <div style="margin-top:26px">{stats(34, 13, '13px 18px')}</div>

  <div style="margin-top:26px">{footer(c, 156, 25, 16, 12, 16)}</div>
</div>"""


def story(c):
    """1080 x 1920"""
    return f"""
<div class="canvas" style="padding:96px 66px 92px">
  <div class="eyebrow" style="font-size:23px;letter-spacing:.2em">{c['eyebrow']}</div>
  <div class="title" style="font-size:104px;margin-top:24px">WE ARE ALL<br>ONE HEART</div>
  <div class="sub" style="font-size:27px;margin-top:18px;color:#3a3527">23 Pieces, One World &nbsp;·&nbsp; {c['date']}</div>

  <div class="shot" style="margin-top:48px">
    <div class="block" style="left:-26px;top:26px;width:58%;height:100%"></div>
    <figure><img src="{GRID}"></figure>
  </div>

  <div class="lead" style="font-family:'Inter';font-size:44px;margin-top:50px">{c['lead']}</div>
  <div class="body" style="font-family:'Inter';font-size:23px;margin-top:16px">{c['body']}</div>

  <div class="strip" style="margin-top:38px">
    <figure><img src="{art(5)}"></figure>
    <figure><img src="{art(12)}"></figure>
    <figure><img src="{art(20)}"></figure>
  </div>

  <div style="margin-top:40px">{stats(44, 15, '18px 22px')}</div>

  <div style="margin-top:40px">{footer(c, 200, 30, 19, 14, 19, 30)}</div>
</div>"""


def wide(c):
    """1200 x 630"""
    return f"""
<div class="canvas" style="display:flex">
  <div style="flex:0 0 52%;padding:46px 34px 42px 52px;display:flex;flex-direction:column">
    <div class="eyebrow" style="font-size:15px;letter-spacing:.2em">{c['eyebrow']}</div>
    <div class="title" style="font-size:56px;margin-top:14px">WE ARE ALL<br>ONE HEART</div>
    <div class="sub" style="font-size:17px;margin-top:10px;color:#3a3527">23 Pieces, One World</div>
    <div class="body" style="font-family:'Inter';font-size:15px;margin-top:16px">{c['body']}</div>
    <div style="flex:1"></div>
    <div>{footer(c, 118, 19, 13, 11, 13, 18)}</div>
  </div>

  <div style="flex:1;position:relative;padding:46px 52px 42px 0;display:flex;
              flex-direction:column;justify-content:center">
    <div class="shot">
      <div class="block" style="left:-20px;top:20px;width:60%;height:100%"></div>
      <figure><img src="{GRID}"></figure>
    </div>
    <div style="margin-top:22px">{stats(28, 12, '12px 14px')}</div>
  </div>
</div>"""


def thumb(c):
    """1280 x 720 - YouTube thumbnail."""
    return f"""
<div class="canvas" style="display:flex;align-items:stretch">
  <div style="flex:0 0 48%;padding:52px 30px 46px 54px;display:flex;flex-direction:column">
    <div class="eyebrow" style="font-size:21px;letter-spacing:.18em">{c['eyebrow']}</div>
    <div class="title" style="font-size:72px;margin-top:18px">WE ARE<br>ALL ONE<br>HEART</div>
    <div class="sub" style="font-size:22px;margin-top:14px;color:#3a3527">23 Pieces, One World</div>
    <div style="flex:1"></div>
    <div>{footer(c, 132, 22, 14, 11, 14, 20)}</div>
  </div>

  <div style="flex:1;position:relative;padding:52px 52px 46px 0;display:flex;
              flex-direction:column;justify-content:center">
    <div class="shot">
      <div class="block" style="left:-22px;top:22px;width:60%;height:100%"></div>
      <figure><img src="{GRID}"></figure>
    </div>
    <div style="margin-top:24px">{stats(32, 13, '13px 15px')}</div>
  </div>
</div>"""


THEMES = {
    "yellow":   {"bg": "#FFD900", "ac": "#E53935"},
    "coral":    {"bg": "#F5EFE2", "ac": "#E0523C"},
    "teal":     {"bg": "#F1F0E6", "ac": "#0E7C7B"},
    "plum":     {"bg": "#F4EDE9", "ac": "#7A3B62"},
    "rose":     {"bg": "#F8EFEF", "ac": "#C2436A"},
    "gold":     {"bg": "#F7F1E1", "ac": "#A8761C"},
}

LAYOUTS = {
    "square": (1080, 1080, square),
    "portrait": (1080, 1350, portrait),
    "story": (1080, 1920, story),
    "wide": (1200, 630, wide),
    "youtube": (1280, 720, thumb),
}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for theme, t in THEMES.items():
          (OUT / theme).mkdir(exist_ok=True)
          for phase, c in COPY.items():
            for name, (w, h, fn) in LAYOUTS.items():
                var = f":root{{--bg:{t['bg']};--ac:{t['ac']}}}"
                html = (f"<html><head><meta charset='utf-8'><style>{FACE}{var}{BASE_CSS}"
                        f"html,body{{width:{w}px;height:{h}px}}</style></head>"
                        f"<body>{fn(c)}</body></html>")
                tmp = BUILD / f"{theme}_{phase}_{name}.html"
                tmp.write_text(html)
                pg = await b.new_page(viewport={"width": w, "height": h},
                                      device_scale_factor=1)
                await pg.goto("file://" + str(tmp))
                await pg.wait_for_timeout(1200)
                over = await pg.evaluate(
                    "()=>document.querySelector('.canvas').scrollHeight")
                flag = "  OVERFLOW" if over > h + 2 else ""
                out = OUT / theme / f"oneheart_{theme}_{phase}_{name}_{w}x{h}.png"
                await pg.screenshot(path=str(out))
                await pg.close()
                print(f"{theme}/{out.name}  {over}/{h}{flag}")
        await b.close()


asyncio.run(main())
