## @file
# Descriptor definition for BIOS Sub Regions
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

import json
import uuid

gFmpCapsuleTsnMacAddrFileGuid        = uuid.UUID ('6fee88ff-49ed-48f1-b77b-ead15771abe7')
gFmpCapsuleOseTsnMacConfigFileGuid   = uuid.UUID ('90c9751d-fa74-4ea6-8c4b-f44d2be8cd4b')
gFmpCapsuleOseFwFileGuid             = uuid.UUID ('aad1e926-23b8-4c3a-8b44-0c9a031664f2')
gFmpCapsuleTccArbFileGuid            = uuid.UUID ('a7ee90b1-fb4a-4478-b868-367ee9ec97e2')
gFmpCapsuleOobManageabilityFileGuid  = uuid.UUID ('bf2ae378-01e0-4605-9e3b-2ee2fc7339de')


class EnumDataTypes (set):
    def __getattr__ (self, name):
        if name in self:
            return name
        raise AttributeError


DataTypes = EnumDataTypes (["DECIMAL", "HEXADECIMAL", "STRING", "FILE"])


class UnknownSubRegionError (Exception):
    def __init__ (self):
        pass

    def __str__ (self):
        return (repr ("Sub Region is unknown."))


class SubRegionDescSyntaxError (Exception):
    def __init__ (self, key):
        self.key = key
        pass

    def __str__ (self):
        return (repr ("Sub Region descriptor invalid syntax. Problem with {} field in JSON file.".format(self.key)))


class SubRegionFfsFile (object):
    def __init__ (self, FfsGuid, Compression, Data):
        self.sFfsGuid = FfsGuid
        try:
            self.FfsGuid = uuid.UUID (self.sFfsGuid)
        except ValueError:
            raise SubRegionDescSyntaxError ("FfsGuid")
        self.FfsGuid = FfsGuid
        self.Compression = Compression
        self.Data = []
        for DataField in Data:
            self.Data.append (SubRegionDataField (DataField))


class SubRegionDataField (object):
    def __init__ (self, datafield):
        self.Name = datafield[0]
        self.Type = datafield[1]
        self.ByteSize = datafield[2]
        self.Value = datafield[3]
        if self.Type == DataTypes.DECIMAL:
            self.dValue = datafield[3]
            self.sValue = str (datafield[3])
        elif self.Type == DataTypes.HEXADECIMAL:
            self.dValue = int (datafield[3], 16)
            self.sValue = str (datafield[3])
        else:
            self.dValue = None
            self.sValue = str (datafield[3])


class SubRegionDescriptor (object):
    ValidGuidList = [gFmpCapsuleTsnMacAddrFileGuid,
                     gFmpCapsuleOseTsnMacConfigFileGuid,
                     gFmpCapsuleOseFwFileGuid,
                     gFmpCapsuleTccArbFileGuid,
                     gFmpCapsuleOobManageabilityFileGuid]

    def __init__ (self):
        self.sFmpGuid = None
        self.FmpGuid = None
        self.Version = None
        self.Fv = None
        self.sFvGuid = None
        self.FvGuid = None
        self.FfsFiles = []

    def ParseJsonData (self, JsonFile):
        with open (JsonFile, 'r') as file_handle:
            DescBuffer = json.loads (file_handle.read ())
            try:
                self.sFmpGuid = DescBuffer["FmpGuid"]
                try:
                    self.FmpGuid = uuid.UUID (self.sFmpGuid)
                    if not self.IsKnownGuid (self.FmpGuid):
                        raise UnknownSubRegionError
                except ValueError:
                    raise SubRegionDescSyntaxError ("FmpGuid")
                self.Version = DescBuffer["Version"]

                self.Fv = DescBuffer["FV"]
                self.sFvGuid = self.Fv["FvGuid"]
                try:
                    self.FvGuid = uuid.UUID (self.sFvGuid)
                except ValueError:
                    raise SubRegionDescSyntaxError ("FvGuid")
                except TypeError:
                    raise SubRegionDescSyntaxError ("FvGuid")

                FfsFileList = self.Fv["FfsFiles"]
                for FfsFile in FfsFileList:
                    FfsGuid = FfsFile["FileGuid"]
                    Compression = FfsFile["Compression"]
                    Data = FfsFile["Data"]
                    self.FfsFiles.append(SubRegionFfsFile (FfsGuid, Compression, Data))

                for FfsFile in self.FfsFiles:
                    if not self.CheckFileGood (FfsFile):
                        raise SubRegionDescSyntaxError ("FfsFile")
            except (KeyError, IndexError) as e:
                raise SubRegionDescSyntaxError (str (e))

    def CheckFileGood (self, FfsFile):
        ValidFile = True

        if FfsFile.Compression not in [False, True]:
            ValidFile = False

        for DataField in FfsFile.Data:
            if type (DataField.Name) not in [str, unicode]:
                ValidFile = False
            if DataField.Type not in DataTypes:
                ValidFile = False
            if DataField.ByteSize <= 0:
                ValidFile = False
            if type (DataField.Value) not in [str, int, unicode]:
                ValidFile = False

        return ValidFile

    def IsKnownGuid (self, Guid):
        return Guid in self.ValidGuidList
