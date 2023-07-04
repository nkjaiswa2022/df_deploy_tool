# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

params = sys.argv

PROJECT_ID = params[1]
REGION = params[2]
SERVICE_ACCOUNT_FILE = params[3]
NAMESPACE = params[4]
INSTANCE = params[5]
PIPELINE_DELETION_LIST_PATH = f"{params[5]}/pipeline_deletion.csv"

ERRORS = []

def delete_pipeline(api_endpoint, token):
    df = pd.read_csv(PIPELINE_DELETION_LIST_PATH, keep_default_na=False)
    df.fillna("", inplace=True)
    content = df.to_json(orient='records')
    for idx, row in enumerate(json.loads(content)):
        pipeline_name = row["Pipeline"]
        
        deployment_url = f"{api_endpoint}/v3/namespaces/{NAMESPACE}/apps/{pipeline_name}"

        headers = CaseInsensitiveDict()
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        response = requests.delete(deployment_url, headers=headers)

        if response.status_code != 200:
            ERRORS.append(response.content)
            raise ValueError(response.content)
            sys.exit(1)
        else:
            _m = f"{pipeline_name} pipeline deleted from '{NAMESPACE}' namespace"
            print(_m)

if os.path.isfile(PIPELINE_DELETION_LIST_PATH) == True:
    token = auth_gcp(SERVICE_ACCOUNT_FILE)
    api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)
    delete_pipeline(api_endpoint, token)
    phase_summary(ERRORS)
else:
    _m = f"Invalid deletion list file: {PIPELINE_DELETION_LIST_PATH}"
    raise ValueError(_m)
    sys.exit(1)