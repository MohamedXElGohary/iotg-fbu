# @file
# Descriptor definition for BIOS Sub Regions
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

import json
import uuid

gFmpCapsuleTsnMacAddressFileGuid = uuid.UUID("6fee88ff-49ed-48f1-b77b-ead15771abe7")
gFmpCapsuleOseTsnMacConfigFileGuid = uuid.UUID("90c9751d-fa74-4ea6-8c4b-f44d2be8cd4b")
gFmpCapsuleOseFwFileGuid = uuid.UUID("aad1e926-23b8-4c3a-8b44-0c9a031664f2")
gFmpCapsuleTccArbFileGuid = uuid.UUID("a7ee90b1-fb4a-4478-b868-367ee9ec97e2")
gFmpCapsuleOobManageabilityFileGuid = uuid.UUID("bf2ae378-01e0-4605-9e3b-2ee2fc7339de")


class EnumDataTypes(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


DataTypes = EnumDataTypes(["DECIMAL", "HEXADECIMAL", "STRING", "FILE"])


class UnknownSubRegionError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return repr("Sub Region is unknown.")


class SubRegionDescSyntaxError(Exception):
    def __init__(self, key):
        self.key = key
        pass

    def __str__(self):
        return repr(
            "Sub Region descriptor invalid syntax. Problem with {} field in "
            "JSON file.".format(self.key)
        )


class SubRegionFfsFile(object):
    def __init__(self, ffs_guid, compression, data):
        self.sFfsGuid = ffs_guid
        try:
            self.FfsGuid = uuid.UUID(self.sFfsGuid)
        except ValueError:
            raise SubRegionDescSyntaxError("ffs_guid")
        self.FfsGuid = ffs_guid
        self.Compression = compression
        self.Data = []
        for DataField in data:
            self.Data.append(SubRegionDataField(DataField))


class SubRegionDataField(object):
    def __init__(self, data_field):
        self.Name = data_field[0]
        self.Type = data_field[1]
        self.ByteSize = data_field[2]
        self.Value = data_field[3]
        if self.Type == DataTypes.DECIMAL:
            if data_field[3] is not None:
                self.dValue = int(data_field[3])
                self.sValue = str(data_field[3])
        elif self.Type == DataTypes.HEXADECIMAL:
            if data_field[3] is not None:
                self.sValue = str(data_field[3])
                self.dValue = int(self.sValue, 16)
        else:
            self.dValue = None
            self.sValue = str(data_field[3])


class SubRegionDescriptor(object):
    ValidGuidList = [
        gFmpCapsuleTsnMacAddressFileGuid,
        gFmpCapsuleOseTsnMacConfigFileGuid,
        gFmpCapsuleOseFwFileGuid,
        gFmpCapsuleTccArbFileGuid,
        gFmpCapsuleOobManageabilityFileGuid,
    ]

    def __init__(self):
        self.sFmpGuid = None
        self.FmpGuid = None
        self.Version = None
        self.Fv = None
        self.sFvGuid = None
        self.FvGuid = None
        self.FfsFiles = []

    def parse_json_data(self, json_file):
        with open(json_file, "r") as file_handle:
            desc_buffer = json.loads(file_handle.read())
            try:
                self.sFmpGuid = desc_buffer["FmpGuid"]
                try:
                    self.FmpGuid = uuid.UUID(self.sFmpGuid)
                    if not self.is_known_guid(self.FmpGuid):
                        raise UnknownSubRegionError
                except ValueError:
                    raise SubRegionDescSyntaxError("FmpGuid")
                self.Version = desc_buffer["Version"]

                self.Fv = desc_buffer["FV"]
                self.sFvGuid = self.Fv["FvGuid"]
                try:
                    self.FvGuid = uuid.UUID(self.sFvGuid)
                except ValueError:
                    raise SubRegionDescSyntaxError("FvGuid")
                except TypeError:
                    raise SubRegionDescSyntaxError("FvGuid")

                ffs_file_list = self.Fv["FfsFiles"]
                for FfsFile in ffs_file_list:
                    ffs_guid = FfsFile["FileGuid"]
                    compression = FfsFile["Compression"]
                    data = FfsFile["Data"]
                    self.FfsFiles.append(SubRegionFfsFile(ffs_guid, compression, data))

                for FfsFile in self.FfsFiles:
                    if not self.check_file_good(FfsFile):
                        raise SubRegionDescSyntaxError("FfsFile")
            except (KeyError, IndexError) as e:
                raise SubRegionDescSyntaxError(str(e))

    def check_file_good(self, ffs_file):
        valid_file = True

        if ffs_file.Compression not in [False, True]:
            valid_file = False

        for DataField in ffs_file.Data:
            if type(DataField.Name) not in [str]:
                valid_file = False
            if DataField.Type not in DataTypes:
                valid_file = False
            if DataField.ByteSize <= 0:
                valid_file = False
            if type(DataField.Value) not in [str, int]:
                valid_file = False

        return valid_file

    def is_known_guid(self, guid):
        return guid in self.ValidGuidList
