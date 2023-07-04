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

SCAN_SUB_DIR = f"preference/{ENV.lower()}" # For 'All' appraoch
SCAN_FILE = "deploy/config/preference" # For 'Diff' approach

ERRORS = []

def deploy_preference(api_endpoint, token, target_namespace, preference_json):
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"

    deployment_url = f"{api_endpoint}/v3/namespaces/{target_namespace}/preferences"
    response = requests.put(deployment_url, json=preference_json, headers=headers)
    
    _m = f"Preference updated succesfully to '{target_namespace}' namespace"
    process_response_message(response, _m)
    

def add_preference(api_endpoint, token, target_namespace, preference_file):
    # Get existing preferences for the namespace
    # existing_preference_json = get_namespace_preferences(api_endpoint, token, target_namespace)

    # Get new preference json 
    new_preference_json = getJSONContent(preference_file)

    # # Merge and deploy
    # merged = existing_preference_json
    # if isinstance(new_preference_json, list):
    #     for obj in new_preference_json:
    #         merged = {**merged, **obj}
    # elif isinstance(new_preference_json, dict):
    #         merged = {**existing_preference_json, **new_preference_json}

    deploy_preference(api_endpoint, token, target_namespace, new_preference_json)

def delete_preference(api_endpoint, token, target_namespace, preference_file):
    # Get existing preferences for the namespace
    existing_preference_json = get_namespace_preferences(api_endpoint, token, target_namespace)

    # Get new preference json 
    del_preference_json = getJSONContent(preference_file)

    # Remove and deploy
    for o in del_preference_json:
        if o in existing_preference_json:
            del existing_preference_json[o]

    deploy_preference(api_endpoint, token, target_namespace, existing_preference_json)

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                preference_file = f
                add_preference(api_endpoint, token, NAMESPACE, f"{SCAN_DIR}/{preference_file}")
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
            preference_file = ''.join(val.split(",")[1].split())
            if preference_file.endswith(".json"):
                if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                    # Assuming there is a single preference JSON file
                    add_preference(api_endpoint, token, NAMESPACE, f"{DEPLOYMENT_LOCATION}/{preference_file}")
                elif mode.strip().upper() == 'D':
                    delete_preference(api_endpoint, token, NAMESPACE, f"{DEPLOYMENT_LOCATION}/{preference_file}")
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)