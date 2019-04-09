# SIIP Stitch Tool

SoC Independent Intellectual Property (SIIP) refers to a new BIOS firmware loading architecture that specifies an unified flow loading one or more firmware modules of SoC IP components from SPI flash to memory by BIOS.

The SIIP firmware image is stored in the BIOS region. A post processing step, knowns as stitching is required to replace the pre-built firmware module into the BIOS region.

The SIIP Stitch Tool is used to swap a SIIP firmware without rebuilding BIOS image.


## Environment Requirements

SIIP Stitch Tool supports python 2.7.15 or 3.7.2. Additionally, it utilizes the following utilities and tools to perform required functions:

* Firmware Module Management Tool ([FMMT](https://firmware.intel.com/develop))
* [EDK II Base Tools](https://github.com/tianocore/tianocore.github.io/wiki/EDK-II-Tools-List)

SIIP Stitch Tool runs on Windows 10 OS. Linux is not yet supported.

## Usage

```
usage: SIIPStitch [-h] -k priv_key.pem -ip ipname [-v] [-o FileName]
                  IFWI_IN IPNAME_IN

positional arguments:
  IFWI_IN               Input BIOS Binary file (Ex: IFWI.bin) to be updated
                        with the given input IP firmware
  IPNAME_IN             Input IP firmware Binary file (Ex: oseFw.Bin) to be
                        replaced in the IFWI.bin

optional arguments:
  -h, --help            Shows this help message and exit.
  -k priv_key.pem, --priv_key priv_key.pem
                        Private RSA 2048 key in PEM format to sign IFWI_IN.
                        This is required.
  -ip ipname, --ipname ipname
                        ipname is the name of the firmware region to replace in
                        the IFWI_IN (Ex: -ip pse). This is required.
  -v, --version         Shows the current version of the Bio Stitching Tool.
  -o FileName, --outputfile FileName
                        IFWI binary file with the IP replaced with the IPNAME_IN.

```

## Step-by-Step Instructions

### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\SIIPStitch`)

### STEP 2: Copy RSA private key and rename to `privkey.pem` into the same working directory

### STEP 3: Prepare initial BIOS image (e.g., `BIOS.bin`) and SIIP firmware to be replaced (e.g. `OseFw.bin`)

At this point, the working directory should contain the following files and directories:

```

Directory of C:\SIIPStitch

04/04/2019  02:17 PM    <DIR>          .
04/04/2019  02:17 PM    <DIR>          ..
04/04/2019  01:52 PM    <DIR>          BaseTools
01/08/2019  12:44 AM        33,554,432 BIOS.BIN
12/18/2018  09:37 PM            56,076 OseFw.bin
12/27/2016  08:15 AM             1,706 privkey.pem
04/04/2019  02:02 PM            18,285 SIIPStitch.py
               4 File(s)     33,630,499 bytes
               3 Dir(s)  343,111,000,064 bytes free

```


### STEP 5: Run SIIP Stitch Tool to create new BIOS image (e.g., `BIOS2.bin`)

For example:

```
C:\SIIPStitch>python SIIPStitch.py BIOS.bin OseFw.bin -k privkey.pem -ip pse -o BIOS2.bin
#########################################################################################
Purpose of this utility is to replace the section in System BIOS ROM file with new section
#########################################################################################
 Running on Windows

Finding the Firmware Volume
Found a child Firmware volume: FV0.
Found a new Firmware volume: FV2.
Found a child Firmware volume: FV3.
Found a child Firmware volume: FV5.
Found a child Firmware volume: FV7.
Found a child Firmware volume: FV9.
Found a child Firmware volume: FV11.
Found a new Firmware volume: FV13.
Found a new Firmware volume: FV14.
Found a new Firmware volume: FV15.
Found a new Firmware volume: FV16.

The Firmware volume is FV16


Starting merge and replacement of section
Encoding
Decoding
-d
-o
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.4"
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.3"
OpenSSL 1.1.1a  20 Nov 2018


Decoding
-d
-o
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.8"
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.7"
OpenSSL 1.1.1a  20 Nov 2018


Decoding
-d
-o
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.c"
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.b"
OpenSSL 1.1.1a  20 Nov 2018


Decoding
-d
-o
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.g"
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.f"
OpenSSL 1.1.1a  20 Nov 2018


Decoding
-d
-o
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.k"
"C:\SIIPStitch\SIIP_wrkdir\FmmtTemp\sgps.j"
OpenSSL 1.1.1a  20 Nov 2018


Decoding
Decoding
Decoding
Intel(R) Firmware Module Management Tool(FMMT). Version 0.22, Mar 16 2018. Build 5204f5.

The Guid Tool Definition comes from the 'C:\SIIPStitch\BaseTools\Bin\win32\FmmtConf.ini'.
WARNING: The newly replace file must have a user interface (UI) section, otherwise it cannot be deleted or replaced.
Create New FD file successfully.

Done!

 Firmware Merge complete

C:\SIIPStitch>
```

The new image `BIOS2.bin` is generated with `OseFw.bin` embedded in the BIOS image.
