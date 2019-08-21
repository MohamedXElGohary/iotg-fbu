###########################################################
##
##
##
## SIIPStitchUnitTest
## Testing the SIIP Stitching Tool.
#################################################################################################
##Copyright (c) 2019, Intel Corporation. All rights reserved.<BR>
#
# This program and the accompanying materials are licensed and made available under
# the terms and conditions of the
##################################################
## Name SIIPStitchUnitTest.py
## Author: Kimberly Barnes
##
##
##  File Description:
##   Test functionality and error testing of the tool.
##
##   TestFunctionality - test the general functionality of the tool
##   TestFilesOutsideDir - test finding input files outside of the working directory
##   TestErrorCases - test the error cases. 
##   TestReplaceSubRegions - test for replacing subregions
##   TestReplaceGop - test replacing of the Graphic output Protocal regions
##   TestExceptions - force exception code to execute
##
## License: {license}
## Version: 0.6.0
## Status: Intial Development
#################################################################################################
import os
import sys
import argparse
import unittest
import pytest
import subprocess
import filecmp
import shutil
import platform



SIIPSTITCH=os.path.join('..', 'siipstitch', 'siip_stitch.py')


class TestFunctionality(unittest.TestCase):
    """Test general functionality of SIIP Stitch Tool"""

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()
        pass

    def test_help(self):
        cmd = ['python', SIIPSTITCH, '-h']
        subprocess.check_call(cmd, cwd='tests')

    def test_version(self): 
        cmd = ['python', SIIPSTITCH, '-v']
        subprocess.check_call(cmd, cwd='tests')

    def test_replace_pseFw_using_default(self):  #no output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'PseFw.bin','-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.BIN'), 
                                    os.path.join('tests', 'BIOS2.bin')))

    def test_replace_oseFw_give_outputfile(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'PseFw.bin','-ip', 'pse', 
               '-o', 'IFWI.bin']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'IFWI.bin')))
        os.remove(os.path.join('tests', 'IFWI.BIN'))

class TestFilesOutsideDir(unittest.TestCase):
    """Test finding input files outside of the working directory"""
    @classmethod
    def setUpClass(cls):
         os.mkdir(os.path.join('tests', 'TMPDIR'))

    @classmethod
    def tearDownClass(cls):  
        shutil.rmtree(os.path.join('tests', 'TMPDIR'))

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_bios_ip_in_different_dirs(self):  #Bios image not in current working directory
        shutil.copy(os.path.join('tests', 'BIOS.bin'), os.path.join('tests', 'TMPDIR'))
        INPUT = os.path.join('TMPDIR', 'BIOS.bin')


        os.mkdir(os.path.join('tests', 'TMPDIR', 'TMPDIR2'))

        shutil.copy(os.path.join('tests', 'PseFw.bin'), os.path.join('tests','TMPDIR', 'TMPDIR2'))
        INPUT2 = os.path.join('TMPDIR', 'TMPDIR2', 'PseFw.bin' )

        cmd = ['python', SIIPSTITCH, INPUT, INPUT2, '-ip', 'pse']

        subprocess.check_call(cmd, cwd='tests')

        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'BIOS2.bin')))

    def test_bios_in_different_dir(self):  #Bios image not in current working directory
        shutil.copy(os.path.join('tests', 'BIOS.bin'), os.path.join('tests', 'TMPDIR'))
        INPUT = os.path.join('TMPDIR', 'BIOS.bin')

        cmd = ['python', SIIPSTITCH, INPUT, 'PseFw.bin', '-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'BIOS2.bin')))

    def test_pseFw_in_different_dir(self):  #Ose Firmeware not in current working directory
        shutil.copy(os.path.join('tests', 'PseFw.bin'), os.path.join('tests', 'TMPDIR'))
        REPLACE =os.path.join('TMPDIR', 'PseFw.bin')

        cmd = ['python', SIIPSTITCH, 'BIOS.bin', REPLACE, '-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'BIOS2.bin')))

    def test_key_in_different_dir(self):  #private key not in current working directory
        shutil.copy(os.path.join('tests', 'priv_key.pem'), os.path.join('tests', 'TMPDIR'))
        REPLACE =os.path.join('TMPDIR', 'priv_key.pem')


        cmd = ['python', SIIPSTITCH, 'BIOS_old.bin', 'IntelGopDriver.efi', '-k', REPLACE, '-ip', 'gop']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests','rom_drvr.bin')))


class TestErrorCases(unittest.TestCase):
    """Test error cases of siipstitch script"""

    def setUp(self):
        pass

    def tearDown(self) :
        cleanup()
        pass

    def test_invalid_ip(self):  #invalid ipname
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','PseFw.bin', '-ip', 'ose']
        try:
            results=subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

    def test_bios_file_do_not_exist(self):  #Bios input file does not exists
        cmd = ['python', SIIPSTITCH, 'SIIP.bin', 'PseFw.bin', '-ip', 'pse']

        try:
            results=subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError as Error:
            pass

    def test_ip_file_does_not_exist(self):  #ip input file does not exists
        cmd = ['python', SIIPSTITCH, 'BIOS.BIN', 'ose.bin', '-ip', 'pse']

        try:
            results=subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

    def test_bios_file_is_empty(self):  #BIOS input file is blank
        cmd = ['python', SIIPSTITCH, 'BIOS_NUL.BIN', 'PseFw.bin', '-ip', 'pse']

        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'file is empty' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipstitch')

    def test_ip_file_is_empty(self):  #BIOS input file is blank
        cmd = ['python', SIIPSTITCH, 'BIOS.BIN', 'OseFw_NUL.bin', '-ip', 'pse']

        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'file is empty' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipstitch')

    def test_inputfile_w_incorrect_format(self):  #BIOS input file is not in correct format
        cmd = ['python', SIIPSTITCH, 'BIOS_badFormat.bin', 'PseFw.bin', '-ip', 'pse']

        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'FMMT.exe timed out' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipstitch')

    def test_no_fv_found(self):  #Firmware volume not found in the file
        cmd = ['python', SIIPSTITCH,'BIOS_old.bin', 'dummy_2.bin', '-ip', 'oob']
        
        results=subprocess.run(cmd, cwd='tests', capture_output=True)
        assert b"Could not find file" in results.stdout

    def test_extra_inputfile(self):  #Replacement does not require 2 input files
        cmd = ['python', SIIPSTITCH, 'BIOS_old.bin', 'PseFw.bin', 'IntelGraphicsPeim.depex', '-ip', 'pse']

        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'IPNAME_IN2 input file is not required' in results:
              pass
           else:
              self.fail('\nNot correct error')
        except:
           self.fail('\nSIIPStitch should have handled error')

    def test_missing_key(self):
        """Missing priviate key"""

        cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','Vbt.bin','-ip', 'vbt']
        try:
            subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

    def test_missing_inputfile(self):
       """Replacement requires 2 input files"""

       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','IntelGraphicsPeim.efi', '-k', 'privkey.pem', '-ip', 'pei']

       try:
           results=subprocess.check_call(cmd, cwd='tests')
           self.fail('a call process eror should have occured')
       except subprocess.CalledProcessError:
           pass

    def test_large_privkey(self):
       """Verifies that large key file will genarate an error"""

       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin', 'Vbt.bin', '-ip', 'vbt', '-k', 'privkey2.pem']

       results=subprocess.run(cmd, cwd='tests', capture_output=True)
       assert b"is larger than 2KB!" in results.stderr
    
    def test_non_privkey(self):
       """Verifies that non rsa key file will genarate an error"""

       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin', 'Vbt.bin', '-ip', 'vbt', '-k', 'nonprivkey.pem']

       results=subprocess.run(cmd, cwd='tests', capture_output=True)
       assert b"is not an RSA priviate key" in results.stderr

class TestReplaceSubRegions(unittest.TestCase):
    """ Test replacement of subregions"""
    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_replace_TsnMacAdr_using_default(self):  # tmac
        cmd = ['python', SIIPSTITCH, 'EHL_v1322.bin',
               'tsn_mac_sub_region.bin', '-ip', 'tmac']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'EHL_v1322.tmac_updated.bin')))

    def test_replace_ptmac_using_default(self):  # ptmac
        cmd = ['python', SIIPSTITCH, 'EHL_v1322.bin',
                         'tsn_config_sub_region.bin', '-ip', 'tsn']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'EHL_v1322.tsn_updated.bin')))

    def test_replace_oob_using_default(self):  # oob
        cmd = ['python', SIIPSTITCH, 'EHL_v1322.bin',
                                     'oob_sub_region.bin','-ip', 'oob']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'EHL_v1322.oob_updated.bin')))

    def test_replace_tsnip_using_default(self):  # tsn_ip
        cmd = ['python', SIIPSTITCH, 'EHL_v1322.bin',
                                     'tsn_ip_sub_region.bin', '-ip', 'tsnip']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'EHL_v1322.tsnip_updated.bin')))

    def test_replace_tcc_using_default(self):  # tcc
        cmd = ['python', SIIPSTITCH, 'EHL_v1322.bin',
                                     'dummy_2.bin', '-ip', 'tcc']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'BIOS_OUT.bin')))


class TestReplaceGOP(unittest.TestCase):
    """ Test replacement of the GOP"""

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_replace_gopvbt(self):
       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','Vbt.bin','-ip', 'vbt', '-k', 'privkey.pem']
       subprocess.check_call(cmd, cwd='tests')
       self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                   os.path.join('tests', 'rom_vbt.bin')))

    def test_replace_gopdriver(self):
       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','IntelGopDriver.efi','-ip', 'gop', '-k', 'privkey.pem']
       subprocess.check_call(cmd, cwd='tests')
       self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                   os.path.join('tests', 'rom_drvr.bin')))

    def test_replace_peigraphics(self):
       cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','IntelGraphicsPeim.efi', 'IntelGraphicsPeim.depex', '-ip', 
              'pei', '-k', 'privkey.pem']
       subprocess.check_call(cmd, cwd='tests')
       self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                   os.path.join('tests', 'rom_pei.bin')))
    
    def test_key_with_different_name(self):
        """Different name for priviate key"""

        cmd = ['python', SIIPSTITCH, 'BIOS_old.bin','IntelGraphicsPeim.efi', 'IntelGraphicsPeim.depex', '-ip', 'pei', '-k', 'priv_key.pem']

        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'),
                                    os.path.join('tests', 'rom_pei.bin')))


class TestExceptions(unittest.TestCase):
    """Force Exception code to execute"""

    tool_path = os.path.join('siipsupport','Bin', 'Win32')

    @classmethod
    def setUpClass(cls):
         # back up the siipsupport directory
         shutil.copytree(os.path.join('siipsupport', 'Bin'),os.path.join('siipSupport2', 'Bin'))

    @classmethod
    def tearDownClass(cls):  

        shutil.rmtree(os.path.join('siipsupport','Bin'),ignore_errors=True)

        #return to orignal folder
        shutil.move(os.path.join('siipSupport2','Bin','Win32'),
                    os.path.join(TestExceptions.tool_path)
                   )
        shutil.rmtree(os.path.join('siipSupport2'),ignore_errors=True)

    def setUp(self):
        pass

    def tearDown(self):
        wrkdir = os.path.join('tests', 'SIIP_wrkdir')

        if os.path.exists(wrkdir):
             shutil.rmtree(wrkdir)
        pass

    def test_exception_missing_genFfs(self):  #missing 3rd party files
        """ Missing third party tool GenFfs"""

        os.rename(os.path.join(TestExceptions.tool_path, 'GenFfs.exe'), \
                  os.path.join(TestExceptions.tool_path, 'GenFfs2.exe'))

        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'PseFw.bin', '-ip', 'pse']
        try:
            subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

        os.rename(os.path.join(TestExceptions.tool_path, 'GenFfs2.exe'), \
                      os.path.join(TestExceptions.tool_path, 'GenFfs.exe'))

    def test_exception_missing_GenFv(self):  
        """ Missing third party tool GenFv"""

        os.rename(os.path.join(TestExceptions.tool_path, 'GenFv.exe'), \
                  os.path.join(TestExceptions.tool_path, 'GenFv2.exe'))

        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'PseFw.bin', '-ip', 'pse']
        try:
            subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

        os.rename(os.path.join(TestExceptions.tool_path, 'GenFv2.exe'), \
                      os.path.join(TestExceptions.tool_path, 'GenFv.exe'))

def cleanup():
    try:
        os.remove(os.path.join('tests', 'BIOS_OUT.BIN'))
    except:
        pass

