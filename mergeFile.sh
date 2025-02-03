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
## \file   mergeFile.sh
## \author Romain Schotter <romain.schotter@cern.ch>
##
## \brief  Scripts to merge all output files according to a given run list
##

INPUT_REPO=alice
RUN_LIST_STRING="526641, 526964, 527041, 527057, 527109, 527240, 527850, 527871, 527895, 527899, 528292, 528461, 528531"
IFS=", " read -ra RUN_LIST <<< "${RUN_LIST_STRING}"

# keep track of which runs are actually used in the merging (some runs might be missing)
echo "Merging summary info" > merge_summary.txt
INITIAL_RUN_LIST_LOG=""
USED_RUN_LIST_LOG=""
for key in "${!RUN_LIST[@]}"; 
do 
INITIAL_RUN_LIST_LOG="${INITIAL_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
string=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_REPO}) 
if [ -n "${string}" ]; then
    USED_RUN_LIST_LOG="${USED_RUN_LIST_LOG} ${RUN_LIST[${key}]}, "
fi
done
echo "Initial/wanted runlist" >> merge_summary.txt
echo ${INITIAL_RUN_LIST_LOG::-2} >> merge_summary.txt
echo "Actually used runlist" >> merge_summary.txt
echo ${USED_RUN_LIST_LOG::-2} >> merge_summary.txt

# proceed to merging
hadd -k AnalysisResults_LHC22oRuns.root $(for key in "${!RUN_LIST[@]}"; do string=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_REPO}) ; echo ${string/download_summary.txt/AnalysisResults.root}; done)
more merge_summary.txt