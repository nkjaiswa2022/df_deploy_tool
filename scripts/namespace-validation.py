# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

params = sys.argv

PROJECT_ID = params[1]
REGION = params[2]
INSTANCE = params[3]
SERVICE_ACCOUNT_FILE = params[4]
DEPLOYMENT_LOCATION = params[5]
NAMESPACE = params[6]
ENV = params[7]
DEPLOYMENT_TYPE = params[8]

# SCAN_SUB_DIR = "src" # For 'All' appraoch, scan this directory for the pipeline JSON files
# SCAN_FILE = "deploy/config/src" # For 'Diff' approach, read this file for modified pipeline files

ERRORS = []

def validate_namespace(api_endpoint, token, namespace):
    namespaces_list = get_namespaces(api_endpoint, token)

    if any(ns['name'] == namespace for ns in namespaces_list) == False:
        _m = f"Namespace '{namespace}' missing in {INSTANCE}"
        log.error(_m)
    else:
        _m = f"Namespace '{namespace}' validated successfully in {INSTANCE}"
        print(_m)

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

validate_namespace(api_endpoint, token, NAMESPACE)