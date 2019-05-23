## @file
# Unit Tests for Data Blob Generator
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

import unittest
import SubRegionDescriptor as srd
import SubRegionImage as sri
import uuid
import struct
from math import log


class JsonPayloadParserTestCase(unittest.TestCase):
    def test_ParseJsonSubRegDescriptorFiles(self):
        SubRegionDesc = srd.SubRegionDescriptor()
        SubRegionDesc.ParseJsonData("./Tests/Collateral/GoodSubRegDescExample.json")
        self.assertEqual(srd.gFmpCapsuleTsnMacAddrFileGuid, SubRegionDesc.FmpGuid)
        self.assertEqual(1, SubRegionDesc.Version)
        SampleFfsFile = SubRegionDesc.FfsFiles[0]
        self.assertNotEqual(None, SampleFfsFile.Data)
        DataField = SampleFfsFile.Data[0]
        self.assertEqual("field_one", DataField.Name)
        self.assertEqual(srd.DataTypes.DECIMAL, DataField.Type)
        self.assertEqual(1, DataField.ByteSize)
        self.assertEqual(0, DataField.dValue)
        DataField = SampleFfsFile.Data[1]
        self.assertEqual("field_two", DataField.Name)
        self.assertEqual(srd.DataTypes.HEXADECIMAL, DataField.Type)
        self.assertEqual(2, DataField.ByteSize)
        self.assertEqual(524, DataField.dValue)

        # Json with missing fields
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            SubRegionDesc.ParseJsonData("./Tests/Collateral/MissingFieldSubRegDescExample.json")

        # Json with bad guid
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            SubRegionDesc.ParseJsonData("./Tests/Collateral/BadGuidSubRegDescExample.json")

        # Json with unknown guid
        with self.assertRaises(srd.UnknownSubRegionError):
            SubRegionDesc.ParseJsonData("./Tests/Collateral/UnknownGuidSubRegDescExample.json")

        # Json with bad data field
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            SubRegionDesc.ParseJsonData("./Tests/Collateral/BadDataFieldSubRegDescExample.json")

    def test_CheckIfDataFieldValid(self):
        SubRegionDesc = srd.SubRegionDescriptor()
        GoodGuid = "1A803C55-F034-4E60-AD9E-9D3F32CE273C"
        BadGuid  = "xxxxxxxx-F034-4E60-AD9E-9D3F32CE273C"
        DataFieldGood1 = ["field_1", srd.DataTypes.DECIMAL, 1, 0]
        DataFieldGood2 = ["field_1", srd.DataTypes.STRING, 1, "_STDIN_"]
        DataFieldBadFieldName = [1, srd.DataTypes.DECIMAL, 1, 0]
        DataFieldBadByteSize1 = ["field_1", srd.DataTypes.DECIMAL, 0, 0]
        DataFieldBadByteSize2 = ["field_1", srd.DataTypes.DECIMAL, -1, 0]
        DataFieldBadNoneData  = ["field_1", srd.DataTypes.DECIMAL, 1, None]
        DataFieldBadType  = ["field_1", "SOMETHING", 1, 0]

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertTrue(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, True, Data)
        self.assertTrue(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadFieldName]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadByteSize1]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadByteSize2]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadNoneData]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2, DataFieldBadType]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, False, Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        FfsFile = srd.SubRegionFfsFile(GoodGuid, "somethingelse", Data)
        self.assertFalse(SubRegionDesc.CheckFileGood(FfsFile))

        Data = [DataFieldGood1, DataFieldGood2]
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            FfsFile = srd.SubRegionFfsFile(BadGuid, False, Data)
            SubRegionDesc.CheckFileGood(FfsFile)

    def test_HandlePayloadGuids(self):
        SubRegDesc = srd.SubRegionDescriptor()
        self.assertTrue(SubRegDesc.IsKnownGuid(srd.gFmpCapsuleOobManageabilityFileGuid))
        self.assertTrue(SubRegDesc.IsKnownGuid(srd.gFmpCapsuleOseFwFileGuid))
        self.assertTrue(SubRegDesc.IsKnownGuid(srd.gFmpCapsuleTccArbFileGuid))
        self.assertTrue(SubRegDesc.IsKnownGuid(srd.gFmpCapsuleTsnMacAddrFileGuid))
        self.assertTrue(SubRegDesc.IsKnownGuid(srd.gFmpCapsuleOseTsnMacConfigFileGuid))
        self.assertFalse(SubRegDesc.IsKnownGuid(uuid.UUID('e526c123-d3e9-41dd-af3c-59adc77cd3a5')))


class SubRegionImageGeneratorTestCase(unittest.TestCase):
    def test_GenerateSubRegionImage(self):
        pass

    def test_HandleNumberDataFields(self):
        ONE_BYTE_VAL = 0xAB
        TWO_BYTE_VAL = 0xABCD
        MULTI_BYTE_VAL = 0xDEADBEEF0BADF00D

        def GetNumBytes(num):
            if num == 0:
                return 1
            return int(log(num, 256)) + 1

        OneByteData = srd.SubRegionDataField(["field", srd.DataTypes.DECIMAL, GetNumBytes(ONE_BYTE_VAL), ONE_BYTE_VAL])
        TwoByteData = srd.SubRegionDataField(["field", srd.DataTypes.DECIMAL, GetNumBytes(TWO_BYTE_VAL), TWO_BYTE_VAL])
        MultiByteData = srd.SubRegionDataField(["field", srd.DataTypes.DECIMAL, GetNumBytes(MULTI_BYTE_VAL), MULTI_BYTE_VAL])
        UnderflowData = srd.SubRegionDataField(["field", srd.DataTypes.DECIMAL, 1, TWO_BYTE_VAL])
        OverflowData = srd.SubRegionDataField(["field", srd.DataTypes.DECIMAL, 2, ONE_BYTE_VAL])

        # Number Data
        DataBuffer = sri.CreateBufferFromDataField(OneByteData)
        self.assertEqual(struct.pack("<B", ONE_BYTE_VAL), DataBuffer)

        DataBuffer = sri.CreateBufferFromDataField(TwoByteData)
        self.assertEqual(struct.pack("<H", TWO_BYTE_VAL), DataBuffer)

        DataBuffer = sri.CreateBufferFromDataField(MultiByteData)
        self.assertEqual(struct.pack("<Q", MULTI_BYTE_VAL), DataBuffer)

        #DataBuffer = sri.CreateBufferFromDataField(UnderflowData)
        #self.assertEqual(struct.pack("<B", TWO_BYTE_VAL), DataBuffer)

        #DataBuffer = sri.CreateBufferFromDataField(OverflowData)
        #self.assertEqual(struct.pack("<H", ONE_BYTE_VAL), DataBuffer)

    def test_HandleFileDataFields(self):
        DUMMY_FILE = "./Tests/Collateral/DummyFile.txt"
        DUMMY_BIN = "./Tests/Collateral/DummyBin.Bin"

        DataFieldFile  = srd.SubRegionDataField(["field_1", srd.DataTypes.FILE, 8, DUMMY_FILE])

        # File Data
        DataBuffer = sri.CreateBufferFromDataField(DataFieldFile)
        with open(DUMMY_FILE, 'rb') as df:
            self.assertEqual(df.read(), DataBuffer)

    def test_HandleStdinDataFields(self):
        STDIN = "_STDIN_"
        DUMMY_TXT = "Can't touch this"

        DataFieldStdin = srd.SubRegionDataField(["field_1", srd.DataTypes.STRING, 1, STDIN])
        DataFieldString = srd.SubRegionDataField(["field_1", srd.DataTypes.STRING, len(DUMMY_TXT), DUMMY_TXT])
        DataFieldStringTrunc = srd.SubRegionDataField(["field_1", srd.DataTypes.STRING, len(DUMMY_TXT)-1, DUMMY_TXT])
        DataFieldStringPad = srd.SubRegionDataField(["field_1", srd.DataTypes.STRING, len(DUMMY_TXT)+1, DUMMY_TXT])

        # Stdin (need to write test)
        #DataBuffer = sri.CreateBufferFromDataField(DataFieldStdin)
        #self.assertEqual(DUMMY_INPUT, DataBuffer)
        DataBuffer = sri.CreateBufferFromDataField(DataFieldString)
        self.assertEqual(bytes(DUMMY_TXT, 'utf-8'), DataBuffer)

        DataBuffer = sri.CreateBufferFromDataField(DataFieldStringTrunc)
        self.assertEqual(bytes(DUMMY_TXT[:len(DUMMY_TXT)-1], 'utf-8'), DataBuffer)

        DataBuffer = sri.CreateBufferFromDataField(DataFieldStringPad)
        self.assertEqual(bytes(DUMMY_TXT+"\0", 'utf-8'), DataBuffer)

    def test_CreateGenCommands(self):
        SubRegionDesc = srd.SubRegionDescriptor()
        SubRegionDesc.ParseJsonData("./Tests/Collateral/GoodSubRegDescExample.json")
        FmpGuid = "8C8CE578-8A3D-4F1C-9935-896185C32DD3"
        DummyFile = "somefile.bin"
        DummyUiName = "DummyUi"
        Ws = "./temp/"
        for Index, FfsFile in enumerate(SubRegionDesc.FfsFiles):
            OutSecName = Ws + "SubRegionSec" + str(Index) + ".sec"
            GenSecCmdExp = "GenSec -o " + OutSecName + " -s EFI_SECTION_RAW -c PI_NONE " + DummyFile
            GenSecCmd = sri.CreateGenSecCommand(FfsFile, ImageFile=DummyFile, OutputFile=Ws+"SubRegionSec"+str(Index)+".sec")
            self.assertEqual(GenSecCmdExp, ' '.join(GenSecCmd))
            OutSecName = Ws + "SubRegionSecUi" + str(Index) + ".sec"
            GenSecCmdExp = "GenSec -o " + OutSecName + " -s EFI_SECTION_USER_INTERFACE -n " + DummyUiName
            GenSecCmd = sri.CreateGenSecCommand(FfsFile, OutputFile=OutSecName, Name=DummyUiName)
            self.assertEqual(GenSecCmdExp, ' '.join(GenSecCmd))

            OutFfsName = Ws + "SubRegionFfs" + str(Index) + ".ffs"
            GenFfsCmdExp = "GenFfs -o " + OutFfsName + " -t EFI_FV_FILETYPE_FREEFORM -g " + FfsFile.sFfsGuid + " -i " + DummyFile
            GenFfsCmd = sri.CreateGenFfsCommand(FfsFile, DummyFile, OutputFile=OutFfsName)
            self.assertEqual(GenFfsCmdExp, ' '.join(GenFfsCmd))

        DummyFfsFiles = [Ws + "SubRegionFfs1.ffs", Ws + "SubRegionFfs2.ffs"]
        GenFvCmdExp  = "GenFv -o OutputFile.Fv -b 0x10000 -f " + ' -f '.join(DummyFfsFiles) + " -g " + FmpGuid + " --FvNameGuid " + SubRegionDesc.sFvGuid
        GenFvCmd = sri.CreateGenFvCommand(SubRegionDesc, "OutputFile.Fv", DummyFfsFiles)
        self.assertEqual(GenFvCmdExp, ' '.join(GenFvCmd))
        DummyFfsFile = [Ws + "SubRegionFfs1.ffs"]
        GenFvCmdExp  = "GenFv -o OutputFile.Fv -b 0x10000 -f " + DummyFfsFile[0] + " -g " + FmpGuid + " --FvNameGuid " + SubRegionDesc.sFvGuid
        GenFvCmd = sri.CreateGenFvCommand(SubRegionDesc, "OutputFile.Fv", DummyFfsFile)
        self.assertEqual(GenFvCmdExp, ' '.join(GenFvCmd))

if __name__ == '__main__':
    unittest.main()
