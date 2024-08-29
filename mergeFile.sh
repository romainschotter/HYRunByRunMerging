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

INPUT_MC_REPO=alice
declare -a RUN_LIST
RUN_LIST=(526641 526964 527041 527057 527109 527240 527850 527871 527895 527899 528292 528461 528531)


hadd AnalysisResults.root $(for key in "${!RUN_LIST[@]}"; do string=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_MC_REPO}) ; echo ${string/download_summary.txt/AnalysisResults.root}; done)