
# Hyperloop Run-by-Run Merging

This repository contains scripts for downloading output files from Hyperloop, run by run, and merging them locally based on a specified run list.

## Contents

The repository includes the following files:

- **`hyperDownload.py`**: A Python script for downloading output files from Hyperloop run by run.
- **`run-by-run-merging.sh`**: A bash script to merge the files associated with a specified run list.
- **`merge.sh`**: A bash script to merge all `AnalysisResults.root` files located under the `alice` directory.
- **`cleanup.sh`**: A bash script for cleaning up the directory by removing the `alice` directory, `AnalysisResults*` and `AO2D*` files.

## How to Use

### 1. Downloading Files Run by Run

To merge files from a specific run list, you first need to download them. This is achieved by running the `hyperDownload.py` script.

#### Steps:
1. **Edit the Train ID**:
   - Open `hyperDownload.py` and modify **line 79** with your train ID.
   - For example, to download files from train `272211`, modify **line 79** to:  
     ```python
     xml_list = getXMLList(272211)
     ```

2. **Derived Data**:
   - If your train produces derived data, uncomment the following line:
     ```python
     xml.copy_from_alien(file_type="AO2D.root")
     ```

3. **Environment Setup**:
   - Load the O2/O2Physics environment.
   - Ensure your certificates are loaded.

4. **Run the Download Script**:
   - Execute the script by typing:
     ```bash
     python3 hyperDownload.py
     ```
   The script will download a JSON file containing job results and then retrieve the output files for each job.

### 2. Merging Files Locally by Run Number

After running `hyperDownload.py`, a new directory called `alice` will be created, containing subdirectories with files like `AO2D.root` and `AnalysisResults.root`.

#### Steps to Merge Files:
1. Open `run-by-run-merging.sh`.
2. Modify **line 7** to include your desired run list.
   - **Important**: The run list should be a bash array, and elements should be separated by spaces (not commas). For example:
     ```bash
     RUN_LIST=(526964 526641)
     ```
3. Once you've updated the run list, run the script by typing:
   ```bash
   bash run-by-run-merging.sh
   ```
   This will merge all output files from the specified run list into a single file.

- To merge **all** `AnalysisResults.root` files under the `alice` directory, you can use:
   ```bash
   bash merge.sh
   ```

The merged files will be named as `AnalysisResults_$run_number.root`. Additionally, a text file containing paths to the corresponding `AO2D.root` files will be created named `AO2Ds_$run_number.txt`.

### 3. Cleaning Up the Directory

If you wish to clean up the directory after merging, you can use the `cleanup.sh` script. This will remove all related files and directories, including `alice`, `HyperloopID*`, `AnalysisResults*`, and `AO2D*`.

#### To execute the cleanup:
```bash
bash cleanup.sh
```

The script contains the following commands:
```bash
#!/bin/bash
rm -rf alice
rm -rf HyperloopID*
rm AnalysisResults*
rm AO2D*
```

## Troubleshooting

For any further assistance, feel free to contact us:
- **Mattermost**: rschotte, rnepeivo
- **Email**:  
   - Romain Schotter: [romain.schotter@cern.ch](mailto:romain.schotter@cern.ch)
   - Roman Nepeivoda: [roman.nepeivoda@cern.ch](mailto:roman.nepeivoda@cern.ch)