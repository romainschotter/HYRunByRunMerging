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
VERBOSE_MODE = False
DRY_MODE_RUNNING = False

def run_cmd(cmd):
    #print("Running command:", f"`{cmd}`")
    #cmd = cmd.split()
    if DRY_MODE_RUNNING:
        print("Dry mode!!!")
        return
    if "capture_output" in inspect.signature(subprocess.run).parameters:
        # Python 3.7+
        run_result = subprocess.run(cmd, shell=True, capture_output=not VERBOSE_MODE)
    else:
        run_result = subprocess.run(cmd, shell=True)
    #print(run_result)
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
                        write_download_summary=True,
                        overwrite=False,
                        overwrite_summary=True):
        out_path = path.dirname(self.out_filename())
        if not path.isdir(out_path):
            print("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
        else:
            print("Directory", f"`{out_path}`", "already present")
        if write_download_summary and (overwrite_summary or not path.isfile(path.join(out_path, "download_summary.txt"))):
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

        print("---> Downloading", self.get_alien_path(), "to", self.out_filename())
        cmd = f"alien_cp -q {self.get_alien_path()} file:{self.out_filename()}"
        run_cmd(cmd)
        
        if "AO2D.root" in self.get_alien_path():
          print("---> Downloading AnalysisResults too...");
          temporary = self.get_alien_path()
          analysisresults = temporary.replace("AO2D.root", "AnalysisResults.root")
          temporary = self.out_filename()
          analysisresultslocal = temporary.replace("AO2D.root", "AnalysisResults.root")
          
          cmd = f"alien_cp -q {analysisresults} file:{analysisresultslocal}"
          run_cmd(cmd)
          print("---> AR should be at: " + analysisresultslocal)

def getXMLList(train_id=272211,
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
    with open(out_name) as json_data:
        data = json.load(json_data)
        to_list = data["jobResults"]
        for i in to_list:
            print(i)
            hyOut=HyperloopOutput(i, out_path=out_path);
            hyOut.alien_path = hyOut.alien_path + "/AOD/aod_collection.xml"
            print("alien_path internal: "+hyOut.alien_path)
            if( hyOut.merge_state == "done" ):
                sub_file_list.append(hyOut)
            else:
                print("merge_state is not done")
                print("Skipping")
    print("Found", len(sub_file_list), "xml files to download")
    return sub_file_list
    
def getAO2DList(xmlfile="aod_production.xml"):
    print("parse file: "+xmlfile)
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    
    ao2d_file_list = []
    for child in root:
        for element in child:
            for info in element:
                print(info.get('lfn'))
                data = {}
                #data['outputdir'] = info.get('lfn')
                json_data = json.dumps(data)
                hyOut=HyperloopOutput(json_entry=json_data, out_path="./")
                hyOut.alien_path = info.get('lfn')
                print("alien_path internal for posterior download: "+hyOut.alien_path)
                ao2d_file_list.append(hyOut)
    return ao2d_file_list
        
#    sub_file_list = []
#    with open(out_name) as json_data:
#        data = json.load(json_data)
#        to_list = data["jobResults"]
#        for i in to_list:
#            print(i)

        
#        if list_meged_files:
#            to_list = data["mergeResults"]
#        else:
#
#        for i in to_list:
#            sub_file_list.append(HyperloopOutput(i, out_path=out_path))
        
#
#    tree = ET.parse('aod_collection.xml')
#    root = tree.getroot()
#    for child in root:
#        for element in child:
#            for info in element:
#                print(info.get('lfn'))

xml_list = getXMLList()
for xml in xml_list:
  xml.copy_from_alien(overwrite=False)
  xmlString=xml.out_filename()
  print("XML file now at: "+xmlString)
  ao2d_file_list=getAO2DList(xmlfile=xmlString)
  downloaded = []
  for i in tqdm.tqdm(ao2d_file_list, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
      downloaded.append(i.copy_from_alien(overwrite=False))

