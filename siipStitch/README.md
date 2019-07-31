# SIIP Stitch Tool

SoC Independent Intellectual Property (SIIP) refers to a new BIOS firmware for loading architecture that specifies an unified flow loading one or more firmware modules of SoC IP components from SPI flash to memory by BIOS.

The SIIP firmware image is stored in the BIOS region. A post processing step, knowns as stitching is required to replace the pre-built firmware module into the BIOS region.

The SIIP Stitch Tool is used to swap a SIIP firmware without rebuilding BIOS image.

The SIIP Stitch Tool supports replacing the following regions:
  * programmable software engine (pse) firmware
  * tmac address
  * pse tmac (ptmac) address
  * tcc configuration
  * out of band (oob) configuration
  * Graphical Output Protocol (gop) Driver
  * PEI Graphics
  * GOP Visual BIOS Table (vbt)


## Environment Requirements

SIIP Stitch Tool supports python 3.7.2. Additionally, it utilizes the following utilities and tools to perform required functions:

* Firmware Module Management Tool ([FMMT](https://firmware.intel.com/develop))
* [EDK II Base Tools](https://github.com/tianocore/tianocore.github.io/wiki/EDK-II-Tools-List)

These tools are included in the release.

SIIP Stitch Tool runs on Windows 10 OS. Linux support will be added in the future releases.

## Usage

```
usage: siip_stitch [-h] -ip ipname [-k PRIVATE_KEY] [-v] [-o FileName]
                   IFWI_IN IPNAME_IN [IPNAME_IN2]

positional arguments:
  IFWI_IN               Input BIOS Binary file(Ex: IFWI.bin) to be updated with
                        the given input IP firmware
  IPNAME_IN             Input IP firmware Binary file(Ex: OseFw.bin to be
                        replaced in the IFWI.bin
  IPNAME_IN2            The 2nd input IP firmware Binary file needed
                        to replaced the PEI Graphics

optional arguments:
  -h, --help            show this help message and exit
  -ip ipname, --ipname ipname
                        The name of the IP in the IFWI_IN file to be replaced.
                        This is required.
  -k PRIVATE_KEY, --private-key PRIVATE_KEY
                        Private RSA key in PEM format. Note: Key is required
                        for stitching GOP features
  -v, --version         Shows the current version if the BIOS Stitching Tool
  -o FileName, --outputfile FileName
                        IFWI binary file with the IP replaced with the
                        IPNAME_IN
```

## Step-by-Step Instructions

### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\Siip_Tools`)

At this point the directory should contain the following files and directory:

```
Directory of c:\siip_tools

07/25/2019  04:53 PM    <DIR>          .
07/25/2019  04:53 PM    <DIR>          ..
05/02/2019  03:00 PM             1,365 LICENSE
07/18/2019  09:28 AM             2,960 README.md.html
07/18/2019  09:28 AM            74,828 Releasenotes.docx
07/24/2019  10:26 PM    <DIR>          siipSign
07/24/2019  10:26 PM    <DIR>          siipStitch
07/25/2019  04:20 PM    <DIR>          siipSupport
07/24/2019  10:26 PM             2,498 siip_constants.py
07/25/2019  11:43 AM             2,315 siip_support.py
07/25/2019  10:35 AM    <DIR>          SubRegionCapsule


```

### STEP 2: Install python3 and required python module `cryptography` using pip

```
    pip install cryptography
```

If the host is behind proxy server, add `--proxy=<proxy_server>:<proxy_port>`


### STEP 3: Prepare RSA private key and rename to `privkey.pem` into the same working directory

** NOTE: **: An RSA signing key is required to stitch GOP, PEIM GFX and VBT images with the BIOS image. This signing key must be the same key used by BIOS. If they are different, the output image may not be bootable when security is enabled on the platform.


### STEP 4: Prepare initial BIOS image (e.g., `BIOS.bin`) and SIIP firmware to be replaced (e.g. `OseFw.bin`)

At this point, the working directory should contain the following files and directories:

```

Directory of c:\siip_tools\siipStitch

06/10/2019  02:50 PM    <DIR>          .
06/10/2019  02:50 PM    <DIR>          ..
06/04/2019  01:16 PM        33,554,432 BIOS.BIN
06/04/2019  01:16 PM            56,076 OseFw.bin
05/03/2019  01:23 PM            44,882 README.md.html
06/07/2019  11:22 AM            17,187 SIIPStitch.py

```


### STEP 5: Run SIIP Stitch Tool to create new BIOS image (e.g., `BIOS2.bin`)

For example:

```
C:\siip_tools\siipStitch>siip_stitch.py -ip pse -o BIOS2.bin BIOS.BIN OseFw.bin
#########################################################################################
Purpose of this utility is to replace the section in System BIOS ROM file with new section
#########################################################################################
 Running on Windows

Finding the Firmware Volume

The Firmware volume is FV10


Starting merge and replacement of section
Encoding
Intel(R) Firmware Module Management Tool(FMMT). Version 0.22, Mar 16 2018. Build 5204f5.

The Guid Tool Definition comes from the 'C:\gitlab\pmt\siip_tools\SiipSupport\bin\win32\FmmtConf.ini'.
Decoding
Decoding
Decoding
Decoding
Decoding
Decoding
Decoding
Decoding
WARNING: The newly replace file must have a user interface (UI) section, otherwise it cannot be deleted or replaced.
Create New FD file successfully.

Done!

 Firmware Merge complete

C:\siip_tools\siipStitch>
```

The new image `BIOS2.bin` is generated with `OseFw.bin` embedded in the BIOS image.
