#!/usr/bin/env python

##  TITLE stitch.bat - performs a batch of stitching files.
##
##  File Description:
##   Batch file for stitching different regions into IFWI.
##
## Usage
## stitch.bat testfolder complete_siip_stitch_path [output_image_folder]
##    testfolder - input IFWI file should start with vxxxx and official or debug in title
##                    example: v1355_official_spi.bin or v1355_debug_spi.bin
##                 ip module file to be replace in the IFWI should start with IPname_
##                    example: vbt_v106.bin or tsnip_tsn_ip_config.json
##                 privkey.pem is hard coded and expected to be in the file
##                 
## if output_image_folder is not include will default to stitch_out in current directory
##     output_image_folder - output IFWI is the name of IPMODE file and IFWI file 
##            example v1355_official_spi.bin vbt_v106.bin -> vbt_v106_v1355_official_spi.bin
##
## NOTE: Python path is hard coded
##
##example Usage
## batch_stitch.py C:\Users\kdbarnes\ww39\WW39.4\v1355 .\scripts\siip_stitch.py stitch_image_out
##----------------------------------------------------------------------------


from __future__ import print_function

import os
import sys
import subprocess
import fnmatch
import glob
import argparse
import unittest
import platform


# Use colors in terminals
CRED = '\033[91m'
CGRN = '\033[92m'
CEND = '\033[0m'

__prog__ = "batch_stitch"
__version__ = "0.0.5"
TOOLNAME = "Calls SIIP Stitching Tool to do stitch batch of files"

def file_not_exist(file):
    """Verify that file does not exist."""

    if os.path.isfile(file):
        raise argparse.ArgumentTypeError("{} exist!".format(file))
    return file

def parse_cmdline():
    """ Parsing and validating input arguments."""

    # initiate the parser
    parser = argparse.ArgumentParser(prog=__prog__,
                                     description=__doc__,)

    parser.add_argument(
        "TestFolder",
        help="Input folder that contains IFWI files and IP filenames",
    )
    parser.add_argument(
        "OutputFolder",
        type=file_not_exist,
        help="Folder that will contain the updated IFWI Images",
        default="outputfolder",
    )
    return parser

def stitch_files(ifwi_in,test_dir,out_dir,ip_regions,key=None):
    SIIPSTITCH = os.path.join(os.getcwd(), "scripts", "siip_stitch.py")
    
    file_ext=[".json", ".efi", ".bin"]
    
    inputfile = os.path.basename(ifwi_in)
    ifwi_filename, _ = os.path.splitext(inputfile)

    STITCH_CMD=['python', '-u', SIIPSTITCH, ifwi_in]
    success_count = 0
    ip_count = 0
    for ipname in ip_regions:
        if key != None:
            STITCH_CMD.extend(['-k',key])

        # check if graphic ip file is found
        
        for ipfile in glob.glob(os.path.join(test_dir,ipname)):
            ip_count +=1
            ip_inputfile =os.path.basename(ipfile)
            ip_filename, ip_ext = os.path.splitext(ip_inputfile)
            if ip_ext in file_ext:
                ip,_=ipname.split('_',1)
                output_name = ip_filename + "_" + inputfile
                log_name = ip_filename + "_" + ifwi_filename + ".log"
                output= os.path.join(out_dir, output_name)
                logfile = os.path.join(out_dir, log_name)
                STITCH_CMD.extend([ipfile, '-ip', ip, '-o', output])
                with open(logfile,"w") as log:
                    print("\n{}".format(" ".join(STITCH_CMD)))
                    result=subprocess.run(STITCH_CMD,stdout=log,stderr=log)
                    if result.returncode == 0:
                        success_count += 1
                        print("{}SUCCESS.{}".format(CGRN, CEND))
                    else:
                        print("{}ERROR.{}".format(CRED, CEND))
                STITCH_CMD=['python', SIIPSTITCH, ifwi_in]
            else:
                print("{} {} not an IP File{}".format(CRED, ipfile, CEND))
        
    return ip_count, success_count

def main():
     """Entry to script."""

     parser = parse_cmdline()
     args = parser.parse_args()
     
     output_dir = os.path.abspath(args.OutputFolder)
     os.mkdir(output_dir)

     INPUT_PATTERN=r'*[v][1-9][0-9][0-9]*[_]["off|deb"]*[".bin|.rom"]'
     ip_subregion=["pse_*","tmac_*", "tsnip_*", "tsn_*", "tcc_*", "oob_*"] 
     ip_graphic=["vbt_*", "gop_*", "gfxpeim_*"]
     KEYFILE_PATTERN=r'*.pem*'

     total_stitched = 0
     total_keys = 0
     file = None
     # find inputfile
     total_stitched = 0
     num_ipfiles_gpx = 0
     num_stitched = 0
     num_ipfiles = 0
     for in_index, file in enumerate(glob.glob(os.path.join(args.TestFolder,INPUT_PATTERN))):
        #check for keyfile to perform graphics stitching 
        keyfile = None
        
        for key_index, keyfile in enumerate(glob.glob(os.path.join(args.TestFolder,KEYFILE_PATTERN))):
            num_ipfiles_gpx, num_stitched = stitch_files(file,args.TestFolder,output_dir,ip_graphic,keyfile)
            total_stitched += num_stitched
        if not keyfile:
            print("No key file found. Skipping Graphic stitching")
        else:
            total_keys += key_index
        # No key required for stitching 
        num_ipfiles, num_stitched = stitch_files(file,args.TestFolder,output_dir,ip_subregion)
        total_stitched += num_stitched
     if file is None:
         print("{} No input files found in {} {}".format(CRED, args.TestFolder, CEND))
     else:
         total_ip = num_ipfiles_gpx + num_ipfiles
         in_index += 1
         not_stitched = in_index * total_ip - total_stitched
         print("{} Input files found. {} ip_files found. {} files where stitched successfuly".format(in_index, total_ip, total_stitched))
         print("{} files where not stitched successfuly".format(not_stitched))

if __name__ == "__main__":
    main()
