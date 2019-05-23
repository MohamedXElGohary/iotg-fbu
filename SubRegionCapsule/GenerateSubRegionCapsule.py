## @file
# Generate a Sub Region capsule.
#
# This tool generates a Sub Region image and wraps it in a UEFI Capsule around an FMP Capsule.
#
# This tool is intended to be used to generate UEFI Capsules to update the
# system firmware or device firmware for integrated devices.  In order to
# keep the tool as simple as possible, it has the following limitations:
#   * Do not support multiple payloads in a capsule.
#   * Do not support optional drivers in a capsule.
#   * Do not support vendor code bytes in a capsule.
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

import sys
import argparse
import subprocess

import SubRegionImage as sri
import SubRegionDescriptor as srd

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

#
# Globals for help information
#
__prog__        = 'GenerateSubRegionCapsule'
__version__     = '0.1'
__copyright__   = 'Copyright (c) 2019, Intel Corporation. All rights reserved.'
__description__ = 'Generate a sub region capsule.\n'


def CreateArgParser ():
    def convert_arg_line_to_args (arg_line):
        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg

    parser = argparse.ArgumentParser (
        prog=__prog__,
        description=__description__ + __copyright__,
        conflict_handler='resolve',
        fromfile_prefix_chars='@'
    )
    parser.convert_arg_line_to_args = convert_arg_line_to_args
    parser.add_argument ("InputFile", help="Input JSON sub region descriptor filename.")
    parser.add_argument ("-o", "--output", dest='OutputCapsuleFile', help="Output capsule filename.")
    parser.add_argument ("-s", "--signer-private-cert", dest='OpenSslSignerPrivateCertFile',
                         help="OpenSSL signer private certificate filename.")
    parser.add_argument ("-p", "--other-public-cert", dest='OpenSslOtherPublicCertFile',
                         help="OpenSSL other public certificate filename.")
    parser.add_argument ("-t", "--trusted-public-cert", dest='OpenSslTrustedPublicCertFile',
                         help="OpenSSL trusted public certificate filename.")
    parser.add_argument ("--signing-tool-path", dest = 'SigningToolPath',
                         help = "Path to signtool or OpenSSL tool.  Optional if path to tools are already in PATH.")
    return parser


if __name__ == "__main__":
    parser = CreateArgParser ()
    args = parser.parse_args ()

    SubRegionFvFile = "./SubRegionFv.fv"
    SubRegionImageFile = "./SubRegionImage.bin"
    SubRegionDesc = srd.SubRegionDescriptor ()
    SubRegionDesc.ParseJsonData (args.InputFile)
    sri.GenerateSubRegionFv (SubRegionImageFile, SubRegionDesc, SubRegionFvFile)

    GenCapCmd = ["python", "GenerateCapsule.py"]
    GenCapCmd += ["--encode"]
    GenCapCmd += ["--guid", SubRegionDesc.sFmpGuid]
    GenCapCmd += ["--fw-version", str(SubRegionDesc.Version)]
    GenCapCmd += ["--lsv", "0"]
    GenCapCmd += ["--capflag", "PersistAcrossReset"]
    GenCapCmd += ["--capflag", "InitiateReset"]
    GenCapCmd += ["-o", args.OutputCapsuleFile]
    GenCapCmd += ["--signer-private-cert", args.OpenSslSignerPrivateCertFile]
    GenCapCmd += ["--other-public-cert", args.OpenSslOtherPublicCertFile]
    GenCapCmd += ["--trusted-public-cert", args.OpenSslTrustedPublicCertFile]
    GenCapCmd += ["-v"]
    if args.SigningToolPath is not None:
        GenCapCmd += ["--signing-tool-path", args.SigningToolPath]
    GenCapCmd += [SubRegionFvFile]

    PopenObject = subprocess.Popen (' '.join(GenCapCmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while PopenObject.returncode == None:
        PopenObject.wait ()

    sys.exit(PopenObject.returncode)


