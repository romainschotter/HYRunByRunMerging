#!/bin/bash

INPUT_MC_REPO=alice
declare -a RUN_LIST
RUN_LIST=(526641 526964 527041 527057 527109 527240 527850 527871 527895 527899 528292 528461 528531)


hadd AnalysisResults.root $(for key in "${!RUN_LIST[@]}"; do string=$(grep -r -l ${RUN_LIST[${key}]} ${INPUT_MC_REPO}) ; echo ${string/download_summary.txt/AnalysisResults.root}; done)
