## @file
# Sub Region Image functions
#
# Functions used to generate images from Sub Region descriptors and wrap them in Firmware Volumes
#
# This tool is intended to be used to generate UEFI Capsules to update the
# system firmware or device firmware for integrated devices.
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
# This program and the accompanying materials
# are licensed and made available under the terms and conditions of the BSD License
# which accompanies this distribution.  The full text of the license may be found at
# http://opensource.org/licenses/bsd-license.php
#
# THE PROGRAM IS DISTRIBUTED UNDER THE BSD LICENSE ON AN "AS IS" BASIS,
# WITHOUT WARRANTIES OR REPRESENTATIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED.
#

import struct
import sys
import os
import shutil
import subprocess
import SubRegionDescriptor as srd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SIIPSupport import ToolsLoc as tdir

DefaultWorkspace = "./temp/"

SectionNameLookupTable = {
    "EBA4A247-42C0-4C11-A167-A4058BC9D423": "IntelOseFw",
    "12E29FB4-AA56-4172-B34E-DD5F4B440AA9": "IntelTsnMacAddr",
    "4FB7994D-D878-4BD1-8FE0-777B732D0A31": "IntelOseTsnMacConfig"
}


def CreateBufferFromDataField (DataField):
    Buffer = None
    if DataField.Type == srd.DataTypes.FILE:
        with open (DataField.Value, 'rb') as DataFile:
            Buffer = DataFile.read()

    if DataField.Type == srd.DataTypes.STRING:
        if DataField.Value == '_STDIN_':
            Buffer = sys.stdin.readline()
        else:
            Fmt = "{}s".format(DataField.ByteSize)
            print(Fmt)
            Buffer = struct.pack(Fmt, bytes(DataField.sValue, 'utf-8'))

    if DataField.Type in [srd.DataTypes.DECIMAL, srd.DataTypes.HEXADECIMAL]:
        if DataField.ByteSize == 1:
            Buffer = struct.pack("<B", DataField.dValue)
        elif DataField.ByteSize == 2:
            Buffer = struct.pack("<H", DataField.dValue)
        elif DataField.ByteSize == 4:
            Buffer = struct.pack("<I", DataField.dValue)
        elif DataField.ByteSize == 8:
            Buffer = struct.pack("<Q", DataField.dValue)
        else:
            fmt = "<{0}B".format(DataField.ByteSize)
            Buffer = struct.pack(fmt, bytearray.fromhex(format(DataField.dValue, 'x')))
    return Buffer


def GenerateSubRegionImage (FfsFile, OutputFile="./output.bin"):
    with open (OutputFile, "wb") as OutBuffer:
        for DataField in FfsFile.Data:
            LineBuffer = CreateBufferFromDataField (DataField)
            OutBuffer.write (LineBuffer)


def LookupSectionName (FfsGuid):
    try:
        return SectionNameLookupTable[FfsGuid]
    except KeyError:
        return None


def CreateGenSecCommand (FfsFile, ImageFile=None, Index=0, OutputFile="SubRegionSec.sec", Name=None):
    CompressionScheme = None
    GenSecCmd = ["GenSec"]
    GenSecCmd += ["-o", OutputFile]
    if Name is not None:
        SectionType = "EFI_SECTION_USER_INTERFACE"
    elif FfsFile.Compression is True:
        SectionType = "EFI_SECTION_COMPRESSION"
        CompressionScheme = "PI_STD"
    else:
        SectionType = "EFI_SECTION_RAW"
        CompressionScheme = "PI_NONE"
    GenSecCmd += ["-s", SectionType]
    if CompressionScheme is not None:
        GenSecCmd += ["-c", CompressionScheme]
    if ImageFile is not None:
        GenSecCmd += [ImageFile]
    if Name is not None:
        GenSecCmd += ["-n", Name]
    return GenSecCmd

def CreateGenFfsCommand (FfsFile, SectionFile, OutputFile="SubRegionFfs.ffs"):
    GenFfsCmd = ["GenFfs"]
    GenFfsCmd += ["-o", OutputFile]
    GenFfsCmd += ["-t", "EFI_FV_FILETYPE_FREEFORM"]
    GenFfsCmd += ["-g", FfsFile.sFfsGuid]
    GenFfsCmd += ["-i", SectionFile]
    return GenFfsCmd

def CreateGenFvCommand (SubRegionDesc, OutputFvFile, FfsFiles):
    GenFvCmd  = ["GenFv"]
    GenFvCmd += ["-o", OutputFvFile]
    GenFvCmd += ["-b", "0x10000"]
    GenFvCmd += ["-f", ' -f '.join(FfsFiles)]
    GenFvCmd += ["-g", "8C8CE578-8A3D-4F1C-9935-896185C32DD3"]  # gEfiFirmwareFileSystem2Guid
    GenFvCmd += ["--FvNameGuid", SubRegionDesc.sFvGuid]
    return GenFvCmd

def CreateCleanWorkspace (Path):
    if os.path.isdir(Path):
        shutil.rmtree(Path)
    os.mkdir(Path)

def GenerateSubRegionFv (ImageFile, SubRegionDesc, OutputFvFile="./SubRegion.FV"):
    SubRegionImageFile = "SubRegionImage.bin"
    WorkspacePath = DefaultWorkspace
    CreateCleanWorkspace(WorkspacePath)

    if os.name == 'nt':
        BinPath = tdir.TOOLSWINDIR
    else:
        print ("Only support Windows OS")
        exit (-1)
    os.environ["PATH"] += os.pathsep + BinPath

    FvFfsFileList = []
    for FileIndex, FfsFile in enumerate(SubRegionDesc.FfsFiles):
        GenerateSubRegionImage (FfsFile, SubRegionImageFile)
        SecFilePath = "{0}SubRegionSec{1}.sec".format(WorkspacePath, FileIndex)
        GenSecCmd = CreateGenSecCommand (FfsFile, ImageFile=SubRegionImageFile, Index=FileIndex, OutputFile=SecFilePath)
        PopenObject = subprocess.Popen (' '.join(GenSecCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while PopenObject.returncode == None:
            PopenObject.wait ()
        if PopenObject.returncode != 0:
            print ("Error generating Section")
            exit(-1)

        SecUiName = LookupSectionName(FfsFile.FfsGuid)
        if SecUiName is not None:
            SecUiFile = "{0}SubRegionSecUi{1}.sec".format(WorkspacePath, FileIndex)
            GenSecUiCmd = CreateGenSecCommand (FfsFile, Name=SecUiName, OutputFile=SecUiFile)
            PopenObject = subprocess.Popen (' '.join (GenSecUiCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            while PopenObject.returncode == None:
                PopenObject.wait ()
            if PopenObject.returncode != 0:
                print ("Error generating UI Section")
                exit(-1)

            ## Cat Image Section with UI Section
            with open (SecFilePath, "ab") as SecFileHandle, open (SecUiFile, "rb") as SecUiFileHandle:
                SecFileHandle.write (SecUiFileHandle.read ())

        FfsFilePath = "{0}SubRegionFfs{1}.ffs".format(WorkspacePath, FileIndex)
        GenFfsCmd = CreateGenFfsCommand (FfsFile, SecFilePath, OutputFile=FfsFilePath)
        PopenObject = subprocess.Popen (' '.join (GenFfsCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while PopenObject.returncode == None:
            PopenObject.wait ()
        if PopenObject.returncode != 0:
            print ("Error generating FFS File")
            exit(-1)
        FvFfsFileList.append(FfsFilePath)

    GenFvCmd = CreateGenFvCommand (SubRegionDesc, OutputFvFile, FvFfsFileList)
    PopenObject = subprocess.Popen (' '.join (GenFvCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    print(' '.join(GenFvCmd))
    while PopenObject.returncode == None:
        PopenObject.wait ()
    if PopenObject.returncode != 0:
        print ("Error generating FV File")
        exit(-1)


if __name__ == "__main__":
    SubRegionFvFile = "./SubRegionFv.fv"
    SubRegionImageFile = "./SubRegionData.bin"
    SubRegionDesc = srd.SubRegionDescriptor ()
    SubRegionDesc.ParseJsonData ("./Tests/Collateral/GoodSubRegDescExample.json")
    GenerateSubRegionImage (SubRegionDesc, SubRegionImageFile)
    GenerateSubRegionFv (SubRegionImageFile, SubRegionDesc, SubRegionFvFile)
