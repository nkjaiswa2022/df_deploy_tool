# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

ERRORS = []

params = sys.argv

PROJECT_ID = params[1] 
REGION = params[2]
MASTER_INSTANCE = params[3] # Instance to be considered as golden copy
COMPARING_INSTANCES = params[4] # Comma separated names of instances which need to be compared with the golden instance
RECON_FILE = params[5] # Name of the output file
SERVICE_ACCOUNT_FILE_PATH = params[6]

# Convert comparing instances to array
INSTANCES = []
if COMPARING_INSTANCES.find(",") >= 0:
    for i in COMPARING_INSTANCES.split(','):
        if len(i.strip()) > 0:
            INSTANCES.append(i.strip()) 
elif len(COMPARING_INSTANCES.strip()) > 0:
    INSTANCES = [COMPARING_INSTANCES.strip()]

token = auth_gcp(SERVICE_ACCOUNT_FILE_PATH)

def is_namespace_present(namespace, namespaces):
    return namespace['name'] in [n['name'] for n in namespaces]

def is_namespace_in_instance(namespace, instance):
    api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, instance)
    ns_list = get_namespaces(api_endpoint, token)
    return is_namespace_present(namespace, ns_list)

def is_plugin_present(plugin, plugins):
    name = plugin['name']
    version = plugin['version']
    nameCheck = name in [p['name'] for p in plugins]
    versionCheck = version in [p['version'] for p in plugins] 
    return nameCheck == True and versionCheck == True 

def is_pipeline_present(pipeline, pipelines):
    name = pipeline['name']
    nameCheck = name in [p['name'] for p in pipelines] 
    return nameCheck

def is_preference_present(preference, preference_list):
    if preference_list[preference]:
        return True
    else:
        return False

def is_securekey_present(securekey, securekey_list):
    keyname = securekey['name']
    nameCheck = keyname in [k['name'] for k in securekey_list]
    return nameCheck

def get_instance_header(primary_instance, instance):
    key = ''
    if instance.lower() == primary_instance.lower():
        key = f"{instance} (Golden copy)"
    else:
        key = instance
    return key

def compare_namespaces():
    obj = {}

    main_instance = MASTER_INSTANCE
    main_instance_api = get_CDAPendpoint(PROJECT_ID, REGION, main_instance)
    main_nslist = get_namespaces(main_instance_api, token)

    if MASTER_INSTANCE not in INSTANCES:
        INSTANCES.insert(0, MASTER_INSTANCE)

    obj['Namespace'] = []
    for i in INSTANCES:
        obj[get_instance_header(main_instance, i)] = []

    for n in main_nslist:
        obj['Namespace'].append(n['name'])
        obj['Namespace'].append('')

    ns_list = []
    for i in INSTANCES:
        api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, i)
        ns_list = get_namespaces(api_endpoint, token)
        for element in main_nslist:
            if is_namespace_present(element, ns_list):
                obj[get_instance_header(main_instance, i)].append('Yes')
            else:
                obj[get_instance_header(main_instance, i)].append('-')
            obj[get_instance_header(main_instance, i)].append('')

    diff = pd.DataFrame(obj)
    return diff

def compare_plugins():
    obj = {}

    main_instance = MASTER_INSTANCE
    main_instance_api = get_CDAPendpoint(PROJECT_ID, REGION, main_instance)
    main_nslist = get_namespaces(main_instance_api, token)

    if MASTER_INSTANCE not in INSTANCES:
        INSTANCES.insert(0, MASTER_INSTANCE)

    obj['Namespace'] = []
    obj['Plugin'] = []
    obj['Version'] = []
    for i in INSTANCES:
        obj[get_instance_header(main_instance, i)] = []
    
    for n in main_nslist:
        obj['Namespace'].append(n['name'])
        obj['Plugin'].append('')
        obj['Version'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')
        
        master_plugin_list = get_user_plugins(main_instance_api, token, n['name'])

        for p in master_plugin_list:
            obj['Namespace'].append('')
            obj['Plugin'].append(p['name'])
            obj['Version'].append(p['version'])

            for i in INSTANCES:
                if is_namespace_in_instance(n, i) == True:
                    api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, i)
                    plugin_list = get_user_plugins(api_endpoint, token, n['name'])

                    if is_plugin_present(p, plugin_list) == True:
                        obj[get_instance_header(main_instance, i)].append('Yes')
                    else:
                        obj[get_instance_header(main_instance, i)].append('-')
                else:
                    obj[get_instance_header(main_instance, i)].append('-')
    
        # Insert empty line
        obj['Namespace'].append('')
        obj['Plugin'].append('')
        obj['Version'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')

    
    diff = pd.DataFrame(obj)
    return diff

def compare_pipelines():
    obj = {}

    main_instance = MASTER_INSTANCE
    main_instance_api = get_CDAPendpoint(PROJECT_ID, REGION, main_instance)
    main_nslist = get_namespaces(main_instance_api, token)

    if MASTER_INSTANCE not in INSTANCES:
        INSTANCES.insert(0, MASTER_INSTANCE)
    
    obj['Namespace'] = []
    obj['Pipeline'] = []
    for i in INSTANCES:
        obj[get_instance_header(main_instance, i)] = []
    
    for n in main_nslist:
        obj['Namespace'].append(n['name'])
        obj['Pipeline'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')
        
        master_pipeline_list = get_namespace_pipelines(main_instance_api, token, n['name'])

        if master_pipeline_list:
            for p in master_pipeline_list:
                obj['Namespace'].append('')
                obj['Pipeline'].append(p['name'])

                for i in INSTANCES:
                    if is_namespace_in_instance(n, i) == True:

                        api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, i)
                        pipeline_list = get_namespace_pipelines(api_endpoint, token, n['name'])

                        if pipeline_list:
                            if is_pipeline_present(p, pipeline_list) == True:
                                obj[get_instance_header(main_instance, i)].append('Yes')
                            else:
                                obj[get_instance_header(main_instance, i)].append('-')
                        else:
                            obj[get_instance_header(main_instance, i)].append('-')    

                    else:
                        obj[get_instance_header(main_instance, i)].append('-')

        # Insert empty line
        obj['Namespace'].append('')
        obj['Pipeline'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')


    diff = pd.DataFrame(obj)
    return diff

def compare_preferences():
    obj = {}

    main_instance = MASTER_INSTANCE
    main_instance_api = get_CDAPendpoint(PROJECT_ID, REGION, main_instance)
    main_nslist = get_namespaces(main_instance_api, token)

    if MASTER_INSTANCE not in INSTANCES:
        INSTANCES.insert(0, MASTER_INSTANCE)
    
    obj['Namespace'] = []
    obj['Preference'] = []
    for i in INSTANCES:
        obj[get_instance_header(main_instance, i)] = []
    
    for n in main_nslist:
        obj['Namespace'].append(n['name'])
        obj['Preference'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')
        
        master_preference_list = get_namespace_preferences(main_instance_api, token, n['name'])

        if master_preference_list:
            for p in master_preference_list:
                obj['Namespace'].append('')
                obj['Preference'].append(p)

                for i in INSTANCES:
                    if is_namespace_in_instance(n, i) == True:

                        api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, i)
                        preference_list = get_namespace_preferences(api_endpoint, token, n['name'])

                        if preference_list:
                            if is_preference_present(p, preference_list) == True:
                                obj[get_instance_header(main_instance, i)].append('Yes')
                            else:
                                obj[get_instance_header(main_instance, i)].append('-')
                        else:
                            obj[get_instance_header(main_instance, i)].append('-')    

                    else:
                        obj[get_instance_header(main_instance, i)].append('-')

        # Insert empty line
        obj['Namespace'].append('')
        obj['Preference'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')

    diff = pd.DataFrame(obj)
    return diff

def compare_securekeys():
    obj = {}

    main_instance = MASTER_INSTANCE
    main_instance_api = get_CDAPendpoint(PROJECT_ID, REGION, main_instance)
    main_nslist = get_namespaces(main_instance_api, token)

    if MASTER_INSTANCE not in INSTANCES:
        INSTANCES.insert(0, MASTER_INSTANCE)
    
    obj['Namespace'] = []
    obj['Secure Keys'] = []
    for i in INSTANCES:
        obj[get_instance_header(main_instance, i)] = []
    
    for n in main_nslist:
        obj['Namespace'].append(n['name'])
        obj['Secure Keys'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')
        
        master_securekeys_list = get_namespace_securekeys(main_instance_api, token, n['name'])

        if master_securekeys_list:
            for p in master_securekeys_list:
                obj['Namespace'].append('')
                obj['Secure Keys'].append(p['name'])

                for i in INSTANCES:
                    if is_namespace_in_instance(n, i) == True:

                        api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, i)
                        securekeys_list = get_namespace_securekeys(api_endpoint, token, n['name'])

                        if securekeys_list:
                            if is_securekey_present(p, securekeys_list) == True:
                                obj[get_instance_header(main_instance, i)].append('Yes')
                            else:
                                obj[get_instance_header(main_instance, i)].append('-')
                        else:
                            obj[get_instance_header(main_instance, i)].append('-')    

                    else:
                        obj[get_instance_header(main_instance, i)].append('-')

        # Insert empty line
        obj['Namespace'].append('')
        obj['Secure Keys'].append('')
        for i in INSTANCES:
            obj[get_instance_header(main_instance, i)].append('')

    diff = pd.DataFrame(obj)
    return diff

def compare_instances():
    ns_diff = compare_namespaces() # Get difference of namespaces
    plugin_diff = compare_plugins() # Get difference of plugins
    pipeline_diff = compare_pipelines() # Get difference of pipelines
    preference_diff = compare_preferences() # Get difference of preferences
    securekeys_diff = compare_securekeys() # Get the difference of securekeys

    # Write out to xlsx file
    with pd.ExcelWriter(RECON_FILE) as writer:
        ns_diff.to_excel(writer, sheet_name='Namespaces', index=False)
        plugin_diff.to_excel(writer, sheet_name='Plugins', index=False)
        pipeline_diff.to_excel(writer, sheet_name='Pipelines', index=False)
        preference_diff.to_excel(writer, sheet_name='Preferences', index=False)
        securekeys_diff.to_excel(writer, sheet_name='Secure Keys', index=False)

if len(INSTANCES) > 0:
    compare_instances()
else:
    _m = f"Comparing instances missing"
    log.error(_m)
    raise ValueError(_m)
    sys.exit(1)