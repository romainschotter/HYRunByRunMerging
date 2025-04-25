#!/bin/bash

# Copyright 2019-2020 CERN and copyright holders of ALICE O2.
# See https://alice-o2.web.cern.ch/copyright for details of the copyright holders.
# All rights not expressly granted are reserved.
#
# This software is distributed under the terms of the GNU General Public
# License v3 (GPL Version 3), copied verbatim in the file "COPYING".
#
# In applying this license CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction
#
##
## \file   mergeByCommonRun.sh
## \author Romain Schotter <romain.schotter@cern.ch>
##
## \brief  Scripts to merge all output files according to runs in common in two datasets (real data and MC, for example) and according to a given runlist (e.g. CBT, etc)
##

TAG=$(date +%F_%H-%M-%S)
INPUT_REPO_REAL=/home/romain/alice_analysis_work/PbPb/Data/LF_LHC23_PbPb_pass4_Strangeness/LHC23_full_withUPCinfo_EvgenyNewEvSelNewOcc_v5_InteractionRate
INPUT_REPO_MC=/home/romain/alice_analysis_work/PbPb/Data/MC/LHC24g3_pass4_withUPCinfo_EvgenyNewEvSelNewOcc_v10_InteractionRate
RUN_LIST_STRING="544013, 544032, 544028, 544095, 544098, 544116, 544121, 544122, 544123, 544124, 544184, 544389, 544390, 544391, 544392, 544185, 544454, 544474, 544475, 544476, 544477, 544490, 544491, 544492, 544508, 544511, 544512, 544510, 544548, 544550, 544551, 544564, 544567, 544568, 544580, 544582, 544583, 544585, 544549, 544565, 544614, 544652, 544672, 544674, 544692, 544693, 544694, 544696, 544739, 544742, 544754, 544767, 544653, 544794, 544795, 544813, 545345, 545289, 545184, 545103, 545086, 545060, 545004, 544991, 544963, 544931, 544868, 544887, 544914, 544917, 544961, 544964, 544968, 545008, 545009, 545041, 545042, 545044, 545047, 545062, 545063, 545117, 545171, 545185, 545210, 545222, 545223, 545246, 545249, 545262, 545291, 545295, 545312"
IFS=", " read -ra RUN_LIST <<< "${RUN_LIST_STRING}"

USED_FILES_REAL=""
USED_FILES_MC=""
# keep track of which runs are actually used in the merging (some runs might be missing)
echo "########################" > merge_summary_${TAG}.txt
echo "# Merging summary info #" >> merge_summary_${TAG}.txt
echo "########################" >> merge_summary_${TAG}.txt
INITIAL_RUN_LIST_LOG=""
USED_RUN_LIST_LOG=""
MISSING_RUN_LIST_LOG=""
MISSING_RUN_REASON_LOG=""
for key in "${!RUN_LIST[@]}"; 
do 
INITIAL_RUN_LIST_LOG="${INITIAL_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
string_real=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_REPO_REAL}/alice) 
string_mc=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_REPO_MC}/alice) 
if [ -n "${string_real}" ] && [ -n "${string_mc}" ]; then # check that the directories associated to this run have been downloaded
    file_real_exist=$(find ${string_real/download_summary.txt//} -name AnalysisResults.root)
    file_mc_exist=$(find ${string_mc/download_summary.txt//} -name AnalysisResults.root)
    if [ -n "${file_real_exist}" ] && [ -n "${file_mc_exist}" ]; then # check that there are .root files in those directories (could be missing if merging has not been done)
        USED_RUN_LIST_LOG="${USED_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
        USED_FILES_REAL="${USED_FILES_REAL} ${string_real/download_summary.txt/AnalysisResults.root} "
        USED_FILES_MC="${USED_FILES_MC} ${string_mc/download_summary.txt/AnalysisResults.root} "
    elif [ -n "${file_real_exist}" ]; then
        MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
        MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG} - ${RUN_LIST[${key}]}: AnalysisResults.root file not found for ${INPUT_REPO_REAL} (please check on Hyperloop if merging was done)\n")
    elif [ -n "${file_mc_exist}" ]; then
        MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
        MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG} - ${RUN_LIST[${key}]}: AnalysisResults.root file not found for ${INPUT_REPO_MC} (please check on Hyperloop if merging was done)\n")
    else
        MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
        MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG} - ${RUN_LIST[${key}]}: AnalysisResults.root file not found anywhere (please check on Hyperloop if merging was done for both ${INPUT_REPO_REAL} and ${INPUT_REPO_MC})\n")
    fi
elif [ -n "${string_real}" ]; then
    MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
    MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG}\n - ${RUN_LIST[${key}]}: no directory found for this run for ${INPUT_REPO_REAL} (are you sure this run belongs to this dataset?)\n")
elif [ -n "${string_mc}" ]; then
    MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
    MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG}\n - ${RUN_LIST[${key}]}: no directory found for this run for ${INPUT_REPO_MC} (are you sure this run belongs to this dataset?)\n")
else
    MISSING_RUN_LIST_LOG="${MISSING_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
    MISSING_RUN_REASON_LOG=$(printf "${MISSING_RUN_REASON_LOG}\n - ${RUN_LIST[${key}]}: no directory found for this run anywhere (are you sure this run belongs to this dataset?)\n")
fi
done
echo "Initial/wanted runlist" >> merge_summary_${TAG}.txt
echo ${INITIAL_RUN_LIST_LOG::-2} >> merge_summary_${TAG}.txt
echo "Actually used runlist" >> merge_summary_${TAG}.txt
echo ${USED_RUN_LIST_LOG::-2} >> merge_summary_${TAG}.txt
echo "Missing runs" >> merge_summary_${TAG}.txt
echo ${MISSING_RUN_LIST_LOG::-2} >> merge_summary_${TAG}.txt
echo "Reason(s) for missing runs:" >> merge_summary_${TAG}.txt
printf '%s\n' "${MISSING_RUN_REASON_LOG}" >> merge_summary_${TAG}.txt
echo "########################" >> merge_summary_${TAG}.txt
echo "########################" >> merge_summary_${TAG}.txt

# proceed to merging
(cd ${INPUT_REPO_REAL} ; hadd -k AnalysisResults_${TAG}.root ${USED_FILES_REAL} )
(cd ${INPUT_REPO_MC} ; hadd -k AnalysisResults_${TAG}.root ${USED_FILES_MC} )
cp merge_summary_${TAG}.txt ${INPUT_REPO_REAL}
cp merge_summary_${TAG}.txt ${INPUT_REPO_MC}
more merge_summary_${TAG}.txt