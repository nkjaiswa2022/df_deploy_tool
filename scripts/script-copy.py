# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *
import paramiko

urllib3.disable_warnings()

params = sys.argv
BUILD_DATE = params[1]
SCRIPT_LIST_CSV = f"deploy/config/{BUILD_DATE}/script-list.csv"
SCRIPT_PATH_PREFIX = ""

# Authenticate SSH client and start connection
ssh = paramiko.SSHClient() 
ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
ssh.connect(server, username=username, password=password)
sftp = ssh.open_sftp()

def script_copy(namespace, script):
    script_path = f"{SCRIPT_PATH_PREFIX}/edgenode/{namespace}/scripts"
    target_directory = f"/target_directory"
    sftp.put(script_path, target_directory)

sftp.close()
ssh.close()

token = auth_gcp()
csv_data = read_csv_details(w)
for row in csv_data:
    print(row)
    project_id = row[0]
    region = row[1]
    instance = row[2]
    namespace = row[3]
    script = row[4]

    script_copy(namespace, script)
    