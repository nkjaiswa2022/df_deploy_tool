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
ENV = params[6]
DEPLOYMENT_TYPE = params[7]

SCAN_SUB_DIR = f"system/config/preference/{ENV.lower()}" # For 'All' appraoch
SCAN_FILE = "deploy/config/preference" # For 'Diff' approach

ERRORS = []

def deploy_preference(api_endpoint, token, preference_json):
    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"

    deployment_url = f"{api_endpoint}/v3/preferences"
    response = requests.put(deployment_url, json=preference_json, headers=headers)
    
    _m = f"Preference deployed succesfully to system"
    process_response_message(response, _m)

def add_preference(api_endpoint, token, preference_file):
    # Get existing preferences for the namespace
    # existing_preference_json = get_system_preferences(api_endpoint, token)

    # Get new preference json 
    new_preference_json = getJSONContent(preference_file)

    # Merge and deploy
    # merged = existing_preference_json
    # if isinstance(new_preference_json, list):
    #     for obj in new_preference_json:
    #         merged = {**merged, **obj}
    # elif isinstance(new_preference_json, dict):
    #         merged = {**existing_preference_json, **new_preference_json}

    deploy_preference(api_endpoint, token, new_preference_json)

def delete_preference(api_endpoint, token, preference_file):
    # Get existing preferences for the namespace
    existing_preference_json = get_system_preferences(api_endpoint, token)

    # Get new preference json 
    del_preference_json = getJSONContent(preference_file)

    # Remove and deploy
    for o in del_preference_json:
        if o in existing_preference_json:
            del existing_preference_json[o]

    deploy_preference(api_endpoint, token, existing_preference_json)


token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                preference_file = f"{SCAN_DIR}/{f}"
                add_preference(api_endpoint, token, preference_file)
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
            mode = val.split(",")[0].strip() # Get mode - A (Add), D (Delete) or M (Modify)
            system_preference = ''.join(val.split(",")[1].split())

            if system_preference.startswith(f"system/config/preference/{ENV.lower()}"):
                preference_file = system_preference.replace(f"system/config/preference/{ENV.lower()}/", "") # Remove path prefix to get the name
                if preference_file.endswith(".json"):
                    if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                        # Assuming there is a single preference JSON file
                        add_preference(api_endpoint, token, f"{DEPLOYMENT_LOCATION}/{preference_file}")
                    elif mode.strip().upper() == 'D':
                        delete_preference(api_endpoint, token, f"{DEPLOYMENT_LOCATION}/{preference_file}")
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)   