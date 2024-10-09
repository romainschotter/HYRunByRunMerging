import os
import json
import subprocess
from os import path

# Modes
VERBOSE_MODE = False
DRY_MODE_RUNNING = False

def run_cmd(cmd):
    if DRY_MODE_RUNNING:
        print("Dry mode! Command not executed:", cmd)
        return
    return subprocess.run(cmd, shell=True, capture_output=not VERBOSE_MODE)

class HyperloopDownloader:
    def __init__(self, json_entry):
        self.alien_path = json_entry.get("outputdir")

    def get_alien_path(self, path):
        if path.startswith("alien://"):
            raise RuntimeError(f"Path {path} is already an alien path")
        return "alien://" + path

    def copy_from_alien(self, file_type, write_download_summary=True, overwrite=False, overwrite_summary=True):
            alien_ls_parent = subprocess.run(f"alien_ls {self.alien_path}", shell=True, capture_output=True, text=True)
            alien_paths = []

            # Check if AOD directory exists
            if "AOD" in alien_ls_parent.stdout:   
                print("Job has AOD folder -> processing standard derived data output")
                self.alien_path += "/AOD"

                # List subdirectories in the AOD folder
                alien_ls_sub = subprocess.run(f"alien_ls {self.alien_path}", shell=True, capture_output=True, text=True)
                subfolders = alien_ls_sub.stdout.splitlines()

                # Process each folder in the AOD subdirectory
                for folder in alien_ls_sub.stdout.splitlines():
                    if folder != "aod_collection.xml":
                        alien_path_curr = self.alien_path + "/" + folder + file_type
                        alien_paths.append(alien_path_curr)
            else:
                alien_paths.append(self.alien_path + "/" + file_type)

            print("Files to download:")
            for item in alien_paths:
                print(item)

            for path in alien_paths:   
                current_dir = os.path.dirname(os.path.abspath(__file__))
                directory = os.path.dirname(current_dir + path)
                os.makedirs(directory, exist_ok=True)

                print("---> Downloading", self.get_alien_path(path), "to", directory)
                cmd = f"alien_cp -q {self.get_alien_path(path)} file:{directory}"
                run_cmd(cmd)

def getXMLList(train_id=272211, alien_path="https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=", key_file="~/.globus/userkey.pem", cert_file="~/.globus/usercert.pem"):
    out_name = f"HyperloopID_{train_id}.json"

    for file in (key_file, cert_file):
        if not path.isfile(file):
            print(f"Cannot find {file}")

    if not path.isfile(out_name):
        run_cmd(f"curl --key {key_file} --cert {cert_file} --insecure {alien_path}{train_id} -o {out_name}")

    with open(out_name) as json_data:
        data = json.load(json_data)
        sub_file_list = [HyperloopDownloader(job) for job in data["jobResults"] if job["merge_state"] == "done"]
    
    print(f"Found {len(sub_file_list)} jobs to download")
    return sub_file_list

def main():
    xml_list = getXMLList(273979)
    for xml in xml_list:
        print(xml.alien_path)
        xml.copy_from_alien(file_type="AnalysisResults.root")
        # xml.copy_from_alien(file_type="AO2D.root")

if __name__ == "__main__":
    main()
