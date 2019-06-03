#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###################################################################################################
## SIIP Stitching Tool
## {The SIIP Stitching Tool replaces specified firmware sections in the
## current BIOS.bin file with the new version.}
###################################################################################################
#
# Copyright 2019 Intel Corporation
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice, this list of
#     conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice, this list of
#     conditions and the following disclaimer in the documentation and/or other materials provided
#     with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#################################################################################################


#################################################################################################
## Name SIIPStitch.py
## Author: Kimberly Barnes
##
##
##  File Description:
##
## License: {license}
## Version: 0.5.2
## Status: Intial Development
#################################################################################################
import os
import platform
import subprocess
import sys
import argparse
import shutil
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SIIPSupport import ToolsLoc as tdir



__version__ = '0.5.2'
################################################################################################
##
## Global Variables
##
################################################################################################

# excutables used to perform merging and replacing of PSE Firmware
PROG = ['GenSec', 'LzmaCompress', 'GenFfs', 'FMMT.exe']

#data dictionary of REGIONS that can be replaced
REGIONS = {
    #IP/Region : Fileguid
    'pse'  : ['EE4E5898-3914-4259-9D6E-DC7BD79403CF', 'EBA4A247-42C0-4C11-A167-A4058BC9D423'],
    'tmac' : [None, '12E29FB4-AA56-4172-B34E-DD5F4B440AA9'],
    'ptmac' : [None, '4FB7994D-D878-4BD1-8FE0-777B732D0A31'],
    'tcc' : [None, '7F6AD829-15E9-4FDE-9DD3-0548BB7F56F3'],
    'oob' : [None, '4DB2A373-C936-4544-AA6D-8A194AA9CA7F']
}

# options used to replace REGIONS
IP_OPTIONS = {
    # Region:[Options]
    'pse' : ['IntelOseFw', 'PROCESSING_REQUIRED', '1K', 'PI_NONE'],
    'tmac' : ['IntelTsnMacAddrFv', None, '1K', 'PI_NONE'],
    'ptmac' : ['IntelOseTsnMacConfig', None, '1K', 'PI_NONE'],
    'tcc' : ['IntelTccConfig', None, '1K', 'PI_NONE'],
    'oob' : ['IntelOob2Config', None, '1K', 'PI_NONE']
}

#################################################################################################
##
##  Display Utility Information
##
#################################################################################################

print('#########################################################################################')
print('Purpose of this utility is to replace the section in System BIOS ROM file with new section')
print('#########################################################################################')


if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

#################################################################################################
##
## Search for the firmware volume
##
#################################################################################################

def search_for_fv(inputfile, ipname, myenv, workdir):
    '''Search for the firmware volume.'''

    global IP_OPTIONS

    # use to find the name of the firmware in order to locate the firmware volume
    ip_filename = IP_OPTIONS.get(ipname)

    print("\nFinding the Firmware Volume")
    fwvol = None
    status = 0

    command = ['FMMT.exe', '-v', os.path.abspath(inputfile), '>', 'temp.txt']

    try:
        print(' '.join(command))
        subprocess.check_call(command, env=myenv, cwd=workdir, shell=True)
    except subprocess.CalledProcessError as status:
        print("\nError using FMMT.exe")
        return 1, fwvol

    # search FFS by name in firmware volumes
    fwvol_found = False
    fwvol_child = False
    with open(os.path.join(workdir, 'temp.txt'), 'r') as searchfile:
        for line in searchfile:
            m = re.match(r'(^FV\d+) :', line)
            if m:
                fwvol_found = True
                fw_vol = m.groups()[0]
                continue
            if fwvol_found:
                n = re.match(r'File "(%s)"' % ip_filename[0], line.lstrip())
                if n:
                    break;

    return status, fw_vol


###############################################################################################
##
## Create Commands for the merge and replace of firmware section
##
###############################################################################################
def create_commands(filename, ipname, fwvol):
    '''Create Commands for the merge and replace of firmware section.'''

    global PROG, REGIONS, IP_OPTIONS
    options = ['-s', '-n', '-o', '-e', '-g', '-r', '-t', '-a', '-i', '-c']
    tempfile = ['tempSect.sec', 'temp.raw', 'temp.cmps', 'temp.guided', 'temp.ffs']
    section_type = ['EFI_SECTION_USER_INTERFACE', 'EFI_SECTION_RAW', 'EFI_SECTION_GUID_DEFINED', \
                   'EFI_FV_FILETYPE_FREEFORM']
    guid_values = REGIONS.get(ipname)
    option_strings = IP_OPTIONS.get(ipname)
    cmds = []

    #GenSec.exe -s EFI_SECTION_USER_INTERFACE -n "IntelOseFw" -o IntelOseFw.sec
    cmd0 = [PROG[0], options[0], section_type[0], options[1], option_strings[0], \
           options[2], tempfile[0]]

    #GenSec.exe -s EFI_SECTION_RAW -c PI_STD -o IntelOseFw.raw OseFw.bin
    cmd1 = [PROG[0], options[0], section_type[1], options[9], option_strings[3], filename[1], \
           options[2], tempfile[1]]

    #GenSec.exe  IntelOseFw.raw IntelOseFw.sec -o IntelOseFw.raw
    cmd2 = [PROG[0], tempfile[1], tempfile[0], options[2], tempfile[1]]

    # add commands to cmd list
    cmds.extend([cmd0, cmd1, cmd2])

    #determine if compression will be used for firmware section
    if option_strings[1] is not None:
        num = 3
       #LZMAcompress -e IntelOseFw.raw -o IntelOseFw.tmp
        cmd3 = [PROG[1], options[3], tempfile[1], options[2], tempfile[2]]

        #GenSec -s EFI_SECTION_GUID_DEFINED -g EE4E5898-3914-4259-9D6E-DC7BD79403CF \
        #       -r PROCESSING_REQUIRED IntelOseFw.tmp -o OseFw.guided
        cmd4 = [PROG[0], options[0], section_type[2], options[4], guid_values[0], options[5], \
               option_strings[1], tempfile[2], options[2], tempfile[3]]
        #update cmds list with commands
        cmds.extend([cmd3, cmd4])
    else:
        num = 1 # Skips the files used for compression


    #GenFfs.exe -t EFI_FV_FILETYPE_FREEFORM -g EBA4A247-42C0-4C11-A167-A4058BC9D423 -a 1K
    #           -i OseFw.guided   -o IntelOseFw.ffs
    cmd5 = [PROG[2], options[6], section_type[3], options[4], guid_values[1], options[7], \
          option_strings[2], options[8], tempfile[num], options[2], tempfile[4]]

    #FMMT.exe -r BIOS.bin %FIRMWARE_VOLUME% IntelOseFw IntelOseFw.ffs BIOS_OUTPUT.bin
    cmd6 = [PROG[3], options[5], filename[0], fwvol, option_strings[0], tempfile[4], filename[2]]

    cmds.extend([cmd5, cmd6])

    return cmds

###############################################################################################
##
## Perform merge and replace of section using different excutables
##
###############################################################################################
def merge_and_replace(filename, guid_values, fwvol, env_vars, workdir):
    '''Perform merge and replace of section using different excutables.'''

    cmds = create_commands(filename, guid_values, fwvol)

    print("\nStarting merge and replacement of section")

   #Merging and Replacing
    for command in cmds:
        try:
            print(' '.join(command))
            subprocess.check_call(command, env=env_vars, cwd=workdir, shell=True)
        except subprocess.CalledProcessError as status:
            print("\nError executing {}".format(command[0]))
            print("\nStatus Message: {}".format(status))
            return 1

    return 0

##################################################################################################
##
## Remove files from directory
##
##################################################################################################
def cleanup(wk_dir):
    '''Remove files from directory.'''

    os_sys = platform.system()

    #change directory
    try:
        os.chdir(wk_dir[0])
    except OSError as error:
        sys.exit("\nUnable to Change Directory : {}\n{}".format(wk_dir[0], error))
    except:
        sys.exit("\nUnexpected error:{}".format(sys.exc_info()))

   # determine platform in order to use correct command for the OS
    if os_sys == "Windows":
        cmd = ['rmdir', wk_dir[1], '/s', '/q']
    else: # linux
        cmd = ["rm", "-fr", wk_dir[1]]

    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as status:
        sys.exit("\nError: excuting {},\n{}".format(cmd, status))

##################################################################################################
##
##  Determine platform and set working path and Engine Development Kit path
##
##################################################################################################

def set_environment_vars():
    '''Determine platform and set working path and Engine Development Kit path.'''
    os_sys = platform.system()
    progs = [ 'GenSec',
              'LzmaCompress',
              'GenFfs',
              'FMMT.exe',
              'FmmtConf.ini',
              'StripSignature.py',
            ]

   # Determine operating system that script is running

    if os_sys == "Linux" or os_sys == "linux2":
        # linux
        os_dir = "BinWrappers/PosixLike"
        cmd = 'which'
        print("Running on Linux")
    elif os_sys == "Windows":
      # windows
        os_dir = tdir.TOOLSWINDIR
        cmd = 'where'
        print(" Running on Windows")
    else:
        sys.exit("\n{},is not supported".format(os_sys))

   # set up enviroment variables
    path = os.environ.get("PATH")
    myenv = os.environ.copy()
    my_path = os.getcwd()

   # path to Base Tools
    edk_tools_path = os.path.join(os.sep, my_path, tdir.TOOLSDIR)
    edk_tools_bin = os.path.join(os.sep, edk_tools_path, os_dir)
    myenv["PATH"] = edk_tools_bin + ';'  + path

    #redirect output
    dev_null = open(os.devnull, 'w')

    for  base_tool in progs:
        command = [cmd, base_tool]

        try:
            # check to see if the required tools are installed
            subprocess.check_call(command, stdout=dev_null, env=myenv)
        except subprocess.CalledProcessError:
            sys.exit("\nError base_tool is not located: {}".format(base_tool))

    return myenv

##################################################################################################
##
## 'Type' for argparse
##  Verify that file does not exist
##
##################################################################################################
def file_not_exist(file):
    '''Verify that file does not exist.'''

    if os.path.isfile(file):
        raise argparse.ArgumentTypeError("{} exist!".format(file))
    return file

##################################################################################################
##
## 'Type' for argparse
##  Check if file exist
##
##################################################################################################
def file_exist(file):
    ''' Check if file exist.'''
    if not os.path.isfile(file):
        raise argparse.ArgumentTypeError("{} does not exist!".format(file))
    return file


##################################################################################################
##
## Parsing and validating input arguments
##
##################################################################################################

def parse_cmdline():
    ''' Parsing and validating input arguments.'''

    # initiate the parser
    parser = argparse.ArgumentParser(prog='SIIPStitch')

    parser.add_argument("IFWI_IN", type=argparse.FileType('rb+'), help="Input BIOS Binary file \
                       (Ex: IFWI.bin) to be updated with the given input IP firmware")
    parser.add_argument("IPNAME_IN", type=argparse.FileType('rb'), help="Input IP firmware \
                       Binary file (Ex: oseFw.Bin) to be replaced in the IFWI.bin")
    parser.add_argument("-ip", "--ipname", help="The name of the IP in the IFWI_IN \
                       file to be replaced. This is required.", metavar="ipname", required=True, choices=list(REGIONS.keys()))
    parser.add_argument("-v", "--version", help="Shows the current version of the Bio Stitching \
                       Tool", action="version", version="%(PROG)s {version}".\
                       format(version=__version__))
    parser.add_argument("-o", "--outputfile", dest="OUTPUT_FILE", type=file_not_exist,\
                       help="IFWI binary file with the IP replaced with the IPNAME_IN",\
                       metavar="FileName", default='BIOS_OUT.bin')

    # storing received  arguments
    args = parser.parse_args()

    return args


def copy_file(files, new_dir):
    '''Move file to directory.'''

    status = 0

    for  file in files:
        try:
            shutil.copy(file, new_dir)
        except IOError as error:
            print("\nUnable to copy file: {}{}".format(file, error))
            status = 1
            break
        except:
            print("\nUnexpected error. %s" %error)
            status = 1
            break

    return status

####################################################################################################
##
##  Setup enviroment variables
##  Parse commandline arguments
##  Find the Firmware Volume to replace in the BIOS file
##  Merge the file with new header section and then replace OSE firmware  with new OseFw
##
###################################################################################################

def main():
    '''Entry to script.'''

    args = parse_cmdline()
    env_vars = set_environment_vars()

    #current directory and working director
    dirs = [os.getcwd(), 'SIIP_wrkdir']

   #Create working directory
    try:
        os.mkdir(dirs[1])
    except (IOError, OSError) as exception:
        sys.exit("\nUnable to create directory: {}\n{}".format(dirs[1], exception))
    except:
        sys.exit("\nUnexpected error occuring when trying to create directory")

    # move files to working directory
    filenames = [args.IFWI_IN.name, args.IPNAME_IN.name]
    status = copy_file(filenames, dirs[1])
    if status != 0:
        cleanup(dirs)
        sys.exit()

    #search for firmware volume
    status, fw_volume = search_for_fv(args.IFWI_IN.name, args.ipname, env_vars, dirs[1])

    # Check for error in using FMMT.exe or if firmware volume was not found.
    if status == 1 or fw_volume is None:
        cleanup(dirs)
        if status == 0:
            print("\nError: No Firmware volume found")
        sys.exit()

    # firmeware volume was found
    print("\nThe Firmware volume is {}\n".format(fw_volume))


    # setup files of executable programs to be used to perform the merge and repalce
    filenames = [args.IFWI_IN.name, args.IPNAME_IN.name, args.OUTPUT_FILE]
    filenames = [os.path.abspath(f) for f in filenames]

    # create oseFW header, merge header and replace in Binary
    status = merge_and_replace(filenames, args.ipname, fw_volume, env_vars, dirs[1])

    cleanup(dirs)

if __name__ == "__main__":
    main()
