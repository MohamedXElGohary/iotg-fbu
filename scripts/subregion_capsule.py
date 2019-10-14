#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

"""A capsule image utility to generate UEFI sub-region capsule images
"""


import sys
import os
import argparse
import subprocess
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import common.sub_region_descriptor as srd
import common.sub_region_image as sri
from common.tools_path import EDK2_CAPSULE_TOOL
from common.siip_constants import IP_OPTIONS
from common.banner import banner
import common.logging as logging

logger = logging.getLogger("siip_sign")

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

#
# Globals for help information
#
__prog__ = "subregion_capsule"
__version__ = "0.7.1"

TOOLNAME = "Sub-Region Capsule Tool"

banner(TOOLNAME, __version__)

# Translate IP_OPTIONS dict into a GUID-to-NAME lookup dict
section_name_lookup_table = {
    option[-1][1]: option[0][1] for option in IP_OPTIONS.values()}


def cleanup():
    to_remove = glob.glob("tmp.*")
    to_remove.extend(glob.glob("SubRegionFv.*"))
    to_remove.append("SubRegionImage.bin")

    for f in to_remove:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def generate_sub_region_fv(
        image_file, sub_region_descriptor, output_fv_file=os.path.join(os.path.curdir, "SubRegion.FV")
):
    sub_region_image = "SubRegionImage.bin"

    fv_ffs_file_list = []
    for file_index, ffs_file in enumerate(sub_region_descriptor.ffs_files):
        sri.generate_sub_region_image(ffs_file, sub_region_image)
        sec_file_path = "tmp.{}.sec".format(file_index)
        gen_sec_cmd = sri.create_gen_sec_command(
            ffs_file,
            image_file=sub_region_image,
            index=file_index,
            output_file=sec_file_path,
        )
        p_open_object = subprocess.Popen(
            " ".join(gen_sec_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while p_open_object.returncode is None:
            p_open_object.wait()
        if p_open_object.returncode != 0:
            logger.critical("Error generating Section")
            exit(-1)

        sec_ui_name = section_name_lookup_table.get(ffs_file.ffs_guid, None)
        if sec_ui_name is not None:
            sec_ui_file = "tmp.ui.{}.sec".format(file_index)
            gen_sec_ui_cmd = sri.create_gen_sec_command(
                ffs_file, name=sec_ui_name, output_file=sec_ui_file
            )
            p_open_object = subprocess.Popen(
                " ".join(gen_sec_ui_cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            while p_open_object.returncode is None:
                p_open_object.wait()
            if p_open_object.returncode != 0:
                logger.critical("Error generating UI Section")
                exit(-1)

            # Cat Image Section with UI Section
            with open(sec_file_path, "ab") as sec_file_handle, open(
                    sec_ui_file, "rb"
            ) as sec_ui_file_handle:
                sec_file_handle.write(sec_ui_file_handle.read())

        ffs_file_path = "tmp.{}.ffs".format(file_index)
        gen_ffs_cmd = sri.create_gen_ffs_command(
            ffs_file, sec_file_path, output_file=ffs_file_path
        )
        p_open_object = subprocess.Popen(
            " ".join(gen_ffs_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while p_open_object.returncode is None:
            p_open_object.wait()
        if p_open_object.returncode != 0:
            logger.critical("Error generating FFS File")
            exit(-1)
        fv_ffs_file_list.append(ffs_file_path)

    gen_fv_cmd = sri.create_gen_fv_command(sub_region_descriptor,
                                           output_fv_file, fv_ffs_file_list)
    p_open_object = subprocess.Popen(
        " ".join(gen_fv_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True
    )
    logger.debug(" ".join(gen_fv_cmd))
    while p_open_object.returncode is None:
        p_open_object.wait()
    if p_open_object.returncode != 0:
        logger.critical("Error generating FV File")
        exit(-1)


def create_arg_parser():
    def convert_arg_line_to_args(arg_line):
        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg

    my_parser = argparse.ArgumentParser(
        prog=__prog__,
        description=__doc__,
        conflict_handler="resolve",
        fromfile_prefix_chars="@",
    )
    my_parser.convert_arg_line_to_args = convert_arg_line_to_args
    my_parser.add_argument(
        "InputFile", help="Input JSON sub region descriptor filename."
    )
    my_parser.add_argument(
        "-o", "--output", dest="OutputCapsuleFile",
        help="Output capsule filename."
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

    sub_region_fv_file = os.path.join(os.path.curdir, "SubRegionFv.fv")
    sub_region_image_file = os.path.join(os.path.curdir, "SubRegionImage.bin")
    sub_region_desc = srd.SubRegionDescriptor()
    sub_region_desc.parse_json_data(args.InputFile)
    generate_sub_region_fv(sub_region_image_file, sub_region_desc,
                           sub_region_fv_file)

    gen_cap_cmd = ["python", EDK2_CAPSULE_TOOL]
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
        " ".join(gen_cap_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True
    )
    while popen_object.returncode is None:
        out, err = popen_object.communicate()
        logger.warning("Error messages  :\n%s" % err.decode("utf-8"))
        logger.warning("Output messages :\n%s" % out.decode("utf-8"))

    cleanup()

    sys.exit(popen_object.returncode)
