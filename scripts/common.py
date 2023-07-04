# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google. 

import os
import requests
import json
import sys
import csv
import urllib3
import logging as log
from datetime import datetime
import pandas as pd
import openpyxl
from requests.structures import CaseInsensitiveDict
from google.oauth2 import service_account
from enum import Enum
import builtins as __builtin__

import google.auth
import google.auth.transport.requests

urllib3.disable_warnings()

loggerPresent = False

class D_TYPE(Enum):
    ALL = 'All'
    DIFF = 'diff'


class RECORD_TYPE(Enum):
    ADD = 'A'
    MODIFY = 'M'
    DELETE = 'D'

# --------------------------------------------------
# Overload default print function to include logging
# --------------------------------------------------
def print(*args, **kwargs):
    log.debug(*args, **kwargs)
    return __builtin__.print(*args, **kwargs)

# --------------------------------------------------
# Read data from a CSV file
# --------------------------------------------------
def read_csv_details(file_path):
    if os.path.isfile(file_path) == True:
        df = pd.read_csv(file_path, skiprows=0)
        data = df.to_string(header=False, index=False, index_names=False).split('\n')
        contents = [','.join(ele.strip().split()) for ele in data]
        return contents
    else:
        contents = ""
        _m = f"CSV file not found: {file_path}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)


# --------------------------------------------------
# Get JSON content from a JSON file
# --------------------------------------------------
def getJSONContent(json_path):
    if os.path.isfile(json_path) == True:
        with open(json_path, 'r') as j:
            contents = json.loads(j.read())
            return contents
    else:
        contents = ""
        _m = f"JSON file not found: {json_path}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)


# --------------------------------------------------
# Check REST API response for status 200. If not,
# then raise an error with response content
# --------------------------------------------------
def process_response_json(response):
    if response.status_code != 200:
        log.error(response.content)
        raise SystemError(response.content)
        sys.exit(1)
    else:
        return response.json()

# --------------------------------------------------
# Check REST API response for status 200. If not,
# then raise an error with response content, else
# print the message provided as argument
# --------------------------------------------------
def process_response_message(response, message):
    if response.status_code != 200:
        log.error(response.content)
        raise SystemError(response.content)
        sys.exit(1)
    else:
        print(message)


# --------------------------------------------------
# Get REST API end-point based on project id, 
# region and data fusion instance
# --------------------------------------------------
def get_CDAPendpoint(project_id, region, instance_name):
    region_list = {'us-central1':'usc1','us-east1':'use1','us-east4':'use4','us-west1': 'usw1'}
    region_short = region_list[region]
    cdap_endpoint = "https://"+ instance_name + "-" + project_id + "-dot-" + region_short + ".datafusion.googleusercontent.com/api"
    return cdap_endpoint


# --------------------------------------------------
# Google cloud authentication mechanism based on
# service account
# --------------------------------------------------
def auth_gcp(service_account_file):
    # credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    if os.path.isfile(service_account_file) == True:
        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/userinfo.email'])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        token = credentials.token
        return token
    else:
        _m = f"Service account file not found : {service_account_file}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)


# --------------------------------------------------
# Get all namespaces within a specified instance
# --------------------------------------------------
def get_namespaces(api_endpoint, token):
    request_url = f"{api_endpoint}/v3/namespaces/"
    headers = {'Authorization': f"Bearer {token}"}
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get plugins (scope:USER) for a namespace 
# --------------------------------------------------
def get_user_plugins(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts?scope=USER"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get all plugins (scope: SYSTEM and scope: USER)
# for a namespace
# --------------------------------------------------
def get_namespace_plugins(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get all pipelines deployed within a namespace
# --------------------------------------------------
def get_namespace_pipelines(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{namespace}/apps"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get all namspace level preferences
# --------------------------------------------------
def get_namespace_preferences(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{namespace}/preferences"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get data fusion instance level preference
# --------------------------------------------------
def get_system_preferences(api_endpoint, token):
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    deployment_url = f"{api_endpoint}/v3/preferences"
    response = requests.get(deployment_url, headers=headers)
    return process_response_json(response)


# --------------------------------------------------
# Get namespace level secure keys
# --------------------------------------------------
def get_namespace_securekeys(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{namespace}/securekeys"
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(request_url, headers=headers)
    return process_response_json(response)
