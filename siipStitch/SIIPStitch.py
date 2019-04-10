##################################################################################################
## SIIP Stitching Tool
## {The SIIP Stitching Tool replaces specified firmware sections in the 
## current BIOS.bin file with the new version.}
#################################################################################################
##Copyright (c) 2019, Intel Corporation. All rights reserved.
#
INTEL CONFIDENTIAL
# Copyright 2016 Intel Corporation.
#
# The source code contained or described herein and all documents related to the
# source code ("Material") are owned by Intel Corporation or its suppliers or
# licensors. Title to the Material remains with Intel Corporation or its suppliers
# and licensors. The Material may contain trade secrets and proprietary and
# confidential information of Intel Corporation and its suppliers and licensors,
# and is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.
#
# Unless otherwise agreed by Intel in writing, you may not remove or alter
# this notice or any other notice embedded in Materials by Intel or
# Intel's suppliers or licensors in any way.
#
# This file contains a 'Sample Driver' and is licensed as such under the terms
# of your license agreement with Intel or your vendor. This file may be modified
# by the user, subject to the additional terms of the license agreement.
#################################################################################################


##################################################
## Name SIIPStitch.py
## Author: Kimberly Barnes
##
## 
##  File Description:
##   
## License: {license}
## Version: 0.5.1
## Status: Intial Development
#################################################################################################

import os
import platform
import subprocess
import sys
import argparse
import shutil
import shlex 
import stat

__version__ = '0.5.1'
################################################################################################
##
## Global Variables
##
################################################################################################

# excutables used to perform merging and replacing of PSE Firmware
prog = ['GenSec','LzmaCompress', 'GenFfs', 'FMMT.exe']

#data dictionary of regions that can be replaced
regions = {
          #IP/Region : Fileguid
          'pse':['EE4E5898-3914-4259-9D6E-DC7BD79403CF','EBA4A247-42C0-4C11-A167-A4058BC9D423']
          }


# options used to replace regions
ipOptions = {
            # Region:[Options]
            'pse':['IntelOseFw', 'PROCESSING_REQUIRED', '1K']
            }

#################################################################################################
## 
##  Display Utility Information
##
#################################################################################################

print('#########################################################################################')
print('Purpose of this utility is to replace the section in System BIOS ROM file with new section')
print('#########################################################################################')

########################################################################################################
##
## Search for the firmware volume
##   
########################################################################################################

def search_for_fv(inputfile, myenv):
    print("\nFinding the Firmware Volume")
    fwvol = None
    status = 0

    command = [ 'FMMT.exe', '-v', inputfile, '>', 'temp.txt']

    try:
       subprocess.check_call(command, env=myenv,shell=True)

    except subprocess.CalledProcessError as status:
       print("\nError using FMMT.exe") 
       return 1, fwvol     

    ##  Starting Search for firmware volume ###########

    fwvol_found = False
    fwvol_child = False

    #############################################################################################
    # Note: the 'with open' and 'For in iter' is used instead of 'for in searchfile'            #
    #       beacause the peek_line function uses 'tell' and they cannot work together           #
    #############################################################################################

    with open('temp.txt','r') as searchfile:
       #Read line from file and search for the Keyword FV
       for currentline in iter(searchfile.readline, ""):

          if 'FV' in currentline:
             fv = currentline.split(' :')
             # Keyword 'FV was found so search next lines for IntelOseFw or for Child
             while not (peek_line(searchfile).startswith('FV')):
                nextline = searchfile.readline()

                # check to see if new firmware or Child Firmware
                if 'IntelOseFw' in nextline:
                   fwvol=fv[0]
                   fwvol_found = True
                   break
                elif 'Child' in nextline:
                   print ("Found a child Firmware volume: {}.".format(fv[0]))
                   fwvol_child = True
                   break

              # if child Firmware not found we have new Firmware  
             if fwvol_child == False:
                fwvol =fv[0]
                print ("Found a new Firmware volume: {}.".format(fv[0]))
             # Else child found reset flag
             else:
                fwvol_child = False

          #Firmware Volume was found exit loop/
          if fwvol_found:
             break
    return status, fwvol


################################################################################################
##
## Get nextline but keep pointer to the same line
##
################################################################################################
def peek_line(file):
   current_pos = file.tell()
   line = file.readline()
   file.seek(current_pos)
   return line


###############################################################################################
##
## Perform merge and replace of section using different excutables
##
###############################################################################################
def merge_and_replace(filename, guid_values, fwvol, env_vars):
    global prog, ipOptions, regions

    options = [ '-s','-n','-o','-e','-g','-r','-t','-a','-i']
    #option_strings = ['IntelOseFw', 'PROCESSING_REQUIRED', '1K']
    tempfile = ['tempSect.sec','temp.raw','temp.cmps','temp.guided','temp.ffs']
    section_type=['EFI_SECTION_USER_INTERFACE','EFI_SECTION_RAW','EFI_SECTION_GUID_DEFINED','EFI_FV_FILETYPE_FREEFORM']


    #find the ipname to replace using the guid_values
    ipname = [key for key, value in regions.items() if value == guid_values][0]

    #get the options strings for replace firmware volume
    option_strings = ipOptions.get(ipname)

    cmds = {
            #GenSec.exe -s EFI_SECTION_USER_INTERFACE -n "IntelOseFw" -o IntelOseFw.sec
           'cmd0' : [prog[0],options[0],section_type[0],options[1],"'{}'".format(option_strings[0]),options[2],tempfile[0]],

           #GenSec.exe -s EFI_SECTION_RAW -o IntelOseFw.raw OseFw.bin
           'cmd1' : [prog[0],options[0],section_type[1],options[2],tempfile[1],filename[1]],

           #GenSec.exe -o IntelOseFw.raw IntelOseFw.raw IntelOseFw.sec
           'cmd2' : [prog[0],options[2],tempfile[1],tempfile[1],tempfile[0]],

           #LZMAcompress -e IntelOseFw.raw -o IntelOseFw.tmp
           'cmd3' : [prog[1],options[3],tempfile[1],options[2],tempfile[2]],

           #GenSec -s EFI_SECTION_GUID_DEFINED -g EE4E5898-3914-4259-9D6E-DC7BD79403CF -r PROCESSING_REQUIRED -o OseFw.guided   IntelOseFw.tmp
           'cmd4' : [prog[0],options[0],section_type[2],options[4],guid_values[0],options[5], option_strings[1], options[2],tempfile[3],tempfile[2]],

           #GenFfs.exe -t EFI_FV_FILETYPE_FREEFORM -g EBA4A247-42C0-4C11-A167-A4058BC9D423  -a 1K -i  OseFw.guided   -o IntelOseFw.ffs
           'cmd5' : [prog[2],options[6],section_type[3],options[4],guid_values[1],options[7],option_strings[2], options[8],tempfile[3], options[2],tempfile[4]],

           #FMMT.exe -r BIOS.bin %FIRMWARE_VOLUME% IntelOseFw IntelOseFw.ffs BIOS_OUTPUT.bin
           'cmd6' : [prog[3],options[5],filename[0], fwvol,option_strings[0], tempfile[4],filename[2]]
    }

    print("\nStarting merge and replacement of section")

   #Merging and Replacing
    for cmd_name, command in sorted(cmds.items()):
       try:
          subprocess.check_call(command, env=env_vars, shell=True)
       except subprocess.CalledProcessError as status:
          print("\nError executing {}".format(cmd_name))
          return 1

    return 0

##################################################################################################
##
## Remove files from directory
##
##################################################################################################
def cleanup(dir):
    osSys = platform.system()

    #change directory
    try:
       os.chdir(dir[0])  
    except OSError as error:
       sys.exit("\nUnable to Change Directory : {}\n{}".format(dir[0],error))
    except :
       sys.exit("\nUnexpected error:{}".format(sys.exc_info()))

   # determine platform in order to use correct command for the OS
    if osSys == "Windows":
       cmd = ['rmdir', dir[1], '/s', '/q']
    else: # linux
       cmd  = ["rm","-fr",dir[1]]

    try:
       subprocess.check_call(cmd,shell=True)
    except subprocess.CalledProcessError as status:
       sys.exit("\nError: excuting {},\n{}".format(cmd,status))

##################################################################################################
##
##  Determine platform and set working path and Engine Development Kit path
##
##################################################################################################

def set_environment_vars():
    osSys = platform.system()
    progs = ['GenSec','LzmaCompress', 'GenFfs', 'FMMT.exe', 'FmmtConf.ini', 'python27.dll',\
             'Rsa2048Sha256SignPlatform.bat','Rsa2048Sha256Sign.exe']

   # Determine operating system that script is running

    if osSys == "Linux" or osSys == "linux2":
       # linux
       osDir ="BinWrappers/PosixLike"
       cmd = 'which'
       print("Running on Linux")
    elif osSys == "Windows":
      # windows
      osDir ="Bin\win32"
      cmd = 'where'

      print(" Running on Windows")
    else:
      sys.exit("\n{},is not supported".format(osSys))

   # set up enviroment variables
    path = os.environ.get("PATH")
    myenv = os.environ.copy()
    myPath = os.getcwd()

   # path to Base Tools
    edkToolsPath = os.path.join(os.sep, myPath, "BaseTools")
    edkToolsBin = os.path.join(os.sep,edkToolsPath,osDir)

    if not os.environ.get('EDK_TOOLS_PATH'):
       if os.path.isdir(edkToolsPath):
          myenv["EDK_TOOLS_PATH"] = edkToolsPath
          myenv["WORKSPACE_TOOLS_PATH"] = edkToolsPath
       else :
          sys.exist("\nError: Cannot find the tools path{}".format(edkToolsBin))
    if not os.environ.get('EDK_TOOLS_BIN'):
       if os.path.isdir(edkToolsPath):
          myenv["EDK_TOOLS_BIN"] = edkToolsBin
          myenv["PATH"] = myenv["EDK_TOOLS_BIN"] + ';'  + path 
       else :
          sys.exist("\nError: Cannot find the tools path{}".format(edkToolsBin))      

    #redirect output 
    devNull = open(os.devnull, 'w')

    for  baseTool in progs:
       command = [cmd, baseTool]

       try:
         # check to see if the required tools are installed
         #subprocess.Popen(command, env=myenv, stdout=devNull, stderr =subprocess.STDOUT)
         subprocess.check_call(command, stdout=devNull, env=myenv)
       except subprocess.CalledProcessError as status:
         sys.exit("\nError baseTool is not located: {}".format(baseTool))

    return myenv   
   
##################################################################################################
##
## 'Type' for argparse 
##  Verify that file does not exist
##
##################################################################################################
def file_not_exist(file):
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
    if not os.path.isfile(file):
       raise argparse.ArgumentTypeError("{} does not exist!".format(file))
    return file

##################################################################################################
##
## 'Type' for argparse = chk_ip
## Verify valid IP or region name to be replaced
##
##################################################################################################

def chk_ip(ip):
    global regions

    if ip.lower() not in regions:
        raise argparse.ArgumentTypeError("Replace {} IP is not supported. Here is the list of supported "
                                         "regions: {}".format(ip,regions.keys())) 
    return regions.get(ip.lower())

##################################################################################################
##
## 'Type' for argparse = chk_platform
## Verify platform is supported
##
##################################################################################################

def chk_platform(platform):
    global platforms

    if platform.lower() not in platforms:
        raise argparse.ArgumentTypeError("{} platform is not supported. Here is the list of supported "
                                         "platforms: {}".format(platform,platforms.keys())) 
    return platforms.get(platform.lower())

##################################################################################################
##
## Parsing and validating input arguments 
##
##################################################################################################

def parse_cmdline():
    # initiate the parser
    parser = argparse.ArgumentParser(prog='SIIPStitch')

    parser.add_argument("IFWI_IN", type=argparse.FileType('rb+'), help="Input BIOS Binary file\
                       (Ex: IFWI.bin) to be updated with the given input IP firmware" ) 
    parser.add_argument("IPNAME_IN", type=argparse.FileType('rb'), help="Input IP firmware Binary file\
                       (Ex: oseFw.Bin) to be replaced in the IFWI.bin" )
    parser.add_argument("-k","--priv_key", dest="PRIV_KEY",type=file_exist,help="Private RSA 2048\
                       key in PEM format to decode the firmware volume. This is required.",metavar="priv_key.pem",\
                       required=True)
    parser.add_argument("-ip","--ipname", type=chk_ip,help="The name of the IP in the IFWI_IN file to be replaced.\
                       This is required.", metavar="ipname",required=True)   
    parser.add_argument("-v", "--version",help="Shows the current version of the Bio Stitching Tool",\
                       action="version", version="%(prog)s {version}".format(version=__version__))
    parser.add_argument("-o", "--outputfile", dest="OUTPUT_FILE",type=file_not_exist, help="IFWI binary\
                       file with the IP replaced with the IPNAME_IN",metavar="FileName", \
                       default='BIOS_OUT.bin' ) 

    # storing received  arguments
    args = parser.parse_args()

    return args

######################################################################################################
##
## Move file to directory
##
#######################################################################################################
def copy_file(files,dir):
    status = 0

    for  file in files:  

       try:
          shutil.copy(file,dir)
       except IOError as error:
          print("\nUnable to copy file: {}{}".format(file,error))
          status = 1
          break
       except :
          print("\nUnexpected error. %s" % e)
          status = 1
          break

    return status

#####################################################################################################################################
##
##  Setup enviroment variables 
##  Parse commandline arguments
##  Find the Firmware Volume to replace in the BIOS file
##  Merge the file with new header section and then replace OSE firmware  with new OseFw 
## 
#####################################################################################################################################  

def main():
    args = parse_cmdline()
    envVars = set_environment_vars()

    #current directory and working director
    dirs=[os.getcwd(),'SIIP_wrkdir']

   #Create working directory
    try:
       os.mkdir(dirs[1])
    except (IOError,OSError) as exception:
       sys.exit("\nUnable to create directory: {}\n{}".format(dirs[1],exception))
    except:
       sys.exit("\nUnexpected error occuring when trying to create directory")

    # move files to working directory
    filenames = [args.IFWI_IN.name, args.IPNAME_IN.name, args.PRIV_KEY]
    status= copy_file(filenames,dirs[1])
    if status !=0:
       cleanup(dirs)
       sys.exit()

    ## files copied to working directory

    # change to working directory

    try:
       os.chdir(dirs[1])
    except IOError as error:
       sys.exit("\nUnable to change directory : {}{}".format(dirs[1],error))
    except:
       sys.exit("\nUnexpected error:{}".format(sys.exc_info()))

    #search for firmware volume
    status, fwVolume = search_for_fv(args.IFWI_IN.name,envVars)

    # Check for error in using FMMT.exe or if firmware volume was not found.
    if status ==1 or fwVolume == None:
       cleanup(dirs)
       if status ==0:
           print("\nError: No Firmware volume found")
       sys.exit()

    # firmeware volume was found   
    print ("\nThe Firmware volume is {}\n".format(fwVolume)) 


    # setup files of executable programs to be used to perform the merge and repalce
    filenames = [args.IFWI_IN.name,args.IPNAME_IN.name, args.OUTPUT_FILE]

    # create oseFW header, merge header and replace in Binary
    status = merge_and_replace(filenames, args.ipname, fwVolume,envVars)

    # merge and replace was successful move output file to users current directory
    if status == 0:
       status = copy_file([args.OUTPUT_FILE],dirs[0])
       if status == 0:
          print("\n Firmware Merge complete")

    cleanup(dirs)
    return

if __name__== "__main__":
  main()



