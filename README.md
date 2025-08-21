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

## 注意事項

- リソースのアップロード時、ファイル形式は`CSV`として登録されます。他の形式（Excelなど）を想定している場合は、スクリプト内の`"format": "CSV"`の部分を適宜修正してください。

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。
