#!/bin/bash

# Copyright 2022 Google LLC. This software is provided as is, without warranty 
# or representation for any use or purpose. 
# Your use of it is subject to your agreement with Google.

python_env=$1
projectId=$2
region=$3
serviceaccountkeyfilePath=$4
pipelineDir=$5
deployment_type=${6,,}
env=${7,,}
ins_master_list_path=$8
tf_base_path=$9

curr_dir_path="$(pwd)"
diff_flag="diff"

echo "******** Merging the Iinstance file into One Master File **********"

fn_merge_file() {
	input_dir=$1
	output_dir=$2
	deploy_env=$3
	counter=0
	mkdir -p ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}
	for file in ${input_dir}/instance/config/${deploy_env}/*.csv;
	do
		if [ ${counter} = 0 ]
		then
			cat ${file} > ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/tmp_instance_list.csv
		else
			echo $'\n' >> ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/tmp_instance_list.csv
			tail +2 ${file} >> ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/tmp_instance_list.csv
		fi
		((counter++))
	done
	cat ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/tmp_instance_list.csv |  grep '\S' > ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/instance_list.csv
}

fn_merge_file ${pipelineDir} ${ins_master_list_path} ${env}

echo "****************** Starting Instance Creation Process *************"

. ${curr_dir_path}/instance_creation.sh ${projectId} ${region} ${serviceaccountkeyfilePath} ${env} ${deployment_type} ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/instance_list.csv ${tf_base_path}
if [ $? -ne 0 ]
then
    echo "Instance Creation Process FAILED"
    exit 1
else
    echo "Instance Creation SUCCESSFUL"
fi

echo "******** Read the Git Diff Output File to get the new instance and Namespace ****"

ins_diff_file="${HOME}/deploy/config/instance"
ns_diff_file="${pipelineDir}/deploy/config/namespace"

fn_handle_gitdiff_file() {
    input_file=$1
    file_suffix=$2
    mkdir -p ${HOME}/ins_temp_dir && cd ${HOME}/ins_temp_dir #Check if we can do this?
    sed 's/\t/ /g' ${input_file} |sed 's/  */ /g' |sed 's/ /,/g' |awk -F"," -v filetype="${file_suffix}" '{print> ($1 "_" filetype ".csv")}'
}

if [ -e ${ins_diff_file} ]
then
    fn_handle_gitdiff_file ${ins_diff_file} "instance"
fi

if [ -e ${ns_diff_file} ]
then
    fn_handle_gitdiff_file ${ns_diff_file} "namespace"
fi

cd ${curr_dir_path}

echo "************** Setting up Python Virtual Environment **************"
python3 -m venv $python_env
source $python_env/bin/activate

echo "************** Dependency Installation **************"

$python_env/bin/pip3 install -r requirements.txt
if [ $? -gt 0 ];
then
    echo "Dependency installation failed"
    exit 1
else
    echo "Dependencies installed successfully"
fi

echo "******************* Deployment Started ****************************"

if [ -e ${HOME}/ins_temp_dir/A_instance.csv ]
then
	while read ins
	do
		. ${curr_dir_path}/infrasructure_deployment.sh ${python_env} ${projectId} ${region} ${serviceaccountkeyfilePath} ${pipelineDir} ${deployment_type} ${env} ${ins}
		if [ $? -ne 0 ]
        then
            echo " Deployment of Namespace/Preferences/Plugin FAILED for Instance: ${ins} "
            exit 1
        else
            echo " Deployment of Namespace/Preferences/Plugin SUCCESSFUL for Instance: ${ins} "
        fi
	done < <(awk -F'/' '{print $(NF)}' ${HOME}/ins_temp_dir/A_instance.csv |awk -F'.' '{print $1}')
else
    echo " No Newly Added Instance Found "
fi

if [ -e ${HOME}/ins_temp_dir/M_instance.csv ]
then
	while read ins
	do
		. ${curr_dir_path}/infrasructure_deployment.sh ${python_env} ${projectId} ${region} ${serviceaccountkeyfilePath} ${pipelineDir} ${diff_flag} ${env} ${ins}
		if [ $? -ne 0 ]
        then
            echo "Deployment of Namespace/Preferences/Plugin FAILED for Instance: ${ins} "
            exit 1
        else
            echo " Deployment of Namespace/Preferences/Plugin SUCCESSFUL for Instance: ${ins} "
        fi
	done < <(awk -F'/' '{print $(NF)}' ${HOME}/ins_temp_dir/M_instance.csv |awk -F'.' '{print $1}')
fi


while read ins
do
    . ${curr_dir_path}/infrasructure_deployment.sh ${python_env} ${projectId} ${region} ${serviceaccountkeyfilePath} ${pipelineDir} ${diff_flag} ${env} ${ins}
	if [ $? -ne 0 ]
    then
        echo "Deployment of Namespace/Preferences/Plugin FAILED for Instance: ${ins} "
        exit 1
    else
        echo " Deployment of Namespace/Preferences/Plugin SUCCESSFUL for Instance: ${ins} "
    fi       
done < <(sed 1d ${HOME}/cdf_tmp_dir/${output_dir}/${deploy_env}/instance_list.csv | cut -d ',' -f1)


echo "******************* Deployment Completed **************************"

echo "******************* Housekeeping **********************************"

rm -r ${HOME}/ins_temp_dir
rm -r ${HOME}/cdf_tmp_dir
deactivate