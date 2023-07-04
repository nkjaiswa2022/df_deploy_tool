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

SCAN_SUB_DIR = f"securekey/{ENV.lower()}" # For 'All' appraoch, scan this directory for the pipeline JSON files
SCAN_FILE = "deploy/config/securekey" # For 'Diff' approach, read this file for modified pipeline files

ERRORS = []

def deploy_securekeys(api_endpoint, namespace, token, securekeys_file):
    headers = {'Authorization': f"Bearer {token}", 'Content-Type': "application/json", 'Accept': "application/json"}
    securekeys_json = getJSONContent(securekeys_file)
    
    if isinstance(securekeys_json, list):
        for obj in securekeys_json:
            keyname = obj['name']
            keyvalueprop = obj['value']
            deployment_url = f"{api_endpoint}/v3/namespaces/{namespace}/securekeys/{keyname}"
            response = requests.put(deployment_url, json=keyvalueprop, headers=headers)
            if response.status_code != 200:
                ERRORS.append(response.content)
                raise ValueError(response.content)
                sys.exit(1)
    elif isinstance(securekeys_json, dict):
        keyname = securekeys_json['name']
        keyvalueprop = securekeys_json['value']
        deployment_url = f"{api_endpoint}/v3/namespaces/{namespace}/securekeys/{keyname}"
        response = requests.put(deployment_url, json=keyvalueprop, headers=headers)
        if response.status_code != 200:
            ERRORS.append(response.content)
            raise ValueError(response.content)
            sys.exit(1)
    
    _m = f"Secure keys deployed to '{namespace}' namespace"
    print(_m)

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                securekey_file = f
                deploy_securekeys(api_endpoint, token, NAMESPACE, securekey_file)
    else:
        _m = f"Invalid location: {SCAN_DIR}"
        log.error(_m)
        raise SystemError(_m)

else:
    
    # ------------- Deployment type - 'Diff' --------------
    
    SCAN_FILE = f"{DEPLOYMENT_LOCATION}/{SCAN_FILE}"
    
    if (os.path.exists(SCAN_FILE)):
        df = pd.read_csv(SCAN_FILE, sep="\s+", header=None)
        data = df.to_string(header=False,
                  index=False,
                  index_names=False).split('\n')
        contents = [','.join(ele.strip().split()) for ele in data]
        
        for val in contents:
            # temp = content.split(' ') # Split each row into an array
            # temp = content
            mode = val.split(",")[0].strip() # Get mode - A (Add), D (Delete) or M (Modify)
            temp = ''.join(val.split(",")[1].split())

            if temp.startswith('securekey'):
                securekey_file = temp.replace('securekey/', '') # Remove path prefix to get the name
                if securekey_file.endswith(".json"):
                    if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                        # Assuming there is a single secure keys JSON file
                        deploy_securekeys(api_endpoint, token, NAMESPACE, securekey_file)
                    # elif mode.strip().upper() == 'D':
                        # delete_preference(api_endpoint, token, preference_file)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)