"""Test core functionality and error handling

   TestFunctionality - test the general functionality of the tool
   TestErrorCases - test the error cases.
   TestReplaceSubRegions - test for replacing subregions
   TestReplaceGop - test replacing of the Graphic output Protocal regions
   TestExceptions - force exception code to execute
"""

import os
import sys
import argparse
import unittest
import pytest
import subprocess
import filecmp
import shutil
import platform
import glob

sys.path.insert(0, "..")
from common.tools_path import TOOLS_DIR, GENFV, GENFFS, GENSEC, FMMT, LZCOMPRESS, RSA_HELPER, FMMT_CFG

SIIPSTITCH = os.path.join("scripts", "siip_stitch.py")
IMAGES_PATH = os.path.join("tests", "images")


class TestFunctionality(unittest.TestCase):
    """Test general functionality of SIIP Stitch Tool"""

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_help(self):
        cmd = ['python', SIIPSTITCH, '-h']
        subprocess.check_call(cmd)

    def test_version(self):
        cmd = ['python', SIIPSTITCH, '-v']
        subprocess.check_call(cmd)

    def test_replace_pse_using_default(self):  #no output file given
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_EDK_13M_EDK_1352_00_D_Simics.bin'),
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp(os.path.join(IMAGES_PATH, 'rom_pse.bin'), 'BIOS_OUT.bin'))

    def test_replace_pse_give_outputfile(self):  #output file given
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_EDK_13M_EDK_1352_00_D_Simics.bin'),
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse', '-o', 'IFWI.bin']
        subprocess.check_call(cmd)


class TestErrorCases(unittest.TestCase):
    """Test error cases of siipstitch script"""

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.exists('rename'):
            os.rename('rename', TOOLS_DIR)
        cleanup()

    def test_invalid_ip(self):  # invalid ipname
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                     os.path.join(IMAGES_PATH,'PseFw.bin'), '-ip', 'ose']
        try:
            results=subprocess.check_call(cmd)
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

    def test_for_bad_inputfiles(self):
        no_file = b"No such file or directory"
        file_empty = b"file is empty"
        file_large = b"file exceeds the size of the BIOS/IFWI"

        # Bios input file does not exists
        cmd = ['python', SIIPSTITCH, 'non_exist_file.bin',
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse']
        results = subprocess.run(cmd, capture_output=True)
        assert no_file in results.stderr

        # ip input file does not exists
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.BIN'),
                                     os.path.join(IMAGES_PATH, 'ose.bin'),
                                     '-ip', 'pse']
        results = subprocess.run(cmd, capture_output=True)
        assert no_file in results.stderr

        # BIOS input file is blank
        open('empty.bin', 'a').close()
        cmd = ['python', SIIPSTITCH, 'empty.bin',
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse']
        results = subprocess.run(cmd, capture_output=True)
        assert file_empty in results.stdout

        # IP input file is blank
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.BIN'),
                                     'empty.bin',
                                     '-ip', 'pse']
        results = subprocess.run(cmd, capture_output=True)
        assert file_empty in results.stdout

        # IP input file is too large
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                     '-ip', 'pse']
        results = subprocess.run(cmd, capture_output=True)
        assert file_large in results.stdout

    def test_inputfile_w_incorrect_format(self):  #BIOS input file is not in correct format
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_BadFormat.bin'),
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse']

        results=subprocess.run(cmd, capture_output=True)
        assert b"FMMT.exe timed out" in results.stdout

    def test_no_fv_found(self):  #  Firmware volume not found in the file
        with open('tmp.dummy.bin', 'wb') as fd:
            fd.write(b'\xab' * 128)
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                                 'tmp.dummy.bin',
                                                 '-ip', 'pse']

        results = subprocess.run(cmd, capture_output=True)
        assert b"Could not find file" in results.stdout

    def test_missing_key(self):
        """Missing priviate key"""

        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                     os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                     '-ip', 'vbt']
        try:
            subprocess.check_call(cmd)
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

    def test_large_privkey(self):
       """Verifies that large key file will genarate an error"""

       with open('large_key.pem', 'wb') as f:
           f.write(bytearray(2048+1))

       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                    os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                    '-ip', 'vbt',
                                    '-k', 'large_key.pem']

       results=subprocess.run(cmd, capture_output=True)
       assert b"the key file size must be greater than 0 and less than 2k!" in results.stderr

    def test_empty_privkey(self):
       """Verifies that empty key file will genarate an error"""

       with open('empty_key.pem', 'wb') as f:
           pass

       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                    os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                    '-ip', 'vbt',
                                    '-k', 'empty_key.pem']

       results=subprocess.run(cmd, capture_output=True)
       assert b"the key file size must be greater than 0 and less than 2k!" in results.stderr
       os.remove('empty_key.pem')

    def test_non_privkey(self):
       """Verifies that non rsa key file will genarate an error"""

       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                    os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                    '-ip', 'vbt',
                                    '-k', os.path.join(IMAGES_PATH, 'nonprivkey.pem')]

       results=subprocess.run(cmd, capture_output=True)
       assert b"is not an RSA priviate key" in results.stderr

    def test_privkey_not_exist(self):
       """Verifies that non rsa key file will genarate an error"""

       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS_old.bin'),
                                    os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                    '-ip', 'vbt',
                                    '-k', os.path.join(IMAGES_PATH, 'priv_key2.pem')]

       results=subprocess.run(cmd, capture_output=True)
       assert b"does not exist" in results.stderr

    def test_missing_tools(self):
        """Verify script report errors if any thirdparty tool is missing"""

        os.rename(TOOLS_DIR, 'rename')
        for f in (FMMT, GENFV, GENFFS, GENSEC, LZCOMPRESS, RSA_HELPER, FMMT_CFG):
            cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                     os.path.join(IMAGES_PATH, 'PseFw.bin'),
                                     '-ip', 'pse']
            results = subprocess.run(cmd, capture_output=True)
            assert b"Thirdparty tool not found" in results.stderr


class TestReplaceSubRegions(unittest.TestCase):
    """ Test replacement of subregions"""

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_load_json_to_stitch(self):
        JSON_FILES = {
            "tsn": "tsn_config.json",
            "tsnip": "tsn_ip_config.json",
            "tmac": "tsn_mac_address.json",
        }
        for k, v in JSON_FILES.items():
            cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                         os.path.join('scripts', 'Examples', v),
                                         '-o', 'tmp.{}.bin'.format(k),
                                         '-ip', k]
            subprocess.check_call(cmd)

    def test_oob_with_testkey(self):
        shutil.copy(os.path.join(IMAGES_PATH,'privkey.pem'), 'telit.pem')
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                         os.path.join('scripts', 'Examples', 'oob_manageability.json'),
                                         '-o', 'tmp.oob.bin',
                                         '-ip', 'oob']
        subprocess.check_call(cmd)

    def test_replace_TsnMacAdr_using_default(self):  # tmac
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                     os.path.join(IMAGES_PATH, 'tsn_mac_sub_region.bin'),
                                     '-ip', 'tmac']
        subprocess.check_call(cmd)

    def test_replace_ptmac_using_default(self):  # ptmac
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                     os.path.join(IMAGES_PATH, 'tsn_config_sub_region.bin'),
                                     '-ip', 'tsn']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'EHL_v1322.tsn_updated.bin')))

    def test_replace_oob_using_default(self):  # oob
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                     os.path.join(IMAGES_PATH, 'oob_sub_region.bin'),
                                     '-ip', 'oob']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'EHL_v1322.oob_updated.bin')))

    def test_replace_tsnip_using_default(self):  # tsn_ip
        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                     os.path.join(IMAGES_PATH, 'tsn_ip_sub_region.bin'), '-ip', 'tsnip']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'EHL_v1322.tsnip_updated.bin')))

    def test_replace_tcc_using_default(self):  # tcc
        with open('tmp.dummy.bin', 'wb') as fd:
            fd.write(b'\xcd' * 128)

        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'EHL_v1322.bin'),
                                     'tmp.dummy.bin',
                                     '-ip', 'tcc']
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists('BIOS_OUT.bin'))


class TestReplaceGOP(unittest.TestCase):
    """ Test replacement of the GOP"""

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_replace_gopvbt(self):
       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                    os.path.join(IMAGES_PATH, 'Vbt.bin'),
                                    '-ip', 'vbt',
                                    '-k', os.path.join(IMAGES_PATH, 'privkey.pem')]
       subprocess.check_call(cmd)
       self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'rom_vbt.bin')))

    def test_replace_gopdriver(self):
       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                    os.path.join(IMAGES_PATH, 'IntelGopDriver.efi'),
                                    '-ip', 'gop',
                                    '-k', os.path.join(IMAGES_PATH, 'privkey.pem')]
       subprocess.check_call(cmd)
       self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'rom_gop.bin')))

    def test_replace_peigraphics(self):
       cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                    os.path.join(IMAGES_PATH, 'IntelGraphicsPeim.efi'),
                                    '-ip', 'gfxpeim',
                                    '-k', os.path.join(IMAGES_PATH, 'privkey.pem')]
       subprocess.check_call(cmd)

    def test_key_with_different_name(self):
        """Different name for priviate key"""

        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                     os.path.join(IMAGES_PATH, 'IntelGopDriver.efi'),
                                     '-ip', 'gop',
                                     '-k', os.path.join(IMAGES_PATH, 'priv_key.pem')]

        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'rom_gop.bin')))

class TestFilesAbsPath(unittest.TestCase): # files with absolute path
    TMP_DIR = os.path.join(os.getcwd(), "scripts", "tmp")

    def setUp(self):
        #TMP_Dir = os.path.join("scripts", "tmp")
        os.mkdir(TestFilesAbsPath.TMP_DIR, mode=0o666)
        shutil.copy(os.path.join(IMAGES_PATH,'privkey.pem'),TestFilesAbsPath.TMP_DIR)
        shutil.copy(os.path.join(IMAGES_PATH,'IntelGopDriver.efi'),TestFilesAbsPath.TMP_DIR)
        pass

    def tearDown(self):
        #TMP_Dir = os.path.join("scripts", "tmp")
        shutil.rmtree(TestFilesAbsPath.TMP_DIR)
        cleanup()

    def test_keyfile_outside_dir(self): #Key with a direct path

        cmd = ['python', SIIPSTITCH, os.path.join(IMAGES_PATH, 'BIOS.bin'),
                                     os.path.join(TestFilesAbsPath.TMP_DIR, 'IntelGopDriver.efi'),
                                    '-ip', 'gop',
                                    '-k', os.path.join(TestFilesAbsPath.TMP_DIR, 'privkey.pem')]
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', os.path.join(IMAGES_PATH, 'rom_gop.bin')))


def cleanup():
    print("Cleaning up generated files ...")
    to_remove = [
        'IFWI.bin',
        'BIOS_OUT.bin',
        'empty.bin',
        'large_key.pem',
        'temp.txt',
        os.path.join(TOOLS_DIR, 'privkey.pem'),
    ]
    to_remove.extend(glob.glob('tmp.*', recursive=True))

    for f in to_remove:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

