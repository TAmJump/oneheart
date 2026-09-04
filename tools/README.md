# tools — 画像生成スクリプト

チャットのコンテナは毎回リセットされるので、生成スクリプトはここに置いてある。
次のセッションでは `git clone` 後、下の準備をしてから実行する。

## 準備

```bash
pip install playwright pillow qrcode --break-system-packages
python3 -m playwright install chromium
mkdir -p /home/claude/fonts && cd /home/claude/fonts
npm install @fontsource/inter @fontsource/noto-sans-jp
```

スクリプトは以下の絶対パスを前提にしている。clone 先が違う場合は書き換える。

- リポジトリ: `/home/claude/oneheart`
- フォント: `/home/claude/fonts/node_modules/@fontsource`
- QR: `/home/claude/qr_ks.png`（このフォルダの `assets/qr_ks.png` をコピー）

## スクリプト

| ファイル | 出力 | 内容 |
|---|---|---|
| `make_set.py` | `ceo-set/` | ①〜⑤が1本の流れになる5枚組（黄×黒×赤・1080×1440）**最新版** |
| `make_final_yellow.py` | `ceo-final-yellow/` | 独立5枚（黄×黒×赤） |
| `make_final.py` | `ceo-final/` | 独立5枚（クリーム＋5色） |
| `make_world_posters.py` | `world-posters/` | 全世界向け5枚（日英併記・1080×1350） |
| `make_posters.py` | `posters/` | 告知文A〜E（日本語・1080×1350） |
| `make_ceo_posters2.py` | `ceo-posters-v2/` | 旧5枚（医療制度から入る版） |
| `make_flyers.py` | `flyers/` | SNSチラシ 6配色×5サイズ×2フェーズ＝60点 |

## QRの作り直し

```python
import qrcode
from qrcode.constants import ERROR_CORRECT_M
url = "https://www.kickstarter.com/projects/tamj/we-are-all-one-heart-23-pieces-one-world"
qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=16, border=2)
qr.add_data(url); qr.make(fit=True)
qr.make_image(fill_color="#111111", back_color="#FFFFFF").save("/home/claude/qr_ks.png")
```

参照元タグ付きURLに変えるときは `url` を差し替えて再生成し、各スクリプトを回し直す。

## はみ出し制御

各スクリプトは `zoom` を 0.02 刻みで上下させて、`.canvas` の高さがキャンバスに収まる最大値を探す。
文言を足したら自動で縮み、削ったら自動で拡大するので、フォントサイズを手で調整する必要はない。
