#!/bin/bash

# Define the path to the JSON file
JSON_FILE="HyperloopID_272211.json"

# Define the list of run numbers
RUN_LIST=(526964 527041)

# Initialize an empty array for storing the output directories
OUTPUT_DIR_LIST=()

# Loop over each run number in the RUN_LIST
for run in "${RUN_LIST[@]}"; do
    # Extract the block containing the run number and preceding lines
    block=$(grep -B 5 -E "\"run\"[[:space:]]*:[[:space:]]*$run" "$JSON_FILE")

    # If the run is found, find the corresponding "outputdir"
    if [ ! -z "$block" ]; then
        # Get the outputdir from the lines preceding the run number
        outputdir_line=$(echo "$block" | grep "\"outputdir\"")
        
        # Extract the outputdir path using sed and remove escape backslashes
        outputdir=$(echo "$outputdir_line" | sed -E 's/.*"outputdir"[[:space:]]*:[[:space:]]*"(.*)".*/\1/' | sed 's/\\//g')
        
        # Add "./" prefix to make the paths relative to the current working directory
        outputdir=".$outputdir"

        # Append the cleaned outputdir to the OUTPUT_DIR_LIST array
        OUTPUT_DIR_LIST+=("$outputdir")
    fi
done

# Loop over each output directory in the OUTPUT_DIR_LIST and merge the files
for i in "${!OUTPUT_DIR_LIST[@]}"; do
    run=${RUN_LIST[$i]}
    output_dir=${OUTPUT_DIR_LIST[$i]}
    
    echo "Processing run $run in directory $output_dir"

    # Define the output file name for the merged result
    merged_output_file="AnalysisResults_${run}.root"
    
    # Find all AnalysisResults.root files under the corresponding directory and merge them using hadd
    find "$output_dir" -name "AnalysisResults.root" | xargs hadd -f "$merged_output_file"
    find "$output_dir" -name "AO2D.root" > "AO2Ds_${run}.txt"
    
    echo "Merged AnalysisResults for run $run into $merged_output_file"
done
