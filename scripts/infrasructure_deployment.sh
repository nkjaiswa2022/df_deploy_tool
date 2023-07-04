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
deployment_type=$6
env=$7
gcpdatafusioninstance=$8

new_ins_file="${HOME}/ins_temp_dir/A_instance.csv"
namespace_diff_file="${pipelineDir}/deploy/config/namespace"
preference_diff_file="${pipelineDir}/deploy/config/preference"
plugin_diff_file="${pipelineDir}/deploy/config/plugin"

fn_namespace_creation() {
    deploy_type=$1
    echo "*********************************  NAMESPACE CREATION ***********************************************"
    $python_env/bin/python3 namespace-creation.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $env $deploy_type
    if [ $? -gt 0 ];
    then
        echo "Namespace creation failed"
        exit 1
    else
        echo "Namespace created"
    fi
}

fn_plugin_deployment() {
    deploy_type=$1
    namespace_ind=$2
    echo "*********************************  PLUGIN DEPLOYMENT ***********************************************"
    $python_env/bin/python3 plugin-deployment.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir ${namespace_ind} $env $deploy_type
    if [ $? -gt 0 ];
    then
        echo "Plugins deployment failed"
        exit 1
    else
        echo "Plugins deployed"
    fi
}

fn_sys_pref_deployment() {
    deploy_type=$1
    echo "*********************************  SYSTEM PREFERENCE DEPLOYMENT ***********************************************"
    $python_env/bin/python3 system-preference-deployment.py $projectId $region $gcpdatafusioninstance $serviceaccountkeyfilePath $pipelineDir $env $deploy_type
    if [ $? -gt 0 ];
    then
        echo "System preference deployment failed"
        exit 1
    else
        echo "System preference deployed"
    fi
}

##### When New instance is created. 
if [[ -e ${HOME}/ins_temp_dir/A_insatnce.csv ]]
then
    echo "Create all Namespace, deploy all plugins and preferences to new instance"
    fn_namespace_creation "all"
    fn_plugin_deployment "all" "#"
    fn_sys_pref_deployment "all"
fi

if [[ ! -e ${namespace_diff_file} && ! -e ${preference_diff_file} && ! -e ${plugin_diff_file} ]]
then
    echo "No New Namespace/Preference/Plugin found for deployment"
    echo "Exiting Gracefully "
    exit 0
fi

if [[ -e ${namespace_diff_file} ]]
then
    echo "Create New Namespace"
    echo "Install all plugins in new namespaces"
    fn_namespace_creation "diff"
    while read namespace_nm
    do
        fn_plugin_deployment "all" "${namespace_nm}"
    done < <(awk -F'/' '{print $(NF)}' ${HOME}/ins_temp_dir/A_namespace.csv)
fi

if [[ -e ${preference_diff_file} ]]
then
    echo "Deploy New System Preference to all instance"
    fn_sys_pref_deployment "diff"
fi

if [[ -e ${plugin_diff_file} ]]
then
    echo "Deploy New Plugin to all namespace"
    fn_plugin_deployment "diff" "#"
fi