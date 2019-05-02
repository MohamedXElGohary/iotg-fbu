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

SIIPSTITCH=os.path.join(os.path.dirname(__file__), 'SIIPStitch.py')
BASETOOLS =os.path.join(os.path.dirname(__file__), 'BaseTools')
TMPDIR=os.path.join(os.path.dirname(__file__), 'TMPDIR')
BASETOOLSDIR=os.path.join(os.getcwd(),'BASETOOLS')

def setUpModule():
    #copy basetools directory in test directory
    shutil.copytree(BASETOOLS, BASETOOLSDIR, symlinks=False, ignore=None)

def tearDownModule():
    shutil.rmtree(BASETOOLSDIR)
 
###############################################################################################################################
##MyTestSet1:
## Test general functionality of SIIPStitch Tool
##
###############################################################################################################################
class MyTestSet1(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        try:
            os.remove('BIOS_OUT.BIN')
        except OSError:
            pass

        dirs = [os.getcwd(), 'SIIP_wrkdir']

        try:
            cleanup(dirs)
        except OSError:
            pass

    def test_help(self):
        cmd = ['python', SIIPSTITCH, '-h']
        subprocess.check_call(cmd)

    def test_version(self): 
        cmd = ['python', SIIPSTITCH, '-v']
        subprocess.check_call(cmd)

    def test_replace_pseFw_using_default(self):  #no output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', 'privkey.pem', '-ip', 'pse']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.BIN', 'BIOS2.bin'))
        
    def test_replace_pseFw_with_ipname_allCaps(self):  #no output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', 'privkey.pem', '-ip', 'PSE']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.BIN', 'BIOS2.bin'))

    def test_replace_oseFw_give_outputfile(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', 'privkey.pem', '-ip', 'pse', '-o', 'IFWI.bin']
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists('IFWI.bin'))
        os.remove('IFWI.bin')

###############################################################################################################################
##MyTestSet2:
## Test finding input files outside of the working directory        
##
###############################################################################################################################
class MyTestSet2(unittest.TestCase):

    def setUp(self):
        os.mkdir(TMPDIR)
        pass

    def tearDown(self):

        try:
            os.remove('BIOS_OUT.BIN')
        except OSError:
            pass

        dirs = [os.getcwd(), 'SIIP_wrkdir',TMPDIR]
        try:
            cleanup(dirs)
        except OSError:
            pass
                
    def test_keyfile_in_different_dir(self):  #key not in current working directory
        shutil.copy('privkey.pem',TMPDIR)
        KEY = os.path.join(TMPDIR,'privkey.pem')
       
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', KEY,'-ip', 'pse']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', 'BIOS2.bin'))
       
    def test_bios_in_different_dir(self):  #Bios image not in current working directory
        shutil.copy('BIOS.bin',TMPDIR)
        INPUT =os.path.join(TMPDIR,'BIOS.bin')
        
        cmd = ['python', SIIPSTITCH, INPUT,'OseFw.bin','-k', 'privkey.pem', '-ip', 'pse']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', 'BIOS2.bin'))
        
    def test_pseFw_in_different_dir(self):  #Ose Firmeware not in current working directory
        shutil.copy('OseFw.bin',TMPDIR)
        REPLACE =os.path.join(TMPDIR,'OseFw.bin')

        cmd = ['python', SIIPSTITCH, 'BIOS.bin', REPLACE,'-k', 'privkey.pem', '-ip', 'pse']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.bin', 'BIOS2.bin'))
        
###############################################################################################################################
##MyTestSet3:
## Test error cases of SIIPSTITCH Tool        
##
###############################################################################################################################
class MyTestSet3(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self) :  
        dirs = [os.getcwd(), 'SIIP_wrkdir']

        try:
            cleanup(dirs)
        except OSError:
            pass
            
    def test_invalid_ip(self):  #invalid ipname
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', 'privkey.pem', '-ip', 'ose']
        try:
            results=subprocess.check_call(cmd)
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass
    
    def test_key_wrong_name(self):  #Keyfile has wrong file name
        cmd = ['python', SIIPSTITCH, 'BIOS.bin','OseFw.bin','-k', 'privkey.perm', '-ip', 'pse']

        try:
            results=subprocess.check_call(cmd)
            self.fail('a call process eror should have occured')
        except subprocess.CalledProcessError:
            pass

###############################################################################################################################
##MyTestSet4:
## Test replacement of the subregions
##
###############################################################################################################################
class MyTestSet4(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):

        try:
            os.remove('BIOS_OUT.BIN')
        except OSError:
            pass

        dirs = [os.getcwd(), 'SIIP_wrkdir']

        try:
            cleanup(dirs)
        except OSError:
            pass

    def test_replace_TsnMacAdr_using_default(self):  #no output file given
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom','TsnMacAddr_test.bin','-k', 'privkey.pem', '-ip', 'tmac']
        subprocess.check_call(cmd)
        self.assertTrue(filecmp.cmp('BIOS_OUT.BIN', 'tmac_updated.bin'))


    def test_replace_ptmac_using_default(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom','dummy_2.bin','-k', 'privkey.pem', '-ip', 'ptmac']
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists('BIOS_OUT.bin'))

    def test_replace_oob_using_default(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom','dummy_2.bin','-k', 'privkey.pem', '-ip', 'oob']
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists('BIOS_OUT.bin'))

    def test_replace_oob_using_default(self):  #output file given
        cmd = ['python', SIIPSTITCH, 'EHL_FSPWRAPPER_1172_00.rom','dummy_2.bin','-k', 'privkey.pem', '-ip', 'tcc']
        subprocess.check_call(cmd)
        self.assertTrue(os.path.exists('BIOS_OUT.bin'))

### use during the different clase tearDown to remove directories and files.
def cleanup(dirs):
    osSys = platform.system()

    #change directory
    try:
        os.chdir(dirs[0])  
    except OSError: 
        pass

    for dir in range(1, len(dirs)):
        # determine platform in order to use correct command for the OS

        if osSys == "Windows":
            cmd = ['rmdir', dirs[dir], '/s', '/q']
        else: # linux
            cmd  = ["rm","-fr",dirs[dir]]

        try:
            subprocess.check_call(cmd,shell=True)
        except subprocess.CalledProcessError as status:
            pass



         
if __name__ == '__main__':
    suite_loader = unittest.TestLoader()
    suite1 = suite_loader.loadTestsFromTestCase(MyTestSet1)
    suite2 = suite_loader.loadTestsFromTestCase(MyTestSet2)
    suite3 = suite_loader.loadTestsFromTestCase(MyTestSet3)
    suite4 = suite_loader.loadTestsFromTestCase(MyTestSet4)
    suite = unittest.TestSuite([suite1, suite2,suite3, suite4])
    runner = unittest.TextTestRunner()
    results = runner.run(suite)
