"""chiso コマンド（CLI）。

サブコマンド: fetch / terrain / assess / stagnation / export / serve / run
`chiso run --pref demo` でデータ生成〜出力までを一本で再現できる（受け入れ基準6）。

CHISO.md の原則を遵守: 三層を混ぜない / 合成スコアを持たない /
limitations を必須 / 断定語を出さない / 乱数を使わない。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import click
import pandas as pd

from . import __version__
from .config import (DERIVED_DIR, OUTPUT_DIR, RAW_DIR, VIEWER_DIR,
                     ensure_dirs, get_prefecture)
from .dem import DemGrid


def _load_aux(pref_key: str) -> dict:
    p = RAW_DIR / f"aux_{pref_key}.json"
    if not p.exists():
        raise click.ClickException(
            f"補助レイヤーが未取得: {p}. 先に `chiso fetch --pref {pref_key}` を実行。")
    return json.loads(p.read_text(encoding="utf-8"))


@click.group(help="地相（CHISO）: 地形が養える産業と、詰まりの兆候を層を分けて並べて見せる。")
@click.version_option(__version__, prog_name="chiso")
def main() -> None:
    ensure_dirs()


# --- F-01 fetch ---------------------------------------------------------------
@main.command(help="対象県のデータを取得（実データ or 合成デモ）し data/raw/ に保存。")
@click.option("--pref", default="demo", show_default=True, help="県キー: demo/nagano/oita/yamagata")
@click.option("--demo", "force_demo", is_flag=True, help="合成デモデータを生成（ネットワーク不要）")
@click.option("--force", is_flag=True, help="キャッシュを無視して再取得")
def fetch(pref: str, force_demo: bool, force: bool) -> None:
    p = get_prefecture(pref)
    dem_path = RAW_DIR / f"dem_{p.key}.npz"
    if dem_path.exists() and not force:
        click.echo(f"[fetch] キャッシュ済み: {dem_path} (--force で再取得)")
        return

    if p.synthetic or force_demo:
        from .fetch.demo import generate_demo
        dem, aux = generate_demo(p)
        click.echo(f"[fetch] 合成デモ生成: {p.name_ja} "
                   f"DEM {dem.nrows}x{dem.ncols} / 補助レイヤー {len(aux['layers'])}種")
        click.echo("[fetch] 注意: これは合成データです。実在の土地を表しません。")
    else:
        from .fetch.gsi_dem import fetch_dem
        from .fetch.known import has_known, build_known_aux
        click.echo(f"[fetch] GSI DEM タイル取得を試行: {p.name_ja} ...")
        try:
            dem = fetch_dem(p)
        except Exception as e:  # noqa: BLE001 — 到達不能/ポリシー遮断を明示する
            raise click.ClickException(
                f"GSI 標高タイルに到達できませんでした: {e}\n"
                "  この環境はネットワークポリシーで GSI を遮断していることがあります。\n"
                "  GSI に到達できるローカル環境で実行してください。"
                "（動作確認だけなら `chiso run --pref demo`）")
        dem.save(dem_path)
        # 既知の温泉地は、地質分類・温泉存在のみを引用付きで手動投入（known.py）。
        if has_known(p.key):
            aux = build_known_aux(p)
            click.echo(f"[fetch] 既知事実を手動投入: 火山性地質={bool(aux['layers']['volcanic_geology']['polygons'])} / "
                       f"温泉点={len(aux['layers']['onsen_points']['points'])}")
            click.echo("[fetch] 注意: 法規制/河川/統計は未投入（空）。地形は DEM から算出。")
        else:
            # その他の実県の補助レイヤー取り込みは v0.2。空 aux を置く。
            aux = {"synthetic": False, "pref": p.key, "pref_name_ja": p.name_ja,
                   "layers": {}, "municipalities": []}
            click.echo("[fetch] 注意: 補助レイヤー（河川/温泉/法規制/統計）取り込みは v0.2 未実装。"
                       " 地形由来の ESTIMATE のみ評価されます。")
        (RAW_DIR / f"aux_{p.key}.json").write_text(
            json.dumps(aux, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"[fetch] 保存: {dem_path}")


# --- F-02 terrain -------------------------------------------------------------
@main.command(help="DEM から地形指標を算出し 1kmメッシュに集約（parquet 出力）。")
@click.option("--pref", default="demo", show_default=True)
def terrain(pref: str) -> None:
    from .terrain.metrics import compute_terrain_mesh
    p = get_prefecture(pref)
    dem_path = RAW_DIR / f"dem_{p.key}.npz"
    if not dem_path.exists():
        raise click.ClickException(f"DEM 未取得: {dem_path}. 先に `chiso fetch --pref {pref}`。")
    dem = DemGrid.load(dem_path)
    df = compute_terrain_mesh(dem)
    out = DERIVED_DIR / f"terrain_{p.key}.parquet"
    df.to_parquet(out, index=False)
    click.echo(f"[terrain] メッシュ数 {len(df)} → {out}")


# --- F-03 assess --------------------------------------------------------------
@main.command(help="rules/*.yaml を読み、メッシュ×業種の適性を層別に評価（合成しない）。")
@click.option("--pref", default="demo", show_default=True)
def assess(pref: str) -> None:
    from .assess.rules import load_all_rules
    from .assess.engine import World, assess as run_assess
    p = get_prefecture(pref)
    tpath = DERIVED_DIR / f"terrain_{p.key}.parquet"
    if not tpath.exists():
        raise click.ClickException(f"地形指標 未算出: {tpath}. 先に `chiso terrain --pref {pref}`。")
    terrain_df = pd.read_parquet(tpath)
    aux = _load_aux(p.key)
    rules = load_all_rules()
    world = World(terrain_df, aux)
    long_df, wide_df = run_assess(world, rules)
    long_df.to_parquet(DERIVED_DIR / f"assessment_long_{p.key}.parquet", index=False)
    wide_df.to_parquet(DERIVED_DIR / f"assessment_{p.key}.parquet", index=False)
    click.echo(f"[assess] 業種 {len(rules)} / 評価行 {len(long_df)} → "
               f"assessment_{p.key}.parquet")


# --- F-04 stagnation ----------------------------------------------------------
@main.command(help="市区町村単位の詰まり指標（空き家率・高齢化率・事業所減少率）を並置。")
@click.option("--pref", default="demo", show_default=True)
def stagnation(pref: str) -> None:
    from .stagnation.metrics import compute_stagnation
    p = get_prefecture(pref)
    aux = _load_aux(p.key)
    df = compute_stagnation(aux)
    out = DERIVED_DIR / f"stagnation_{p.key}.parquet"
    df.to_parquet(out, index=False)
    click.echo(f"[stagnation] 市区町村 {len(df)} → {out}")


# --- F-05 export --------------------------------------------------------------
@main.command(help="GeoJSON + CSV + meta を output/ に生成（layer と limitations を含む）。")
@click.option("--pref", default="demo", show_default=True)
def export(pref: str) -> None:
    from .assess.rules import load_all_rules
    from .export import writers
    p = get_prefecture(pref)
    terrain_df = pd.read_parquet(DERIVED_DIR / f"terrain_{p.key}.parquet")
    wide = pd.read_parquet(DERIVED_DIR / f"assessment_{p.key}.parquet")
    long_df = pd.read_parquet(DERIVED_DIR / f"assessment_long_{p.key}.parquet")
    stag = pd.read_parquet(DERIVED_DIR / f"stagnation_{p.key}.parquet")
    aux = _load_aux(p.key)
    rules = load_all_rules()

    g1 = writers.write_mesh_geojson(p, terrain_df, wide, long_df)
    g2 = writers.write_layers_geojson(p, aux)
    csvs = writers.write_csvs(p, terrain_df, long_df, stag)
    meta = writers.write_meta(p, rules)
    for f in [g1, g2, *csvs, meta]:
        click.echo(f"[export] {f}")


# --- F-06 serve ---------------------------------------------------------------
@main.command(help="output/ をビューアに配置し、ローカル HTTP サーバで地図を開く。")
@click.option("--pref", default="demo", show_default=True)
@click.option("--port", default=8765, show_default=True)
@click.option("--no-server", is_flag=True, help="サーバを起動せずファイル配置のみ")
def serve(pref: str, port: int, no_server: bool) -> None:
    p = get_prefecture(pref)
    data_dir = VIEWER_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in [f"mesh_{p.key}.geojson", f"layers_{p.key}.geojson", f"meta_{p.key}.json"]:
        src = OUTPUT_DIR / name
        if not src.exists():
            raise click.ClickException(f"出力が無い: {src}. 先に `chiso export --pref {pref}`。")
        shutil.copy(src, data_dir / name)
    (data_dir / "current.json").write_text(
        json.dumps({"pref": p.key, "pref_name_ja": p.name_ja,
                    "synthetic": p.synthetic}, ensure_ascii=False),
        encoding="utf-8")
    click.echo(f"[serve] ビューアへ配置: {data_dir}")
    if no_server:
        click.echo(f"[serve] 手動起動: python3 -m http.server {port} -d {VIEWER_DIR}")
        return
    import functools
    import http.server
    import socketserver
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(VIEWER_DIR))
    click.echo(f"[serve] http://localhost:{port}/  (Ctrl-C で停止)")
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\n[serve] 停止")


# --- run: full pipeline -------------------------------------------------------
@main.command(help="fetch→terrain→assess→stagnation→export を一本で実行（受け入れ基準6）。")
@click.option("--pref", default="demo", show_default=True)
@click.option("--force", is_flag=True)
@click.pass_context
def run(ctx: click.Context, pref: str, force: bool) -> None:
    ctx.invoke(fetch, pref=pref, force=force)
    ctx.invoke(terrain, pref=pref)
    ctx.invoke(assess, pref=pref)
    ctx.invoke(stagnation, pref=pref)
    ctx.invoke(export, pref=pref)
    p = get_prefecture(pref)
    click.echo("")
    click.echo(f"[run] 完了: {p.name_ja}")
    if p.synthetic:
        click.echo("[run] 注意: 合成データです。実在の土地・統計を表しません。")
    click.echo(f"[run] 地図で見る: chiso serve --pref {pref}")


if __name__ == "__main__":
    main()
