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
##   MyTestSet1 - test the general functionality of the tool
##   MyTestSet2 - test when the input files are in different directory than the workign directory
##   MyTestSet3 - test the error cases. Formating issues of the guids and not having correct name
##                of key file.
##   MyTestSet4 - test for replacing other subregions
##
## License: {license}
## Version: 0.6.0
## Status: Intial Development
#################################################################################################
import os
import sys
import unittest
import subprocess
import filecmp
import shutil
import platform



SIIPSTITCH=os.path.join('..', 'SIIPStitch.py')

###############################################################################################################################
##MyTestSet1:
## Test general functionality of SIIPStitch Tool
##
###############################################################################################################################
class MyTestSet1(unittest.TestCase):
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
        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'OseFw.bin','-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.BIN'), 
                                    os.path.join('tests', 'BIOS2.bin')))
        
    def test_replace_oseFw_give_outputfile(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin', 'OseFw.bin','-ip', 'pse', 
               '-o', 'IFWI.bin']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'IFWI.bin')))
        os.remove(os.path.join('tests', 'IFWI.BIN'))

###############################################################################################################################
##MyTestSet2:
## Test finding input files outside of the working directory        
##
###############################################################################################################################
class MyTestSet2(unittest.TestCase):
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
        pass

    def test_bios_in_different_dir(self):  #Bios image not in current working directory
        shutil.copy(os.path.join('tests', 'BIOS.bin'), os.path.join('tests', 'TMPDIR'))
        INPUT = os.path.join('TMPDIR', 'BIOS.bin')
        
        cmd = ['python', SIIPSTITCH, INPUT, 'OseFw.bin', '-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'), 
                                    os.path.join('tests', 'BIOS2.bin')))
        
    def test_pseFw_in_different_dir(self):  #Ose Firmeware not in current working directory
        shutil.copy(os.path.join('tests', 'OseFw.bin'), os.path.join('tests', 'TMPDIR'))
        REPLACE =os.path.join('TMPDIR', 'OseFw.bin')

        cmd = ['python', SIIPSTITCH, 'BIOS.bin', REPLACE, '-ip', 'pse']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(filecmp.cmp(os.path.join('tests', 'BIOS_OUT.bin'), 
                                    os.path.join('tests', 'BIOS2.bin')))
        
###############################################################################################################################
##MyTestSet3:
## Test error cases of SIIPSTITCH Tool        
##
###############################################################################################################################
class MyTestSet3(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self) :  
        cleanup()
        pass
            
    def test_invalid_ip(self):  #invalid ipname
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin', '-ip', 'ose']
        try:
            results=subprocess.check_call(cmd, cwd='tests')
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass
    
    def test_bios_file_do_not_exist(self):  #Bios input file does not exists
        cmd = ['python', SIIPSTITCH, 'SIIP.bin', 'OseFw.bin', '-ip', 'pse']

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
        cmd = ['python', SIIPSTITCH, 'BIOS_NUL.BIN', 'OseFw.bin', '-ip', 'pse']
        
        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'file is empty' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipStitch')
            
    def test_ip_file_is_empty(self):  #BIOS input file is blank
        cmd = ['python', SIIPSTITCH, 'BIOS.BIN', 'OseFw_NUL.bin', '-ip', 'pse']
        
        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'file is empty' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipStitch')
            
    def test_inputfile_w_incorrect_format(self):  #BIOS input file is not in correct format
        cmd = ['python', SIIPSTITCH, 'BIOS_badFormat.bin', 'OseFw.bin', '-ip', 'pse']
        
        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'FMMT.exe timed out' in results:
               pass
           else:
               self.fail('Wrong Error has occured')
        except:
            self.fail('Error should have been handle by siipStitch')

    def test_no_fv_found(self):  #Firmware volume not found in the file
        cmd = ['python', SIIPSTITCH,'BIOS.bin', 'dummy_2.bin', '-ip', 'oob']

        try:
           results=subprocess.check_output(cmd, cwd='tests')
           if b'No Firmware volume found' in results:
              pass
           else:
              self.fail('\nNot correct error')
        except:
           self.fail('\nSIIPStitch should have handled error')
           
           

###############################################################################################################################
##MyTestSet4:
## Test replacement of the subregions
##
###############################################################################################################################
class MyTestSet4(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        cleanup()

    def test_replace_TsnMacAdr_using_default(self):  # tmac
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom', 
               'TsnMacAddr_test.bin', '-ip', 'tmac']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'BIOS_OUT.bin')))

    def test_replace_ptmac_using_default(self):  # ptmac
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom',
                         'dummy_2.bin', '-ip', 'ptmac']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'BIOS_OUT.bin')))

    def test_replace_oob_using_default(self):  # oob
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom',
                                     'dummy_2.bin','-ip', 'oob']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'BIOS_OUT.bin')))

    def test_replace_tcc_using_default(self):  # tcc
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom',
                                     'dummy_2.bin', '-ip', 'tcc']
        subprocess.check_call(cmd, cwd='tests')
        self.assertTrue(os.path.exists(os.path.join('tests', 'BIOS_OUT.bin')))


def cleanup():
    try:
        os.remove(os.path.join('tests', 'BIOS_OUT.BIN'))
    except: 
        pass

