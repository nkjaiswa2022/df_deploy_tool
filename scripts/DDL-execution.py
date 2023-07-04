# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *
from google.cloud import bigquery

params = sys.argv

PROJECT_ID = params[1]
REGION = params[2]
INSTANCE = params[3]
SERVICE_ACCOUNT_FILE = params[4]
DEPLOYMENT_LOCATION = params[5]
NAMESPACE = params[6]
ENV = params[7]
DEPLOYMENT_TYPE = params[8]

SCAN_SUB_DIR = f"sql" # For 'All' appraoch, scan this directory for the pipeline JSON files
ROLLBACK_SUB_DIR = f"rollback" # For sql rollback
SCAN_FILE = "deploy/config/sql" # For 'Diff' approach, read this file for modified pipeline files

def get_query(query_file):
    if os.path.isfile(query_file) == True:
        with open(query_file, 'r') as j:
            contents = j.read()

        return contents
    else:
        content = ""
        _m = f"SQL file not found: {query_file}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1)

def execute_ddl_query(query, query_file):
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    if os.path.isfile(SERVICE_ACCOUNT_FILE) != True:
        # credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/userinfo.email'])
        client = bigquery.Client(project=PROJECT_ID, location=REGION, credentials=credentials)
        query_job = client.query(query)
        result = query_job.result()
    else:
        _m = f"Service account file not found : {SERVICE_ACCOUNT_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)
        sys.exit(1) 

def deploy_sql(query_file):
    query = get_query(query_file)
    execute_ddl_query(query, query_file)

token = auth_gcp(SERVICE_ACCOUNT_FILE)

if DEPLOYMENT_TYPE.lower() == D_TYPE.ALL.value.lower():

    # ------------- Deployment type - 'All' --------------

    SCAN_DIR = f"{DEPLOYMENT_LOCATION}/{SCAN_SUB_DIR}"
  
    if (os.path.exists(SCAN_DIR)):
        for f in os.listdir(SCAN_DIR):
            if f.endswith(".sql"):
                sql_file = f
                deploy_sql(f"{SCAN_DIR}/{sql_file}")
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
            temp = ''.join(val.split(",")[1].split())
            if temp.endswith(".sql"):            
                sql_file = temp
                if mode.strip().upper() == 'A' or mode.strip().upper() == 'M' or mode.strip().upper() == 'C':
                    deploy_sql(f"{DEPLOYMENT_LOCATION}/{sql_file}")
                # elif mode.strip().upper() == 'D':
                    # delete_pipeline(api_endpoint, token, NAMESPACE, pipeline)
    else:
        _m = f"Invalid file location: {SCAN_FILE}"
        log.error(_m)
        raise FileNotFoundError(_m)