# Hyperloop run-by-run merging

Repository containing files for downloading all output files from Hyperloop run by run (together with the configuration of the train), and merging locally only the files associated to a given run list.

## What is present?
Four files are present in the repository:
- `derived.py`, a Python script in charge of downloading all AnalysisResults.root (and AO2D.root in case of derived data) files from Hyperloop run by run, as well as the configuration of the train,
- `download.sh`, a bash script in charge of downloading a single file from a given url, typically a file from the working directory of a train test,
- `mergeFile.sh`, a bash script in charge of merging the files associated to a given run list.
- `mergeByCommonRun.sh`, a bash script in charge of merging only the files in common in two datasets and according to a given run list.

## How to run it?

In order to merge only the files from a certain runlist, one needs first to download them all run by run. This is achieved by executing the script `derived.py`.

### Downloading files run by run
Before executing the script `derived.py`, 
- edit the line 18 with your train ID. For instance, let's say we want to download all the files from the train `251632`, the line 18 should be `TRAIN_NUMBER = 251632`.
- load a O2/O2Physics environment,
- load your certificates and
- proceed to downloading all the files run by run by typing `python3 derived.py`.

The script will first download the configuration of the train (see the section below), then a json file containing the info of the job results related to the corresponding train ID, and finally the output file of each job.

**IMPORTANT 1:** in order to download the files faster, the download is performed in parallel on 12 jobs. In case, you want to reduce the number of jobs, you need to change the variable `NUMBER_OF_JOBS` at line 19. For disabling the parallel download, set the `NUMBER_OF_JOBS` to `1`.

**IMPORTANT 2:** by default, a directory is created for each run. In case you want to download the output in directories matching the output train directories on the grid (`alice/cern.ch/user/a/alihyperloop/jobs/0<000>/hy_<trainID>`), the variable `RUN_NUMBER_FOR_OUTPUT_PATH` needs to be switched to `False`

**IMPORTANT 3:** in case of derived data, you will not have one file per run, but several files belonging to the same run scattered over different subdirectories. That is because there is no final merging for derived data, there is only an intermediate merging and the train is set to `done` by operators.
Hence, two options are available: either you can download all AO2D.root and AnalysisResults.root files before any merging (default option), or you can only download the files from the intermediate merging. The choice of option can be changed by turning on True or False, respectively, the boolean at line 22 `DOWNLOAD_ALL`.

**IMPORTANT 4:** after some time, the train output are deleted on the grid, and thus the first option may no longer be available. Although the second option deals with a fewer number of files, in case there was an issue during the merging (merging failed or some files were corrupted), there is no way to fix it afterwards; only the first option offers this flexibility.

**IMPORTANT 5:** when running on the grid, it may happen that some subjobs from a given masterjob (or run) finished in error states. If there are too many subjobs in error states, the merging will not start for this masterjob. In such a case, this masterjob will not be considered in the final merging across all masterjobs/runs, i.e. this masterjob/run will not be included in the final output file. By default, the `derived.py` script reproduces this behaviour and will not download output files from masterjobs that could not proceed to merging. In case you are interested in still having the files from those masterjobs, you can tell the script `derived.py` to download them and merge them locally by switching the variable `DOWNLOAD_ALL_IF_MERGEDFILE_MISSING` at line 23 on `True`. Please note, however, that the best course of action would be to understand why too many jobs went in error. 

### Downloading the configuration of the train
On top of the output files, the script also downloads the configuration of the train from the working directory of the train test, located at `https://alimonitor.cern.ch/train-workdir/tests/00XX/00XXYYYY/`, where `00XXYYYY` is the train ID padded with zeros up to 8 digits, and `00XX` its first four digits. For instance, the test of the train `717653` is at `https://alimonitor.cern.ch/train-workdir/tests/0071/00717653/`.

Three files are downloaded in the directory from which the script is executed, next to the directories of the runs:
- `full_config.json`,
- `configuration.json`,
- `stdout.log`.

This step is controlled by the variable `DOWNLOAD_CONFIGURATION` at line 24 (set it to `False` to skip it), and the list of files to download is given by the variable `CONFIGURATION_FILES` at line 25. Files that are already there are not downloaded again, unless the variable `OVERWRITE_FILES` at line 20 is set to `True`.

If one of these files cannot be accessed (it may not exist for this train, or the working directory of the test may no longer be available), the download of the train output is **not** interrupted: the script carries on, and prints at the very end of its execution the list of the files that could not be downloaded, for instance:
```
!!! Some configuration files could not be downloaded !!!
   - `configuration.json` is not available at https://alimonitor.cern.ch/train-workdir/tests/0071/00717653 (http code 404)
Check that https://alimonitor.cern.ch/train-workdir/tests/0071/00717653 is accessible with your grid certificate
```

### Entering your pass phrase only once
Reading the Hyperloop json file and the working directory of the train test requires a grid credential. Two of them can be used:
- the JAliEn token (`/tmp/tokencert_<uid>.pem` and `/tmp/tokenkey_<uid>.pem`, or the files pointed to by `$JALIEN_TOKEN_CERT` and `$JALIEN_TOKEN_KEY`), created by `alien-token-init` and used by the alien commands. This token is **not** protected by a pass phrase,
- your grid certificate (`~/.globus/usercert.pem` and `~/.globus/userkey.pem`, see the variables `GRID_KEY_FILE` and `GRID_CERT_FILE` at lines 28 and 29), whose key **is** protected by your pass phrase.

By default (variable `USE_JALIEN_TOKEN` at line 30), the script uses the token, and asks `alien-token-init` for one if there is none or if it is expired. As the very same token is then used to download the output of the train, your pass phrase is asked only once, when the token is created, instead of once for the token and once again for the configuration. If the token is not accepted, the script automatically tries again with your grid certificate, and your pass phrase is then asked.

### Downloading a single file from the working directory of a train test
Any other file of the working directory of a train test can be downloaded by hand with the script `download.sh`, which takes the url of the directory and the name of the file:
```
bash download.sh https://alimonitor.cern.ch/train-workdir/tests/0071/00717653 AO2D.root
```
The file is written in the current directory. This script uses your grid certificate and the CA certificates pointed to by `$X509_CERT_DIR`, so a O2/O2Physics environment has to be loaded, and your pass phrase will be asked. It is independent from `derived.py`, which does not call it.

### Merging files locally based on the run number
This section only applies to the case where we want to merge the output from an analysis train, not from a derived data production. If you do need to merge output files from a train producing derived data, please contact me in order to find a solution.

After executing the script `derived.py`, new directories should be present (or one new directory called `alice` with numerous subdirectories in case `RUN_NUMBER_FOR_OUTPUT_PATH` has been turned on `False`), each containing two files: AnalysisResults.root and download_summary.txt. 

To initiate the merging of the AnalysisResults.root files according to a given runlist, 
- open the file `mergeFile.sh`,
- edit the line 22 with your desired runlist, separated with a comma followed by a space like this ", ". If you use different separators, please edit line 23.
    NOTE: if you copy-paste the runlist from Hyperloop, runs are already separated with ", ", so you don't need to change the separators.
- Once this is done, in the same directory as the one containing the file `derived.py`, type `bash mergeFile.sh`.

From this stage, all AnalysisResults.root files coming from your train ID and your desired runlist have been merged into one single file :-D

### Merging files locally from runs in common between two datasets and based on the run number
This section only applies to the case where we want to merge the output from two analysis trains (not from a derived data production) in such a way that we consider only the runs belonging to your favorite runlist and common between the two trains (for example, the typical use case could be: you want to make sure that you look at the same runs in the data and in MC). This section only applies to analysis trains, not to trains producing derived data. If you are interested in the latter, please contact me in order to find a solution.

After executing the script `derived.py` twice (one for each analysis train) in separate directories, you should have two directories (one for each analysis train) containing directories for each run in the dataset (or one directory called `alice` with numerous subdirectories in case `RUN_NUMBER_FOR_OUTPUT_PATH` has been turned on `False`). It should contain two files: AnalysisResults.root and download_summary.txt. 

To initiate the merging of the AnalysisResults.root files for the two productions according to a given runlist, 
- in one of the two directories, open the file `mergeByCommonRun.sh`,
- edit the line 22 with with the path to the first directory,
- edit the line 23 with with the path to the second directory,
- edit the line 24 with your desired runlist, separated with a comma followed by a space like this ", ". If you use different separators, please edit line 25.
    NOTE: if you copy-paste the runlist from Hyperloop, runs are already separated with ", ", so you don't need to change the separators.
- Once this is done, type `bash mergeByCommonRun.sh`.

From this stage, both directories should contain a AnalysisResults.root, containing the merged output files coming from your desired runlist and from runs in common between both trains :-D

## Troubleshooting

### FileNotFoundError: [Errno 2] No such file or directory: \'./HyperloopID_251632.json\'
It can happen that the download of the json file fails. In which case, you can always download it yourself and execute the script. This will bypass this error.

Download the file at the address `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=` + train ID. Again, using the previous example of train `251632`, one needs to enter access the url `https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=251632`. 
Download this file and, VERY IMPORTANTLY, name it `HyperloopID_#TRAINID.json`. Taking our previous example for the train `251632`, the file should named `HyperloopID_251632.json`.

NOTE: the `HyperloopID_#TRAINID.json` should be placed in the same directory as the `derived.py` file.

Execute the script `derived.py` and the downloading of the file should start.

### NameError: name \'tqdm\' is not defined
The script `derived.py` uses a Python package called `tqdm` to estimate the remaining time for downloading a file. In case such a package is missing, the script will crash with the above error.

You can install this package by typing `pip install tqdm` or `pip3 install tqdm`. Please note that you HAVE TO type that command inside a O2/O2Physics envrionment or it will not work! because O2/O2Physics uses its own Python installation. 
The installation may be unsuccessful because `pip` or `pip3` is not installed for the Python version installed with O2/O2Physics. You can however force to use the `pip` that belongs to which ever Python's `python` or `python3` by typing `python3 -m pip install tqdm` or `python3 -m pip3 install tqdm`.

If the installation of the `tqdm` is successful, the following message should be printed: `Successfully installed tqdm-x.xx.x`. From that point, you can proceed to downloading your files via `python3 derived.py`.

In case you are still facing this error after following the above instructions, please find help in the `Others` category.

### Some configuration files could not be downloaded
At the end of its execution, the script prints the list of the configuration files it could not get, together with the http code returned by the server. This never prevents the output of the train from being downloaded.

A http code `404` means that this file does not exist in the working directory of the train test: nothing can be done about it, simply remove it from the list `CONFIGURATION_FILES` at line 25 if you do not want to be told about it again. Any other code points to an access problem: check that the url printed by the script can be opened in your browser, and that your token is still valid (`alien-token-info`). You can also set the variable `USE_JALIEN_TOKEN` at line 30 to `False` to use your grid certificate directly (your pass phrase will then be asked).

### Others
In case you are facing difficulties: please contact me either on Mattermost (rschotte) or via mail (romain.schotter@cern.ch).
