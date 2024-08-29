# Hyperloop run-by-run merging

Repository containing files for downloading all output files from Hyperloop run by run, and merging locally only the files associated to a given run list.

## What is present?
Two files are present in the repository:
- `derived.py`, a Python script in charge of downloading all output files from Hyperloop run by run,
- `mergeFile.sh`, a bash script in charge of merging the files associated to a given run list.

## How to run it?

In order to merge only the files from a certain runlist, one needs first to download them all run by run. This is achieved by executing the script `derived.py`.

### Downloading files run by run
Before executing the script `derived.py`, 
- edit the line 157 with your train ID. For instance, let's say we want to download all the files from the train `251632`, the line 157 should be `def getXMLList(train_id=251632,`.
- load a O2/O2Physics environment,
- load your certificates and
- proceed to downloading all the files run by run by typing `python3 derived.py`.

The script will first download a json file containing the info of the job results related to the corresponding train ID, and then it will download the output file of each job.

### Merging files locally based on the run number
After executing the script `derived.py`, a new directory should be present called `alice`. It should contain numerous subdirectories, each containing two files: AO2D.root and download_summary.txt.

To initiate the merging of the output files according to a given runlist, 
- open the file `mergeFile.sh`,
- edit the line 23 with your desired runlist.
    BE CAREFUL: this is a Bash array, the elements of an array are separated with spaces, not with commas. SO provide your runlist with space separation, not comma separation.
- Once this is done, in the same directory as the one containing the file `derived.py`, type `bash mergeFile.sh`.

From this stage, all output files coming from your train ID and your desired runlist have been merged into one single file :-D

## Troubleshooting

### FileNotFoundError: [Errno 2] No such file or directory: \'./HyperloopID_251632.json\'
It can happen that the download of the json file fails. In which case, you can always download it yourself and execute the script. This will bypass this error.

Download the file at the address `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=` + train ID. Again, using the previous example of train `251632`, one needs to enter access the url `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=251632`. 
Download this file and, VERY IMPORTANTLY, name it `HyperloopID_#TRAINID.json`. Taking our previous example for the train `251632`, the file should named `HyperloopID_251632.json`.

NOTE: the `HyperloopID_#TRAINID.json` should be placed in the same directory as the `derived.py` file.

Execute the script `derived.py` and the downloading of the file should start.

### Others
In case you are facing difficulties: please contact me either on Mattermost (rschotte) or via mail (romain.schotter@cern.ch).
