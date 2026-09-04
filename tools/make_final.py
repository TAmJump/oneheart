#!/usr/bin/env python3
"""ONE HEART — CHILDREN CEO PROJECT, corrected five-panel set."""

import asyncio
import pathlib

from playwright.async_api import async_playwright

ROOT = pathlib.Path("/home/claude/oneheart")
FONTS = pathlib.Path("/home/claude/fonts/node_modules/@fontsource")
OUT = pathlib.Path("/mnt/user-data/outputs/ceo-final")
OUT.mkdir(parents=True, exist_ok=True)
BUILD = pathlib.Path("/home/claude/finalbuild")
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
.canvas{width:100%;min-height:100%;background:var(--bg);display:flex;
        flex-direction:column;padding:52px 50px 44px}
img{display:block;width:100%;height:auto}

.top{display:flex;align-items:flex-start;gap:20px}
.num{flex:0 0 70px;height:70px;background:var(--fg);color:var(--bg);
     font-family:'Inter';font-weight:900;font-size:40px;display:flex;
     align-items:center;justify-content:center;line-height:1}
.tt{flex:1}
h1{font-weight:900;letter-spacing:-.025em;line-height:1.2;font-size:50px}
.deck{font-weight:700;line-height:1.7;margin-top:14px;font-size:20px;opacity:.94}

.block{background:#FFF8EC;color:#111;padding:22px 24px;margin-top:14px}
.block h3{font-weight:900;font-size:26px;line-height:1.35}
.block p{font-weight:400;font-size:18px;line-height:1.85;margin-top:10px}
.block .hl{font-weight:900}
.block ul{margin-top:10px;list-style:none}
.block li{font-weight:700;font-size:18px;line-height:1.7;padding-left:26px;position:relative}
.block li::before{content:"—";position:absolute;left:0;font-weight:900;color:var(--bg)}

.accent{background:var(--fg);color:var(--bg);padding:24px 26px;margin-top:16px;
        font-weight:900;line-height:1.42;font-size:30px}
.accent .s{display:block;font-size:19px;font-weight:700;margin-top:10px;opacity:.94}

.row{display:flex;gap:9px;margin-top:14px}
.row .c{flex:1;background:#FFF8EC;color:#111;padding:15px 10px;text-align:center;
        font-weight:700;font-size:16px;line-height:1.45}
.row .c b{display:block;font-weight:900;font-size:18px;margin-bottom:5px}

.flow{display:flex;gap:9px;margin-top:14px}
.st{flex:1;background:#FFF8EC;color:#111;padding:16px 13px}
.st .n{font-family:'Inter';font-weight:900;font-size:19px;color:var(--bg);background:#111;
       width:31px;height:31px;display:flex;align-items:center;justify-content:center;line-height:1}
.st h4{font-weight:900;font-size:18px;line-height:1.3;margin-top:11px}
.st p{font-weight:400;font-size:14px;line-height:1.6;margin-top:7px}

.grid22{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-top:12px}
.grid22 figure{border:2px solid #111;background:#111;line-height:0}

.two{display:flex;gap:14px;margin-top:14px}
.two > div{flex:1;margin-top:0}

.note{font-weight:400;font-size:15px;line-height:1.75;margin-top:14px;opacity:.92}

.spacer{flex:1;min-height:12px}
.bar{display:flex;align-items:center;gap:20px;border-top:5px solid var(--fg);
     margin-top:18px;padding-top:18px}
.bar .qr{flex:0 0 104px;border:4px solid var(--fg);background:#fff;line-height:0}
.bar .id{flex:1}
.bar .id .b{font-family:'Inter';font-weight:900;font-size:23px;line-height:1.05}
.bar .id .b small{display:block;font-size:11px;letter-spacing:.2em;margin-top:6px;opacity:.82}
.bar .id .t{font-weight:700;font-size:14px;line-height:1.6;margin-top:9px;opacity:.9}
.bar .kpi{display:flex;gap:10px}
.bar .kpi div{background:var(--fg);color:var(--bg);padding:12px 14px;text-align:center;
              min-width:104px}
.bar .kpi .n{font-family:'Inter';font-weight:900;font-size:25px;line-height:1}
.bar .kpi .l{font-family:'Inter';font-weight:700;font-size:10px;letter-spacing:.14em;
             margin-top:6px}
.tag{font-family:'Inter';font-weight:900;font-size:14px;letter-spacing:.12em;
     margin-top:12px;text-align:right;opacity:.88}
"""

W, H = 1080, 1440


def head(n, title, deck=""):
    d = f'<div class="deck">{deck}</div>' if deck else ""
    return f"""<div class="top"><div class="num">{n}</div>
<div class="tt"><h1>{title}</h1>{d}</div></div>"""


BAR = f"""
<div class="spacer"></div>
<div class="bar">
  <figure class="qr"><img src="{QR}"></figure>
  <div class="id">
    <div class="b">ONE HEART<small>CHILDREN CEO PROJECT</small></div>
    <div class="t">22のアイデアから生まれたキャラクターを、アートから商品へ。世界へ。未来へ。<br>
    2026.09.08 TUE — 10.08 THU ／ Kickstarter ／ oneheart.tamjump.com</div>
  </div>
  <div class="kpi">
    <div><div class="n">22</div><div class="l">CHARACTERS</div></div>
    <div><div class="n">60,000</div><div class="l">PEOPLE</div></div>
  </div>
</div>
<div class="tag">CREATE VALUE. CHOOSE YOUR LIFE.</div>"""


def p1():
    cells = "".join(f'<figure><img src="{art(i)}"></figure>' for i in range(1, 23))
    return head(1, "自分で生み出した<br>価値は、自分のものだ。",
                "使い道も、自分で決めていい。") + f"""
<div class="block">
  <h3>22のアイデアから生まれた、22体のキャラクター。</h3>
  <div class="grid22">{cells}</div>
  <p>22体は、病気と向き合う子どもたちのアイデアから生まれました。絵にしたのは私です。</p>
</div>
<div class="row">
  <div class="c"><b>治療に</b>使ってもいい</div>
  <div class="c"><b>好きな服を</b>買ってもいい</div>
  <div class="c"><b>好きなものを</b>食べてもいい</div>
  <div class="c"><b>家族と</b>出かけてもいい</div>
  <div class="c"><b>将来のために</b>貯めてもいい</div>
</div>
<div class="accent">自分の人生は、自分で決める。
  <span class="s">用途まで大人が決めた瞬間、また大人がその子の人生を決めることになる。</span></div>
<div class="note">これは寄付ではありません。子ども自身が価値を生み、収益を得られるようにするための仕組みを、
いまつくっているところです。まず1作品を成立させる段階です。</div>
""" + BAR


def p2():
    return head(2, "その選択肢は、<br>誰が決めた？",
                "治療も、教育も、仕事も、暮らしも。<br>本当は自分で選びたいのに、選ぶ前に決まっていることが多い。") + """
<div class="block">
  <h3>選択肢は、生まれた時点でもう狭まっている。</h3>
  <p>生まれた場所。家庭。経済状況。制度の線引き。
  病気の治療も、進学先も、働き方も、住む場所も、自分で選ぶ前から範囲が決まっていることがあります。
  <span class="hl">誰かが間違えているわけではなく、設計上そうなっています。</span></p>
</div>
<div class="block">
  <h3>必要なのは、誰かの正解より、自分の納得。</h3>
  <p>大人の都合や、常識や、ルールに合わせて、自分の考えを引っ込めてきた人がいます。
  それでも、その人生を生きるのは本人です。</p>
</div>
<div class="block">
  <h3>選択肢は、つくることもできる。</h3>
  <p>学ぶ。試す。つながる。声を出す。その一歩が、自分だけでなく、
  同じ場所にいる誰かの範囲も広げます。</p>
</div>
<div class="accent">選択肢は、与えられるものだけじゃない。
  <span class="s">自分でも、つくれる。</span></div>
""" + BAR


def p3():
    return head(3, "選べることも、<br>生きる力になる。",
                "治療を受けることは、スタートライン。<br>その先にある人生を、自分で選べるようにする。") + """
<div class="block">
  <h3>治療の先にある、人生の選択肢を広げる。</h3>
  <p>病気を治すだけではありません。暮らす場所、働き方、学び、つながり、お金の使い方。
  医療を入口にして、その先まで広げていきます。</p>
</div>
<div class="block">
  <h3>それぞれのペースで進めばいい。</h3>
  <p>できない日があってもいい。ゆっくりでもいい。比べる必要も、競う必要もありません。
  自分のペースで進み続けた積み重ねが、自分らしい人生をつくる力になります。</p>
</div>
<div class="block">
  <h3>支え合うからこそ、選べる未来がつくれる。</h3>
  <p>ひとりでは解決できないことがあります。だからこそ、支え合い、知恵を出し合う。
  国や立場を超えて選択肢を増やしていけば、誰もが安心して未来を選べる社会に近づきます。</p>
</div>
<div class="row">
  <div class="c"><b>治療を受ける</b>健康を取り戻す</div>
  <div class="c"><b>学ぶ</b>可能性を広げる</div>
  <div class="c"><b>仕事を選ぶ</b>やりがいと収入</div>
  <div class="c"><b>安心して暮らす</b>自分らしい生活</div>
  <div class="c"><b>人とつながる</b>孤立せずに済む</div>
</div>
<div class="accent">命を支える。その先の人生まで、本人が選べる未来へ。</div>
""" + BAR


def p4():
    return head(4, "人間は、<br>2度生まれる。",
                "生まれることは選べない。どう生きるかは、これから選べる。") + """
<div class="two">
  <div class="block">
    <h3>1度目は、在るために。</h3>
    <p>生きていること。そこにいること。生きるための条件が整うまでは、
    そこに在ることだけで力を使いきる時期があります。</p>
  </div>
  <div class="block">
    <h3>2度目は、生きるために。</h3>
    <p>何のために生きるかを自分で決めること。食わず嫌いをしなければ、
    案外それが自分の力になるかもしれない。おっかなびっくりで構いません。</p>
  </div>
</div>
<div class="block">
  <h3>どちらの段階にも、その人なりの難しさがある。</h3>
  <p>生きるための条件が足りないときの難しさと、条件はあるのに何のために生きるか分からないときの
  難しさ。<span class="hl">どちらが軽いということはありません。どちらも、生きていく過程です。</span></p>
</div>
<div class="accent">大切なのは、どちらの生き方も否定しないこと。
  <span class="s">自分のペースで、自分の力で、自分の人生をつくっていく。</span></div>
<div class="note">「人間は2度生まれる。1度目は存在するために、2度目は生きるために」
— ジャン＝ジャック・ルソー『エミール』より</div>
""" + BAR


def p5():
    return head(5, "君のアイデアが、<br>君の未来をつくる。",
                "アイデアがキャラクターになり、作品になり、世界の人の心を動かす。<br>"
                "その先を、本人の未来につなげる。これがつくろうとしている仕組みです。") + """
<div class="flow">
  <div class="st"><div class="n">1</div><h4>アイデアを出す</h4>
    <p>君の考えや想いが<br>キャラクターになる</p></div>
  <div class="st"><div class="n">2</div><h4>作品・商品にする</h4>
    <p>アート作品やグッズなど<br>いろいろな形で展開する</p></div>
  <div class="st"><div class="n">3</div><h4>売上が生まれる</h4>
    <p>世界中の人が共感し<br>キャラクターが価値を持つ</p></div>
  <div class="st"><div class="n">4</div><h4>本人に戻す</h4>
    <p>生まれた利益を<br>発案した本人に帰属させる</p></div>
</div>
<div class="accent">君は、支援されて終わらない。
  <span class="s" style="font-size:46px;font-weight:900;margin-top:12px">君が社長だ。</span></div>
<div class="row">
  <div class="c"><b>世界とつながる</b>国や言葉を超えて<br>心をつなぐ</div>
  <div class="c"><b>誰かの支えになる</b>次の子どもを<br>支える力になる</div>
  <div class="c"><b>人生をデザインする</b>収益の使い道を<br>自分で選べる</div>
  <div class="c"><b>循環をつくる</b>子どもも大人も<br>関わる全員に返る</div>
</div>
<div class="note">未成年者の権利保護、保護者同意、著作権と収益分配、税務。国ごとに設計しなければ
成立しない部分が多く、確立された制度があるわけではありません。まず1作品を成立させて、
実務として何が必要かを洗い出す段階です。</div>
""" + BAR


PANELS = [
    {"id": "1", "bg": "#E8A020", "fg": "#111111", "fn": p1},
    {"id": "2", "bg": "#1F6FA5", "fg": "#FFF8EC", "fn": p2},
    {"id": "3", "bg": "#0B7A72", "fg": "#FFF8EC", "fn": p3},
    {"id": "4", "bg": "#6E3159", "fg": "#FFF8EC", "fn": p4},
    {"id": "5", "bg": "#D6402C", "fg": "#FFF8EC", "fn": p5},
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
            out = OUT / f"oneheart_final_{p['id']}_{W}x{H}.png"
            await pg.screenshot(path=str(out))
            await pg.close()
            print(f"{out.name}  scale={fit:.2f}")
        await b.close()


asyncio.run(main())
