# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google. 

from common import *

urllib3.disable_warnings()

params = sys.argv
PROJECT_ID = params[1]
REGION = params[2]
INSTANCE = params[3]
SERVICE_ACCOUNT_FILE = params[4]
DEPLOYMENT_LOCATION = params[5]
ENV = params[6]
DEPLOYMENT_TYPE = params[7]

SCAN_SUB_DIR = "system/config/namespace" # For 'All' appraoch
SCAN_FILE = "deploy/config/namespace" # For 'Diff' approach

ERRORS = []

def create_namespace(api_endpoint, token, new_namespace):
    request_url = f"{api_endpoint}/v3/namespaces/{new_namespace}"
    log.debug(request_url)
    
    headers = {'Authorization': f"Bearer {token}"}
    response = requests.put(request_url, headers=headers)

    _m = f"'{new_namespace}' namespace created succesfully in '{INSTANCE}' instance"
    process_response_message(response, _m)
    assign_defaultComputeprofile(api_endpoint, token, new_namespace)
    assign_namespace_preference(api_endpoint, token, new_namespace)

def assign_defaultComputeprofile(api_endpoint, token, new_namespace):
    headers = {'Authorization': f"Bearer {token}", "Content-Type": "application/json"}
    compute_profile_data="{\"system.profile.name\": \"SYSTEM:dataproc\"}"
    url = f"{api_endpoint}/v3/namespaces/{new_namespace}/preferences"
    response = requests.put(url, data = compute_profile_data, headers=headers, verify=False)
    _m = f"Compute profile asssgined to {new_namespace}"
    process_response_message(response, _m)

def assign_namespace_preference(api_endpoint, token, new_namespace):
    preference_src = f"system/config/preferences/{ENV.lower()}/preference.json"
    if os.path.isfile(preference_src) == True:
        preference_json = getJSONContent(json_path=preference_src)
        headers = {'Authorization': f"Bearer {token}", 'Content-Type': "application/json", 'Accept': "application/json"}
        deployment_url = f"{api_endpoint}/v3/namespaces/{new_namespace}/preferences"
        response = requests.put(deployment_url, data=json.dumps(preference_json), headers=headers)
        _m = f"Namespace preference asssgined to {new_namespace}"
        process_response_message(response, _m)

def assign_RBAC(project_id, region, instance_name, new_namespace, user_type, user_id, role_name):
    rbac_cmd = "gcloud beta data-fusion add-iam-policy-binding {} --project {} --location={} --namespace={} --member=\"{}:{}\" --role=\"roles/datafusion.{}\"".format(instance_name, project_id, region, new_namespace, user_type, user_id, role_name)
    status_code = os.system(rbac_cmd)
    if status_code != 0:
        _m = f"RBAC assignment failed on '{new_namespace}' namespace for user '{user_id}'"
        log.error(_m)
        raise SystemError(_m)
        sys.exit(1)
    else:
        _m = f"RBAC assigned successfully to '{new_namespace}' namespace for user '{user_id}'"
        print(_m)

def delete_namespace(api_endpoint, token, namespace):
    request_url = f"{api_endpoint}/v3/unrecoverable/namespaces/{namespace}"
    headers = {'Authorization': f"Bearer {token}"}
    response = requests.delete(request_url, headers=headers)
    _m = f"'{namespace}' namespace deleted succesfully from '{INSTANCE}' instance"    
    process_response_message(response, _m)

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():
    
    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"

    if (os.path.exists(SCAN_DIR)):
        namespaces = os.listdir(SCAN_DIR)
        for namespace in namespaces:
            create_namespace(api_endpoint, token, namespace)
    else:
        _m = f"Invalid location: {SCAN_DIR}"
        log.error(_m)
        raise SystemError(_m)
        sys.exit(1)

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
            pathSplit = temp.split("/")
            namespace = pathSplit[-1]

            if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                create_namespace(api_endpoint, token, namespace)
            elif mode.strip().upper() == 'D':
                delete_namespace(api_endpoint, token, namespace)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)
