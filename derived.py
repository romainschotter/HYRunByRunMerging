from os import path
import os
import json
import argparse
import sys
import inspect
from multiprocessing import Pool
import subprocess
import xml.etree.ElementTree as ET
try:
    import tqdm
except ImportError as e:
    print("Module tqdm is not imported.",
          "Progress bar will not be available (you can install tqdm for the progress bar) `pip3 install --user tqdm`")

# Modes
DOWNLOAD_ALL = True # only in case of downloading derived data! Download ALL AO2Ds and AnalysisResults.root or only those from final merging?
DOWNLOAD_ALL_IF_MERGEDFILE_MISSING = False # in case the merging (per run) was not done, should we download the output file of each subjobs and do the merging ourselves?

def run_cmd(cmd, stdout_encoded_in_text = False):
    run_result = subprocess.run(cmd, shell=True, capture_output=True, text = stdout_encoded_in_text)
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
            print("---> Downloading", self.get_alien_path(), "to", self.out_filename())
            cmd = f"alien_cp -q {self.get_alien_path()} file:{self.out_filename()}"
            if not run_cmd(cmd).returncode == 0:
                print("!!! No AO2Ds found in ", self.get_alien_path()," !!!")
            
            if "AO2D.root" in self.get_alien_path():
                print("---> Downloading AnalysisResults too...");
                temporary = self.get_alien_path()
                analysisresults = temporary.replace("AO2D.root", "AnalysisResults.root")
                temporary = self.out_filename()
                analysisresultslocal = temporary.replace("AO2D.root", "AnalysisResults.root")
                
                cmd = f"alien_cp -q {analysisresults} file:{analysisresultslocal}"
                run_cmd(cmd)
                if not run_cmd(cmd).returncode == 0:
                    print("!!! No AnalysisResults.root found in ", analysisresults, " !!!")
                else:
                    print("---> AR should be at: " + analysisresultslocal)
        else: # merging was not done
            if DOWNLOAD_ALL_IF_MERGEDFILE_MISSING:
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

def getXMLList(train_id=251632,
               alien_path="https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=",
               out_path="./",
               key_file="~/.globus/userkey.pem",
               cert_file="~/.globus/usercert.pem"):
    out_name = path.join(out_path, f"HyperloopID_{train_id}.json")
    if not path.isfile(key_file):
        print("Cannot find key file", key_file)
    if not path.isfile(cert_file):
        print("Cannot find cert file", cert_file)
    if not path.isfile(out_name):
        download_cmd = f"curl --key {key_file} --cert {cert_file} --insecure {alien_path}{train_id} -o {out_name}"
        print("run command: " + download_cmd)
        run_cmd(download_cmd)
        
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
        return run_cmd(cmd, True)
    
def getAO2DList(xmlfile="aod_production.xml"):
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
                    hyOut.alien_path = info.get('lfn')
                    print("alien_path internal for posterior download: "+hyOut.alien_path)
                    ao2d_file_list.append(hyOut)
    return ao2d_file_list

xml_list, is_from_analysis = getXMLList()
for xml in xml_list:
  mergedfile_is_missing = xml.copy_from_alien(overwrite=False)
  if is_from_analysis or mergedfile_is_missing: 
    continue # if output comes from analysis or from a job where the merging was not done, no need to go further and download AO2Ds
  # look for the list of AO2Ds to download (if not already downloaded)
  xmlString=xml.out_filename()
  print("XML file now at: "+xmlString)
  ao2d_file_list=getAO2DList(xmlfile=xmlString)
  downloaded = []
  for i in tqdm.tqdm(ao2d_file_list, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
      downloaded.append(i.copy_from_alien(overwrite=False))

