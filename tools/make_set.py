#!/usr/bin/env python3
"""ONE HEART — connected five-panel set (yellow / black / red)."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/ceo-set")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/setbuild")
BUILD.mkdir(exist_ok=True)

INTER = FONTS / "inter/files"
NOTO = FONTS / "noto-sans-jp/files"
QR = "file:///home/claude/qr_ks.png"
GRID = f"file://{ROOT}/images/23grid.jpg"

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
body{background:#FFD900;color:#111;font-family:'NotoJP','Inter',sans-serif;
     -webkit-font-smoothing:antialiased}
.canvas{width:100%;min-height:100%;background:#FFD900;display:flex;
        flex-direction:column;padding:50px 50px 42px}
img{display:block;width:100%;height:auto}
.red{color:#E32219}

.track{display:flex;align-items:center;gap:9px;margin-bottom:22px}
.track .d{width:34px;height:9px;background:#111;opacity:.22}
.track .d.on{opacity:1;background:#E32219}
.track .lb{margin-left:auto;font-family:'Inter';font-weight:900;font-size:14px;
           letter-spacing:.18em}

.top{display:flex;align-items:flex-start;gap:20px}
.num{flex:0 0 68px;height:68px;background:#111;color:#FFD900;
     font-family:'Inter';font-weight:900;font-size:38px;display:flex;
     align-items:center;justify-content:center;line-height:1}
.tt{flex:1}
h1{font-weight:900;letter-spacing:-.03em;line-height:1.16;font-size:54px}
.deck{font-weight:700;line-height:1.65;margin-top:13px;font-size:20px}

.block{background:#111;color:#FFF8EC;padding:22px 24px;margin-top:13px}
.block h3{font-weight:900;font-size:26px;line-height:1.32;color:#FFD900}
.block p{font-weight:400;font-size:18px;line-height:1.85;margin-top:10px}
.block .hl{font-weight:900;color:#FFD900}

.accent{background:#111;color:#FFF8EC;padding:24px 26px;margin-top:14px;
        font-weight:900;line-height:1.4;font-size:33px}
.accent .s{display:block;font-size:19px;font-weight:700;margin-top:11px;color:#FFD900}

.row{display:flex;margin-top:13px;border:4px solid #111}
.row .c{flex:1;background:#FFD900;padding:15px 10px;text-align:center;
        font-weight:700;font-size:16px;line-height:1.45;border-right:3px solid #111}
.row .c:last-child{border-right:0}
.row .c b{display:block;font-weight:900;font-size:18px;margin-bottom:5px}

.flow{display:flex;gap:9px;margin-top:13px}
.st{flex:1;background:#FFF8EC;padding:16px 13px;border:4px solid #111}
.st .n{font-family:'Inter';font-weight:900;font-size:19px;color:#FFD900;background:#111;
       width:31px;height:31px;display:flex;align-items:center;justify-content:center;line-height:1}
.st h4{font-weight:900;font-size:18px;line-height:1.3;margin-top:11px}
.st p{font-weight:400;font-size:14px;line-height:1.6;margin-top:7px}

.grid22{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:12px}
.grid22 figure{border:2px solid #FFD900;background:#111;line-height:0}

.shot{margin-top:13px}
.shot figure{border:5px solid #111;background:#111;line-height:0}

.kpirow{display:flex;margin-top:13px;border:4px solid #111;background:#111}
.kpirow div{flex:1;padding:16px 12px;text-align:center;border-right:3px solid #FFD900}
.kpirow div:last-child{border-right:0}
.kpirow .n{font-family:'Inter';font-weight:900;font-size:38px;color:#FFD900;line-height:1}
.kpirow .l{font-weight:700;font-size:14px;color:#FFF8EC;margin-top:8px}

.note{font-weight:400;font-size:15px;line-height:1.75;margin-top:12px}

.spacer{flex:1;min-height:10px}
.next{background:#E32219;color:#fff;padding:16px 24px;margin-top:14px;
      display:flex;align-items:center;gap:16px}
.next .a{font-family:'Inter';font-weight:900;font-size:15px;letter-spacing:.16em}
.next .t{font-weight:900;font-size:24px;line-height:1.25}

.bar{display:flex;align-items:center;gap:20px;border-top:5px solid #111;
     margin-top:16px;padding-top:16px}
.bar .qr{flex:0 0 98px;border:4px solid #111;background:#fff;line-height:0}
.bar .id{flex:1}
.bar .id .b{font-family:'Inter';font-weight:900;font-size:22px;line-height:1.05}
.bar .id .b small{display:block;font-size:11px;letter-spacing:.2em;margin-top:5px}
.bar .id .t{font-weight:700;font-size:14px;line-height:1.6;margin-top:8px}
.bar .kpi{display:flex;gap:9px}
.bar .kpi div{background:#111;color:#FFD900;padding:11px 13px;text-align:center;min-width:98px}
.bar .kpi .n{font-family:'Inter';font-weight:900;font-size:24px;line-height:1}
.bar .kpi .l{font-family:'Inter';font-weight:700;font-size:10px;letter-spacing:.14em;margin-top:5px}
.tag{font-family:'Inter';font-weight:900;font-size:14px;letter-spacing:.12em;
     margin-top:11px;text-align:right}
"""

W, H = 1080, 1440


def track(n):
    dots = "".join(f'<div class="d{" on" if i <= n else ""}"></div>' for i in range(1, 6))
    return f'<div class="track">{dots}<div class="lb">{n} / 5</div></div>'


def head(n, title, deck=""):
    d = f'<div class="deck">{deck}</div>' if deck else ""
    return track(n) + f"""<div class="top"><div class="num">{n}</div>
<div class="tt"><h1>{title}</h1>{d}</div></div>"""


def nxt(label, title):
    return f"""<div class="next"><div class="a">{label}</div>
<div class="t">{title}</div></div>"""


BAR = f"""
<div class="bar">
  <figure class="qr"><img src="{QR}"></figure>
  <div class="id">
    <div class="b">ONE HEART<small>CHILDREN CEO PROJECT</small></div>
    <div class="t">2026.09.08 TUE — 10.08 THU ／ Kickstarter ／ oneheart.tamjump.com</div>
  </div>
  <div class="kpi">
    <div><div class="n">23</div><div class="l">ARTWORKS</div></div>
    <div><div class="n">60,000</div><div class="l">PEOPLE</div></div>
  </div>
</div>
<div class="tag">CREATE VALUE. CHOOSE YOUR LIFE.</div>"""


def p1():
    return head(1, "選択肢は、<br>選ぶ前に<span class=\"red\">決まっている</span>。",
                "治療も、学びも、働き方も、住む場所も。<br>"
                "自分で選ぶ前から、範囲が決まっていることがある。") + """
<div class="block">
  <h3>最初から狭まっている。</h3>
  <p>生まれた場所。家庭。経済状況。制度の線引き。
  自分では選べなかったものが、その先の選べる範囲を決めています。</p>
</div>
<div class="block">
  <h3>支える仕組みは、必要だ。</h3>
  <p>家族が支え、税と保険が集まり、制度がつくられ、医療が届く。
  この道があるから治療が受けられます。<span class="hl">否定するために始めた話ではありません。</span></p>
</div>
<div class="block">
  <h3>ただ、本人が動かせる部分が少ない。</h3>
  <p>誰かが間違えているわけではなく、設計上そうなっています。
  よかれと思って決めたことが、その子の選べる範囲を静かに形づくっていきます。</p>
</div>
<div class="accent">選択肢は、与えられるものだけじゃない。
  <span class="s" style="font-size:32px;color:#E32219">自分でも、つくれる。</span></div>
<div class="spacer"></div>
""" + nxt("NEXT — 02", "もう一本、道をつくる。") + BAR


def p2():
    cells = "".join(f'<figure><img src="{art(i)}"></figure>' for i in range(1, 23))
    return head(2, "もう一本、<br>道を<span class=\"red\">つくる</span>。",
                "支える道はそのまま。生み出す道を、1本足す。") + f"""
<div class="flow">
  <div class="st"><div class="n">1</div><h4>アイデアを出す</h4>
    <p>その子の考えが<br>キャラクターになる</p></div>
  <div class="st"><div class="n">2</div><h4>作品・商品にする</h4>
    <p>アートやグッズなど<br>いろいろな形で展開する</p></div>
  <div class="st"><div class="n">3</div><h4>価値が生まれる</h4>
    <p>世界中の人が共感し<br>キャラクターに価値がつく</p></div>
  <div class="st"><div class="n">4</div><h4>本人に戻す</h4>
    <p>生まれた利益を<br>発案した本人に帰属させる</p></div>
</div>
<div class="block">
  <h3>22のアイデアから生まれた、22体のキャラクター。</h3>
  <div class="grid22">{cells}</div>
  <p>22体は、病気と向き合う子どもたちのアイデアから生まれました。絵にしたのは私です。</p>
</div>
<div class="note">これは寄付ではありません。子ども自身が価値を生み、収益を得られるようにするための
仕組みを、いまつくっているところです。</div>
<div class="spacer"></div>
""" + nxt("NEXT — 03", "その第一歩が、1枚の顔写真。") + BAR


def p3():
    return head(3, "第一歩は、<br>1枚の<span class=\"red\">顔写真</span>。",
                "世界中から顔写真を集めて、モザイク作品をつくる。") + f"""
<div class="shot" style="width:76%;margin-left:auto"><figure><img src="{GRID}"></figure></div>
<div class="kpirow">
  <div><div class="n">23</div><div class="l">作品</div></div>
  <div><div class="n">2,500</div><div class="l">枚で1作品</div></div>
  <div><div class="n">60,000</div><div class="l">ピース</div></div>
  <div><div class="n">&yen;500</div><div class="l">1枠</div></div>
</div>
<div class="block">
  <h3>顔が1つあれば、参加できる。</h3>
  <p>国も、年齢も、職業も問いません。受け取るのは完成作品のデジタル版と、
  作品名・ピース番号・座標が入った参加証明書です。
  <span class="hl">2026年9月8日、Kickstarterで公開します。</span></p>
</div>
<div class="accent">作品を見る人ではなく、<span class="red">作品の中身</span>になる。</div>
<div class="spacer"></div>
""" + nxt("NEXT — 04", "生まれた価値を、どうするか。") + BAR


def p4():
    return head(4, "使い道は、<br><span class=\"red\">本人</span>が決める。",
                "自分で生み出した価値なら、何に使うかも自分で決められる。") + """
<div class="row">
  <div class="c"><b>治療に</b>使ってもいい</div>
  <div class="c"><b>好きな服を</b>買ってもいい</div>
  <div class="c"><b>好きなものを</b>食べてもいい</div>
  <div class="c"><b>家族と</b>出かけてもいい</div>
  <div class="c"><b>将来のために</b>貯めてもいい</div>
</div>
<div class="block">
  <h3>用途を決めた瞬間、元に戻る。</h3>
  <p>「病気なんだから治療に使いなさい」と大人が使い道を決めた瞬間、
  また大人がその子の人生を決めることになります。
  <span class="hl">使い道を決める経験そのものが、この仕組みで渡したいものです。</span></p>
</div>
<div class="accent">自分で生み出した価値だから、<br>自分で<span class="red">使い道</span>を決める。</div>
<div class="note">未成年者の権利保護、保護者同意、著作権と収益分配、税務。国ごとに設計しなければ
成立しない部分が多く、確立された制度があるわけではありません。まず1作品を成立させて、
実務として何が必要かを洗い出す段階です。</div>
<div class="spacer"></div>
""" + nxt("NEXT — 05", "だから、君が社長だ。") + BAR


def p5():
    return head(5, "君は、<br>支援されて終わらない。") + """
<div class="accent" style="font-size:78px;text-align:center;padding:36px 26px;
     letter-spacing:.02em">君が<span class="red">社長</span>だ。</div>
<div class="row">
  <div class="c"><b>世界とつながる</b>国や言葉を超えて<br>心をつなぐ</div>
  <div class="c"><b>誰かの支えになる</b>次の子どもを<br>支える力になる</div>
  <div class="c"><b>人生をデザインする</b>収益の使い道を<br>自分で選べる</div>
  <div class="c"><b>循環をつくる</b>子どもも大人も<br>関わる全員に返る</div>
</div>
<div class="block">
  <h3>参加は1枠500円。23作品から選べます。</h3>
  <p>顔写真1枚が1ピースになり、2,500枚で1作品が完成します。
  <span class="hl">2026年9月8日から10月8日まで、Kickstarterで公開します。</span>
  下のQRから参加できます。</p>
</div>
<div class="spacer"></div>
<div class="next"><div class="a">JOIN</div>
<div class="t">WE ARE ALL ONE HEART ／ 世界中の人と一緒に、未来を変えていこう。</div></div>
""" + BAR


PANELS = [
    {"id": "1", "fn": p1},
    {"id": "2", "fn": p2},
    {"id": "3", "fn": p3},
    {"id": "4", "fn": p4},
    {"id": "5", "fn": p5},
]


def page(p, scale):
    return f"""<html><head><meta charset="utf-8"><style>
{FACE}
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
            f = BUILD / f"p{p['id']}.html"
            scale, fit = 1.0, None
            for _ in range(60):
                if await measure(b, p, scale, f) <= H:
                    fit = scale
                    break
                scale = round(scale - 0.02, 2)
            if fit and fit >= 0.999:
                while fit < 1.24:
                    trial = round(fit + 0.02, 2)
                    if await measure(b, p, trial, f) > H:
                        break
                    fit = trial
            f.write_text(page(p, fit))
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto("file://" + str(f))
            await pg.wait_for_timeout(900)
            out = OUT / f"oneheart_set_{p['id']}_{W}x{H}.png"
            await pg.screenshot(path=str(out))
            await pg.close()
            print(f"{out.name}  scale={fit:.2f}")
        await b.close()


asyncio.run(main())
