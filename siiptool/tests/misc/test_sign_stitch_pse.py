#!/usr/bin/env python
"""Sign and stitch PSE with BIOS in one step"""

import sys
import os
import subprocess
from random import randint


SIIP_SIGN = os.path.join("scripts", "siip_sign.py")
SIIP_STITCH = os.path.join("scripts", "siip_stitch.py")
IFWI_DIR = "C:\\xfer19\\EHL\\bios\\RomImages\\ElkhartLakeSimics\\"
IFWI_IN = IFWI_DIR + "EHL_FSPWRAPPER_2163_00_D_Simics.bin"
IFWI_OUT = IFWI_DIR + "ifwi.bin"
OEM_KEY = "oem_privkey.pem"
PSE_KEY = "priv3k.pem"
#PSE_KEY = "priv2k.pem"
PSE_FW = "PseFw.bin"
HASH_ALG = "sha384"


def main():

    # Cleanup old files
    for f in [IFWI_OUT, "out.bin", "signed.bin", "fkm.bin"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

    # Sign
#    keyfile = os.path.join("tests", "images", "privkey.pem"),
    cmd = ["python", SIIP_SIGN, "sign", "-o", "signed.bin",
           "-i", PSE_FW,
           "-k", PSE_KEY,
           "-s", HASH_ALG,
           ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, shell=True)

    # Corrupt manifest for testing
#    corrupt("fkm.bin")
#    corrupt("signed.bin", offset=0x4b0)

    # Stitch key manifest
#    cmd = ["python", SIIP_STITCH, "-ip", "fkm",
#           "-o", "out.bin", IFWI_IN, "fkm.bin"
#           ]
#    print(" ".join(cmd))
#    subprocess.check_call(cmd, shell=True)

    # Stitch signed PSE file
    cmd = ["python", SIIP_STITCH, "-ip", "pse",
           "-o", IFWI_OUT, IFWI_IN, "signed.bin"
           ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, shell=True)

    print("Done.")


def corrupt(file, offset=-1):
    """Corrupt one byte in a file"""

    with open(file, "rb") as fd:
        data = fd.read()
        # Corrupt one byte
        if offset == -1:
            offset = randint(0, len(data) - 1)
        ndata = bytearray(data)
        ndata[offset] = ~ndata[offset] & 0xff

    print("**** CORRUPTING {} @ offset 0x{:x} ...".format(file, offset))
    with open(file, "wb") as fd:
        fd.write(ndata)


if __name__ == "__main__":
    sys.exit(main())
