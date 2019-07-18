# @file
# Unit Tests for Data Blob Generator
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

import os
import struct
import subprocess
import unittest
import uuid
from math import log


import SubRegionCapsule.SubRegionDescriptor as Srd
import SubRegionCapsule.SubRegionImage as Sri


class JsonPayloadParserTestCase(unittest.TestCase):
    def test_ParseJsonSubRegDescriptorFiles(self):
        SubRegionDesc = Srd.SubRegionDescriptor()
        SubRegionDesc.parse_json_data("./Tests/Collateral/GoodSubRegDescExample.json")
        self.assertEqual(Srd.gFmpCapsuleTsnMacAddressFileGuid, SubRegionDesc.FmpGuid)
        self.assertEqual(1, SubRegionDesc.Version)
        SampleFfsFile = SubRegionDesc.FfsFiles[0]
        self.assertNotEqual(None, SampleFfsFile.Data)
        DataField = SampleFfsFile.Data[0]
        self.assertEqual("field_one", DataField.Name)
        self.assertEqual(Srd.DataTypes.DECIMAL, DataField.Type)
        self.assertEqual(1, DataField.ByteSize)
        self.assertEqual(0, DataField.dValue)
        DataField = SampleFfsFile.Data[1]
        self.assertEqual("field_two", DataField.Name)
        self.assertEqual(Srd.DataTypes.HEXADECIMAL, DataField.Type)
        self.assertEqual(2, DataField.ByteSize)
        self.assertEqual(524, DataField.dValue)

        # Json with missing fields
        with self.assertRaises(Srd.SubRegionDescSyntaxError):
            SubRegionDesc.parse_json_data(
                "./Tests/Collateral/MissingFieldSubRegDescExample.json"
            )

        # Json with bad guid
        with self.assertRaises(Srd.SubRegionDescSyntaxError):
            SubRegionDesc.parse_json_data(
                "./Tests/Collateral/BadGuidSubRegDescExample.json"
            )

        # Json with unknown guid
        with self.assertRaises(Srd.UnknownSubRegionError):
            SubRegionDesc.parse_json_data(
                "./Tests/Collateral/UnknownGuidSubRegDescExample.json"
            )

        # Json with bad data field
        with self.assertRaises(Srd.SubRegionDescSyntaxError):
            SubRegionDesc.parse_json_data(
                "./Tests/Collateral/BadDataFieldSubRegDescExample.json"
            )

    def test_CheckIfDataFieldValid(self):
        SubRegionDesc = Srd.SubRegionDescriptor()
        GoodGuid = "1A803C55-F034-4E60-AD9E-9D3F32CE273C"
        BadGuid = "xxxxxxxx-F034-4E60-AD9E-9D3F32CE273C"
        DataFieldGood1 = ["field_1", Srd.DataTypes.DECIMAL, 1, 0]
        DataFieldGood2 = ["field_1", Srd.DataTypes.STRING, 1, "_STDIN_"]
        DataFieldBadFieldName = [1, Srd.DataTypes.DECIMAL, 1, 0]
        DataFieldBadByteSize1 = ["field_1", Srd.DataTypes.DECIMAL, 0, 0]
        DataFieldBadByteSize2 = ["field_1", Srd.DataTypes.DECIMAL, -1, 0]
        DataFieldBadNoneData = ["field_1", Srd.DataTypes.DECIMAL, 1, None]
        DataFieldBadType = ["field_1", "SOMETHING", 1, 0]

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertTrue(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, True, Data)
        self.assertTrue(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadFieldName]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadByteSize1]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadByteSize2]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadNoneData]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadType]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = Srd.SubRegionFfsFile(GoodGuid, "somethingelse", Data)
        self.assertFalse(SubRegionDesc.check_file_good(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        with self.assertRaises(Srd.SubRegionDescSyntaxError):
            FfsFile = Srd.SubRegionFfsFile(BadGuid, False, Data)
            SubRegionDesc.check_file_good(FfsFile)

    def test_HandlePayloadGuids(self):
        SubRegDesc = Srd.SubRegionDescriptor()
        self.assertTrue(
            SubRegDesc.is_known_guid(Srd.gFmpCapsuleOobManageabilityFileGuid)
        )
        self.assertTrue(SubRegDesc.is_known_guid(Srd.gFmpCapsuleOseFwFileGuid))
        self.assertTrue(SubRegDesc.is_known_guid(Srd.gFmpCapsuleTccArbFileGuid))
        self.assertTrue(SubRegDesc.is_known_guid(Srd.gFmpCapsuleTsnMacAddressFileGuid))
        self.assertTrue(
            SubRegDesc.is_known_guid(Srd.gFmpCapsuleOseTsnMacConfigFileGuid)
        )
        self.assertFalse(
            SubRegDesc.is_known_guid(uuid.UUID("e526c123-d3e9-41dd-af3c-59adc77cd3a5"))
        )


class SubRegionImageGeneratorTestCase(unittest.TestCase):
    def test_GenerateSubRegionImage(self):

        PrivateCert = os.path.join("Tests", "Collateral", "TestCert.pem")
        PublicCert = os.path.join("Tests", "Collateral", "TestSub.pub.pem")
        TrustedCert = os.path.join("Tests", "Collateral", "TestRoot.pub.pem")
        InputJson = os.path.join("Tests", "Collateral", "TsnMacAddressDescExample.json")
        OutputFile = "capsule.out.bin"

        FullCmdLine = [
            os.path.join('SubRegionCapsule', 'GenerateSubRegionCapsule.py'),
            "-o",
            OutputFile,
            "--signer-private-cert=%s" % PrivateCert,
            "--other-public-cert=%s" % PublicCert,
            "--trusted-public-cert=%s" % TrustedCert,
            InputJson,
        ]

        subprocess.check_call(FullCmdLine, shell=True)
        # TODO: check data fields match the input data and key used

    def test_HandleNumberDataFields(self):
        ONE_BYTE_VAL = 0xAB
        TWO_BYTE_VAL = 0xABCD
        MULTI_BYTE_VAL = 0xDEADBEEF0BADF00D

        def get_num_bytes(num):
            if num == 0:
                return 1
            return int(log(num, 256)) + 1

        OneByteData = Srd.SubRegionDataField(
            ["field", Srd.DataTypes.DECIMAL, get_num_bytes(ONE_BYTE_VAL), ONE_BYTE_VAL]
        )
        TwoByteData = Srd.SubRegionDataField(
            ["field", Srd.DataTypes.DECIMAL, get_num_bytes(TWO_BYTE_VAL), TWO_BYTE_VAL]
        )
        MultiByteData = Srd.SubRegionDataField(
            [
                "field",
                Srd.DataTypes.DECIMAL,
                get_num_bytes(MULTI_BYTE_VAL),
                MULTI_BYTE_VAL,
            ]
        )
        UnderflowData = Srd.SubRegionDataField(
            ["field", Srd.DataTypes.DECIMAL, 1, TWO_BYTE_VAL]
        )
        OverflowData = Srd.SubRegionDataField(
            ["field", Srd.DataTypes.DECIMAL, 2, ONE_BYTE_VAL]
        )

        # Number Data
        DataBuffer = Sri.create_buffer_from_data_field(OneByteData)
        self.assertEqual(struct.pack("<B", ONE_BYTE_VAL), DataBuffer)

        DataBuffer = Sri.create_buffer_from_data_field(TwoByteData)
        self.assertEqual(struct.pack("<H", TWO_BYTE_VAL), DataBuffer)

        DataBuffer = Sri.create_buffer_from_data_field(MultiByteData)
        self.assertEqual(struct.pack("<Q", MULTI_BYTE_VAL), DataBuffer)

        # DataBuffer = sri.create_buffer_from_data_field(UnderflowData)
        # self.assertEqual(struct.pack("<B", TWO_BYTE_VAL), DataBuffer)

        # DataBuffer = sri.create_buffer_from_data_field(OverflowData)
        # self.assertEqual(struct.pack("<H", ONE_BYTE_VAL), DataBuffer)

    def test_HandleFileDataFields(self):
        DUMMY_FILE = "./Tests/Collateral/DummyFile.txt"
        DUMMY_BIN = "./Tests/Collateral/DummyBin.Bin"

        DataFieldFile = Srd.SubRegionDataField(
            ["field_1", Srd.DataTypes.FILE, 8, DUMMY_FILE]
        )

        # File Data
        DataBuffer = Sri.create_buffer_from_data_field(DataFieldFile)
        with open(DUMMY_FILE, "rb") as df:
            self.assertEqual(df.read(), DataBuffer)

    def test_HandleStdinDataFields(self):
        STDIN = "_STDIN_"
        DUMMY_TXT = "Can't touch this"

        DataFieldStdin = Srd.SubRegionDataField(
            ["field_1", Srd.DataTypes.STRING, len(DUMMY_TXT), STDIN]
        )
        DataFieldString = Srd.SubRegionDataField(
            ["field_1", Srd.DataTypes.STRING, len(DUMMY_TXT), DUMMY_TXT]
        )
        DataFieldStringTrunc = Srd.SubRegionDataField(
            ["field_1", Srd.DataTypes.STRING, len(DUMMY_TXT) - 1, DUMMY_TXT]
        )
        DataFieldStringPad = Srd.SubRegionDataField(
            ["field_1", Srd.DataTypes.STRING, len(DUMMY_TXT) + 1, DUMMY_TXT]
        )

        # Stdin (need to write test)
        Sri.sys.stdin.readline = lambda: DUMMY_TXT
        DataBuffer = Sri.create_buffer_from_data_field(DataFieldStdin)
        self.assertEqual(bytes(DUMMY_TXT, "utf-8"), DataBuffer)

        DataBuffer = Sri.create_buffer_from_data_field(DataFieldString)
        self.assertEqual(bytes(DUMMY_TXT, "utf-8"), DataBuffer)

        DataBuffer = Sri.create_buffer_from_data_field(DataFieldStringTrunc)
        self.assertEqual(bytes(DUMMY_TXT[: len(DUMMY_TXT) - 1], "utf-8"), DataBuffer)

        DataBuffer = Sri.create_buffer_from_data_field(DataFieldStringPad)
        self.assertEqual(bytes(DUMMY_TXT + "\0", "utf-8"), DataBuffer)

    def test_CreateGenCommands(self):
        SubRegionDesc = Srd.SubRegionDescriptor()
        SubRegionDesc.parse_json_data("./Tests/Collateral/GoodSubRegDescExample.json")
        FmpGuid = "8C8CE578-8A3D-4F1C-9935-896185C32DD3"
        DummyFile = "somefile.bin"
        DummyUiName = "DummyUi"
        Ws = "./temp/"
        for Index, FfsFile in enumerate(SubRegionDesc.FfsFiles):
            OutSecName = Ws + "SubRegionSec" + str(Index) + ".sec"
            GenSecCmdExp = (
                "GenSec -o "
                + OutSecName
                + " -s EFI_SECTION_RAW -c PI_NONE "
                + DummyFile
            )
            GenSecCmd = Sri.create_gen_sec_command(
                FfsFile,
                image_file=DummyFile,
                output_file=Ws + "SubRegionSec" + str(Index) + ".sec",
            )
            self.assertEqual(GenSecCmdExp, " ".join(GenSecCmd))
            OutSecName = Ws + "SubRegionSecUi" + str(Index) + ".sec"
            GenSecCmdExp = (
                "GenSec -o "
                + OutSecName
                + " -s EFI_SECTION_USER_INTERFACE -n "
                + DummyUiName
            )
            GenSecCmd = Sri.create_gen_sec_command(
                FfsFile, output_file=OutSecName, name=DummyUiName
            )
            self.assertEqual(GenSecCmdExp, " ".join(GenSecCmd))

            OutFfsName = Ws + "SubRegionFfs" + str(Index) + ".ffs"
            GenFfsCmdExp = (
                "GenFfs -o "
                + OutFfsName
                + " -t EFI_FV_FILETYPE_FREEFORM -g "
                + FfsFile.sFfsGuid
                + " -i "
                + DummyFile
            )
            GenFfsCmd = Sri.create_gen_ffs_command(
                FfsFile, DummyFile, output_file=OutFfsName
            )
            self.assertEqual(GenFfsCmdExp, " ".join(GenFfsCmd))

        DummyFfsFiles = [Ws + "SubRegionFfs1.ffs", Ws + "SubRegionFfs2.ffs"]
        GenFvCmdExp = (
            "GenFv -o OutputFile.Fv -b 0x10000 -f "
            + " -f ".join(DummyFfsFiles)
            + " -g "
            + FmpGuid
            + " --FvNameGuid "
            + SubRegionDesc.sFvGuid
        )
        GenFvCmd = Sri.create_gen_fv_command(
            SubRegionDesc, "OutputFile.Fv", DummyFfsFiles
        )
        self.assertEqual(GenFvCmdExp, " ".join(GenFvCmd))
        DummyFfsFile = [Ws + "SubRegionFfs1.ffs"]
        GenFvCmdExp = (
            "GenFv -o OutputFile.Fv -b 0x10000 -f "
            + DummyFfsFile[0]
            + " -g "
            + FmpGuid
            + " --FvNameGuid "
            + SubRegionDesc.sFvGuid
        )
        GenFvCmd = Sri.create_gen_fv_command(
            SubRegionDesc, "OutputFile.Fv", DummyFfsFile
        )
        self.assertEqual(GenFvCmdExp, " ".join(GenFvCmd))


if __name__ == "__main__":
    unittest.main()
