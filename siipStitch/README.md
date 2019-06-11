# SIIP Stitch Tool

SoC Independent Intellectual Property (SIIP) refers to a new BIOS firmware for loading architecture that specifies an unified flow loading one or more firmware modules of SoC IP components from SPI flash to memory by BIOS.

The SIIP firmware image is stored in the BIOS region. A post processing step, knowns as stitching is required to replace the pre-built firmware module into the BIOS region.

The SIIP Stitch Tool is used to swap a SIIP firmware without rebuilding BIOS image.

The SIIP Stitch Tool supports replacing the following regions:
  * programmable software engine(pse) firmware
  * tmac address
  * pse tmac address
  * tcc configuration
  * out of band (oob) configuration


## Environment Requirements

SIIP Stitch Tool supports python 3.7.2. Additionally, it utilizes the following utilities and tools to perform required functions:

* Firmware Module Management Tool ([FMMT](https://firmware.intel.com/develop))
* [EDK II Base Tools](https://github.com/tianocore/tianocore.github.io/wiki/EDK-II-Tools-List)



SIIP Stitch Tool runs on Windows 10 OS. Linux is not yet supported.

## Usage

```
usage: SIIPStitch [-h]  -ip ipname [-v] [-o FileName]
                  IFWI_IN IPNAME_IN

positional arguments:
  IFWI_IN               Input BIOS Binary file (Ex: IFWI.bin) to be updated
                        with the given input IP firmware
  IPNAME_IN             Input IP firmware Binary file (Ex: oseFw.Bin) to be
                        replaced in the IFWI.bin

optional arguments:
  -h, --help            Shows this help message and exit.
  -ip ipname, --ipname ipname
                        ipname is the name of the firmware region to replace in
                        the IFWI_IN (Ex: -ip pse).  This is required.
                        Supported regions that can be replaced
                        [pse, tmac, ptmac, tcc, oob]

  -v, --version         Shows the current version of the Bio Stitching Tool.
  -o FileName, --outputfile FileName
                        IFWI binary file with the IP replaced with the IPNAME_IN.

```

## Step-by-Step Instructions

### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\Siip_Tools`)

At this point the directory should contain the following files and directory:

```
Directory of c:\siip_tools

06/10/2019  10:42 AM    <DIR>          .
06/10/2019  10:42 AM    <DIR>          ..
05/02/2019  03:00 PM             1,365 LICENSE
06/04/2019  10:16 AM             3,652 README.md.html
05/03/2019  01:30 PM            54,663 Releasenotes.docx
06/07/2019  11:30 AM    <DIR>          siipSign
06/07/2019  11:22 AM    <DIR>          siipStitch
06/04/2019  10:16 AM    <DIR>          siipSupport
06/04/2019  10:16 AM             2,354 SIIPSupport.py
06/06/2019  11:36 AM             1,013 SIIPSupport.pyc
06/07/2019  11:32 AM    <DIR>          SubRegionCapsule

```

### STEP 2: Cd into `siipStitch` directory.

### STEP 3: Prepare initial BIOS image (e.g., `BIOS.bin`) and SIIP firmware to be replaced (e.g. `OseFw.bin`)

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


### STEP 4: Run SIIP Stitch Tool to create new BIOS image (e.g., `BIOS2.bin`)

For example:

```
C:\siip_tools\siipStitch>SIIPStitch.py -ip pse -o BIOS2.bin BIOS.BIN OseFw.bin
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
