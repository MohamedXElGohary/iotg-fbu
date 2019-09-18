#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

"""A stitching utility to replace code/data sub-regions in System BIOS image
"""


import os
import platform
import subprocess
import sys
import argparse
import shutil
import re
import glob
import uuid
from pathlib import Path


from cryptography.hazmat.primitives import hashes as hashes
from cryptography.hazmat.backends import default_backend

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.sub_region_descriptor import SubRegionDescriptor
from common.sub_region_image import generate_sub_region_image
from common.ifwi import IFWI_IMAGE
from common.firmware_volume import FirmwareDevice
from common.siip_constants import IP_OPTIONS
from common.tools_path import FMMT, GENFV, GENFFS, GENSEC, LZCOMPRESS, TOOLS_DIR
from common.tools_path import RSA_HELPER, FMMT_CFG
from common.banner import banner

__prog__ = "siip_stitch"
__version__ = "0.7.1"
TOOLNAME = "SIIP Stitching Tool"

banner(TOOLNAME, __version__)


if sys.version_info[0] < 3:
    raise Exception("Python 3 is the minimal version required")

GUID_FVADVANCED = uuid.UUID("B23E7388-9953-45C7-9201-0473DDE5487A")


def search_for_fv(inputfile, ipname):
    """Search for the firmware volume."""

    # use to find the name of the firmware to locate the firmware volume
    build_list = IP_OPTIONS.get(ipname)

    ui_name = build_list[0][1]

    print("\nFinding the Firmware Volume")
    fw_vol = None

    command = [FMMT, "-v", os.path.abspath(inputfile), ">", "tmp.fmmt.txt"]

    try:
        os.environ["PATH"] += os.pathsep + TOOLS_DIR
        subprocess.check_call(" ".join(command), shell=True, timeout=60)
    except subprocess.CalledProcessError as status:
        print("\nError using FMMT: {}".format(status))
        return 1, fw_vol
    except subprocess.TimeoutExpired:
        print(
            "\nFMMT timed out viewing {}! Check input file for correct format".format(inputfile)
        )

        if sys.platform == 'win32':
            result = os.system("taskkill /f /im FMMT.exe")
        elif sys.platform == 'linux':
            result = os.system("killall FMMT")
        if result == 0:
            return 1, fw_vol
        sys.exit("\nError Must kill process")

    # search FFS by name in firmware volumes
    fwvol_found = False

    with open("tmp.fmmt.txt", "r") as searchfile:
        for line in searchfile:
            match_fv = re.match(r"(^FV\d+) :", line)
            if match_fv:
                fwvol_found = True
                fw_vol = match_fv.groups()[0]
                continue
            if fwvol_found:
                match_name = re.match(r'File "(%s)"' % ui_name, line.lstrip())
                if match_name:
                    break
        else:
            fw_vol = None  # firmware volume was not found.
            print("\nCould not find file {} in {}".format(ui_name, inputfile))

    return 0, fw_vol


##############################################################################
#
# Gets the options needed to create commands to replace the ip
#
# The Each List represents a command that needs to be created to replace the
#  given IP
# The following list is for GenSec.exe
# 'ui' creates EFI_SECTION_USER_INTERFACE
# 'raw' creates EFI_SECTION_RAW
# None creaetes EFI_SECTION_ALL that does not require a section header
# 'guid' creates EFI_SECTION_GUID_DEFINED
# 'pe32' creates EFI_SECTION_PE32
# 'depex' creates EFI_SECTION_PEI_DEPEX
# 'cmprs' creates EFI_SECTION_COMPRESSION
#
# 'lzma' calls the LzmaCompress
#
# The following list is for GenFfs.exe
# 'free' creates EFI_FV_FILETYPE_FREEFORM
# 'gop' creates EFI_FV_FILETYPE_DRIVER
# 'peim' creates EFI_FV_FILETYPE_PEIM
##############################################################################


# gets the section type needed for gensec.exe
GENSEC_SECTION = {
    "ui": ["tmp.ui", "-s", "EFI_SECTION_USER_INTERFACE", "-n"],
    "raw": ["tmp.raw", "-s", "EFI_SECTION_RAW", "-c"],
    "guid": ["tmp.guid", "-s", "EFI_SECTION_GUID_DEFINED", "-g"],
    "pe32": ["tmp.pe32", "-s", "EFI_SECTION_PE32"],
    "depex": ["tmp.dpx", "-s", "EFI_SECTION_PEI_DEPEX"],
    "cmprs": ["tmp.cmps", "-s", "EFI_SECTION_COMPRESSION", "-c"],
}

# gets the firmware file system type needed for genFFs
FFS_FILETYPE = {
    "free": "EFI_FV_FILETYPE_FREEFORM",
    "gop": "EFI_FV_FILETYPE_DRIVER",
    "peim": "EFI_FV_FILETYPE_PEIM",
}


def guild_section(sec_type, guild, guid_attrib, inputfile):
    """ generates the GUID defined section """

    cmd = GENSEC_SECTION.get(sec_type)
    cmd += [guild, "-r", guid_attrib, inputfile]
    return cmd


def generate_section(inputfiles, align_sizes):
    """ generates the all section """

    cmd = ["tmp.all"]

    for index, file in enumerate(inputfiles):
        cmd += [file]
        if align_sizes != [None]:
            # the first input is None
            cmd += ["--sectionalign", align_sizes[index + 1]]
    return cmd


def create_gensec_cmd(cmd_options, inputfile):
    """Create genSec commands for the merge and replace of firmware section."""

    cmd = [GENSEC, "-o"]

    if cmd_options[0] == "guid":
        sec_type, guid, attrib = cmd_options
        cmd += guild_section(sec_type, guid, attrib, inputfile[0])
        # EFI_SECTION_RAW, EFI_SECTION_PE32, EFI_SECTION_COMPRESSION or
        # EFI_SECTION_USER_INTERFACE
    elif cmd_options[0] is not None:
        sec_type, option = cmd_options
        cmd += GENSEC_SECTION.get(sec_type)
        if option is not None:
            cmd += [option]
        if sec_type != "ui":
            cmd += [inputfile[0]]
    else:
        cmd += generate_section(inputfile, cmd_options)
    return cmd


def compress(compress_method, inputfile):
    """ compress the sections """

    cmd = [LZCOMPRESS, compress_method, "-o", "tmp.cmps", inputfile]
    return cmd


def create_ffs_cmd(filetype, guild, align, inputfile):
    """ generates the firmware volume according to file type"""

    fv_filetype = FFS_FILETYPE.get(filetype)
    cmd = [GENFFS, "-o", "tmp.ffs", "-t", fv_filetype, "-g",
           guild, "-i", inputfile]
    if align is not None:
        cmd += ["-a", align]
    return cmd


def replace_ip(outfile, fw_vol, ui_name, inputfile):
    """ replaces the give firmware value with the input file """

    cmd = [FMMT, "-r", inputfile, fw_vol, ui_name, "tmp.ffs", outfile]
    return cmd


def ip_inputfiles(filenames, ipname):
    """Create input files per IP"""

    inputfiles = [None, "tmp.raw", "tmp.ui", "tmp.all"]

    num_infiles = 1
    if ipname == "pse":
        inputfiles.extend(["tmp.cmps", "tmp.guid"])
    elif ipname in ["gop", "gfxpeim"]:
        inputfiles.remove("tmp.raw")
        inputfiles.insert(1, "tmp.pe32")
        if ipname == "gfxpeim":
            inputfiles.append("tmp.cmps")

    # add user given input files
    infiles = filenames[1:num_infiles + 1]
    inputfiles[1:1] = infiles

    return inputfiles, num_infiles


def create_commands(filenames, ipname, fwvol):
    """Create Commands for the merge and replace of firmware section."""

    inputfiles, num_replace_files = ip_inputfiles(filenames, ipname)
    build_list = IP_OPTIONS.get(ipname)

    # get the file name to be used to replace firmware volume
    ui_name = build_list[0][1]

    cmd_list = []

    for instr in build_list:
        if GENSEC_SECTION.get(instr[0]) or instr[0] is None:
            files = [inputfiles.pop(0)]
            if instr[0] is None:
                for _ in range(num_replace_files):
                    files += [inputfiles.pop(0)]
            cmd = create_gensec_cmd(instr, files)

        elif instr[0] == "lzma":
            cmd = compress(instr[1], inputfiles.pop(0))
        elif FFS_FILETYPE.get(instr[0]):
            filetype, guild, align = instr
            cmd = create_ffs_cmd(filetype, guild, align, inputfiles.pop(0))
        else:
            sys.exit("unexpected error from create_command function")
        cmd_list.append(cmd)

    cmd = replace_ip(filenames[len(filenames) - 1], fwvol, ui_name,
                     filenames[0])
    cmd_list.append(cmd)

    return cmd_list


def merge_and_replace(filename, guid_values, fwvol):
    """Perform merge and replace of section using different executables."""

    cmds = create_commands(filename, guid_values, fwvol)

    print("\nStarting merge and replacement of section")

    # Merging and Replacing
    for idx, command in enumerate(cmds):
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError as status:
            print("\nError executing {}".format(" ".join(command)))
            print("\nStatus Message: {}".format(status))
            return 1

    return 0


def cleanup():
    """Remove generated files from directory."""

    to_remove = [
        os.path.join(TOOLS_DIR, 'privkey.pem'),
    ]
    to_remove.extend(glob.glob('tmp.*', recursive=True))

    for f in to_remove:
        try:
            os.remove(f)
        except:
            pass


def file_not_exist(file):
    """Verify that file does not exist."""

    if os.path.isfile(file):
        raise argparse.ArgumentTypeError("{} exist!".format(file))
    return file


def check_key(file):
    """ Check if file exist, empty, or over max size"""

    if os.path.isfile(file):
        FIRSTLINE = "-----BEGIN RSA PRIVATE KEY-----"
        LASTLINE = "-----END RSA PRIVATE KEY-----"
        size = os.path.getsize(file)
        if size > 2000 or size == 0:
            raise argparse.ArgumentTypeError("size of {} is {} the key file size must be greater than 0 and less than 2k!".format(file,size))

        else:
            with open(file, "r") as key:
                 key_lines = key.readlines()
            if not ((FIRSTLINE in key_lines[0]) and (LASTLINE in key_lines[-1])):
                raise argparse.ArgumentTypeError("{} is not an RSA priviate key".format(file))
    else:
        raise argparse.ArgumentTypeError("{} does not exist".format(file))

    return file


def check_file_size(files):
    """ Check if file is empty or greater than IFWI/BIOS file"""

    bios_size = os.path.getsize(files[0])

    for file in files:
        filesize = os.path.getsize(file)
        if filesize != 0:
            if not (filesize <= bios_size):
                print("\n{} file is size {} file exceeds the size of the BIOS/IFWI file {}!".format(file, filesize, files[0]))
                return 1
        else:
            print("\n{} file is empty!".format(file))
            return 1

    return 0


def parse_cmdline():
    """ Parsing and validating input arguments."""

    visible_ip_list = list(IP_OPTIONS.keys())
    visible_ip_list.remove("obb_digest")

    epilog = "Supported Sub-Region Names: {}\n".format(visible_ip_list)
    parser = argparse.ArgumentParser(prog=__prog__,
                                     description=__doc__,
                                     epilog=epilog)

    parser.add_argument(
        "IFWI_IN",
        type=argparse.FileType("rb+"),
        help="Input BIOS Binary file(Ex: IFWI.bin) to be updated with the given input IP firmware",
    )
    parser.add_argument(
        "IPNAME_IN",
        type=argparse.FileType("rb"),
        help="Input IP firmware Binary file(Ex: PseFw.Bin to be replaced in the IFWI.bin",
    )
    parser.add_argument(
        "-ip",
        "--ipname",
        help="The name of the IP in the IFWI_IN file to be replaced. This is required.",
        metavar="ipname",
        required=True,
        choices=visible_ip_list,
    )
    parser.add_argument(
        "-k",
        "--private-key",
        type=check_key,
        help="Private RSA key in PEM format. Note: Key is required for stitching GOP features",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Shows the current version of the BIOS Stitching Tool",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    parser.add_argument(
        "-o",
        "--outputfile",
        dest="OUTPUT_FILE",
        type=file_not_exist,
        help="IFWI binary file with the IP replaced with the IPNAME_IN",
        metavar="FileName",
        default="BIOS_OUT.bin",
    )

    return parser


def stitch_and_update(ifwi_file, ip_name, file_list, out_file):

    # search for firmware volume
    status, fw_volume = search_for_fv(ifwi_file, ip_name)

    # Check for error in using FMMT.exe or if firmware volume was not found.
    if status == 1 or fw_volume is None:
        cleanup()
        if status == 0:
            print("\nError: No Firmware volume found")
        sys.exit(status)

    # firmware volume was found
    print("\nThe Firmware volume is {}\n".format(fw_volume))

    # adding the path name to the output file
    file_list.append(os.path.abspath(out_file))

    # Add firmware volume header and merge it in out_file
    status = merge_and_replace(file_list, ip_name, fw_volume)


def update_obb_digest(ifwi_file, digest_file):
    """Calculate OBB hash according to a predefined range"""

    ifwi = IFWI_IMAGE(ifwi_file)
    if not ifwi.is_ifwi_image():
        print("Bad IFWI image")
        exit(1)

    ifwi.parse()
    bios_start = ifwi.region_list[1][1]
    bios_limit = ifwi.region_list[1][2]

    print("Parsing BIOS ...")
    bios = FirmwareDevice(0, ifwi.data[bios_start:bios_limit+1])
    bios.ParseFd()

    # Extract FVs belongs to OBB
    obb_fv_idx = bios.get_fv_index_by_guid(GUID_FVADVANCED.bytes_le)
    if not (0 < obb_fv_idx < len(bios.FvList)):
        raise ValueError("Starting OBB FV is not found")

    print("OBB region starts from FV{}".format(obb_fv_idx))
    obb_offset = bios.FvList[obb_fv_idx].Offset
    obb_length = 0
    if bios.is_fsp_wrapper():
        # FVADVANCED + FVPOSTMEMORY + FSPS
        print("FSP Wrapper BIOS")
        obb_fv_end = obb_fv_idx + 3
    else:
        # FVADVANCED + FVPOSTMEMORY
        print("EDK2 BIOS")
        obb_fv_end = obb_fv_idx + 2
    for fv in bios.FvList[obb_fv_idx:obb_fv_end]:
        obb_length += len(fv.FvData)

    print("OBB offset: {:x} len {:x}".format(obb_offset, obb_length))

    # Hash it
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(bios.FdData[obb_offset:obb_offset+obb_length])
    result = digest.finalize()
    with open(digest_file, "wb") as hash_fd:
        hash_fd.write(result)

    return


def main():
    """Entry to script."""

    parser = parse_cmdline()
    args = parser.parse_args()

    for f in (FMMT, GENFV, GENFFS, GENSEC, LZCOMPRESS, RSA_HELPER, FMMT_CFG):
        if not os.path.exists(f):
            raise FileNotFoundError("Thirdparty tool not found ({})".format(f))

    # Use absolute path because GenSec does not like relative ones
    IFWI_file = Path(args.IFWI_IN.name).resolve()

    # If input IP file is a JSON file, convert it to binary as the real input file
    if args.IPNAME_IN.name.lower().endswith('.json'):
        print("Found JSON as input file. Converting it to binary ...\n")

        desc = SubRegionDescriptor()
        desc.parse_json_data(args.IPNAME_IN.name)

        # Currently only creates the first file
        generate_sub_region_image(desc.ffs_files[0], output_file="tmp.payload.bin")
        IPNAME_file = Path("tmp.payload.bin").resolve()
    else:
        IPNAME_file = Path(args.IPNAME_IN.name).resolve()

    filenames = [str(IFWI_file), str(IPNAME_file)]
    if args.ipname in ["gop", "gfxpeim", "vbt"]:
        if not args.private_key or not os.path.exists(args.private_key):
            print("\nMissing RSA key to stitch GOP/PEIM GFX/VBT from command line\n")
            parser.print_help()
            sys.exit(2)
        else:
            key_file = Path(args.private_key).resolve()
            filenames.append(key_file)

    # verify file is not empty or the IP files are not larger than the input filesvcd
    status = check_file_size(filenames)
    if status != 0:
        sys.exit(status)

    # Copy key file to the required name needed for the rsa_helper.py
    if args.private_key:
    #if key_file in filenames:
        shutil.copyfile(key_file, os.path.join(TOOLS_DIR, "privkey.pem"))
        filenames.remove(key_file)

    print("*** Replacing {} ...".format(args.ipname))
    stitch_and_update(args.IFWI_IN.name, args.ipname, filenames, args.OUTPUT_FILE)

    # Update OBB digest after stitching any data inside OBB region
    if args.ipname in ["vbt", "gfxpeim"]:
        ipname = "obb_digest"
        digest_file = "tmp.obb.hash.bin"

        update_obb_digest(args.OUTPUT_FILE, digest_file)

        filenames = [str(Path(f).resolve()) for f in [args.OUTPUT_FILE, digest_file]]

        print("*** Replacing {} ...".format(ipname))
        stitch_and_update(args.OUTPUT_FILE, ipname, filenames, args.OUTPUT_FILE)

    cleanup()


if __name__ == "__main__":
    main()
