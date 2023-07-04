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

SCAN_SUB_DIR = "src" # For 'All' appraoch, scan this directory for the pipeline JSON files
SCAN_FILE = "deploy/config/src" # For 'Diff' approach, read this file for modified pipeline files

ERRORS = []

def deploy_pipeline(api_endpoint, token, namespace, pipeline_file):
    pipeline_json_src = f"{DEPLOYMENT_LOCATION}/src/{pipeline_file}"
    pipeline_json = getJSONContent(pipeline_json_src)
    
    log.debug(f"Deploying '{pipeline_json['name']}' pipeline to '{namespace}' namespace")

    deployment_url = f"{api_endpoint}/v3/namespaces/{namespace}/apps/{pipeline_json['name']}"

    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    
    response = requests.put(deployment_url, json=pipeline_json, headers=headers)
        
    _m = f"--- {pipeline_json['name']} deployed succesfully to '{namespace}' namespace "
    process_response_message(response, _m)

def delete_pipeline(api_endpoint, token, namespace, pipeline):
    # pipeline_json_src = f"{DEPLOYMENT_LOCATION}/src/{pipeline}"
    # pipeline_json = getJSONContent(pipeline_json_src)

    log.debug(f"Deleting '{pipeline}' pipeline from '{namespace}' namespace")

    deployment_url = f"{api_endpoint}/v3/namespaces/{namespace}/apps/{pipeline}"

    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    
    response = requests.delete(deployment_url, headers=headers)

    _m = f"----- {pipeline} deleted succesfully from '{namespace}' namespace -----"
    process_response_message(response, _m)
        

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' (scan path: ) --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                pipeline_file = f
                deploy_pipeline(api_endpoint, token, NAMESPACE, pipeline_file)
    else:
        _m = f"Invalid location: {SCAN_DIR}"
        log.error(_m)
        raise SystemError(_m)

else:
    
    # ------------- Deployment type - 'Diff' (scan path: ) --------------
    
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
            
            if temp.startswith('src'):
                pipeline = temp.replace('src/', '') # Remove path prefix to get the name
                if pipeline.endswith(".json"):
                    if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                        deploy_pipeline(api_endpoint, token, NAMESPACE, pipeline)
                    elif mode.strip().upper() == 'D':
                        # Assuming pipeline name is same as the JSON file name
                        delete_pipeline(api_endpoint, token, NAMESPACE, pipeline[:-5])
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)   