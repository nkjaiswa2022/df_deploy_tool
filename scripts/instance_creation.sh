#!/bin/bash

# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

project_id=$1
region_id=$2
auth_file=$3
deploy_env=${4,,}
deploy_type=${5,,}
ins_list_path=$6
tf_base_path=$7
if [ ${deploy_type} == "all" ] || [ ${deploy_type} == "diff" ]
then
    echo "The Deployment Type selected : ${deploy_type}"
else
    echo "INCORRECT INPUT. EXPECTED VALUES: 'ALL' or 'DIFF'"
    exit 1
fi

run_dt="$(date +'%Y%m%d%H%M%S')"

cd ${tf_base_path}
gcloud config set project ${project_id}

terraform init -backend-config="bucket=datafusion-tf-state-dev" -backend-config="prefix=terraform/state" -backend-config="credentials=${auth_file}"
if [ $? -ne 0 ]
then
    echo "Terraform Init Failed"
    exit 1
fi
   
terraform plan -var project_id=${project_id} -var region_id=${region_id} -var auth_file=${auth_file} -var deploy_env=${deploy_env} -var deploy_type=${deploy_type} -var ins_list_path=${ins_list_path} -out=plan_${run_dt}.out
if [ $? -ne 0 ]
then
    echo "Terraform Plan Failed"
    exit 1
fi

terraform apply plan_${run_dt}.out
if [ $? -ne 0 ]
then
    echo "Terraform Apply Failed"
    exit 1
fi