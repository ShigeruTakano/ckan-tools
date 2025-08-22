#!/bin/bash

# =================================================================
# ckan_resource_cli.py 実行サンプルスクリプト
# =================================================================

# --- 設定項目 ---
# ご自身の環境に合わせて、以下の変数を設定してください。

# CKANのURL
CKAN_URL="https://data.bodik.jp"

# CKANのAPIキー（APIトークン）
# シェルスクリプトに直接書き込む代わりに、環境変数から読み込むことを推奨します。
# ターミナルで事前に export CKAN_API_KEY="your_api_key" を実行してください。
API_KEY="${CKAN_API_KEY}"

# 操作対象のパッケージ（データセット）ID
PACKAGE_ID="your-package-id"

# 操作対象のリソース名
RESOURCE_NAME="your-resource-name"

# アップロードするファイルのパス (upload時に使用)
FILE_PATH="./data/sample.csv"

# リソースの説明 (upload時に使用、任意)
DESCRIPTION="サンプルデータ (自動更新)"


# --- スクリプト実行 ---

# Pythonスクリプトのパス
SCRIPT_PATH="./ckan_resource_cli.py"

# APIキーが設定されているかチェック
if [ -z "$API_KEY" ]; then
    echo "エラー: 環境変数 CKAN_API_KEY が設定されていません。"
    echo "例: export CKAN_API_KEY=\"your_api_key\""
    exit 1
fi

echo "CKANへの処理を開始します..."
echo "---------------------------------"

# --- upload（作成・更新）を実行 ---
# こちらのブロックを有効にしています。不要な場合はコメントアウトしてください。
echo "操作: upload"
python "$SCRIPT_PATH" \
    --ckan-url "$CKAN_URL" \
    upload \
    "$API_KEY" \
    "$PACKAGE_ID" \
    "$FILE_PATH" \
    --resource-name "$RESOURCE_NAME" \
    --description "$DESCRIPTION"


# --- delete（削除）を実行 ---
# 削除を実行したい場合は、以下のいずれかのブロックのコメントを解除し、
# 上のuploadブロックをコメントアウトしてください。

# --- パターンA: 名前で削除 ---
#
# echo "操作: delete (by name)"
# python "$SCRIPT_PATH" \
#     --ckan-url "$CKAN_URL" \
#     delete \
#     "$API_KEY" \
#     "$PACKAGE_ID" \
#     --resource-name "$RESOURCE_NAME"


# --- パターンB: IDで削除 ---
#
# # 削除したいリソースのIDを設定してください
# RESOURCE_ID_TO_DELETE="your-resource-id-to-delete"
#
# echo "操作: delete (by ID)"
# python "$SCRIPT_PATH" \
#     --ckan-url "$CKAN_URL" \
#     delete \
#     "$API_KEY" \
#     "$PACKAGE_ID" \
#     --resource-id "$RESOURCE_ID_TO_DELETE"

echo "---------------------------------"
echo "処理が完了しました。"
