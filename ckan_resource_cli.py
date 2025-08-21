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
# ----------------

def wait_for_datastore_active(session, resource_id, headers, ckan_url):
    """
    リソースがデータストアでアクティブになるまで待機する。
    """
    print("Waiting for DataStore to become active for resource: {}".format(resource_id))
    start_time = time.time()
    
    while True:
        if time.time() - start_time > WAIT_FOR_DATASTORE_TIMEOUT:
            print("Timeout reached. DataStore not active after {} seconds.".format(WAIT_FOR_DATASTORE_TIMEOUT))
            return False

        try:
            url = "{}/api/3/action/resource_show".format(ckan_url)
            params = {"id": resource_id}
            response = session.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            resource_data = response.json().get("result", {})
            
            if resource_data.get("datastore_active"):
                print("DataStore is now active.")
                return True
            
            if resource_data.get("state") == "error":
                print("DataStore import failed. Please check the resource on CKAN.")
                return False

        except requests.exceptions.RequestException as e:
            print("Error checking resource status: {}".format(e))
        
        print("DataStore not active yet. Waiting {} seconds...".format(POLLING_INTERVAL))
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

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # requestsはファイルアップロード時にContent-Typeを自動設定するため、ここでは削除
    upload_headers = { "Authorization": api_key }

    with requests.Session() as session:
        print("Searching for resource '{}' in package '{}'...".format(resource_name, package_id))
        existing_resource = get_resource_by_name(session, package_id, resource_name, upload_headers, ckan_url)
        
        resource_id = None
        
        try:
            # --- 既存リソースの処理 ---
            if existing_resource:
                resource_id = existing_resource["id"]
                print("Found existing resource with ID: {}. Checking status...".format(resource_id))

                # データストアがアクティブでない場合、復旧を試みる
                if not existing_resource.get("datastore_active"):
                    print("Warning: Resource datastore is not active. Attempting to reset it...")
                    try:
                        reset_url = "{}/api/3/action/datastore_delete".format(ckan_url)
                        reset_data = json.dumps({"resource_id": resource_id, "force": True})
                        
                        # datastore_deleteはContent-Type: application/json が必要
                        response = session.post(reset_url, headers=headers, data=reset_data)
                        
                        # 404はテーブルが存在しない場合なので許容
                        if response.status_code == 404:
                            print("Datastore table did not exist, which is fine.")
                        else:
                            response.raise_for_status()

                        print("Datastore table for resource {} has been reset.".format(resource_id))

                    except requests.exceptions.RequestException as e:
                        print("Error resetting datastore: {}".format(e))
                        if e.response:
                            try:
                                print("Server response: {}".format(e.response.json()))
                            except ValueError:
                                print("Server response: {}".format(e.response.text))
                        print("Proceeding with update anyway...")
                
                # --- リソースを更新 ---
                print("Updating resource...")
                with open(file_path, 'rb') as f:
                    files = {'upload': f}
                    update_url = "{}/api/3/action/resource_update".format(ckan_url)
                    update_data = {"id": resource_id}
                    
                    response = session.post(update_url, headers=upload_headers, files=files, data=update_data)
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
                    
                    response = session.post(create_url, headers=upload_headers, files=files, data=create_data)
                    response.raise_for_status()
                    result = response.json().get("result", {})
                    resource_id = result["id"]
                    print("New resource created successfully with ID: {}.".format(resource_id))

            # --- データストアの完了待機 ---
            if resource_id:
                wait_for_datastore_active(session, resource_id, upload_headers, ckan_url)

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
    parser = argparse.ArgumentParser(description="A command-line tool to create, update, or delete CKAN resources.")
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

    print("
Script finished.")
