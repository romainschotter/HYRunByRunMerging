# Hyperloop run-by-run merging

Repository containing files for downloading all output files from Hyperloop run by run, and merging locally only the files associated to a given run list.

## What is present?
Two files are present in the repository:
- `derived.py`, a Python script in charge of downloading all AnalysisResults.root (and AO2D.root in case of derived data) files from Hyperloop run by run,
- `mergeFile.sh`, a bash script in charge of merging the files associated to a given run list.

## How to run it?

In order to merge only the files from a certain runlist, one needs first to download them all run by run. This is achieved by executing the script `derived.py`.

### Downloading files run by run
Before executing the script `derived.py`, 
- edit the line 136 with your train ID. For instance, let's say we want to download all the files from the train `251632`, the line 136 should be `def getXMLList(train_id=251632,`.
- load a O2/O2Physics environment,
- load your certificates and
- proceed to downloading all the files run by run by typing `python3 derived.py`.

The script will first download a json file containing the info of the job results related to the corresponding train ID, and then it will download the output file of each job.

**IMPORTANT 1:** in case of derived data, you will not have one file per run, but several files belonging to the same run scattered over different subdirectories. That is because there is no final merging for derived data, there is only an intermediate merging and the train is set to `done` by operators.
Hence, two options are available: either you can download all AO2D.root and AnalysisResults.root files before any merging (default option), or you can only download the files from the intermediate merging. The choice of option can be changed by turning on True or False, respectively, the boolean at line 17 `DOWNLOAD_ALL`.
**IMPORTANT 2:** after some time, the train output are deleted on the grid, and thus the first option may no longer be available. Although the second option deals with a fewer number of files, in case there was an issue during the merging (merging failed or some files were corrupted), there is no way to fix it afterwards; only the first option offers this flexibility.

### Merging files locally based on the run number
This section only applies to the case where we want to merge the output from an analysis train, not from a derived data production. If you do need to merge output files from a train producing derived data, please contact me in order to find a solution.

After executing the script `derived.py`, a new directory should be present called `alice`. It should contain numerous subdirectories, each containing two files: AnalysisResults.root and download_summary.txt. 

To initiate the merging of the AnalysisResults.root files according to a given runlist, 
- open the file `mergeFile.sh`,
- edit the line 23 with your desired runlist.
    BE CAREFUL: this is a Bash array, the elements of an array are separated with spaces, not with commas. SO provide your runlist with space separation, not comma separation.
- Once this is done, in the same directory as the one containing the file `derived.py`, type `bash mergeFile.sh`.

From this stage, all AnalysisResults.root files coming from your train ID and your desired runlist have been merged into one single file :-D

## Troubleshooting

### FileNotFoundError: [Errno 2] No such file or directory: \'./HyperloopID_251632.json\'
It can happen that the download of the json file fails. In which case, you can always download it yourself and execute the script. This will bypass this error.

Download the file at the address `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=` + train ID. Again, using the previous example of train `251632`, one needs to enter access the url `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=251632`. 
Download this file and, VERY IMPORTANTLY, name it `HyperloopID_#TRAINID.json`. Taking our previous example for the train `251632`, the file should named `HyperloopID_251632.json`.

NOTE: the `HyperloopID_#TRAINID.json` should be placed in the same directory as the `derived.py` file.

Execute the script `derived.py` and the downloading of the file should start.

### Others
In case you are facing difficulties: please contact me either on Mattermost (rschotte) or via mail (romain.schotter@cern.ch).
