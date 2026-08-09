# viewer/ — 静的HTMLビューア（F-06）

MapLibre GL JS による、層を分けて見せる地図ビューア。**自己完結**（外部CDN・タイル非依存）。

## 使い方

```bash
chiso export --pref demo   # output/ に GeoJSON/meta を生成
chiso serve  --pref demo   # data/ に配置して http://localhost:8765/ を開く
```

`chiso serve` が `output/{mesh,layers,meta}_<pref>` を `viewer/data/` にコピーし、
`viewer/data/current.json` に現在の県を書き出す。ビューアはそれを読む。

## 何が見えるか

- **推定層 ESTIMATE**（メッシュの塗り）：選択業種で、地形条件に合致した割合（重み付き）。
  薄い→濃いの単色。**合成スコアではない**。色は優劣を意味しない。
- **現況層 ACTUAL**（青）：河川・温泉・港・駅・市区町村・事業所の裏づけ。
- **法的層 LEGAL**（橙の破線）：土砂災害警戒区域・保安林・自然公園・農用地区域（相当）。
- 3層は独立トグルで重ねられる。掛け合わせた総合点は存在しない。
- **重みスライダー**：推定層の各条件の重みをUIで動かせる（表示のみ・保存しない）。
- **メッシュをクリック**：右パネルに、推定／現況／法的を**層ごとに分けて**表示し、
  各条件の `limitations`（分からないこと）を併記する。
- 画面下部に `limitations` を常時表示。合成データは `SYNTHETIC` を明示。

## 構成

```
viewer/
├── index.html          本体（バニラJS）
├── vendor/             MapLibre GL JS（同梱・オフライン可）
└── data/               chiso serve が配置する生成物（.gitignore）
```

## 設計判断

合成デモを実在の地図タイルの上に重ねると「実在の場所」と誤認されうるため、
既定では背景地図を敷かず、生成した層だけを中立的な背景に描く
（CHISO.md 迷ったときの判断基準：推定を事実と誤解する余地を作らない）。
