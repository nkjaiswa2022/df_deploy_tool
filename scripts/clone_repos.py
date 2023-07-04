# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

from common import *

params = sys.argv
BUILD_DATE = params[1]
PIPELINE_LIST = f"deploy/config/{BUILD_DATE}/pipeline_list.csv"
TEMPORARY_CHECKOUT_FOLDER = "temp"

def clone_repos(repo_path, project_id, namespace):
    """
    Clone repo to temporary namespace
    TODO: Repo cloning has to be BitBucket repo specific
    implementation
    """
    Repo.clone_from(repo_path, f"./{TEMPORARY_CHECKOUT_FOLDER}/{namespace}", branch='master')

os.mkdir(TEMPORARY_CHECKOUT_FOLDER) # Create temp directory for repo checkout
csv_data = read_csv_details(PIPELINE_LIST)

for row in csv_data:
    project_id = row[0]
    region = row[1]
    instance = row[2]
    pipeline_src = row[3]

    arr = pipeline_src.split("/")
    namespace = arr[4]
    repo_path = f"https://source.developers.google.com/p/{project_id}/r/{namespace}" 
    clone_repos(repo_path, project_id, namespace)