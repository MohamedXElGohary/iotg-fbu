#!/usr/bin/env python

"""Script to support CI/CD automation"""

import sys
import os
import subprocess
import platform
import argparse

TARGETS = [
    "flashtool",
    "siiptool",
]

def create_pkg(targets):

    for idx, target in enumerate(targets):
        print("\n\n*** [{}] Creating release package for target {}".format(idx, target))
        if not os.path.isdir(target):
            raise Exception("Directory \"{}\" not found".format(target))
        subprocess.check_call(["python", "release.py"], cwd=os.path.join(".", target))


def main():

    ap = argparse.ArgumentParser(description=__doc__)

    ap.add_argument("targets",
                    metavar="TARGET",
                    nargs="*",
                    type=str,
                    default=TARGETS,
                    help="Give a tool name to create release package. Create"
                         " for all tools if not given"
                    )

    args = ap.parse_args()

    print("Targets:{}  OS:{}  Python:{}".format(args.targets,
                                                platform.system(),
                                                platform.python_version()))

    create_pkg(args.targets)


if __name__ == "__main__":
    sys.exit(main())
