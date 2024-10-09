#!/bin/bash

# Define the output file name
FILE_TYPE="AnalysisResults.root"
find "$(pwd)" -type f -name "AO2D.root" > "AO2Ds.txt"

# Check if hadd is available (ROOT tool for merging)
if ! command -v hadd &> /dev/null
then
    echo "Error: hadd command not found. Make sure you have ROOT installed and sourced."
    exit 1
fi

# Find all root files matching the pattern
FILES=$(find alice/cern.ch/user/a/alihyperloop/jobs/* -name $FILE_TYPE)

# Check if any files were found
if [ -z "$FILES" ]; then
    echo "No $FILE_TYPE files found in the specified directories."
    exit 1
fi

# Merge the ROOT files using hadd
echo "Merging the following files into $FILE_TYPE:"
echo "$FILES"
hadd -f $FILE_TYPE $FILES

# Check if the merge was successful
if [ $? -eq 0 ]; then
    echo "Merge completed successfully into $FILE_TYPE."
else
    echo "Error: Merge failed."
fi
