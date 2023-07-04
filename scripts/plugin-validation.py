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

def get_pipeline_plugins(target_namespace, pipeline):
    pipeline_plugins = []
    pipeline_src = f"{DEPLOYMENT_LOCATION}/src/{pipeline}"
    pipelineInfo = getJSONContent(pipeline_src)
    config = pipelineInfo['config']
    stages = config['stages']
    for stage in stages:
        pipeline_plugins.append(stage['plugin']['artifact'])

    return pipeline_plugins


def validate_plugin(api_endpoint, token, namespace, pipeline):
    pipeline_plugins = get_pipeline_plugins(namespace, pipeline)
    ns_plugins = get_namespace_plugins(api_endpoint, token, namespace)

    for pipeline_plugin in pipeline_plugins:
        pluginName = pipeline_plugin['name']
        pluginVersion = pipeline_plugin['version']

        nameMismatch = pluginName not in [y['name'] for y in ns_plugins] # Validate presence of plugin name
        versionMismatch = pluginVersion not in [y['version'] for y in ns_plugins] # Validate plugin version
        pluginMismatch = nameMismatch or versionMismatch # Check for mismatch in either name or version
        if pluginMismatch == True:
            _m = f"{pluginName} (version: {pluginVersion}) not present in '{namespace}' namespace"
            log.error(_m)
            raise SystemError(_m)
            sys.exit(1)
        else:
            _m = f"Plugin {pluginName} (version: {pluginVersion}) validated successfully for {pipeline} in namespace '{namespace}'"
            log.debug(_m)
            print(_m)     

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' (scan path: ) --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".json"):
                pipeline_file = f
                validate_plugin(api_endpoint, token, NAMESPACE, pipeline_file)
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

                if mode.strip().upper() == 'A' or mode.strip().upper() == 'M':
                    validate_plugin(api_endpoint, token, NAMESPACE, pipeline)
                # elif mode.strip().upper() == 'D':
                    # delete_pipeline(api_endpoint, token, NAMESPACE, pipeline)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)
