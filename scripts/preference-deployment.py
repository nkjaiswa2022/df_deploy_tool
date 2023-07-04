# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

params = sys.argv
BUILD_DATE = params[1]
PREFERENCE_LIST_CSV = f"deploy/config/{BUILD_DATE}/preference_list.csv"
# PREFERENCE_LIST_CSV = f"/preference.json"

def get_preferences(api_endpoint, source_namespace, token):
    """
    Get preferences from a namespace

    Parameters:
        api_endpoint (string): REST api endpoint for a data-fusion instance
        source_namespace (string): Namespace whose preferences are to be fetched
        token (string): Authenticated token    
    """
    request_url = f"{api_endpoint}/v3/namespaces/{source_namespace}/preferences"
    headers = {'Authorization': f"Bearer {token}"}
    response = requests.get(request_url, headers=headers)
    return response.json()

def assign_namespace_preference(api_endpoint, token, target_namespace, preference):
    """
    Deploy preference to specified namespace

    Parameters:
        api_endpoint (string): REST api endpoint for a data-fusion instance
        token (string): Authenticated token
        target_namespace (string): Namespace where preferences are to be deployed
        preference (string): Preference JSON 
    """
    headers = {'Authorization': f"Bearer {token}", 'Content-Type': "application/json", 'Accept': "application/json"}    
    deployment_url = f"{api_endpoint}/v3/namespaces/{target_namespace}/preferences"
    response = requests.put(deployment_url, data=json.loads(preference), headers=headers)
    if(response.status_code != 200):
        _m = f"Preference deployment failed for namespace '{target_namespace}'"
        raise ValueError(_m)

    _m = f"Preference deployed succesfully to namespace '{target_namespace}'"
    print(_m)


token = auth_gcp()

csv_data = read_csv_details(PREFERENCE_LIST_CSV)
for row in csv_data:
    project_id = row[0]
    region = row[1]
    instance = row[2]
    namespace = row[3]
    preference = row[4]

    api_endpoint = get_CDAPendpoint(project_id, region, instance)
    assign_namespace_preference(api_endpoint, token, namespace, preference)