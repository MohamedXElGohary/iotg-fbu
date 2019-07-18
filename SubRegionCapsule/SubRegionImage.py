# @file
# Sub Region Image functions
#
# Functions used to generate images from Sub Region descriptors and wrap them
# in Firmware Volumes
#
# This tool is intended to be used to generate UEFI Capsules to update the
# system firmware or device firmware for integrated devices.
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# This program and the accompanying materials
# are licensed and made available under the terms and conditions of the BSD
# License which accompanies this distribution.  The full text of the license
# may be found at http://opensource.org/licenses/bsd-license.php
#
# THE PROGRAM IS DISTRIBUTED UNDER THE BSD LICENSE ON AN "AS IS" BASIS,
# WITHOUT WARRANTIES OR REPRESENTATIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED.
#

import struct
import sys
import os
import shutil
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import SubRegionDescriptor as Srd

# TODO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from siip_support import ToolsLoc as TDir  # noqa: E402

DefaultWorkspace = "./temp/"

SectionNameLookupTable = {
    "EBA4A247-42C0-4C11-A167-A4058BC9D423": "IntelOseFw",
    "12E29FB4-AA56-4172-B34E-DD5F4B440AA9": "IntelTsnMacAddr",
    "4FB7994D-D878-4BD1-8FE0-777B732D0A31": "IntelOseTsnMacConfig",
}


def create_buffer_from_data_field(data_field):
    buffer = None
    if data_field.Type == Srd.DataTypes.FILE:
        with open(data_field.Value, "rb") as DataFile:
            buffer = DataFile.read()

    if data_field.Type == Srd.DataTypes.STRING:
        fmt = "{}s".format(data_field.ByteSize)
        if data_field.Value == "_STDIN_":
            buffer = struct.pack(fmt, bytes(sys.stdin.readline(), "utf-8"))
        else:
            buffer = struct.pack(fmt, bytes(data_field.sValue, "utf-8"))

    if data_field.Type in [Srd.DataTypes.DECIMAL, Srd.DataTypes.HEXADECIMAL]:
        if data_field.ByteSize == 1:
            buffer = struct.pack("<B", data_field.dValue)
        elif data_field.ByteSize == 2:
            buffer = struct.pack("<H", data_field.dValue)
        elif data_field.ByteSize == 4:
            buffer = struct.pack("<I", data_field.dValue)
        elif data_field.ByteSize == 8:
            buffer = struct.pack("<Q", data_field.dValue)
        else:
            fmt = "<{0}B".format(data_field.ByteSize)
            buffer = struct.pack(fmt, bytearray.fromhex(format(data_field.dValue, "x")))
    return buffer


def generate_sub_region_image(ffs_file, output_file="./output.bin"):
    with open(output_file, "wb") as OutBuffer:
        for DataField in ffs_file.Data:
            line_buffer = create_buffer_from_data_field(DataField)
            OutBuffer.write(line_buffer)


def lookup_section_name(ffs_guid):
    try:
        return SectionNameLookupTable[ffs_guid]
    except KeyError:
        return None


def create_gen_sec_command(
    ffs_file, image_file=None, index=0, output_file="SubRegionSec.sec", name=None
):
    CompressionScheme = None
    GenSecCmd = ["GenSec"]
    GenSecCmd += ["-o", output_file]
    if name is not None:
        SectionType = "EFI_SECTION_USER_INTERFACE"
    elif ffs_file.Compression is True:
        SectionType = "EFI_SECTION_COMPRESSION"
        CompressionScheme = "PI_STD"
    else:
        SectionType = "EFI_SECTION_RAW"
        CompressionScheme = "PI_NONE"
    GenSecCmd += ["-s", SectionType]
    if CompressionScheme is not None:
        GenSecCmd += ["-c", CompressionScheme]
    if image_file is not None:
        GenSecCmd += [image_file]
    if name is not None:
        GenSecCmd += ["-n", name]
    return GenSecCmd


def create_gen_ffs_command(ffs_file, section_file, output_file="SubRegionFfs.ffs"):
    GenFfsCmd = ["GenFfs"]
    GenFfsCmd += ["-o", output_file]
    GenFfsCmd += ["-t", "EFI_FV_FILETYPE_FREEFORM"]
    GenFfsCmd += ["-g", ffs_file.sFfsGuid]
    GenFfsCmd += ["-i", section_file]
    return GenFfsCmd


def create_gen_fv_command(sub_region_desc, output_fv_file, ffs_files):
    GenFvCmd = ["GenFv"]
    GenFvCmd += ["-o", output_fv_file]
    GenFvCmd += ["-b", "0x10000"]
    GenFvCmd += ["-f", " -f ".join(ffs_files)]
    GenFvCmd += [
        "-g",
        "8C8CE578-8A3D-4F1C-9935-896185C32DD3",
    ]  # gEfiFirmwareFileSystem2Guid
    GenFvCmd += ["--FvNameGuid", sub_region_desc.sFvGuid]
    return GenFvCmd


def create_clean_workspace(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)


def generate_sub_region_fv(
    image_file, sub_region_desc, output_fv_file="./SubRegion.FV"
):
    sub_region_image_file = "SubRegionImage.bin"
    WorkspacePath = DefaultWorkspace
    create_clean_workspace(WorkspacePath)

    if os.name == "nt":
        BinPath = TDir.TOOLSWINDIR
    else:
        print("Only support Windows OS")
        exit(-1)
    os.environ["PATH"] += os.pathsep + BinPath

    FvFfsFileList = []
    for FileIndex, FfsFile in enumerate(sub_region_desc.FfsFiles):
        generate_sub_region_image(FfsFile, sub_region_image_file)
        SecFilePath = "{0}SubRegionSec{1}.sec".format(WorkspacePath, FileIndex)
        GenSecCmd = create_gen_sec_command(
            FfsFile,
            image_file=sub_region_image_file,
            index=FileIndex,
            output_file=SecFilePath,
        )
        PopenObject = subprocess.Popen(
            " ".join(GenSecCmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while PopenObject.returncode is None:
            PopenObject.wait()
        if PopenObject.returncode != 0:
            print("Error generating Section")
            exit(-1)

        SecUiName = lookup_section_name(FfsFile.FfsGuid)
        if SecUiName is not None:
            SecUiFile = "{0}SubRegionSecUi{1}.sec".format(WorkspacePath, FileIndex)
            GenSecUiCmd = create_gen_sec_command(
                FfsFile, name=SecUiName, output_file=SecUiFile
            )
            PopenObject = subprocess.Popen(
                " ".join(GenSecUiCmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            while PopenObject.returncode is None:
                PopenObject.wait()
            if PopenObject.returncode != 0:
                print("Error generating UI Section")
                exit(-1)

            # Cat Image Section with UI Section
            with open(SecFilePath, "ab") as SecFileHandle, open(
                SecUiFile, "rb"
            ) as SecUiFileHandle:
                SecFileHandle.write(SecUiFileHandle.read())

        FfsFilePath = "{0}SubRegionFfs{1}.ffs".format(WorkspacePath, FileIndex)
        GenFfsCmd = create_gen_ffs_command(
            FfsFile, SecFilePath, output_file=FfsFilePath
        )
        PopenObject = subprocess.Popen(
            " ".join(GenFfsCmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while PopenObject.returncode is None:
            PopenObject.wait()
        if PopenObject.returncode != 0:
            print("Error generating FFS File")
            exit(-1)
        FvFfsFileList.append(FfsFilePath)

    GenFvCmd = create_gen_fv_command(sub_region_desc, output_fv_file, FvFfsFileList)
    PopenObject = subprocess.Popen(
        " ".join(GenFvCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    print(" ".join(GenFvCmd))
    while PopenObject.returncode is None:
        PopenObject.wait()
    if PopenObject.returncode != 0:
        print("Error generating FV File")
        exit(-1)


if __name__ == "__main__":
    SubRegionFvFile = "./SubRegionFv.fv"
    SubRegionImageFile = "./SubRegionData.bin"
    SubRegionDesc = Srd.SubRegionDescriptor()
    SubRegionDesc.parse_json_data("./Tests/Collateral/GoodSubRegDescExample.json")
    generate_sub_region_image(SubRegionDesc, SubRegionImageFile)
    generate_sub_region_fv(SubRegionImageFile, SubRegionDesc, SubRegionFvFile)
