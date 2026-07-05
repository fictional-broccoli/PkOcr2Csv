# Pokémon Champions OCR Manager
author:fictional-broccoli

## プロジェクト概要

このプロジェクトは、**Pokémon Champions** のステータス画面スクリーンショットからポケモン情報をOCRで抽出し、CSVとして保存するための個人用ツールです。

対象は個人利用のみであり、公開サービスや多数ユーザー向けシステムは想定していません。
また、使用に際し一切の責任を負いません。

---

# 環境の移行・共有方法（別マシンで使う場合）

Python環境が整っている別のPCへプログラムを移行・共有する場合は、不要なファイルを省いて配布し、以下の手順でセットアップと実行を行います。

### 1. 配布用ファイルの作成（開発者側）
プロジェクトのルートディレクトリで **PowerShell** を開き、以下のコマンドを実行して必要なソースコードと設定ファイルだけを1発でzipにまとめます。
（これにより、重い `.venv` やビルド成果物の `dist` を自動で除外します）

```powershell
Compress-Archive -Path "src", "config", "images", "requirements.txt" -DestinationPath "./getPokemonStatus_source.zip" -Force
```

### 2. 移行先でのセットアップと動作確認（利用者側）

1. 作成された `getPokemonStatus_source.zip` を移行先PCにコピーし、任意の場所に**すべて展開**します。
2. 展開したフォルダ内（`src` や `config` が見えている階層）で **PowerShell** を開きます。
3. Windowsのセキュリティ制限により仮想環境の起動（スクリプト実行）がブロックされるのを防ぐため、まず以下のコマンドを実行して**今開いているPowerShell内だけ一時的に実行を許可**します。
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```
4. 以下のコマンドを順番に実行して、環境構築とプログラムの起動確認を行います。
   ```powershell
   # 仮想環境の作成
   python -m venv .venv

   # 仮想環境の起動（アクティベート）
   .venv\Scripts\Activate.ps1

   # 必要なライブラリの一括インストール
   pip install -r requirements.txt

   # プログラムの実行
   python src/main.py
   ```

---

# 現在の仕様

## 実行方法

### Python から実行する場合

1. 依存関係をインストールします。
   - `pip install -r requirements.txt`
2. 画像を [images](images) フォルダに配置します。
   - 画像は [images](images) 配下の直下に置きます。
   - サブディレクトリ内の画像は対象外です。
3. 実行します。
   - `python src/main.py`
4. 実行時に端末選択、OCR結果の確認、CSV保存が行われます。

### 画像フォルダ・出力先を変更する場合

実行時に以下の方法で指定できます。
引数を追加せずに起動した場合は聞きます

- 引数指定
  - `python src/main.py C:\path\to\images C:\path\to\output`
- 環境変数指定
  - `POKEMON_IMAGES_DIR`
  - `POKEMON_DATABASE_DIR`
- 起動時の対話入力
  - 何も入力しなければ既定値を使います。

### exe 化した場合の使用方法
※なんかできんのよ　調査中
1. 実行ファイルを任意の場所に配置します。
2. 同じフォルダに以下を用意します。
   - [images](images)
   - [config](config)
   - [database](database)
3. [images](images) フォルダ直下に対象画像を置きます。
4. 実行ファイルをダブルクリックして起動します。
5. 起動時に画像フォルダと出力先を入力できます。
6. 端末選択後、OCR結果を確認して保存できます。

> exe 化する場合は、実行ファイルと同じ階層に設定ファイルや出力先ディレクトリがある状態で動作させるのが安全です。

---

## 取得するデータ

1行につき1匹のポケモンをCSVに保存します。

保存対象の項目

- name
- nickname
- type
- hp
- hp_effort
- attack
- attack_effort
- defense
- defense_effort
- sp_attack
- sp_attack_effort
- sp_defense
- sp_defense_effort
- speed
- speed_effort
- nature
- ability
- moves1
- moves2
- moves3
- moves4

---

## データ保存

現時点ではCSV（BOM無し）を正規データとします。

- 1回の実行で複数画像を処理できます。
- 複数画像を処理した場合、同じ日付のCSVへ順に追記されます。
- CSV名は `YYYYMMDD.csv` 形式です。

---

## OCRについて

OCRは固定レイアウトを前提とします。

- 座標は [config/regions.json](config/regions.json) で管理します。
- 項目ごとの文字ルールは [config/fields_schema.json](config/fields_schema.json) で管理します。
- 端末ごとの設定は `active_device` と `devices` で切り替えます。

現在の設定例

- `devices.aquos_sensu_10`
- `devices.iphone13`
- `devices.googlePixel_8a`

---

## ディレクトリ構成

project/

├─ images/
├─ database/
├─ config/
├─ src/
├─ tests/
├─ requirements.txt
└─ README.md

---

# 今後の方針

今後は以下を予定しています。

- OCR精度の向上
- 取得範囲の調整支援
- GUIや操作性の改善
- 検索・整理機能の追加

---

# 開発方針

このプロジェクトでは以下を重視しています。

- 保守性
- 拡張性
- シンプルな構成
- Python のみで完結できること
