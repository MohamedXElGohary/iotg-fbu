#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import sys
import os
import argparse
import subprocess

import SubRegionDescriptor as Srd
import SubRegionImage as Sri

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

#
# Globals for help information
#
__prog__ = "GenerateSubRegionCapsule"
__version__ = "0.6.1"
__copyright__ = "Copyright (c) 2019, Intel Corporation. All rights reserved."
__description__ = "Generate a sub region capsule.\n"


def create_arg_parser():
    def convert_arg_line_to_args(arg_line):
        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg

    my_parser = argparse.ArgumentParser(
        prog=__prog__,
        description=__description__ + __copyright__,
        conflict_handler="resolve",
        fromfile_prefix_chars="@",
    )
    my_parser.convert_arg_line_to_args = convert_arg_line_to_args
    my_parser.add_argument(
        "InputFile", help="Input JSON sub region descriptor filename."
    )
    my_parser.add_argument(
        "-o", "--output", dest="OutputCapsuleFile", help="Output capsule filename."
    )
    my_parser.add_argument(
        "-s",
        "--signer-private-cert",
        dest="OpenSslSignerPrivateCertFile",
        help="OpenSSL signer private certificate filename.",
    )
    my_parser.add_argument(
        "-p",
        "--other-public-cert",
        dest="OpenSslOtherPublicCertFile",
        help="OpenSSL other public certificate filename.",
    )
    my_parser.add_argument(
        "-t",
        "--trusted-public-cert",
        dest="OpenSslTrustedPublicCertFile",
        help="OpenSSL trusted public certificate filename.",
    )
    my_parser.add_argument(
        "--signing-tool-path",
        dest="SigningToolPath",
        help="Path to signtool or OpenSSL tool. "
        " Optional if path to tools are already in PATH.",
    )
    return my_parser


if __name__ == "__main__":
    parser = create_arg_parser()
    args = parser.parse_args()

    SubRegionFvFile = "./SubRegionFv.fv"
    SubRegionImageFile = "./SubRegionImage.bin"
    SubRegionDesc = Srd.SubRegionDescriptor()
    SubRegionDesc.parse_json_data(args.InputFile)
    Sri.generate_sub_region_fv(SubRegionImageFile, SubRegionDesc, SubRegionFvFile)

    # TODO: until we refactor this code, both Generate*.py should be located together
    dir_name = os.path.dirname(os.path.abspath(__file__))

    GenCapCmd = ["python", os.path.join(dir_name, "GenerateCapsule.py")]
    GenCapCmd += ["--encode"]
    GenCapCmd += ["--guid", SubRegionDesc.sFmpGuid]
    GenCapCmd += ["--fw-version", str(SubRegionDesc.Version)]
    GenCapCmd += ["--lsv", "0"]
    GenCapCmd += ["--capflag", "PersistAcrossReset"]
    GenCapCmd += ["--capflag", "InitiateReset"]
    GenCapCmd += ["-o", args.OutputCapsuleFile]
    GenCapCmd += ["--signer-private-cert", args.OpenSslSignerPrivateCertFile]
    GenCapCmd += ["--other-public-cert", args.OpenSslOtherPublicCertFile]
    GenCapCmd += ["--trusted-public-cert", args.OpenSslTrustedPublicCertFile]
    GenCapCmd += ["-v"]
    if args.SigningToolPath is not None:
        GenCapCmd += ["--signing-tool-path", args.SigningToolPath]
    GenCapCmd += [SubRegionFvFile]

    PopenObject = subprocess.Popen(
        " ".join(GenCapCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    while PopenObject.returncode is None:
        out, err = PopenObject.communicate()
        print("Error messages  :\n%s" % err.decode("utf-8"))
        print("Output messages :\n%s" % out.decode("utf-8"))

    sys.exit(PopenObject.returncode)
