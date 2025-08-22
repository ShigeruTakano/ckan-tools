# CKANリソース操作ツール

## 概要

CKAN (Comprehensive Knowledge Archive Network) のデータセットに対して、リソースの作成・更新・削除をコマンドラインから行うためのPythonスクリプトです。

古いPython環境でも動作するよう、Python 2.7および3.x系に対応しています。

## 主な特徴

- **作成と更新**: リソース名またはIDを指定して、CSVファイルをアップロードし、リソースを新規作成または上書き更新します。
- **削除**: リソース名またはIDを指定して、特定のリソースを削除します。
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

リソース名またはリソースIDを使って、リソースを作成・更新します。
- **リソース名** (`--resource-name`) を指定した場合:
  - 存在すれば更新、存在しなければ新規作成します。
- **リソースID** (`--resource-id`) を指定した場合:
  - IDが一致するリソースを直接更新します。リソース名は無視されます。

どちらか一方の指定が必須です。

```bash
# 名前で作成・更新
python ckan_resource_cli.py --ckan-url <CKANのURL> upload <api_key> <package_id> <file_path> --resource-name <リソース名> [--description <説明>]

# IDで更新
python ckan_resource_cli.py --ckan-url <CKANのURL> upload <api_key> <package_id> <file_path> --resource-id <リソースID> [--description <説明>]
```

**引数:**
- `--ckan-url`: (必須) 接続先のCKANのURL (例: `https://data.bodik.jp`)
- `api_key`: CKANのAPIキー
- `package_id`: 対象となるデータセット（パッケージ）のIDまたは名前
- `file_path`: アップロードするCSVファイルのパス
- `--resource-name`: (作成・更新用) リソースの名前。`--resource-id`がない場合は必須です。
- `--resource-id`: (更新用) リソースのID。これを指定すると、名前に関わらずIDで対象を特定します。
- `--description`: (任意) リソースの説明。省略可能です。

### 2. リソースの削除 (`delete`)

リソース名またはリソースIDを使って、特定のリソースを削除します。

- **リソース名** (`--resource-name`) を指定した場合:
  - パッケージ内で一致する名前のリソースを検索して削除します。
- **リソースID** (`--resource-id`) を指定した場合:
  - IDが一致するリソースを直接削除します。

どちらか一方の指定が必須です。

```bash
# 名前で削除
python ckan_resource_cli.py --ckan-url <CKANのURL> delete <api_key> <package_id> --resource-name <リソース名>

# IDで削除
python ckan_resource_cli.py --ckan-url <CKANのURL> delete <api_key> <package_id> --resource-id <リソースID>
```

**引数:**
- `--ckan-url`: (必須) 接続先のCKANのURL (例: `https://data.bodik.jp`)
- `api_key`: CKANのAPIキー
- `package_id`: 対象となるデータセット（パッケージ）のIDまたは名前
- `--resource-name`: (削除用) 削除したいリソースの名前。`--resource-id`がない場合は必須です。
- `--resource-id`: (削除用) 削除したいリソースのID。`--resource-name`がない場合は必須です。

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
リソースID (`resource_id`) を指定すると、そのリソースを直接更新できます。

```python
import os
from ckan_resource_cli import create_or_update_resource

# --- 設定 ---
# CKANインスタンスのURL
CKAN_URL = "https://data.bodik.jp"  # ご自身の環境に合わせて変更してください

# 環境変数からCKANのAPIキーを取得
# 事前に export CKAN_API_KEY="your-api-key" を実行してください
API_KEY = os.environ.get("CKAN_API_KEY")

# 対象のパッケージID
PACKAGE_ID = "your-package-id"      # ご自身の環境に合わせて変更してください

# --- アップロードするファイルの準備 (カレントディレクトリに作成) ---
FILE_PATH = "sample_data.csv"
with open(FILE_PATH, "w") as f:
    f.write("col1,col2\n")
    f.write("data1,data2\n")

# --- 関数の実行 ---
if not API_KEY:
    print("エラー: 環境変数 CKAN_API_KEY が設定されていません。")
else:
    # --- パターン1: 名前でリソースを作成・更新 ---
    print("--- Pattern 1: Create/Update by name ---")
    create_or_update_resource(
        api_key=API_KEY,
        package_id=PACKAGE_ID,
        resource_name="sample-resource-by-name", # 新規作成または更新対象の名前
        file_path=FILE_PATH,
        ckan_url=CKAN_URL,
        description="Created/Updated by name."
    )
    print("\n" + "="*30 + "\n")

    # --- パターン2: IDでリソースを更新 ---
    print("--- Pattern 2: Update by ID ---")
    # resource_idを指定すると、そのIDを持つリソースが直接更新されます。
    # この場合、resource_nameは指定しても無視されます。
    RESOURCE_ID_TO_UPDATE = "your-resource-id-to-update" # 更新したいリソースのIDを指定
    create_or_update_resource(
        api_key=API_KEY,
        package_id=PACKAGE_ID,
        resource_id=RESOURCE_ID_TO_UPDATE,
        file_path=FILE_PATH,
        ckan_url=CKAN_URL,
        description="Updated by ID.",
        resource_name=None # ID指定時は不要
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

- リソースのアップロード時、ファイル形式はファイル名の拡張子から自動的に判別されます（例: `.json` → `JSON`, `.xlsx` → `XLSX`）。認識できない拡張子の場合は、デフォルトで`CSV`として登録されます。

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。