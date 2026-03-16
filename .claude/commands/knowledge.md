# ナレッジ — Knowledge Management

過去の業務ログ・学びを横断的に収集・分析し、組織知として蓄積・活用します。

## 引数
- $ARGUMENTS: サブコマンド（collect / search / report / update-rules）

## サブコマンド

### collect（デフォルト）
過去の学びログを収集し、テーマ別にナレッジベースを更新します。

1. `ai-management/work-log/learnings/` 配下の全学びログをスキャン
2. 以下のカテゴリで分類・集約:
   - **バリュエーション**: 手法選択、前提条件の置き方、よくある論点
   - **DD**: 頻出する調整項目、見落としやすいリスク、効率的な進め方
   - **ストラクチャー**: ディール構造のパターン、税務上の論点
   - **業界知識**: セクター別の特徴、マルチプル水準、KPI基準値
   - **プロセス改善**: 作業効率化のTips、テンプレート改善
   - **判断基準**: Go/No-Go判断、確認すべき閾値
3. ナレッジベースを `ai-management/reference/knowledge-base.md` に保存・更新

### search {キーワード}
蓄積されたナレッジから関連する学びを検索します。

1. `knowledge-base.md` と `work-log/learnings/` を横断検索
2. 関連度の高い学び・知見を一覧表示
3. 過去の類似案件での対応方法を提示

### report
ナレッジの蓄積状況レポートを生成します。

1. カテゴリ別の学び件数
2. 最近追加された知見 Top 10
3. 最も参照頻度の高いナレッジ
4. CLAUDE.mdに未反映の候補一覧
5. カバレッジが薄い領域の指摘

### update-rules
蓄積されたナレッジからCLAUDE.mdへの反映を提案します。

1. `knowledge-base.md` から繰り返し出現するパターンを特定
2. ルール化すべき知見を抽出
3. CLAUDE.mdへの具体的な追記案を提示（反映はユーザー確認後）

## 出力形式（collect）

```markdown
# ナレッジベース — Taiga Capital Group
最終更新: YYYY/MM/DD
収集期間: YYYY/MM/DD 〜 YYYY/MM/DD
学び総数: XX件

## バリュエーション
### 手法選択
- [YYYY/MM/DD] {案件名}: ...
### 前提条件
- [YYYY/MM/DD] {案件名}: ...

## DD
### 頻出調整項目
- [YYYY/MM/DD] {案件名}: ...
### 見落としやすいリスク
- [YYYY/MM/DD] {案件名}: ...

## ストラクチャー
...

## 業界知識
...

## プロセス改善
...

## 判断基準
...
```

## 設計思想
- 個別の学び（evening）→ 体系化されたナレッジ（knowledge collect）→ ルール化（knowledge update-rules → CLAUDE.md）
- このサイクルを回し続けることで、CLAUDE.mdが実務経験に基づいて成長していく
