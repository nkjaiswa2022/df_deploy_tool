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

def validate_pipeline(pipeline_file):
    pipeline_json_src = f"{DEPLOYMENT_LOCATION}/src/{pipeline_file}"
    pipeline_json = getJSONContent(pipeline_json_src)
    
    log.debug(f"Validating '{pipeline_json['name']}' pipeline structure")

    if("config" not in pipeline_json):
        _m = f"Missing 'config' attribute in '{pipeline_json['name']}' pipeline"
        log.error(_m)

    if('config' in pipeline_json) :
        config = pipeline_json['config']                    
        if ('stages' not in config):
            _m = f"Missing 'stages' attribute in 'config' inside '{pipeline_json['name']}' pipeline"
            log.error(_m)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' (scan path: ) --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                pipeline_file = f
                validate_pipeline(pipeline_file)
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

                if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                    validate_pipeline(pipeline)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)