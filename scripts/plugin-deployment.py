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

SCAN_SUB_DIR = f"system/config/plugin" # For 'All' appraoch, scan this directory for the pipeline JSON files
SCAN_FILE = "deploy/config/plugin" # For 'Diff' approach, read this file for modified pipeline files

RESERVED_NAMESPACE_KEYWORD = '#'
ALL_NAMESPACE_LIST = []

def deploy_HUB_plugins(plugin, api_endpoint, namespace, auth_token):
    # Get plugin detains
    artifact_name = plugin[0]
    artifact_version = plugin[1]
    package_name = plugin[3]
    artifact_jar = plugin[4]
    artifact_config = plugin[5]

    # Get the jar file from HUB
    hub_endpoint="https://hub.cdap.io/v2/packages"
    plugin_jar_url = f"{hub_endpoint}/{package_name}/{artifact_version}/{artifact_jar}"
    plugin_jar_file = requests.get(plugin_jar_url, verify=False)

    # Exit with error if response is wrong
    if plugin_jar_file.status_code != 200:
        log.error(plugin_jar_file.content)
        raise ValueError(plugin_jar_file.content)
        sys.exit(1)

    # Get the json file from HUB(Properties & Parents)
    hub_plugin_json_url = f"{hub_endpoint}/{package_name}/{artifact_version}/{artifact_config}"
    plugin_json_file = requests.get(hub_plugin_json_url, verify=False)

    # Exit with error if response is wrong
    plugin_json = process_response_json(plugin_json_file)

    artifact_properties = json.dumps(plugin_json['properties'])
    artifact_parents = '/'.join(plugin_json['parents'])

    header = CaseInsensitiveDict()
    header["Authorization"] = f"Bearer {auth_token}"
    header["Content-Type"] = "application/octet-stream"
    header["Artifact-Version"] = artifact_version
    header["Artifact-Extends"] = artifact_parents

    # Upload jar from file.
    jar_upload_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts/{artifact_name}"
    response = requests.post(jar_upload_url, data = plugin_jar_file, headers = header, verify=False)
    if response.status_code == 200:
        _m = f"{artifact_name} (version: {artifact_version}) deployed successfully to '{namespace}' namespace"
        print(_m)
    elif response.status_code == 409:
        print(response.content)
        log.debug(f"{response.content}")
        sys.exit(0)
    else:
        _m = f"Error deploying plugin {artifact_name} (version; {artifact_version}) to '{namespace}' namespace"
        process_response_message(response, _m)

    # Update plugin properties
    prop_header = CaseInsensitiveDict()
    prop_header["Authorization"] = f"Bearer {auth_token}"
    prop_header["Content-Type"] = "application/json"

    prop_update_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts/{artifact_name}/versions/{artifact_version}/properties"
    response = requests.put(prop_update_url, data=artifact_properties, headers=prop_header, verify=False)
    _m = f"{artifact_name} properties updated successfully in '{namespace}' namespace"
    process_response_message(response, _m)

def deploy_custom_plugins(plugin, api_endpoint, namespace, auth_token):
    # Get plugin details
    package_name = plugin[3]
    package_version = plugin[1]
    
    artifact_name = plugin[0]
    artifact_version = plugin[1]

    # TODO: Change Jar and JSON paths as per folder structure
    artifact_jar = f"datafusion/plugins/{package_name}/{package_version}/{plugin[4]}"
    artifact_json = f"datafusion/plugins/{package_name}/{package_version}/{plugin[5]}"
    
    # Exit with error if jar is missing
    if os.path.isfile(artifact_jar) != True:
        _m = f"Plugin jar file not found: {artifact_jar}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)

    # Exit with error if json is missing
    if os.path.isfile(artifact_json) != True:
        _m = f"Plugin jar file not found: {artifact_json}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)

    with open(artifact_json,'r') as json_file:
        data = json.load(json_file)

    artifact_properties = json.dumps(data['properties'])
    artifact_parents = '/'.join(data['parents'])

    header = CaseInsensitiveDict()
    header["Authorization"] = f"Bearer {auth_token}"
    header["Content-Type"] = "application/octet-stream"
    header["Artifact-Version"] = artifact_version
    header["Artifact-Extends"] = artifact_parents

    # Upload jar from file.
    jar_upload_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts/{artifact_name}"
    response = requests.post(jar_upload_url, data=open(artifact_jar, 'rb'), headers=header, verify=False)
    _m = f"{artifact_name} deployed successfully to '{namespace}' namespace"
    process_response_message(response, _m)

    prop_header = CaseInsensitiveDict()
    prop_header["Authorization"] = f"Bearer {auth_token}"
    prop_header["Content-Type"] = "application/json"

    # Update plugin properties
    prop_update_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts/{artifact_name}/versions/{artifact_version}/properties"
    response = requests.put(prop_update_url, data=artifact_properties, headers=prop_header, verify=False)
    _m = f"{artifact_name} properties updated successfully in '{namespace}' namespace"
    process_response_message(response, _m)

def deploy_drivers(plugin, api_endpoint, namespace, auth_token):
    package_name = plugin[3]
    package_version = plugin[1]

    artifact_name = plugin[0]
    artifact_version = plugin[1]

    # TODO: Change Jar and JSON paths as per folder structure
    artifact_jar = f"datafusion/plugins/{package_name}/{package_version}/{plugin[4]}"
    artifact_json = f"datafusion/plugins/{package_name}/{package_version}/{plugin[5]}"

    # Exit with error if jar is missing
    if os.path.isfile(artifact_jar) != True:
        _m = f"Driver jar file path: {artifact_jar}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)

    # Exit with error if JSON is missing
    if os.path.isfile(artifact_json) != True:
        _m = f"Driver json file path: {artifact_json}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)

    artifact_plugins =  '[ { "name": "oracle", "type": "jdbc", "className": "oracle.jdbc.driver.OracleDriver" } ]'

    header = CaseInsensitiveDict()
    header["Authorization"] = f"Bearer {auth_token}"
    header["Content-Type"] = "application/octet-stream"
    header["Artifact-Version"] = artifact_version
    header["Artifact-Extends"] = artifact_plugins

    artifact_jar = f"datafusion/plugins/{artifact_name}/{artifact_version}/{artifact_name}.jar"
    # upload jar from file.
    jar_upload_url = f"{api_endpoint}/v3/namespaces/{namespace}/artifacts/{artifact_name}"
    response = requests.post(jar_upload_url, data=open(artifact_jar, 'rb'), headers=header, verify=False)
    _m = f"{artifact_name} deployed successfully to '{namespace}' namespace"
    process_response_message(response, _m)

def deploy_plugins(api_endpoint, token, namespace, plugin):
    plugin_type = plugin[2] # Plugin type - HUB, Manual-Install or Driver
    if plugin_type == 'HUB':
        deploy_HUB_plugins(plugin, api_endpoint, namespace, token)
    elif plugin_type == 'Manual-Install':
        deploy_custom_plugins(plugin, api_endpoint, namespace, token)
    else:
        deploy_drivers(plugin, api_endpoint, namespace, token)

token = auth_gcp(SERVICE_ACCOUNT_FILE)
api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)

if NAMESPACE.lower() == RESERVED_NAMESPACE_KEYWORD.lower():
    ALL_NAMESPACE_LIST = get_namespaces(api_endpoint, token)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"

    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".csv"):
                plugin_file = f"{SCAN_DIR}/{f}"
                plugins = read_csv_details(plugin_file)
                for plugin in plugins:
                    if NAMESPACE.lower() == RESERVED_NAMESPACE_KEYWORD.lower():
                        print("-----namespace--- {}",NAMESPACE)
                        for ns in ALL_NAMESPACE_LIST:
                            deploy_plugins(api_endpoint, token, ns['name'], plugin.split(','))
                    else:
                        deploy_plugins(api_endpoint, token, NAMESPACE, plugin.split(','))
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
            mode = val.split(",")[0].strip() # Get mode - A (Add), D (Delete) or M (Modify)
            pluginCSVPath = ''.join(val.split(",")[1].split())
            pluginCsv = f"{DEPLOYMENT_LOCATION}/{pluginCSVPath}"
            if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                if (os.path.exists(pluginCsv)):
                    print(pluginCsv)
                    if pluginCsv.endswith(".csv"):
                        plugins = read_csv_details(pluginCsv)
                        for plugin in plugins:
                            if NAMESPACE.lower() == RESERVED_NAMESPACE_KEYWORD.lower():
                                for ns in ALL_NAMESPACE_LIST:
                                    deploy_plugins(api_endpoint, token, ns['name'], plugin.split(','))
                            else:
                                deploy_plugins(api_endpoint, token, NAMESPACE, plugin.split(','))
                    else:
                        _m = f"No CSV file in location: {pluginCsv}"
                        log.error(_m)
                        raise FileNotFoundError(_m)
                        sys.exit(1)
                else:
                    _m = f"Invalid file location: {pluginCsv}"
                    log.error(_m)
                    raise FileNotFoundError(_m)
                    sys.exit(1)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)