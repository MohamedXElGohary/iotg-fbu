#!/usr/bin/env python

"""Release script to package required files"""

import os
import sys
import zipfile
from datetime import datetime

import pypandoc

OUTDIR = "dist"

BOM = [
    "scripts",
    "common",
    "thirdparty",
    "LICENSE",
    "USER_MANUAL.html",
    "docs/stitching_usage_flow.png",
    "docs/subregion_capsule_usage_flow.png"
]


def create_archive(out_zip, file_list):

    dest_list = []
    for name in file_list:
        if os.path.isdir(name):
            for root, dirs, files in os.walk(name):
                for f in files:
                    if "__pycache__" in root:
                        continue
                    ff = os.path.join(root, f)
                    dest_list.append(ff)
        else:
            dest_list.append(name)

    with zipfile.ZipFile(out_zip, "w") as zip_fd:
        for f in dest_list:
            zip_fd.write(f)
        zip_fd.printdir()
        print("*** Total files: {}".format(len(zip_fd.namelist())))


def main():

    date_created = datetime.now().strftime('%Y%m%d')
    os_str = sys.platform.lower()
    if os_str.startswith('win'):
        os_str = 'win'
    zip_file = os.path.join(OUTDIR, "fbu_siiptool_{}_{}.zip"
                            .format(os_str, date_created))

    pypandoc.convert_file(os.path.join("docs", "user_manual.md"), "html",
                          outputfile="USER_MANUAL.html")

    if not os.path.exists(OUTDIR):
        os.mkdir(OUTDIR)
    create_archive(zip_file, BOM)


if __name__ == "__main__":
    sys.exit(main())
