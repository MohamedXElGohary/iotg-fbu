
import os
import sys
import struct
import subprocess
import unittest
import uuid
import filecmp
import glob
from math import log

import common.subregion_descriptor as dscrptr
import common.subregion_image as img
from common import tools_path
sys.path.insert(0, "..")

SUBREGION_CAPSULE_TOOL = os.path.join('scripts', 'subregion_capsule.py')
IMAGES_PATH = os.path.join("tests", "images")
JSON_PATH = os.path.join("scripts", "Examples")
COLLATER_PATH = os.path.join("tests", "Collateral")

class JsonPayloadParserTestCase(unittest.TestCase):

    def tearDown(self):
        cleanup()

    def test_ParseJsonSubRegDescriptorFiles(self):
        sub_region_desc = dscrptr.SubRegionDescriptor()
        sub_region_desc.parse_json_data(os.path.join("tests", "Collateral", "GoodSubRegDescExample.json"))
        self.assertEqual(dscrptr.FMP_CAPSULE_TSN_MAC_ADDRESS_FILE_GUID, sub_region_desc.fmp_guid)
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
        field_types = [dscrptr.data_types.DECIMAL,
                       dscrptr.data_types.HEXADECIMAL,
                       dscrptr.data_types.DECIMAL,
                       dscrptr.data_types.DECIMAL,
                       dscrptr.data_types.DECIMAL,
                       dscrptr.data_types.HEXADECIMAL,
                       dscrptr.data_types.HEXADECIMAL,
                       dscrptr.data_types.HEXADECIMAL,
                       dscrptr.data_types.HEXADECIMAL]
        for i in range(9):
            data_field = sample_ffs_file.data[i]
            self.assertEqual("field_" + field_names[i], data_field.name)
            self.assertEqual(field_types[i], data_field.Type)
            self.assertEqual(field_sizes[i], data_field.ByteSize)
            self.assertEqual(field_values[i], data_field.dValue)
        # Json with missing fields
        with self.assertRaises(dscrptr.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "MissingFieldSubRegDescExample.json")
            )

        # Json with bad guid
        with self.assertRaises(dscrptr.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "BadGuidSubRegDescExample.json")
            )

        # Json with unknown guid
        with self.assertRaises(dscrptr.UnknownSubRegionError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "UnknownGuidSubRegDescExample.json")
            )

        # Json with bad data field
        with self.assertRaises(dscrptr.SubRegionDescSyntaxError):
            sub_region_desc.parse_json_data(
                os.path.join("tests", "Collateral", "BadDataFieldSubRegDescExample.json")
            )

    def test_CheckIfDataFieldValid(self):
        sub_region_desc = dscrptr.SubRegionDescriptor()
        good_guid = "1A803C55-F034-4E60-AD9E-9D3F32CE273C"
        bad_guid = "xxxxxxxx-F034-4E60-AD9E-9D3F32CE273C"
        data_field_good1 = ["field_1", dscrptr.data_types.DECIMAL, 1, 0]
        data_field_good2 = ["field_1", dscrptr.data_types.STRING, 1, "_STDIN_"]
        data_field_bad_field_name = [1, dscrptr.data_types.DECIMAL, 1, 0]
        data_field_bad_byte_size1 = ["field_1", dscrptr.data_types.DECIMAL, 0, 0]
        data_field_bad_byte_size2 = ["field_1", dscrptr.data_types.DECIMAL, -1, 0]
        data_field_bad_none_data = ["field_1", dscrptr.data_types.DECIMAL, 1, None]
        data_field_bad_type = ["field_1", "SOMETHING", 1, 0]

        data = [data_field_good1, data_field_good2]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertTrue(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, True, data)
        self.assertTrue(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_field_name]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_byte_size1]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_byte_size2]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_none_data]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2, data_field_bad_type]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, False, data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        ffs_file = dscrptr.SubRegionFfsFile(good_guid, "somethingelse", data)
        self.assertFalse(sub_region_desc.check_file_good(ffs_file))

        data = [data_field_good1, data_field_good2]
        with self.assertRaises(dscrptr.SubRegionDescSyntaxError):
            ffs_file = dscrptr.SubRegionFfsFile(bad_guid, False, data)
            sub_region_desc.check_file_good(ffs_file)

    def test_HandlePayloadGuids(self):
        sub_reg_desc = dscrptr.SubRegionDescriptor()
        self.assertTrue(
            sub_reg_desc.is_known_guid(dscrptr.FMP_CAPSULE_OOB_MANAGEABILITY_FILE_GUID)
        )
        self.assertTrue(sub_reg_desc.is_known_guid(dscrptr.FMP_CAPSULE_PSE_FW_FILE_GUID))
        self.assertTrue(sub_reg_desc.is_known_guid(dscrptr.FMP_CAPSULE_TCC_ARB_FILE_GUID))
        self.assertTrue(sub_reg_desc.is_known_guid(dscrptr.FMP_CAPSULE_TSN_MAC_ADDRESS_FILE_GUID))
        self.assertTrue(
            sub_reg_desc.is_known_guid(dscrptr.FMP_CAPSULE_PSE_TSN_MAC_CONFIG_FILE_GUID)
        )
        self.assertFalse(
            sub_reg_desc.is_known_guid(uuid.UUID("e526c123-d3e9-41dd-af3c-59adc77cd3a5"))
        )


class SubRegionImageGeneratorTestCase(unittest.TestCase):

    def tearDown(self):
        cleanup()

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

        one_byte_data = dscrptr.SubRegionDataField(
            ["field", dscrptr.data_types.DECIMAL, get_num_bytes(one_byte_val), one_byte_val]
        )
        two_byte_data = dscrptr.SubRegionDataField(
            ["field", dscrptr.data_types.DECIMAL, get_num_bytes(two_byte_val), two_byte_val]
        )
        multi_byte_data = dscrptr.SubRegionDataField(
            [
                "field",
                dscrptr.data_types.DECIMAL,
                get_num_bytes(multi_byte_val),
                multi_byte_val,
            ]
        )
        underflow_data = dscrptr.SubRegionDataField(
            ["field", dscrptr.data_types.DECIMAL, 1, two_byte_val]
        )
        overflow_data = dscrptr.SubRegionDataField(
            ["field", dscrptr.data_types.DECIMAL, 2, one_byte_val]
        )

        # Number data
        data_buffer = img.create_buffer_from_data_field(one_byte_data)
        self.assertEqual(struct.pack("<B", one_byte_val), data_buffer)

        data_buffer = img.create_buffer_from_data_field(two_byte_data)
        self.assertEqual(struct.pack("<H", two_byte_val), data_buffer)

        data_buffer = img.create_buffer_from_data_field(multi_byte_data)
        self.assertEqual(struct.pack("<Q", multi_byte_val), data_buffer)

        # data_buffer = img.create_buffer_from_data_field(underflow_data)
        # self.assertEqual(struct.pack("<B", TWO_BYTE_VAL), data_buffer)

        # data_buffer = img.create_buffer_from_data_field(overflow_data)
        # self.assertEqual(struct.pack("<H", ONE_BYTE_VAL), data_buffer)

    def test_HandleFileDataFields(self):
        dummy_file = os.path.join("tests", "Collateral", "DummyFile.txt")
        dummy_bin = os.path.join("tests", "Collateral", "DummyBin.Bin")

        data_field_file_exact_size = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.FILE, 11, dummy_file]
        )
        data_field_file_big = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.FILE, 20, dummy_file]
        )
        data_field_file_small = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.FILE, 5, dummy_file]
        )

        # File Data
        data_buffer = img.create_buffer_from_data_field(data_field_file_exact_size)
        with open(dummy_file, "rb") as df:
            self.assertEqual(df.read(), data_buffer)
        self.assertEqual(len(data_buffer), data_field_file_exact_size.ByteSize)
        data_buffer = img.create_buffer_from_data_field(data_field_file_big)
        with open(dummy_file, "rb") as df:
            tmp = df.read()
        self.assertTrue(data_buffer.decode().startswith(tmp.decode()))
        self.assertEqual(len(data_buffer), data_field_file_big.ByteSize)
        data_buffer = img.create_buffer_from_data_field(data_field_file_small)
        with open(dummy_file, "rb") as df:
            tmp = df.read()
        self.assertTrue(tmp.decode().startswith(data_buffer.decode()))
        self.assertEqual(len(data_buffer), data_field_file_small.ByteSize)

    def test_HandleStdinDataFields(self):
        stdin = "_STDIN_"
        dummy_txt = "Can't touch this"

        data_field_stdin = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.STRING, len(dummy_txt), stdin]
        )
        data_field_string = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.STRING, len(dummy_txt), dummy_txt]
        )
        data_field_string_trunc = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.STRING, len(dummy_txt) - 1, dummy_txt]
        )
        data_field_string_pad = dscrptr.SubRegionDataField(
            ["field_1", dscrptr.data_types.STRING, len(dummy_txt) + 1, dummy_txt]
        )

        # Stdin (need to write test)
        img.sys.stdin.readline = lambda: dummy_txt
        data_buffer = img.create_buffer_from_data_field(data_field_stdin)
        self.assertEqual(bytes(dummy_txt, "utf-8"), data_buffer)

        data_buffer = img.create_buffer_from_data_field(data_field_string)
        self.assertEqual(bytes(dummy_txt, "utf-8"), data_buffer)

        data_buffer = img.create_buffer_from_data_field(data_field_string_trunc)
        self.assertEqual(bytes(dummy_txt[: len(dummy_txt) - 1], "utf-8"), data_buffer)

        data_buffer = img.create_buffer_from_data_field(data_field_string_pad)
        self.assertEqual(bytes(dummy_txt + "\0", "utf-8"), data_buffer)

    def test_CreateGenCommands(self):
        sub_region_desc = dscrptr.SubRegionDescriptor()
        sub_region_desc.parse_json_data(os.path.join("tests", "Collateral", "GoodSubRegDescExample.json"))
        fmp_guid = "8C8CE578-8A3D-4F1C-9935-896185C32DD3"
        dummy_file = "somefile.bin"
        dummy_ui_name = "DummyUi"
        ws = os.path.join(os.path.curdir, "temp")
        for index, ffs_file in enumerate(sub_region_desc.ffs_files):
            gen_sec_cmd_exp = (
                tools_path.GENSEC
                + " -o "
                + "tmp.raw"
                + " -s EFI_SECTION_RAW -c PI_NONE "
                + dummy_file
            )
            gen_sec_cmd = img.create_gensec_cmd(["raw", "PI_NONE"], ["somefile.bin"])
            self.assertEqual(gen_sec_cmd_exp, " ".join(gen_sec_cmd))
           
            gen_sec_cmd_exp = (
                tools_path.GENSEC
                + " -o "
                + "tmp.ui"
                + " -s EFI_SECTION_USER_INTERFACE -n "
                + dummy_ui_name
            )
            gen_sec_cmd = img.create_gensec_cmd(["ui",dummy_ui_name], None)
            self.assertEqual(gen_sec_cmd_exp, " ".join(gen_sec_cmd))
            
            gen_ffs_cmd_exp = (
                tools_path.GENFFS
                + " -o "
                + "tmp.ffs"
                + " -t EFI_FV_FILETYPE_FREEFORM -g "
                + ffs_file.s_ffs_guid
                + " -i "
                + dummy_file
            )
            gen_ffs_cmd = img.create_ffs_cmd("free", ffs_file.s_ffs_guid, None, dummy_file)
            self.assertEqual(gen_ffs_cmd_exp, " ".join(gen_ffs_cmd))

        dummy_ffs_files = [ws + "SubRegionFfs1.ffs", ws + "SubRegionFfs2.ffs"]
        gen_fv_cmd_exp = (
            tools_path.GENFV
            + " -o OutputFile.Fv -b 0x1000 -f "
            + dummy_ffs_files[0]
            + " -g "
            + fmp_guid
            + " --FvNameGuid "
            + sub_region_desc.s_fv_guid
        )
        gen_fv_cmd = img.create_gen_fv_command(
            sub_region_desc.s_fv_guid, "OutputFile.Fv", dummy_ffs_files[0]
        )
        self.assertEqual(gen_fv_cmd_exp, " ".join(gen_fv_cmd))
        gen_fv_cmd_exp = (
            tools_path.GENFV
            + " -i OutputFile.Fv"
            + " -o OutputFile.Fv -b 0x1000 -f "
            + dummy_ffs_files[1]
            + " -g "
            + fmp_guid
            + " --FvNameGuid "
            + sub_region_desc.s_fv_guid
        )
        gen_fv_cmd = img.create_gen_fv_command(
            sub_region_desc.s_fv_guid, "OutputFile.Fv", dummy_ffs_files[1],
            "OutputFile.Fv"
        )
        self.assertEqual(gen_fv_cmd_exp, " ".join(gen_fv_cmd))

        fv_cmd_list = [[tools_path.GENFV, "-o", "OutputFile.Fv", "-b", "0x1000",
                        "-f", dummy_ffs_files[0], "-g", fmp_guid,
                        "--FvNameGuid", sub_region_desc.s_fv_guid, '-f',
                        '.\\tempSubRegionFfs2.ffs']]

        gen_fv_cmd_list = img.build_fv_from_ffs_files(
            sub_region_desc, "OutputFile.Fv", dummy_ffs_files
        )
        self.assertEqual(fv_cmd_list , gen_fv_cmd_list)


class SubRegionFunctionalityTestCases(unittest.TestCase):

    def tearDown(self):
        cleanup()

    def test_generate_capsule(self):
        cmd = [
            "python",
            SUBREGION_CAPSULE_TOOL,
            "-o",
            "Tmac_Capsule.bin",
            "-s",
            os.path.join(COLLATER_PATH, "TestCert.pem"),
            "-p",
            os.path.join(COLLATER_PATH, "TestSub.pub.pem"),
            "-t",
            os.path.join(COLLATER_PATH, "TestRoot.pub.pem"),
            os.path.join(JSON_PATH,"tsn_mac_address.json"),
        ]
        subprocess.check_call(cmd)
        os.remove("Tmac_Capsule.bin")

    def test_generate_capsule_without_keys(self):
        cmd = [
            "python",
            SUBREGION_CAPSULE_TOOL,
            "-o",
            "Tmac_Capsule.bin",
            os.path.join(JSON_PATH, "tsn_mac_address.json"),
        ]
        subprocess.check_call(cmd)
        os.remove("Tmac_Capsule.bin")

    def test_generate_capsule_with_missing_keys(self):
        cmd = [
            "python",
            SUBREGION_CAPSULE_TOOL,
            "-o",
            "Tmac_Capsule.bin",
            "-s",
            os.path.join(COLLATER_PATH, "TestCert.pem"),
            "-p",
            os.path.join(COLLATER_PATH, "TestSub.pub.pem"),
            os.path.join(JSON_PATH, "tsn_mac_address.json"),
        ]
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.check_call(cmd)
        self.assertEqual(cm.exception.returncode, 2)

    def test_generate_capsule_with_multi_ffs_files(self):

        cmd = [
            "python",
            SUBREGION_CAPSULE_TOOL,
            "-o",
            "PseCapsule.bin",
            "-s",
            os.path.join(COLLATER_PATH, "TestCert.pem"),
            "-p",
            os.path.join(COLLATER_PATH, "TestSub.pub.pem"),
            "-t",
            os.path.join(COLLATER_PATH, "TestRoot.pub.pem"),
            os.path.join(IMAGES_PATH,"pse.json"),
        ]
        subprocess.check_call(cmd)
        os.remove("PseCapsule.bin")


def cleanup():
    print("Cleaning up generated files ...")
    to_remove = []
    to_remove.extend(glob.glob("tmp.*", recursive=True))

    for f in to_remove:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    unittest.main()
