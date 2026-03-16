# シミュレーション — taiga_sim シミュレーション実行

Taiga Capital Groupの30年ビジネスシミュレーションを実行し、結果を分析します。

## 引数
- $ARGUMENTS: 実行モード（single / monte-carlo / scenarios / all）

## やること

### single（デフォルト）
```bash
python run_simulation.py
```
単一30年シミュレーションを実行し、主要指標（EV、売上、EBITDA、MOIC、IRR）をサマリ表示。

### monte-carlo
```bash
python run_monte_carlo.py
```
1000試行のモンテカルロ分析を実行し、P10/P50/P90の分布を表示。

### scenarios
```bash
python run_scenarios.py
```
Base/Bull/Bearの3シナリオ比較を実行。

### all
```bash
python run_all_analyses.py
```
全分析を一括実行（所要時間: 約60分）。

## 出力
- 実行結果のサマリを画面表示
- チャート・レポートは `data/` に自動保存
- 分析コメントを `ai-management/output/analysis/` に保存
