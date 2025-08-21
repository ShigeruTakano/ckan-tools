# CKANリソース操作ツール

## 概要

CKAN (Comprehensive Knowledge Archive Network) のデータセットに対して、リソースの作成・更新・削除をコマンドラインから行うためのPythonスクリプトです。

古いPython環境でも動作するよう、Python 2.7および3.x系に対応しています。

## 主な特徴

- **作成と更新**: CSVファイルを指定して、リソースを新規作成または上書き更新します。
- **削除**: パッケージIDとリソース名を指定して、特定のリソースを削除します。
- **高精度なデータストア同期**: リソースのアップロード後、CKANの非同期タスク（`task_status_show`）を直接監視することで、データストアへの取り込み完了を正確に待機します。これにより、処理が「保留」のままになる問題を解消します。
- **安全な自動復旧機能**: 更新時にリソースが「保留中」などでスタックしている場合、DataPusherに処理を再実行させることで、安全な復旧を試みます。これにより、既存のデータを削除することなく、スタックした状態からの復帰が可能です。**リソースIDは維持されます。**
- **柔軟な設定**: 接続先CKANのURLをコマンドラインオプションで指定できます。
- **互換性**: Python 2.7とPython 3の両方で動作します。

## 動作環境

- Python 2.7 / 3.x
- `requests` ライブラリ

`requests`ライブラリがインストールされていない場合は、以下のコマンドでインストールしてください。
```bash
pip install requests
```

## 使い方

本ツールは、コマンドラインから操作対象（`upload`または`delete`）と接続先CKANのURLを指定して実行します。

### 1. リソースの作成・更新 (`upload`)

指定したリソース名が存在しない場合は新規作成、存在する場合はそのリソースをファイルで上書き更新します。

```bash
python ckan_resource_cli.py --ckan-url <CKANのURL> upload <api_key> <package_id> <resource_name> <file_path> [--description <説明>]
```

**引数:**
- `--ckan-url`: (必須) 接続先のCKANのURL (例: `https://data.bodik.jp`)
- `api_key`: CKANのAPIキー
- `package_id`: 対象となるデータセット（パッケージ）のIDまたは名前
- `resource_name`: 作成または更新したいリソースの名前
- `file_path`: アップロードするCSVファイルのパス
- `--description`: (任意) リソースの説明。省略可能です。

### 2. リソースの削除 (`delete`)

指定したリソースを削除します。

```bash
python ckan_resource_cli.py --ckan-url <CKANのURL> delete <api_key> <package_id> <resource_name>
```

**引数:**
- `--ckan-url`: (必須) 接続先のCKANのURL (例: `https://data.bodik.jp`)
- `api_key`: CKANのAPIキー
- `package_id`: 対象となるデータセット（パッケージ）のIDまたは名前
- `resource_name`: 削除したいリソースの名前

## 実行サンプル

`run_sample.sh` に具体的な実行例を記載しています。スクリプト内の変数をご自身の環境に合わせて設定し、ご利用ください。

```bash
# スクリプトに実行権限を付与
chmod +x run_sample.sh

# 環境変数にAPIキーを設定
export CKAN_API_KEY="your-api-key-here"

# サンプルスクリプトを実行
./run_sample.sh
```

## ライブラリとしての利用

`ckan_resource_cli.py` は、他のPythonスクリプトから直接インポートして利用することも可能です。
特に `create_or_update_resource` 関数は、外部プログラムからCKANリソースを自動で操作したい場合に便利です。

### サンプルコード

以下は、`create_or_update_resource` 関数を呼び出すサンプルコードです。

```python
import os
from ckan_resource_cli import create_or_update_resource

# --- 設定 ---
# CKANインスタンスのURL
CKAN_URL = "https://data.bodik.jp"  # ご自身の環境に合わせて変更してください

# 環境変数からCKANのAPIキーを取得
# 事前に export CKAN_API_KEY="your-api-key" を実行してください
API_KEY = os.environ.get("CKAN_API_KEY")

# 対象のパッケージIDとリソース名
PACKAGE_ID = "your-package-id"      # ご自身の環境に合わせて変更してください
RESOURCE_NAME = "sample-resource"   # ご自身の環境に合わせて変更してください
DESCRIPTION = "このリソースはサンプルスクリプトから作成されました。"

# アップロードするファイルの準備 (カレントディレクトリに作成)
FILE_PATH = "sample_data.csv"
with open(FILE_PATH, "w") as f:
    f.write("col1,col2\n")
    f.write("data1,data2\n")

# --- 関数の実行 ---
if not API_KEY:
    print("エラー: 環境変数 CKAN_API_KEY が設定されていません。")
else:
    print(f"リソース '{RESOURCE_NAME}' を作成・更新します...")
    create_or_update_resource(
        api_key=API_KEY,
        package_id=PACKAGE_ID,
        resource_name=RESOURCE_NAME,
        file_path=FILE_PATH,
        ckan_url=CKAN_URL,
        description=DESCRIPTION
    )
    print("処理が完了しました。")

# --- 後片付け ---
os.remove(FILE_PATH)
```

### 実行方法

1. 上記のコードを `example.py` のようなファイル名で保存します。
2. ターミナルで環境変数 `CKAN_API_KEY` を設定します。
   ```bash
   export CKAN_API_KEY="your-api-key-here"
   ```
3. スクリプトを実行します。
   ```bash
   python example.py
   ```

## 注意事項

- リソースのアップロード時、ファイル形式は`CSV`として登録されます。他の形式（Excelなど）を想定している場合は、スクリプト内の`"format": "CSV"`の部分を適宜修正してください。

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。