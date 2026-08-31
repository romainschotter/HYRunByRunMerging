from os import path
import os
import json
import argparse
import sys
import inspect
from multiprocessing import Pool
import subprocess
import xml.etree.ElementTree as ET
import tempfile
try:
    import tqdm
except ImportError as e:
    print("Module tqdm is not imported.",
          "Progress bar will not be available (you can install tqdm for the progress bar) `pip3 install --user tqdm`")

# Modes
TRAIN_NUMBER = 494198 # train number
NUMBER_OF_JOBS = 12 # if the number of job is 1, then the download is performed sequentially. If it is greater than 1, the download is performed in parallel using the option -T of the alien_cp command
OVERWRITE_FILES = False # overwrite already downloaded files?
RUN_NUMBER_FOR_OUTPUT_PATH = True # use the run number for the output path. If on False, the same path as on the grid is used.
DOWNLOAD_ALL = False # only in case of downloading derived data! Download ALL AO2Ds and AnalysisResults.root or only those from final merging?
DOWNLOAD_ALL_IF_MERGEDFILE_MISSING = False # in case the merging (per run) was not done, should we download the output file of each subjobs and do the merging ourselves?
DOWNLOAD_CONFIGURATION = True # download the configuration of the train (from the working directory of the train test)?
CONFIGURATION_FILES = ["full_config.json", "configuration.json", "stdout.log"] # files to get from the working directory of the train test
TRAIN_TEST_URL = "https://alimonitor.cern.ch/train-workdir/tests" # base url of the working directories of the train tests

GRID_KEY_FILE = "~/.globus/userkey.pem" # grid key, needed to access the working directory of the train test
GRID_CERT_FILE = "~/.globus/usercert.pem" # grid certificate, needed to access the working directory of the train test
USE_JALIEN_TOKEN = True # use the JAliEn token (the one of the alien commands, which is not protected by a pass phrase) instead of the grid certificate, so that the pass phrase is asked only once
configuration_download_errors = [] # kept along the way and printed at the end of the execution

def run_cmd(cmd, capture = True, stdout_encoded_in_text = False, cwd = None, env = None):
    run_result = subprocess.run(cmd, shell=True, capture_output=capture, text = stdout_encoded_in_text, cwd = cwd, env = env)
    return run_result

class HyperloopOutput:
    def __init__(self,
                 json_entry,
                 out_path="./"):
        if "outputdir" in json_entry:
            self.alien_path = json_entry["outputdir"]
        else:
            self.alien_path = None
        if "run" in json_entry:
            self.run_number = json_entry["run"]
        else:
            self.run_number = None
        if "merge_state" in json_entry:
            self.merge_state = json_entry["merge_state"]
        else:
            self.merge_state = None
        #self.out_path = path.abspath(out_path)
        self.out_path = path.abspath("./")
        # ROOT interface
        self.tfile = None
        self.root_objects = {}

    def get_alien_path(self):
        if "alien://" in self.alien_path:
            raise RuntimeError(f"Path {self.alien_path} is already an alien path")
        return "alien://" + self.alien_path

    def local_file_position(self):
        return self.alien_path.replace("alien://", "")

    def get_run(self):
        return self.run_number

    def out_filename(self):
        in_path = self.alien_path
        file_name = path.basename(in_path)
        dir_name = path.dirname(in_path)
        if RUN_NUMBER_FOR_OUTPUT_PATH:
            if not "hy_" in dir_name.split("/")[-1]:
                dir_name = f"{self.run_number}/{dir_name.split('/')[-1]}"
            else:
                dir_name = str(self.run_number)
        return path.join(self.out_path, dir_name.strip("/"), file_name)

    def exists(self):
        f = self.out_filename()
        check = path.isfile(f)
        if check:
            print("File", f"`{f}`", "already existing")
            return True
        print("File", f"`{f}`", "not existing")
        return False

    def is_sane(self, throw_fatal=True):
        if not self.exists():
            return False
        f = self.out_filename()
        try:
            open(f)
        except:
            if throw_fatal:
                fatal_print("Cannot open", f)
            return False
        print("File", f"`{f}`", "is sane")
        return True

    def __str__(self) -> str:
        p = f"{self.get_alien_path()}, locally {self.out_filename()}, run {self.get_run()}"
        if self.is_sane():
            p += " (already downloaded and ok)"
        return p

    def __repr__(self) -> str:
        return self.__str__()

    def copy_from_alien(self,
                        parallel_download = False,
                        overwrite=False):
        out_path = path.dirname(self.out_filename())
        if not path.isdir(out_path):
            print("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
        else:
            print("Directory", f"`{out_path}`", "already present")
        
        # Please open download_summary.txt and fill it 
        # --> essential for merging because it keeps track of the run number
        with open(path.join(out_path, "download_summary.txt"), "w") as f:
                f.write(self.get_alien_path() + "\n")
                f.write(f"Run{self.get_run()}\n")

        if not overwrite and self.exists():
            if self.is_sane():
                print("File", f"`{self.out_filename()}`",
                    "already present, skipping for download")
                return self.out_filename()
            else:
                os.remove(self.out_filename())
                print("File", self.out_filename(), "was not sane, removing it and attempting second download", color=bcolors.BWARNING)

        if ".root" in self.get_alien_path() or ".xml" in self.get_alien_path():
            if parallel_download:
                cmd = f"echo \"{self.get_alien_path()} file:{self.out_filename()}\" >> files_to_download.txt"
                if not run_cmd(cmd).returncode == 0:
                    print("!!! Cannot execute command ", cmd, " !!!")
            else:
                print("---> Downloading", self.get_alien_path(), "to", self.out_filename())
                cmd = f"alien_cp -q {self.get_alien_path()} file:{self.out_filename()}"
                if not run_cmd(cmd).returncode == 0:
                    print("!!! No AO2Ds found in ", self.get_alien_path()," !!!")
            
            if "AO2D.root" in self.get_alien_path():
                temporary = self.get_alien_path()
                analysisresults = temporary.replace("AO2D.root", "AnalysisResults.root")
                temporary = self.out_filename()
                analysisresultslocal = temporary.replace("AO2D.root", "AnalysisResults.root")

                if parallel_download:
                    cmd = f"echo \"{analysisresults} file:{analysisresultslocal}\" >> files_to_download.txt"
                    if not run_cmd(cmd).returncode == 0:
                        print("!!! Cannot execute command ", cmd, " !!!")
                else:
                    print("---> Downloading AnalysisResults too...");
                    cmd = f"alien_cp -q {analysisresults} file:{analysisresultslocal}"
                    run_cmd(cmd)
                    if not run_cmd(cmd).returncode == 0:
                        print("!!! No AnalysisResults.root found in ", analysisresults, " !!!")
                    else:
                        print("---> AR should be at: " + analysisresultslocal)
        else: # merging was not done
            if DOWNLOAD_ALL_IF_MERGEDFILE_MISSING:
                if parallel_download:
                    cmd = f"echo \"{self.get_alien_path()} file:{out_path}\" >> files_to_download.txt"
                    if not run_cmd(cmd).returncode == 0:
                        print("!!! Cannot execute command ", cmd, " !!!")
                else:
                    print("---> Downloading", self.get_alien_path(), "to", self.out_filename())
                    cmd = f"alien_cp -q -R {self.get_alien_path()} file:{out_path}"
                    run_cmd(cmd)
                    if not DOWNLOAD_ALL:
                        print("---> Merging AnalysisResults")
                        cmd = f"hadd {self.out_filename()}/AnalysisResults.root $(find {self.out_filename()} -name AnalysisResults.root) > {self.out_filename()}/merging_analysis.log"
                        run_cmd(cmd)
                        print("---> AR should be at: " + self.out_filename() + "/AnalysisResults.root")
                        print("---> Merging AO2D (if any)")
                        cmd = f"find {self.out_filename()} -name AO2D.root > {self.out_filename()}/input.txt"
                        run_cmd(cmd)
                        cmd = f"(cd {self.out_filename()} ; o2-aod-merger > merging_AO2D.log)"
                        run_cmd(cmd)
                        print("---> AO2D should be at: " + self.out_filename() + "/AO2D.root")
                cmd = f"mv {out_path}/download_summary.txt {self.out_filename()}"
                run_cmd(cmd)
                return True
            else:
                return

def getJAlienToken():
    # the token created by alien-token-init, and used by the alien commands, is not
    # protected by a pass phrase: using it for curl too avoids a second pass phrase
    if not USE_JALIEN_TOKEN:
        return None
    cert_file = os.environ.get("JALIEN_TOKEN_CERT", f"/tmp/tokencert_{os.getuid()}.pem")
    key_file = os.environ.get("JALIEN_TOKEN_KEY", f"/tmp/tokenkey_{os.getuid()}.pem")
    if not path.isfile(cert_file) or not path.isfile(key_file):
        return None
    if not run_cmd(f"openssl x509 -checkend 60 -noout -in {cert_file}").returncode == 0:
        print("The JAliEn token", f"`{cert_file}`", "is expired")
        return None
    return (cert_file, key_file)

def ensureJAlienToken():
    # ask alien for a token if there is none yet: the pass phrase is then asked by
    # alien-token-init, and by nothing else during the rest of the execution
    token = getJAlienToken()
    if token is not None or not USE_JALIEN_TOKEN:
        return token
    if not run_cmd("command -v alien-token-init").returncode == 0:
        return None
    print("---> No valid JAliEn token, running alien-token-init")
    run_cmd("alien-token-init", False)
    return getJAlienToken()

def getGridCredentials():
    # (certificate, key) pairs to try, in order: the JAliEn token first (no pass phrase),
    # the grid certificate as a fallback (in case the token is not accepted)
    credentials = []
    token = ensureJAlienToken()
    if token is not None:
        credentials.append(token)
    cert_file = path.expanduser(GRID_CERT_FILE)
    key_file = path.expanduser(GRID_KEY_FILE)
    if path.isfile(cert_file) and path.isfile(key_file):
        credentials.append((cert_file, key_file))
    else:
        print("Cannot find the grid certificate", f"`{cert_file}`", "and/or the grid key", f"`{key_file}`")
    return credentials

def getTrainTestUrl(train_id=TRAIN_NUMBER):
    # working directory of the test of the train, e.g. for the train 717653:
    # https://alimonitor.cern.ch/train-workdir/tests/0071/00717653
    full_number = str(train_id).zfill(8)
    return f"{TRAIN_TEST_URL}/{full_number[:4]}/{full_number}"

def isValidDownloadedFile(file_name):
    # a file that could not be accessed is missing, empty, or an html error page
    if not path.isfile(file_name) or path.getsize(file_name) == 0:
        return False
    if file_name.endswith(".json"):
        try:
            with open(file_name) as f:
                json.load(f)
        except Exception:
            return False
        return True
    with open(file_name, errors="ignore") as f:
        beginning = f.read(1024).lstrip().lower()
    return not (beginning.startswith("<!doctype html") or beginning.startswith("<html"))

def downloadConfigurationFiles(base_url, out_dir, file_names, cert_file, key_file):
    # all the files are asked for in a single curl command, so that a pass phrase, if
    # one is needed, is asked only once. Returns the http code of the files that could
    # not be downloaded (0 if curl did not even manage to ask the server)
    codes_file = path.join(tempfile.gettempdir(), f"curl_http_codes_{os.getpid()}.txt")
    cmd = "curl --silent --show-error"
    cert_dir = os.environ.get("X509_CERT_DIR", "/etc/grid-security/certificates")
    if path.isdir(cert_dir):
        cmd += f" --capath {cert_dir}"
    cmd += f" --cert {cert_file} --key {key_file}"
    cmd += " --write-out \"%{http_code}\\n\""
    for file_name in file_names:
        print("---> Downloading", f"{base_url}/{file_name}", "to", path.join(out_dir, file_name))
        cmd += f" {base_url}/{file_name} --output {file_name}"
    # the http codes are kept in a file, so that the output of curl (and the prompt for
    # the pass phrase of the grid key, if any) stays visible
    cmd += f" > {codes_file}"
    run_cmd(cmd, False, cwd=out_dir)

    http_codes = []
    if path.isfile(codes_file):
        with open(codes_file) as f:
            http_codes = [line.strip() for line in f if line.strip() != ""]
        os.remove(codes_file)

    # curl answers with an exit code of 0 and an html error page when a file is not
    # accessible, so the downloaded files themselves have to be checked
    failed = []
    for i, file_name in enumerate(file_names):
        out_name = path.join(out_dir, file_name)
        if not isValidDownloadedFile(out_name):
            if path.isfile(out_name):
                os.remove(out_name)
            failed.append((file_name, http_codes[i] if i < len(http_codes) else "0"))
        else:
            print("---> Configuration file should be at: " + out_name)
    return failed

def downloadConfiguration(train_id=TRAIN_NUMBER,
                          out_path="./",
                          overwrite=OVERWRITE_FILES):
    # get the configuration of the train from the working directory of its test.
    # a file that cannot be accessed is not fatal: the message is kept and printed at the end
    base_url = getTrainTestUrl(train_id)
    out_dir = path.abspath(out_path)
    if not path.isdir(out_dir):
        print("Preparing directory", f"`{out_dir}`")
        os.makedirs(out_dir)

    to_download = []
    for file_name in CONFIGURATION_FILES:
        if not overwrite and isValidDownloadedFile(path.join(out_dir, file_name)):
            print("Configuration file", f"`{path.join(out_dir, file_name)}`", "already present, skipping for download")
        else:
            to_download.append(file_name)
    if len(to_download) == 0:
        return

    credentials = getGridCredentials()
    if len(credentials) == 0:
        for file_name in to_download:
            configuration_download_errors.append(f"`{file_name}`: no grid credential found to read {base_url}")
        return

    for cert_file, key_file in credentials:
        print("---> Reading", base_url, "with", cert_file)
        failed = downloadConfigurationFiles(base_url, out_dir, to_download, cert_file, key_file)
        to_download = []
        for file_name, http_code in failed:
            print("!!! Cannot download ", f"{base_url}/{file_name}", " (http code ", http_code, ") !!!")
            if http_code == "404": # the file is simply not there, another credential will not help
                configuration_download_errors.append(f"`{file_name}` is not available at {base_url} (http code 404)")
            else:
                to_download.append(file_name)
        if len(to_download) == 0:
            break
    for file_name in to_download: # refused with every credential
        configuration_download_errors.append(f"`{file_name}` could not be downloaded from {base_url}")

def getXMLList(train_id=TRAIN_NUMBER,
               alien_path="https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=",
               out_path="./",
               credentials=None):
    out_name = path.join(out_path, f"HyperloopID_{train_id}.json")
    if credentials is None:
        credentials = getGridCredentials()
    if not path.isfile(out_name):
        for cert_file, key_file in credentials:
            download_cmd = f"curl --key {key_file} --cert {cert_file} --insecure {alien_path}{train_id} -o {out_name}"
            print("run command: " + download_cmd)
            run_cmd(download_cmd, False)
            if isValidDownloadedFile(out_name):
                break
            if path.isfile(out_name):
                os.remove(out_name)
            print("!!! Cannot read the train", train_id, "with", cert_file, "!!!")
        
    sub_file_list = []
    is_from_analysis = False
    with open(out_name) as json_data:
        data = json.load(json_data)
        to_list = data["jobResults"]
        for i in to_list:
            print(i)
            hyOut=HyperloopOutput(i, out_path=out_path)
            # check whether there is an AnalysisResults.root file exists in the alien path from the HyperloopID file
            cmd = f"alien_ls {hyOut.alien_path}/AnalysisResults.root"
            if run_cmd(cmd).returncode == 0: # if yes, then we are dealing with output of analysis task
                if( hyOut.merge_state == "done" ):
                    hyOut.alien_path = hyOut.alien_path + "/AnalysisResults.root"
                is_from_analysis = is_from_analysis or True
            else: # otherwise, we are dealing with output of derived producer task
                if( hyOut.merge_state == "done" ):
                    hyOut.alien_path = hyOut.alien_path + "/AOD/aod_collection.xml"
                is_from_analysis = is_from_analysis or False
            
            if( hyOut.merge_state == "done" or DOWNLOAD_ALL_IF_MERGEDFILE_MISSING):
                sub_file_list.append(hyOut)
            else:
                print("merge_state is not done")
                print("Skipping")
            print("alien_path internal: "+hyOut.alien_path)

    print("Found", len(sub_file_list), "xml files to download")
    return sub_file_list, is_from_analysis

def hasMergedFiles(alien_repo_AOD):
        cmd = f"alien.py find {alien_repo_AOD}/ -r -d \".*[0-9]+/$\""
        return run_cmd(cmd, True, True)
    
def getAO2DList(xmlfile="aod_production.xml", run_number = ""):
    print("parse file: "+xmlfile)
    tree = ET.parse(xmlfile) # convert the xml file into a tree
    root = tree.getroot() # get the root of the tree, the list of collection in our case
    ao2d_file_list = []
    for child in root: # loop over collections in aod_collection.xml
        collection_name=str(child.attrib['name'])
        collection_name=collection_name.replace("aod_collection.xml", "")
        print(collection_name)
        listDirMergedAO2D = str(hasMergedFiles(collection_name).stdout).split("\n")
        # should we download ALL AO2Ds or only focusing on those from final merging?
        #
        # --> Download only those from final merging
        #
        if not DOWNLOAD_ALL and len(listDirMergedAO2D) > 1: #always one element being empty (= '')
            for dir in listDirMergedAO2D:
                if(dir == ''): #always one element being empty (= '')
                    continue
                data = {}
                json_data = json.dumps(data) # dummy json entry to create HyperloopOutput
                hyOut=HyperloopOutput(json_entry=json_data, out_path="./")
                hyOut.run_number = run_number
                hyOut.alien_path = dir + "/AO2D.root"
                print("alien_path internal for posterior download: "+hyOut.alien_path)
                ao2d_file_list.append(hyOut)
        #
        # --> DOWNLOAD EVERYTHING!
        #
        else:
            for element in child: # loop over event in aod_collection.xml
                for info in element: # loop over file in aod_collection.xml
                    print(info.get('lfn'))
                    data = {}
                    json_data = json.dumps(data) # dummy json entry to create HyperloopOutput
                    hyOut=HyperloopOutput(json_entry=json_data, out_path="./")
                    hyOut.run_number = run_number
                    hyOut.alien_path = info.get('lfn')
                    print("alien_path internal for posterior download: "+hyOut.alien_path)
                    ao2d_file_list.append(hyOut)
    return ao2d_file_list

if NUMBER_OF_JOBS > 1:
  cmd = f"rm files_to_download.txt"
  if not run_cmd(cmd).returncode == 0:
    print("!!! Cannot execute command ", cmd, " !!!")

if DOWNLOAD_CONFIGURATION:
  try:
    downloadConfiguration(train_id=TRAIN_NUMBER, out_path="./")
  except Exception as e:
    configuration_download_errors.append(f"The configuration of the train {TRAIN_NUMBER} could not be downloaded: {e}")

xml_list, is_from_analysis = getXMLList()
for xml in xml_list:
  mergedfile_is_missing = xml.copy_from_alien(parallel_download = is_from_analysis, overwrite=OVERWRITE_FILES)
  if is_from_analysis or mergedfile_is_missing: 
    continue # if output comes from analysis or from a job where the merging was not done, no need to go further and download AO2Ds
  # look for the list of AO2Ds to download (if not already downloaded)
  xmlString=xml.out_filename()
  print("XML file now at: "+xmlString)
  ao2d_file_list=getAO2DList(xmlfile=xmlString, run_number = xml.get_run())
  downloaded = []
  for i in tqdm.tqdm(ao2d_file_list, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
    downloaded.append(i.copy_from_alien(parallel_download = (NUMBER_OF_JOBS > 1), overwrite=OVERWRITE_FILES))

if NUMBER_OF_JOBS > 1:
  print("---> Downloading with ", NUMBER_OF_JOBS, " jobs")
  cmd = f"parallel --bar --verbose -j {NUMBER_OF_JOBS} --colsep ' ' alien_cp {{1}} {{2}} :::: files_to_download.txt"  
  if not run_cmd(cmd, False).returncode == 0:
    print("!!! Cannot download files from files_to_download.txt !!!")

if DOWNLOAD_CONFIGURATION:
  if len(configuration_download_errors) > 0:
    print("")
    print("!!! Some configuration files could not be downloaded !!!")
    for message in configuration_download_errors:
      print("   -", message)
    print("Check that", getTrainTestUrl(TRAIN_NUMBER), "is accessible with your grid certificate")
  else:
    print("---> Configuration of the train", TRAIN_NUMBER, "downloaded in", path.abspath("./"))
