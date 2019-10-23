#!/usr/bin/env python

"""Run simics to verify booting to UEFI shell"""

from __future__ import print_function

import os
import sys
import subprocess
import glob

# Use colors in terminals
CRED = '\033[91m'
CGRN = '\033[92m'
CEND = '\033[0m'

if sys.platform == "win32":
    SIMICS_CMD = os.path.join(os.getcwd(), "simics.bat")
else:
    SIMICS_CMD = os.path.join(os.getcwd(), "simics")

SIMICS_SCRIPT = os.path.join("targets", "x86-ehl", "ehl.simics")

def run_simics(image_list):
    print("Testing total {} images: ".format(len(image_list)))
    pass_count = 0
    for idx, image in enumerate(image_list):
        print("[{:2d}] {} ... ".format(idx, image), end="")
        sys.stdout.flush()
        cmd = [SIMICS_CMD, "-batch-mode", SIMICS_SCRIPT,
                                          "image_path={}".format(image)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode != 0:
            print("{}FAILED.{}".format(CRED, CEND))
        else:
            pass_count += 1
            print("{}PASSED.{}".format(CGRN, CEND))

    if pass_count < len(image_list):
        raise RuntimeError


def main():
    if len(sys.argv) != 2:
        raise Exception("Usage: {} <image_path>".format(os.path.basename(sys.argv[0])))

    image_path = sys.argv[1]
    if os.path.isdir(image_path):
        # process all files in the folder
        image_list = glob.glob(os.path.join(image_path, "*.bin"))
    else:
        # process a single file
        image_list = [image_path]

    try:
        run_simics(image_list)
    except RuntimeError as e:
        print("*** Some images failed to boot!")
        print(e)
        exit(1)
    except:
        raise Exception("Unexpected exceptions!")


if __name__ == "__main__":
    sys.exit(main())

