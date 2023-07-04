#!/bin/bash

# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.


set -x
python_env=$1
projectId=$2
region=$3
serviceaccountkeyfilePath=$4
pipelineDir=$5
namespace=$6
deployment_type=$7
env=$8
gcpdatafusioninstance=$9 # datafusion instance should be the last parameter.
set +x
python3 -m venv $python_env
source $python_env/bin/activate
echo "*********************************  DEPENDENCY INSTALLATION *******************************************"
$python_env/bin/pip3 install -r requirements.txt
if [ $? -gt 0 ];
then
    echo "Dependency installation failed"
    exit 1
else
    echo "Dependencies installed successfully"
fi
echo "*********************************  NAMESPACE VALIDATION ***********************************************"
$python_env/bin/python3 namespace-validation.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $namespace $env $deployment_type  
if [ $? -gt 0 ]; 
then
    echo "Namespace validation failed"
    exit 1
fi
echo "*********************************  PLUGIN VALIDATION **************************************************"
$python_env/bin/python3 plugin-validation.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $namespace $env $deployment_type
if [ $? -gt 0 ]; 
then
    echo "Plugins validation failed"
    exit 1
fi
echo "********************************* NAMESPACE PREFERENCE DEPLOYMENT **************************************************"
$python_env/bin/python3 namespace-preference-deployment.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $namespace $env $deployment_type
if [ $? -gt 0 ]; 
then
    echo "Namespace preference deployment failed"
    exit 1
fi
echo "*********************************  PIPELINE DEPLOYMENT *************************************************"
$python_env/bin/python3 pipeline-deployment.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $namespace $env $deployment_type
if [ $? -gt 0 ]; 
then
    echo "Pipeline deployment failed"
    exit 1
fi
echo "*********************************  DDL EXECUTION *************************************************"
$python_env/bin/python3 DDL-execution.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $namespace $env $deployment_type
if [ $? -gt 0 ]; 
then
    echo "DDL execution failed"
    exit 1
fi
deactivate