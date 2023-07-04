# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

params = sys.argv

PROJECT_ID = params[1]
REGION = params[2]
SERVICE_ACCOUNT_FILE = params[3]
# PIPELINE_PATH_PREFIX = params[4]
# NAMESPACE = params[5]
INSTANCE = params[6]

NAMESPACE_LIST_CSV = f"deploy/config/namespace_deletion_list.csv"

ERRORS = []

def delete_namespace():
    """
    Delete namespace(s)
    """
    df = pd.read_csv(NAMESPACE_LIST_CSV, keep_default_na=False)
    df.fillna("", inplace=True)
    content = df.to_json(orient='records')
    for idx, row in enumerate(json.loads(content)):
        namespace = row["Namespace"]
        request_url = f"{api_endpoint}/v3/unrecoverable/namespaces/{namespace}"
        headers = {'Authorization': f"Bearer {token}"}
        response = requests.delete(request_url, headers=headers)
        if response.status_code != 200:
            ERRORS.append(response.content)
            raise ValueError(response.content)
            sys.exit(1)

if os.path.isfile(NAMESPACE_LIST_CSV) == True:
    delete_namespace()
    token = auth_gcp(SERVICE_ACCOUNT_FILE)
    api_endpoint = get_CDAPendpoint(PROJECT_ID, REGION, INSTANCE)
    phase_summary(NAMESPACE_LIST_CSV)
else:
    _m = f"Invalid namespace deletion file path: {NAMESPACE_LIST_CSV}"
    raise ValueError(_m)
    sys.exit(1)