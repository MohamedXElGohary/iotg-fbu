#!/usr/bin/env python3

"""Release script to package required files"""

import os
import sys
import zipfile
from datetime import datetime

import pypandoc

OUTDIR = "dist"

BOM = [
    "flashtool",
    "flashtool.py",
    "examples",
    "README.md",
    "docs",
    "LICENSE",
    "setup.py",
    "README.docx",
    "MANIFEST.in"
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
    zip_file = os.path.join(OUTDIR, "fbu_flashtool_{}.zip".format(date_created))

    pypandoc.convert_file("README.md", "docx", outputfile="README.docx")

    if not os.path.exists(OUTDIR):
        os.mkdir(OUTDIR)
    create_archive(zip_file, BOM)


if __name__ == "__main__":
    sys.exit(main())
