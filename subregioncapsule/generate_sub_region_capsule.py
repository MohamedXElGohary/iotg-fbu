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

import sub_region_descriptor as Srd
import sub_region_image as Sri

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

    sub_region_fv_file = "./SubRegionFv.fv"
    sub_region_image_file = "./SubRegionImage.bin"
    sub_region_desc = Srd.SubRegionDescriptor()
    sub_region_desc.parse_json_data(args.InputFile)
    Sri.generate_sub_region_fv(sub_region_image_file, sub_region_desc, sub_region_fv_file)

    # TODO: until we refactor this code, both Generate*.py should be located together
    dir_name = os.path.dirname(os.path.abspath(__file__))

    gen_cap_cmd = ["python", os.path.join(dir_name, "GenerateCapsule.py")]
    gen_cap_cmd += ["--encode"]
    gen_cap_cmd += ["--guid", sub_region_desc.s_fmp_guid]
    gen_cap_cmd += ["--fw-version", str(sub_region_desc.version)]
    gen_cap_cmd += ["--lsv", "0"]
    gen_cap_cmd += ["--capflag", "PersistAcrossReset"]
    gen_cap_cmd += ["--capflag", "InitiateReset"]
    gen_cap_cmd += ["-o", args.OutputCapsuleFile]
    gen_cap_cmd += ["--signer-private-cert", args.OpenSslSignerPrivateCertFile]
    gen_cap_cmd += ["--other-public-cert", args.OpenSslOtherPublicCertFile]
    gen_cap_cmd += ["--trusted-public-cert", args.OpenSslTrustedPublicCertFile]
    gen_cap_cmd += ["-v"]
    if args.SigningToolPath is not None:
        gen_cap_cmd += ["--signing-tool-path", args.SigningToolPath]
    gen_cap_cmd += [sub_region_fv_file]

    popen_object = subprocess.Popen(
        " ".join(gen_cap_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    while popen_object.returncode is None:
        out, err = popen_object.communicate()
        print("Error messages  :\n%s" % err.decode("utf-8"))
        print("Output messages :\n%s" % out.decode("utf-8"))

    sys.exit(popen_object.returncode)
