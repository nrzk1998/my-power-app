# my-power-app

このリポジトリは、建物の電力消費データを読み込み、クラスタリングと気象データを組み合わせて可視化する簡易ツールです。主にStreamlitでインタラクティブに解析・レポート出力を行います。

**主な機能**
- 電力消費データのクラスタリング（PCA + 階層クラスタリング）
- 気象庁データのスクレイピングとキャッシュ
- クラスタごとの代表曲線・カレンダービジュアライズの生成

**前提 / 要件**
- Python 3.8+ が必要
- 依存パッケージは [requirements.txt](requirements.txt) を参照してください。

**セットアップ（例）**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell の場合: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**実行方法**
- ローカルでStreamlitアプリを起動します:

```bash
streamlit run app.py
```

**データ**
- サンプル／補助データは `data/` に置きます。
	- [data/stations.csv](data/stations.csv) : 気象庁地点コード一覧（地点名とコード）
	- [data/weather_岡山_2019.csv](data/weather_岡山_2019.csv) 等: スクレイピングで保存されるキャッシュ済み気象データ

**主要ファイル**
- [app.py](app.py): Streamlit アプリのエントリーポイント（UI、アップロード、実行フロー）
- [scraper.py](scraper.py): 気象庁データの取得／キャッシュ処理
- [analyzer.py](analyzer.py): データ前処理とクラスタリングロジック
- [plotter.py](plotter.py): グラフ／レポート作成ロジック

**使い方の流れ**
1. サイドバーから電力データCSVをアップロード
2. 延床面積や地点名を設定（地点名は `data/stations.csv` の値に合わせる）
3. 「分析実行」を押すと、気象データ取得→クラスタリング→可視化が実行されます
4. サイドバーからCSV/PNGで結果をダウンロード可能

**注意事項**
- 気象データのスクレイピングはネットワークと対象サイトの構造に依存します。取得失敗時の例外処理は最小限なので、必要に応じて堅牢化してください。

---
作成者: (あなたの名前)
