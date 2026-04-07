# my-power-app

建物の電力消費データを読み込み、日別パターンのクラスタリングと気象データの突合を行い、レポートとして可視化する Streamlit アプリです。

電力データの傾向をクラスタ単位で把握しながら、休日や季節との関係を同時に確認できます。

## できること

- 電力消費 CSV をアップロードして日別データを解析
- 延床面積で割った原単位ベースの時系列に変換
- PCA と階層クラスタリングで日別パターンを分類
- 気象庁データを取得して休日判定・季節分類を付与
- クラスタ別の代表曲線レポートを表示
- クラスタと気象条件を並べたカレンダー画像を生成
- 結合済みの RAW データを画面上で確認
- クラスタリング結果とカレンダー画像を Word レポートとして保存

## アプリ画面の構成

このアプリは主に次の 3 つの画面要素で構成されています。

サイドバー:

- 電力データ CSV のアップロード
- 延床面積の入力
- 地点名の入力
- クラスタ数の自動決定または手動指定
- 解析実行ボタン
- 解析後の Word レポート保存

メイン上部:

- アプリ概要の表示
- 解析結果のサマリー表示

解析結果タブ:

- Analysis Report: パターン分析レポート
- Calendar Preview: カレンダープレビュー
- Merged Raw Data: 結合済み RAW データ表

## 解析内容

### 1. 電力データの整形

アップロードした CSV を読み込み、日付をインデックスとして扱います。
その後、電力量を延床面積で割り、Wh/sqm ベースの原単位データに変換します。

### 2. クラスタリング

[analyzer.py](analyzer.py) では以下の流れでクラスタリングを行います。

- 標準化
- PCA 実行
- 固有値 1.0 以上の主成分を採用
- Ward 法による階層クラスタリング
- クラスタ数は自動決定または手動指定

### 3. 気象データの付与

[scraper.py](scraper.py) で気象庁の日別データを取得します。

- 地点コードは [data/stations.csv](data/stations.csv) から取得
- 気温データを取得
- 土日と祝日を休日として判定
- 12月30日から1月3日も休日として判定
- 気温に応じて Cooling / Intermediate / Heating に分類
- 取得済みデータは data フォルダに CSV キャッシュとして保存

### 4. 可視化

[plotter.py](plotter.py) では主に次の 2 種類の可視化を生成します。

統合レポート:

- 生データの日別曲線
- クラスタ色分け後の日別曲線
- クラスタ重心曲線
- 各クラスタの曜日・季節内訳

カレンダーレポート:

- クラスタ別の色分け表示
- 気象・休日条件による色分け表示

## 公開方法

このアプリは GitHub にリポジトリを置き、Streamlit Community Cloud で公開する想定です。

### 公開手順

1. このプロジェクトを GitHub に push する
2. Streamlit Community Cloud にログインする
3. New app から GitHub リポジトリを選ぶ
4. Branch を選び、Main file path に app.py を指定する
5. Deploy を実行する

デプロイ後は、Streamlit Community Cloud 上で Web アプリとして利用できます。

### Streamlit Community Cloud での前提

- 依存パッケージは [requirements.txt](requirements.txt) から自動でインストールされます
- 実行エントリーポイントは [app.py](app.py) です
- data フォルダ内のファイルもリポジトリに含めておく必要があります

## ローカル確認用の環境

- Python 3.8 以上

依存パッケージは [requirements.txt](requirements.txt) に定義しています。

主な使用ライブラリ:

- streamlit
- pandas
- numpy
- scikit-learn
- scipy
- matplotlib
- beautifulsoup4
- jpholiday
- python-docx

## ローカルセットアップ

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ローカル起動方法

```bash
streamlit run app.py
```

起動後、ブラウザで Streamlit アプリが開きます。ローカル確認用の手順であり、本番公開は Streamlit Community Cloud を想定しています。

現在の実装では、最初に簡易パスワード入力があります。
デフォルト値は [app.py](app.py) 内で PASSWORD = "acorn" として定義されています。

## 入力データの前提

アップロードする電力データ CSV は、日付を 1 列目に持ち、各時間帯の列を含む形式を想定しています。

例:

```csv
Date,00:00,00:30,01:00,01:30
2019-04-01,120,118,115,113
2019-04-02,130,127,122,119
```

前提:

- 1 列目は日付
- 時刻列は 00:00 のようにコロンを含む列名
- 1 行が 1 日分のデータ
- 数値列は電力量データ

## 使い方

1. GitHub 経由で公開した Streamlit アプリを開く
2. パスワード画面でパスワードを入力する
3. サイドバーから電力データ CSV をアップロードする
4. 延床面積を入力する
5. 地点名を入力する
6. クラスタ数を自動決定するか、手動で指定する
7. 分析を実行する
8. 結果をタブで確認する
9. 必要に応じて Word レポートを保存する

## 出力されるもの

### Analysis Report

以下を 1 枚の統合レポートとして表示します。

- 生の日別曲線
- クラスタ別に色分けした日別曲線
- クラスタ代表曲線
- クラスタごとの曜日・季節内訳

### Calendar Preview

月ごとのカレンダー上で以下を確認できます。

- 各日の所属クラスタ
- 気象条件と休日条件による分類

### Merged Raw Data

解析後の結合済み RAW データを表形式で表示します。

クラスタリング自体は延床面積で割った原単位データで実行しますが、このタブでは床面積で割っていない値を保持したデータを表示します。

含まれる主な列:

- 時刻別電力データ
- Cluster
- AverageTemperature
- IsHoliday
- Season
- DayType

## データファイル

- [data/stations.csv](data/stations.csv): 地点名と気象庁の地点コード対応表
- [data/weather_岡山_2019.csv](data/weather_岡山_2019.csv): キャッシュ済み気象データ例
- [data/weather_神戸_2019.csv](data/weather_神戸_2019.csv): キャッシュ済み気象データ例

## 主要ファイル

- [app.py](app.py): Streamlit UI、セッション状態管理、分析実行フロー
- [analyzer.py](analyzer.py): PCA と階層クラスタリング
- [scraper.py](scraper.py): 気象庁データ取得、地点コード解決、キャッシュ処理
- [plotter.py](plotter.py): 統合レポートとカレンダー描画

## 注意点

- 気象データ取得は外部サイトの構造やネットワーク状態に依存します
- 地点名は [data/stations.csv](data/stations.csv) の name 列と一致する必要があります
- パスワードは [app.py](app.py) に固定値で書かれているため、公開運用では secrets 管理などへ移した方が安全です
- Streamlit Community Cloud 上では外部アクセスや実行時間に制約がかかる場合があります
- Word レポート出力には python-docx を使用しています
