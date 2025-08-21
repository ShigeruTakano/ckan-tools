#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python 2.7 and 3.x compatibility
from __future__ import print_function, unicode_literals, division, absolute_import

import requests
import sys
import os
import time
import json
import argparse

# --- 設定項目 ---
# データストアへの取り込みを待つ最大時間（秒）
WAIT_FOR_DATASTORE_TIMEOUT = 120
# データストアの状態を確認する間隔（秒）
POLLING_INTERVAL = 5
# DataPusherへの再送信を試みる最大回数
DATAPUSHER_MAX_RETRIES = 2
# ----------------

def wait_for_datastore_active(session, resource_id, headers, ckan_url, max_retries=1):
    """
    リソースのDataPusherタスクが完了し、データストアがアクティブになるまで待機する。
    タイムアウトした場合は、指定された回数だけ再送信を試みる。
    """
    print("Waiting for DataPusher task to complete for resource: {}".format(resource_id))
    
    # 最初のチェックの前に一定時間待機
    print("Initial wait for DataPusher to start... ({} seconds)".format(POLLING_INTERVAL))
    time.sleep(POLLING_INTERVAL)

    retries = 0
    start_time = time.time()

    while True:
        # --- タイムアウトチェック ---
        if time.time() - start_time > WAIT_FOR_DATASTORE_TIMEOUT:
            print("Timeout reached after {} seconds.".format(WAIT_FOR_DATASTORE_TIMEOUT))
            
            if retries < max_retries:
                retries += 1
                print("Attempting to resubmit... (Attempt {} of {})".format(retries, max_retries))
                if resubmit_to_datapusher(session, resource_id, headers, ckan_url):
                    # 再送信が成功したら、タイマーをリセットして再度待機
                    start_time = time.time()
                    print("Resubmitted. Waiting again...")
                    continue
                else:
                    print("Failed to resubmit. Aborting.")
                    return False
            else:
                print("Maximum retries reached. DataPusher task did not complete.")
                return False

        # --- ステータスチェック ---
        try:
            url = "{}/api/3/action/task_status_show".format(ckan_url)
            data = json.dumps({
                "entity_id": resource_id,
                "task_type": "datapusher",
                "key": "datapusher"
            })
            response = session.post(url, headers=headers, data=data)

            if response.status_code == 404:
                print("No pending DataPusher task found. Assuming it is complete.")
                return True

            response.raise_for_status()
            task_data = response.json().get("result", {})
            
            task_state = task_data.get("state")
            print("Current DataPusher task status: {}".format(task_state))

            if task_state == "complete":
                print("DataPusher task succeeded. DataStore should be active now.")
                return True
            
            if task_state in ["failure", "error"]:
                print("DataPusher task failed.")
                if "error" in task_data:
                    print("Error details: {}".format(task_data["error"]))
                return False

        except requests.exceptions.RequestException as e:
            print("Error checking task status: {}".format(e))
        
        print("Task not finished yet. Waiting {} seconds...".format(POLLING_INTERVAL))
        time.sleep(POLLING_INTERVAL)

def get_resource_by_name(session, package_id, resource_name, headers, ckan_url):
    """指定したデータセット内でリソース名が一致するものを検索"""
    url = "{}/api/3/action/package_show".format(ckan_url)
    params = {"id": str(package_id)}
    
    try:
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        package_data = response.json().get("result", {})
        
        for resource in package_data.get("resources", []):
            if resource.get("name") == resource_name:
                return resource
        
        return None

    except requests.exceptions.RequestException as e:
        print("Error retrieving package: {}".format(e))
        sys.exit(1)
    except ValueError:
        print("Error: Invalid JSON response from server.")
        sys.exit(1)

def create_or_update_resource(api_key, package_id, resource_name, file_path, ckan_url, description=''):
    """
    リソースが存在すれば更新し、存在しなければ新規作成する。
    スタックしたリソースの自動復旧を試みる。
    """
    if not os.path.exists(file_path):
        print("Error: File not found at '{}'".format(file_path))
        sys.exit(1)

    # DataPusherのステータス確認など、JSONをPOSTする際に使用
    json_headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # ファイルアップロード時はrequestsがContent-Typeを自動設定するためAuthorizationのみ
    file_upload_headers = { "Authorization": api_key }

    with requests.Session() as session:
        print("Searching for resource '{}' in package '{}'...".format(resource_name, package_id))
        existing_resource = get_resource_by_name(session, package_id, resource_name, file_upload_headers, ckan_url)
        
        resource_id = None
        
        try:
            # --- 既存リソースの処理 ---
            if existing_resource:
                resource_id = existing_resource["id"]
                print("Found existing resource with ID: {}. Updating...".format(resource_id))
                
                # --- リソースを更新 ---
                with open(file_path, 'rb') as f:
                    files = {'upload': f}
                    update_url = "{}/api/3/action/resource_update".format(ckan_url)
                    update_data = {"id": resource_id}
                    
                    response = session.post(update_url, headers=file_upload_headers, files=files, data=update_data)
                    response.raise_for_status()
                    print("Resource updated successfully.")

            # --- 新規リソースの作成 ---
            else:
                print("Resource not found. Creating a new one...")
                with open(file_path, 'rb') as f:
                    files = {'upload': f}
                    create_url = "{}/api/3/action/resource_create".format(ckan_url)
                    create_data = {
                        "package_id": str(package_id),
                        "name": resource_name,
                        "description": description,
                        "format": "CSV"
                    }
                    
                    response = session.post(create_url, headers=file_upload_headers, files=files, data=create_data)
                    response.raise_for_status()
                    result = response.json().get("result", {})
                    resource_id = result["id"]
                    print("New resource created successfully with ID: {}.".format(resource_id))

            # --- データストアの完了待機 ---
            if resource_id:
                wait_for_datastore_active(session, resource_id, json_headers, ckan_url, max_retries=DATAPUSHER_MAX_RETRIES)

        except requests.exceptions.RequestException as e:
            print("An error occurred during the request: {}".format(e))
            if e.response:
                try:
                    print("Server response: {}".format(e.response.json()))
                except ValueError:
                    print("Server response: {}".format(e.response.text))
            sys.exit(1)
        except (IOError, OSError) as e:
            print("File error: {}".format(e))
            sys.exit(1)


def resubmit_to_datapusher(session, resource_id, headers, ckan_url):
    """
    指定されたリソースをDataPusherに再送信する。
    """
    print("Attempting to resubmit resource {} to DataPusher...".format(resource_id))
    try:
        url = "{}/api/3/action/datapusher_submit".format(ckan_url)
        data = json.dumps({"resource_id": resource_id})
        
        # datapusher_submitはContent-Type: application/json が必要
        response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        print("Successfully submitted to DataPusher.")
        return True
    except requests.exceptions.RequestException as e:
        print("Error submitting to DataPusher: {}".format(e))
        if e.response:
            try:
                print("Server response: {}".format(e.response.json()))
            except ValueError:
                print("Server response: {}".format(e.response.text))
        return False

def delete_resource(api_key, package_id, resource_name, ckan_url):
    """
    指定されたリソースを名前で検索し、削除する。
    """
    headers = {
        "Authorization": api_key
    }
    json_headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    with requests.Session() as session:
        print("Searching for resource '{}' in package '{}' to delete...".format(resource_name, package_id))
        resource_to_delete = get_resource_by_name(session, package_id, resource_name, headers, ckan_url)

        if not resource_to_delete:
            print("Resource '{}' not found in package '{}'. Nothing to delete.".format(resource_name, package_id))
            return

        resource_id = resource_to_delete["id"]
        print("Found resource with ID: {}. Deleting...".format(resource_id))

        try:
            url = "{}/api/3/action/resource_delete".format(ckan_url)
            data = {"id": resource_id}
            response = session.post(url, headers=json_headers, data=json.dumps(data))
            response.raise_for_status()
            print("Resource '{}' (ID: {}) deleted successfully.".format(resource_name, resource_id))

        except requests.exceptions.RequestException as e:
            print("An error occurred while deleting the resource: {}".format(e))
            if e.response:
                try:
                    print("Server response: {}".format(e.response.json()))
                except ValueError:
                    print("Server response: {}".format(e.response.text))
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CKANリソースを作成・更新・削除するためのコマンドラインツール。データストアへのアップロードが滞った際の自動復旧機能を備えています。")
    parser.add_argument("--ckan-url", required=True, help="The base URL of the CKAN instance (e.g., https://data.bodik.jp)")
    
    subparsers = parser.add_subparsers(dest="operation", help="Available operations")
    subparsers.required = True

    # Upload command
    parser_upload = subparsers.add_parser("upload", help="Create or update a resource.")
    parser_upload.add_argument("api_key", help="CKAN API key")
    parser_upload.add_argument("package_id", help="ID or name of the target package")
    parser_upload.add_argument("resource_name", help="Name of the resource to create or update")
    parser_upload.add_argument("file_path", help="Path to the data file (e.g., CSV)")
    parser_upload.add_argument("--description", default="Data uploaded via script", help="Optional resource description")

    # Delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a resource.")
    parser_delete.add_argument("api_key", help="CKAN API key")
    parser_delete.add_argument("package_id", help="ID or name of the target package")
    parser_delete.add_argument("resource_name", help="Name of the resource to delete")

    args = parser.parse_args()

    if args.operation == "upload":
        create_or_update_resource(args.api_key, args.package_id, args.resource_name, args.file_path, args.ckan_url, description=args.description)
    elif args.operation == "delete":
        delete_resource(args.api_key, args.package_id, args.resource_name, args.ckan_url)

    print("Script finished.")
