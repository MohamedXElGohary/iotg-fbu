
import os
import sys
import struct
import subprocess
import unittest
import uuid
from math import log

import common.sub_region_descriptor as srd
import common.sub_region_image as sri
from common import tools_path

SUBREGION_CAPSULE_TOOL = os.path.join('scripts', 'subregion_capsule.py')

class JsonPayloadParserTestCase(unittest.TestCase):
    def test_ParseJsonSubRegDescriptorFiles(self):
        sub_region_desc = srd.SubRegionDescriptor()
        sub_region_desc.parse_json_data(os.path.join("tests", "Collateral", "GoodSubRegDescExample.json"))
        self.assertEqual(srd.FMP_CAPSULE_TSN_MAC_ADDRESS_FILE_GUID, sub_region_desc.fmp_guid)
        self.assertEqual(1, sub_region_desc.version)
        sample_ffs_file = sub_region_desc.ffs_files[0]
        self.assertNotEqual(None, sample_ffs_file.data)

        field_names = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        field_values = [0,
                        524,
                        333,
                        -98230498723950780,
                        98230984023984,
                        255,
                        819,
                        162364294545257138462923369967,
                        2106967472293113107385212910597918500865023886834641740578657241782190877997108]
        field_sizes = [1, 2, 3, 15, 20, 1, 3, 20, 21]
        field_types = [srd.data_types.DECIMAL,
                       srd.data_types.HEXADECIMAL,
                       srd.data_types.DECIMAL,
                       srd.data_types.DECIMAL,
                       srd.data_types.DECIMAL,
                       srd.data_types.HEXADECIMAL,
                       srd.data_types.HEXADECIMAL,
                       srd.data_types.HEXADECIMAL,
                       srd.data_types.HEXADECIMAL]
        for i in range(9):
            data_field = sample_ffs_file.data[i]
            self.assertEqual("field_" + field_names[i], data_field.name)
            self.assertEqual(field_types[i], data_field.Type)
            self.assertEqual(field_sizes[i], data_field.ByteSize)
            self.assertEqual(field_values[i], data_field.dValue)
        # Json with missing fields
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "MissingFieldSubRegDescExample.json")
            )

        # Json with bad guid
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "BadGuidSubRegDescExample.json")
            )

        # Json with unknown guid
        with self.assertRaises(srd.UnknownSubRegionError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "UnknownGuidSubRegDescExample.json")
            )

        # Json with bad data field
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "BadDataFieldSubRegDescExample.json")
            )

    def test_CheckIfDataFieldValid(self):
        sub_region_desc = srd.SubRegionDescriptor()
        good_guid = "1A803C55-F034-4E60-AD9E-9D3F32CE273C"
        bad_guid = "xxxxxxxx-F034-4E60-AD9E-9D3F32CE273C"
        data_field_good1 = ["field_1", srd.data_types.DECIMAL, 1, 0]
        data_field_good2 = ["field_1", srd.data_types.STRING, 1, "_STDIN_"]
        data_field_bad_field_name = [1, srd.data_types.DECIMAL, 1, 0]
        data_field_bad_byte_size1 = ["field_1", srd.data_types.DECIMAL, 0, 0]
        data_field_bad_byte_size2 = ["field_1", srd.data_types.DECIMAL, -1, 0]
        data_field_bad_none_data = ["field_1", srd.data_types.DECIMAL, 1, None]
        data_field_bad_type = ["field_1", "SOMETHING", 1, 0]

        data = [data_field_good1, data_field_good2]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertTrue(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        ffs_file = srd.SubRegionFfsFile(good_guid, True, data)
        self.assertTrue(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_field_name]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_byte_size1]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_byte_size2]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_none_data]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_type]
        ffs_file = srd.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        ffs_file = srd.SubRegionFfsFile(good_guid, "somethingelse", data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        with self.assertRaises(srd.SubRegionDescSyntaxError):
            ffs_file = srd.SubRegionFfsFile(bad_guid, False, data)
            sub_region_desc.check_file_good(ffs_file)

    def test_HandlePayloadGuids(self):
        sub_reg_desc = srd.SubRegionDescriptor()
        self.assertTrue(
            sub_reg_desc.is_known_guid(srd.FMP_CAPSULE_OOB_MANAGEABILITY_FILE_GUID)
        )
        self.assertTrue(sub_reg_desc.is_known_guid(srd.FMP_CAPSULE_PSE_FW_FILE_GUID))
        self.assertTrue(sub_reg_desc.is_known_guid(srd.FMP_CAPSULE_TCC_ARB_FILE_GUID))
        self.assertTrue(sub_reg_desc.is_known_guid(srd.FMP_CAPSULE_TSN_MAC_ADDRESS_FILE_GUID))
        self.assertTrue(
            sub_reg_desc.is_known_guid(srd.FMP_CAPSULE_PSE_TSN_MAC_CONFIG_FILE_GUID)
        )
        self.assertFalse(
            sub_reg_desc.is_known_guid(uuid.UUID("e526c123-d3e9-41dd-af3c-59adc77cd3a5"))
        )


class SubRegionImageGeneratorTestCase(unittest.TestCase):
    def test_GenerateSubRegionImage(self):

        private_cert = os.path.join("tests", "Collateral", "TestCert.pem")
        public_cert = os.path.join("tests", "Collateral", "TestSub.pub.pem")
        trusted_cert = os.path.join("tests", "Collateral", "TestRoot.pub.pem")
        input_json = os.path.join("tests", "Collateral", "TsnMacAddressDescExample.json")
        output_file = "capsule.out.bin"

        full_cmd_line = [
            SUBREGION_CAPSULE_TOOL,
            "-o", output_file,
            "--signer-private-cert=%s" % private_cert,
            "--other-public-cert=%s" % public_cert,
            "--trusted-public-cert=%s" % trusted_cert,
            input_json
        ]
        full_cmd_line_str = " ".join(full_cmd_line)

        subprocess.check_call(full_cmd_line_str, shell=True)

        os.remove('capsule.out.bin')

        # TODO: check data fields match the input data and key used

    def test_HandleNumberDataFields(self):
        one_byte_val = 0xAB
        two_byte_val = 0xABCD
        multi_byte_val = 0xDEADBEEF0BADF00D

        def get_num_bytes(num):
            if num == 0:
                return 1
            return int(log(num, 256)) + 1

        one_byte_data = srd.SubRegionDataField(
            ["field", srd.data_types.DECIMAL, get_num_bytes(one_byte_val), one_byte_val]
        )
        two_byte_data = srd.SubRegionDataField(
            ["field", srd.data_types.DECIMAL, get_num_bytes(two_byte_val), two_byte_val]
        )
        multi_byte_data = srd.SubRegionDataField(
            [
                "field",
                srd.data_types.DECIMAL,
                get_num_bytes(multi_byte_val),
                multi_byte_val,
            ]
        )
        underflow_data = srd.SubRegionDataField(
            ["field", srd.data_types.DECIMAL, 1, two_byte_val]
        )
        overflow_data = srd.SubRegionDataField(
            ["field", srd.data_types.DECIMAL, 2, one_byte_val]
        )

        # Number data
        data_buffer = sri.create_buffer_from_data_field(one_byte_data)
        self.assertEqual(struct.pack("<B", one_byte_val), data_buffer)

        data_buffer = sri.create_buffer_from_data_field(two_byte_data)
        self.assertEqual(struct.pack("<H", two_byte_val), data_buffer)

        data_buffer = sri.create_buffer_from_data_field(multi_byte_data)
        self.assertEqual(struct.pack("<Q", multi_byte_val), data_buffer)

        # data_buffer = sri.create_buffer_from_data_field(underflow_data)
        # self.assertEqual(struct.pack("<B", TWO_BYTE_VAL), data_buffer)

        # data_buffer = sri.create_buffer_from_data_field(overflow_data)
        # self.assertEqual(struct.pack("<H", ONE_BYTE_VAL), data_buffer)

    def test_HandleFileDataFields(self):
        dummy_file = os.path.join("tests", "Collateral", "DummyFile.txt")
        dummy_bin = os.path.join("tests", "Collateral", "DummyBin.Bin")

        data_field_file_exact_size = srd.SubRegionDataField(
            ["field_1", srd.data_types.FILE, 11, dummy_file]
        )
        data_field_file_big = srd.SubRegionDataField(
            ["field_1", srd.data_types.FILE, 20, dummy_file]
        )
        data_field_file_small = srd.SubRegionDataField(
            ["field_1", srd.data_types.FILE, 5, dummy_file]
        )

        # File Data
        data_buffer = sri.create_buffer_from_data_field(data_field_file_exact_size)
        with open(dummy_file, "rb") as df:
            self.assertEqual(df.read(), data_buffer)
        self.assertEqual(len(data_buffer), data_field_file_exact_size.ByteSize)
        data_buffer = sri.create_buffer_from_data_field(data_field_file_big)
        with open(dummy_file, "rb") as df:
            tmp = df.read()
        self.assertTrue(data_buffer.decode().startswith(tmp.decode()))
        self.assertEqual(len(data_buffer), data_field_file_big.ByteSize)
        data_buffer = sri.create_buffer_from_data_field(data_field_file_small)
        with open(dummy_file, "rb") as df:
            tmp = df.read()
        self.assertTrue(tmp.decode().startswith(data_buffer.decode()))
        self.assertEqual(len(data_buffer), data_field_file_small.ByteSize)

    def test_HandleStdinDataFields(self):
        stdin = "_STDIN_"
        dummy_txt = "Can't touch this"

        data_field_stdin = srd.SubRegionDataField(
            ["field_1", srd.data_types.STRING, len(dummy_txt), stdin]
        )
        data_field_string = srd.SubRegionDataField(
            ["field_1", srd.data_types.STRING, len(dummy_txt), dummy_txt]
        )
        data_field_string_trunc = srd.SubRegionDataField(
            ["field_1", srd.data_types.STRING, len(dummy_txt) - 1, dummy_txt]
        )
        data_field_string_pad = srd.SubRegionDataField(
            ["field_1", srd.data_types.STRING, len(dummy_txt) + 1, dummy_txt]
        )

        # Stdin (need to write test)
        sri.sys.stdin.readline = lambda: dummy_txt
        data_buffer = sri.create_buffer_from_data_field(data_field_stdin)
        self.assertEqual(bytes(dummy_txt, "utf-8"), data_buffer)

        data_buffer = sri.create_buffer_from_data_field(data_field_string)
        self.assertEqual(bytes(dummy_txt, "utf-8"), data_buffer)

        data_buffer = sri.create_buffer_from_data_field(data_field_string_trunc)
        self.assertEqual(bytes(dummy_txt[: len(dummy_txt) - 1], "utf-8"), data_buffer)

        data_buffer = sri.create_buffer_from_data_field(data_field_string_pad)
        self.assertEqual(bytes(dummy_txt + "\0", "utf-8"), data_buffer)

    def test_CreateGenCommands(self):
        sub_region_desc = srd.SubRegionDescriptor()
        sub_region_desc.parse_json_data(os.path.join("tests", "Collateral", "GoodSubRegDescExample.json"))
        fmp_guid = "8C8CE578-8A3D-4F1C-9935-896185C32DD3"
        dummy_file = "somefile.bin"
        dummy_ui_name = "DummyUi"
        ws = os.path.join(os.path.curdir, "temp")
        for index, ffs_file in enumerate(sub_region_desc.ffs_files):
            out_sec_name = ws + "SubRegionSec" + str(index) + ".sec"
            gen_sec_cmd_exp = (
                tools_path.GENSEC
                + " -o "
                + out_sec_name
                + " -s EFI_SECTION_RAW -c PI_NONE "
                + dummy_file
            )
            gen_sec_cmd = sri.create_gen_sec_command(
                ffs_file,
                image_file=dummy_file,
                output_file=ws + "SubRegionSec" + str(index) + ".sec",
            )
            self.assertEqual(gen_sec_cmd_exp, " ".join(gen_sec_cmd))
            out_sec_name = ws + "SubRegionSecUi" + str(index) + ".sec"
            gen_sec_cmd_exp = (
                tools_path.GENSEC
                + " -o "
                + out_sec_name
                + " -s EFI_SECTION_USER_INTERFACE -n "
                + dummy_ui_name
            )
            gen_sec_cmd = sri.create_gen_sec_command(
                ffs_file, output_file=out_sec_name, name=dummy_ui_name
            )
            self.assertEqual(gen_sec_cmd_exp, " ".join(gen_sec_cmd))

            out_ffs_name = ws + "SubRegionFfs" + str(index) + ".ffs"
            gen_ffs_cmd_exp = (
                tools_path.GENFFS
                + " -o "
                + out_ffs_name
                + " -t EFI_FV_FILETYPE_FREEFORM -g "
                + ffs_file.s_ffs_guid
                + " -i "
                + dummy_file
            )
            gen_ffs_cmd = sri.create_gen_ffs_command(
                ffs_file, dummy_file, output_file=out_ffs_name
            )
            self.assertEqual(gen_ffs_cmd_exp, " ".join(gen_ffs_cmd))

        dummy_ffs_files = [ws + "SubRegionFfs1.ffs", ws + "SubRegionFfs2.ffs"]
        gen_fv_cmd_exp = (
            tools_path.GENFV
            + " -o OutputFile.Fv -b 0x1000 -f "
            + " -f ".join(dummy_ffs_files)
            + " -g "
            + fmp_guid
            + " --FvNameGuid "
            + sub_region_desc.s_fv_guid
        )
        gen_fv_cmd = sri.create_gen_fv_command(
            sub_region_desc, "OutputFile.Fv", dummy_ffs_files
        )
        self.assertEqual(gen_fv_cmd_exp, " ".join(gen_fv_cmd))
        dummy_ffs_file = [ws + "SubRegionFfs1.ffs"]
        gen_fv_cmd_exp = (
            tools_path.GENFV
            + " -o OutputFile.Fv -b 0x1000 -f "
            + dummy_ffs_file[0]
            + " -g "
            + fmp_guid
            + " --FvNameGuid "
            + sub_region_desc.s_fv_guid
        )
        gen_fv_cmd = sri.create_gen_fv_command(
            sub_region_desc, "OutputFile.Fv", dummy_ffs_file
        )
        self.assertEqual(gen_fv_cmd_exp, " ".join(gen_fv_cmd))


if __name__ == "__main__":
    unittest.main()
