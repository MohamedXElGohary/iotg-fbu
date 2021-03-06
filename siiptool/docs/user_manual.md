User's Manual
=============

This software contains the following command line programs to modify, sign and create UEFI-based BIOS images:

* **Signing Tool** (`siip_sign.py`): Signs an image according to SIIP specification
* **Stitching Tool** (`siip_stitch.py`): Replaces an image inside a UEFI image
* **Subregion Capsule Tool** (`subregion_capsule.py`): Creates a UEFI capsule image with sub-region file

The following diagrams provide inputs and outputs generated by these tools:

![Stitch Flow](docs/stitching_usage_flow.png)
![Sub-Region Flow](docs/subregion_capsule_usage_flow.png)


### Abbreviations

| Abbreviation       | Description |
| :----------------: | ----------- |
| UEFI | Unified Extensible Firmware Interface |
| PSE | Intel® Programmable Services Engine |
| SIIP | SoC Independent Intellectual Property |
| FKM | Firmware Key Manifest |



# Getting Started

## Hardware and Software Requirement

The SIIP tools are written in Python with support from third party utilities. It can
 run on a PC with Windows or Linux OS installed. The SIIP Tools have been verified on Windows 10 (64-bit) and Ubuntu 18.04 LTS Linux.

All third party utilities are included in the release package. However, for
initial setup, users are required to install Python software and additional
modules before running these tools:

- The minimum Python version is 3.6.x.
- Python module `cryptography`
- Python module `click`


## Install Python 3.6.x

For Windows:
1. Download Python from: https://www.python.org/downloads/
2. Start installation and choose 'Customized Install'
3. Change install path to `C:\Python36`
4. Make sure pip and 'Add to PATH' are selected
5. Complete installation

For Ubuntu Linux 18.04 LTS:
```shell
  sudo apt-get update
  sudo apt-get -y install software-properties-common
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt-get -y install curl python3.6
  curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
  sudo python3.6 get-pip.py
  sudo ln -s /usr/bin/python3.6 /usr/bin/python
```

Note: On Windows, files with extension `.py` may not be associated to Python interpreter, e.g `*.py` is opened by text editor by default. You may need to fix this problem before running the script. Otherwise, stitching feature will fail.


## Install Python Modules

Set PROXY environment if your host is behind proxy server:


For Windows
```batch
  D:\tmp>set HTTP_PROXY=<SERVER>:<PORT>
  D:\tmp>set HTTPS_PROXY=<SERVER>:<PORT>
```

For Linux
```shell
  $ export http_proxy=<SERVER>:<PORT>
  $ export https_proxy=<SERVER>:<PORT>
```

Install additional Python modules

For Windows
```batch
  C:\Python36\Scripts\pip.exe install cryptography
  C:\Python36\Scripts\pip.exe install click
```

For Linux
```shell
  $ python3.6 -m pip install --user cryptography
  $ python3.6 -m pip install --user click
```

Note: If there are multiple Python versions installed on the host, it is highly recommended to use `virtualenv` or `pipenv` before running the scripts.

Go to the following sections for each tool or directly in **Examples** for how to run these tools:

* [SIIP Stitching Tool](#siip-stitching-tool)
* [Sub-Region Capsule Tool](#sub-region-capsule-tool)
* [SIIP Signing Tool](#siip-signing-tool)
* [Examples](#examples)
* [FAQ](#faqs)


# SIIP Stitching Tool

The SIIP Stitch Tool is used to swap or replace the firmware module
 into the BIOS image without re-compiling it.

## Supported component types and their short names

| Supported Component | Short name on command line |
| ------------------- | :------------------------: |
| Intel® Programmable Services Engine firmware (PSE) | pse |
| Firmware Key Manifest | fkm |
| TSN MAC address | tmac |
| TSN configuration | tsn |
| TSN IP configuration | tsnip |
| Time Coordinated Computing configuration | tcc |
| Out-of-Band configuration | oob |
| Graphical Output Protocol Driver (GOP) | gop |
| Graphics PEIM Module | gfxpeim |
| Video BIOS Table | vbt |


## Usage

```
usage: siip_stitch [-h] -ip ipname [-k PRIVATE_KEY] [-v] [-o FileName]
                   IFWI_IN IPNAME_IN

positional arguments:
  IFWI_IN               Input BIOS Binary file(Ex: IFWI.bin) to be updated with
                        the given input IP firmware
  IPNAME_IN             Input IP firmware Binary file(Ex: PseFw.bin) to be
                        replaced in the IFWI.bin

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

### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\siip_tools`)

At this point the directory should contain the following files and directory:

```
10/09/2019  03:45 PM    <DIR>          .
10/09/2019  03:45 PM    <DIR>          ..
10/09/2019  05:36 PM    <DIR>          common
27/08/2019  02:23 PM             1,347 LICENSE
10/09/2019  03:44 PM            60,254 README.docx
10/09/2019  02:53 PM             3,073 README.md
10/09/2019  05:38 PM    <DIR>          scripts
10/09/2019  03:45 PM    <DIR>          thirdparty
               3 File(s)         64,674 bytes
               5 Dir(s)  11,534,508,032 bytes free

```

### STEP 2: Prepare RSA private key and rename to `privkey.pem` into the same working directory

** NOTE: **: An RSA signing key is required to stitch GOP, PEIM GFX and VBT
images with the BIOS image. This signing key must be the same key used by BIOS.
If they are different, the output image may not be bootable if security is
enabled on the platform.


### STEP 3: Prepare initial IFWI image (e.g., `IFWI.bin`) and SIIP firmware to be replaced (e.g. `PseFw.bin`)

### STEP 4: Run SIIP Stitch Tool to create the new IFWI image

For example:

```
C:\siip_tools\scripts>siip_stitch.py -ip pse -o IFWI2.bin IFWI.BIN PseFw.bin
#########################################################################################
Purpose of this utility is to replace the section in System BIOS ROM file with new section
#########################################################################################
 Running on Windows

Finding the Firmware Volume

The Firmware volume is FV10


Starting merge and replacement of section
Encoding
Intel(R) Firmware Module Management Tool(FMMT). Version 0.22, Mar 16 2018. Build 5204f5.

The Guid Tool Definition comes from the 'C:\siip_tools\thirdparty\bin\win32\FmmtConf.ini'.
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

C:\siip_tools\scripts>
```

The new image `IFWI2.bin` is generated with `PseFw.bin` embedded in the IFWI image.



# Sub-Region Capsule Tool

The Sub-Region Capsule tool creates a capsule to update sub-regions, which are
regions located within the system firmware (e.g. BIOS).

## Installation

Sub Region Capsule script depends on EDKII capsule tool (included) and OpenSSL
to generate the output. You will need to install OpenSSL manually to the host
and add it to the system environment variable `PATH`.

Pre-compiled OpenSSL for Windows can be downloaded from https://wiki.openssl.org/index.php/Binaries


## Usage

```
The usage for JSON input for one or more payload capsules is
usage: subregion_capsule [-h] [-o OUTPUTCAPSULEFILE]
                                   [--signer-private-cert OPENSSLSIGNERPRIVATECERTFILE]
                                   [--other-public-cert OPENSSLOTHERPUBLICCERTFILE]
                                   [--trusted-public-cert OPENSSLTRUSTEDPUBLICCERTFILE]
                                   [--signing-tool-path SIGNINGTOOLPATH]
                                   InputFile

Generate a sub region capsule. Copyright (c) 2019, Intel Corporation. All
rights reserved.

positional arguments:
  InputFile             Input JSON sub region descriptor filename.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUTCAPSULEFILE, --output OUTPUTCAPSULEFILE
                        Output capsule filename.
  -s, --signer-private-cert OPENSSLSIGNERPRIVATECERTFILE
                        OpenSSL signer private certificate filename.
  -p, --other-public-cert OPENSSLOTHERPUBLICCERTFILE
                        OpenSSL other public certificate filename.
  -t, --trusted-public-cert OPENSSLTRUSTEDPUBLICCERTFILE
                        OpenSSL trusted public certificate filename.
  --signing-tool-path SIGNINGTOOLPATH
                        Path to signtool or OpenSSL tool. Optional if path to
                        tools are already in PATH.

```

## JSON Input Format

The input file is a JSON file that describes the BIOS sub region. Sub-regions
are firmware volumes that contain one or many FFS files which contain the data
or code. Example JSON files are located in `Examples` directory.

Format of the JSON payload descriptor file:
```
{
  "FmpGuid": <string (GUID)>,
  "Version": <integer>,
  "FV" :
  {
    "FvGuid": <string (GUID)>,
    "FfsFiles":
    [
      {
        "FileGuid": <string (GUID)>,
        "Compression": <boolean>,
        "Data" :
        [
          [<string (member_name)>, <string (data_type)>, <integer (byte_size)>, <integer|string (member_value)>],
          ...
        ]
      }
    ]
  }
}
```

`data_type` - One of the following is supported ["DECIMAL", "HEXADECIMAL", "STRING", "FILE"]

`member_value` - An integer or string. If a the string is "\_STDIN\_" then value will come from stdin


## Step-by-Step Instructions


### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\siip_tools`)

At this point the directory should contain the following files and directory:

```

10/09/2019  03:45 PM    <DIR>          .
10/09/2019  03:45 PM    <DIR>          ..
10/09/2019  05:36 PM    <DIR>          common
27/08/2019  02:23 PM             1,347 LICENSE
10/09/2019  03:44 PM            60,254 README.docx
10/09/2019  02:53 PM             3,073 README.md
10/09/2019  05:38 PM    <DIR>          scripts
10/09/2019  03:45 PM    <DIR>          thirdparty
               3 File(s)         64,674 bytes
               5 Dir(s)  11,534,508,032 bytes free
```

### STEP 2: Copy Capsule certificate files used for capsule generation to the working directory (e.g., `C:\siip_tools\scripts`)

The following certificate files are required:
```
	TestCert.pem
	TestSub.pub.pem
	TestRoot.pub.pem
```


### STEP 3: Run Sub-Region Capsule tool to create capsule image (output: `capsule.out.bin`)

```
C:\siip_tools\scripts>subregion_capsule.py -o capsule.out.bin --signer-private-cert=TestCert.pem --other-public-cert=TestSub.pub.pem --trusted-public-cert=TestRoot.pub.pem Examples\tsn_mac_address.json
C:\siip_tools\thirdparty\Bin\Win32\GenFV.exe -o ./SubRegionFv.fv -b 0x1000 -f tmp.0.ffs -g 8C8CE578-8A3D-4F1C-9935-896185C32DD3 --FvNameGuid 1A803C55-F034-4E60-AD9E-9D3F32CE273C
Error messages  :

Output messages :
Read binary input file ./SubRegionFv.fv
FMP_PAYLOAD_HEADER.Signature              = 3153534D (MSS1)
FMP_PAYLOAD_HEADER.HeaderSize             = 00000010
FMP_PAYLOAD_HEADER.FwVersion              = 00000001
FMP_PAYLOAD_HEADER.LowestSupportedVersion = 00000000
sizeof (Payload)                          = 00001000
EFI_FIRMWARE_IMAGE_AUTHENTICATION.MonotonicCount                = 0000000000000000
EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.dwLength         = 00000AED
EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.wRevision        = 0200
EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.wCertificateType = 0EF1
EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.CertType             = 4AAFD29D-68DF-49EE-8AA9-347D375665A7
sizeof (EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.CertData)    = 00000AD5
sizeof (Payload)                                                = 00001010
EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.Version             = 00000001
EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.EmbeddedDriverCount = 00000000
EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.PayloadItemCount    = 00000001
EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.ItemOffsetList      =
  0000000000000010
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.Version                = 00000002
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageTypeId      = 6FEE88FF-49ED-48F1-B77B-EAD15771ABE7
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageIndex       = 00000001
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageSize        = 00001B05
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateVendorCodeSize   = 00000000
EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateHardwareInstance = 0000000000000000
sizeof (Payload)                                                    = 00001B05
sizeof (VendorCodeBytes)                                            = 00000000
EFI_CAPSULE_HEADER.CapsuleGuid      = 6DCBD5ED-E82D-4C44-BDA1-7194199AD92A
EFI_CAPSULE_HEADER.HeaderSize       = 00000020
EFI_CAPSULE_HEADER.Flags            = 00050000
  OEM Flags                         = 0000
  CAPSULE_FLAGS_PERSIST_ACROSS_RESET
  CAPSULE_FLAGS_INITIATE_RESET
EFI_CAPSULE_HEADER.CapsuleImageSize = 00001B5D
sizeof (Payload)                    = 00001B3D
Write binary output file capsule.out.bin
Success
```
The capsule file `capsule.out.bin` is generated


# SIIP Signing Tool

Before the system firmware executes a firmware module, it must validate the
authenticity and integrity of it by verifying the manifest data associated
with the firmware image.

The SIIP Sign Tool is used to create manifest data for the firmware image to be
authenticated by the system firmware.

## Features

* Generate a signed image from a single payload
* Decompose a signed image to multiple files including FKM, FBM, Meta file and payload
  - This is a debugging feature
* Run a self-test that mimics SIIP verification flow BIOS performs
  - This is a debugging feature

* Supported signing algorithms:
  - Hashing algorithm: SHA256, SHA384, SHA512
  - RSA signing key: 2048-bit and 3072-bit
  - RSA Padding scheme: PKCS#1 v1.5
* Support different RSA keys to sign FKM data and FBM data
  - Note: both signing keys must have the same length

The default configuration is RSA 3072-bit RSA key with SHA384 hashing for signing.


## Usage

```
usage: siip_sign.py [-h] [-V] {sign,decompose,verify} ...

A SIIP signing tool to create manifest data supporting SIIP firmware loading
specification

positional arguments:
  {sign,decompose,verify}
                        command
    sign                Sign an image
    decompose           Decompose a signed image
    verify              Verify a signed image

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
```

## Step-by-Step Instructions


### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\siip_tools`)
At this point the directory should contain the following files and directory:

```
10/09/2019  03:45 PM    <DIR>          .
10/09/2019  03:45 PM    <DIR>          ..
10/09/2019  05:36 PM    <DIR>          common
27/08/2019  02:23 PM             1,347 LICENSE
10/09/2019  03:44 PM            60,254 README.docx
10/09/2019  02:53 PM             3,073 README.md
10/09/2019  05:38 PM    <DIR>          scripts
10/09/2019  03:45 PM    <DIR>          thirdparty
               3 File(s)         64,674 bytes
               5 Dir(s)  11,534,508,032 bytes free
```

### STEP 2: Copy RSA private key and rename to `privkey.pem` into the same working directory (e.g., `C:\siip_tools\scripts`)

For testing, you can generate a test key using OpenSSL:

```
openssl genrsa -out privkey.pem 2048
```

### STEP 3: Copy SIIP firmware image to be signed (e.g. `PseFw.bin`)


### STEP 4: Run SIIP Sign Tool to sign the SIIP image

For example:

```
C:\siip_tools\scripts>siip_sign.py sign -i PseFw.bin -k privkey.pem -o out.bin

Outputs:

Creating image with manifest data using key privkey.pem ...
Hashing Algorithm : sha256
FKM signing key : privkey.pem
FBM signing key : privkey.pem
Public Key (privkey.pem) (260 Bytes):
19 2b 49 2c 14 18 d2 0f aa b3 d8 76 af 74 90 29  .+I,.......v.t.)
4b 28 66 0a 88 b6 b6 33 11 3f c2 b7 55 fa bc 6e  K(f....3.?..U..n
b2 2e 12 ce 10 9b d8 99 e6 2d 21 9e 5d b8 d7 41  .........-!.]..A
e8 88 9e 78 b4 57 7a e0 bf 15 85 65 d1 60 b1 5b  ...x.Wz....e.`.[
25 4f 66 3b 3d f4 da 4d d2 09 01 3a 78 c1 58 5d  %Of;=..M...:x.X]
16 2c 39 68 60 19 3d 59 58 9e e4 a9 e0 b3 22 4f  .,9h`.=YX....."O
69 be 39 44 34 06 84 bc 5d 3d 7c ae 47 0c f2 6b  i.9D4...]=|.G..k
c1 a0 19 c3 7b 1e 4e 77 34 bf 47 08 f5 c9 dc 31  ....{.Nw4.G....1
5f 79 f6 fe 95 86 7b 25 81 6a 7b f0 24 94 89 95  _y....{%.j{.$...
4e c1 fc a3 df cc 5f 2e 4a 44 2d 13 48 de a3 5f  N....._.JD-.H.._
d2 0d d8 6c c7 ee 0d fb eb 1d 49 24 30 1b 1c ec  ...l......I$0...
f0 25 4a 6f de 72 de 5c 03 8e 6e 51 a7 70 b3 b6  .%Jo.r.\..nQ.p..
6c 29 f1 46 63 a9 81 7d 20 bb 7f 49 d3 91 73 20  l).Fc..}...I..s.
ce da 8b b3 39 d4 37 af b8 b2 21 8a cc 83 03 4b  ....9.7...!....K
45 20 6a b4 6e 00 89 8e e1 05 5a b2 62 9e ac 90  E.j.n.....Z.b...
9d 60 f0 3e 20 8e c8 b6 57 2c 8d 37 04 99 76 cc  .`.>....W,.7..v.
01 00 01 00                                      ....
FKM Public Key (260 Bytes):
19 2b 49 2c 14 18 d2 0f aa b3 d8 76 af 74 90 29  .+I,.......v.t.)
4b 28 66 0a 88 b6 b6 33 11 3f c2 b7 55 fa bc 6e  K(f....3.?..U..n
b2 2e 12 ce 10 9b d8 99 e6 2d 21 9e 5d b8 d7 41  .........-!.]..A
e8 88 9e 78 b4 57 7a e0 bf 15 85 65 d1 60 b1 5b  ...x.Wz....e.`.[
25 4f 66 3b 3d f4 da 4d d2 09 01 3a 78 c1 58 5d  %Of;=..M...:x.X]
16 2c 39 68 60 19 3d 59 58 9e e4 a9 e0 b3 22 4f  .,9h`.=YX....."O
69 be 39 44 34 06 84 bc 5d 3d 7c ae 47 0c f2 6b  i.9D4...]=|.G..k
c1 a0 19 c3 7b 1e 4e 77 34 bf 47 08 f5 c9 dc 31  ....{.Nw4.G....1
5f 79 f6 fe 95 86 7b 25 81 6a 7b f0 24 94 89 95  _y....{%.j{.$...
4e c1 fc a3 df cc 5f 2e 4a 44 2d 13 48 de a3 5f  N....._.JD-.H.._
d2 0d d8 6c c7 ee 0d fb eb 1d 49 24 30 1b 1c ec  ...l......I$0...
f0 25 4a 6f de 72 de 5c 03 8e 6e 51 a7 70 b3 b6  .%Jo.r.\..nQ.p..
6c 29 f1 46 63 a9 81 7d 20 bb 7f 49 d3 91 73 20  l).Fc..}...I..s.
ce da 8b b3 39 d4 37 af b8 b2 21 8a cc 83 03 4b  ....9.7...!....K
45 20 6a b4 6e 00 89 8e e1 05 5a b2 62 9e ac 90  E.j.n.....Z.b...
9d 60 f0 3e 20 8e c8 b6 57 2c 8d 37 04 99 76 cc  .`.>....W,.7..v.
01 00 01 00                                      ....
CPD Header CRC32 : 0x20C721F2
CPD Header CRC32 : 0xAB5B8E46
Payload Hash (32 Bytes):
b7 dc 5c b8 d4 2f cb cd f0 0f 6b 00 e7 34 38 c5  ..\../....k..48.
4e c3 c9 71 75 44 8d c7 99 37 8b f5 9d 41 0f c5  N..quD...7...A..
FBM Public Key (260 Bytes):
19 2b 49 2c 14 18 d2 0f aa b3 d8 76 af 74 90 29  .+I,.......v.t.)
4b 28 66 0a 88 b6 b6 33 11 3f c2 b7 55 fa bc 6e  K(f....3.?..U..n
b2 2e 12 ce 10 9b d8 99 e6 2d 21 9e 5d b8 d7 41  .........-!.]..A
e8 88 9e 78 b4 57 7a e0 bf 15 85 65 d1 60 b1 5b  ...x.Wz....e.`.[
25 4f 66 3b 3d f4 da 4d d2 09 01 3a 78 c1 58 5d  %Of;=..M...:x.X]
16 2c 39 68 60 19 3d 59 58 9e e4 a9 e0 b3 22 4f  .,9h`.=YX....."O
69 be 39 44 34 06 84 bc 5d 3d 7c ae 47 0c f2 6b  i.9D4...]=|.G..k
c1 a0 19 c3 7b 1e 4e 77 34 bf 47 08 f5 c9 dc 31  ....{.Nw4.G....1
5f 79 f6 fe 95 86 7b 25 81 6a 7b f0 24 94 89 95  _y....{%.j{.$...
4e c1 fc a3 df cc 5f 2e 4a 44 2d 13 48 de a3 5f  N....._.JD-.H.._
d2 0d d8 6c c7 ee 0d fb eb 1d 49 24 30 1b 1c ec  ...l......I$0...
f0 25 4a 6f de 72 de 5c 03 8e 6e 51 a7 70 b3 b6  .%Jo.r.\..nQ.p..
6c 29 f1 46 63 a9 81 7d 20 bb 7f 49 d3 91 73 20  l).Fc..}...I..s.
ce da 8b b3 39 d4 37 af b8 b2 21 8a cc 83 03 4b  ....9.7...!....K
45 20 6a b4 6e 00 89 8e e1 05 5a b2 62 9e ac 90  E.j.n.....Z.b...
9d 60 f0 3e 20 8e c8 b6 57 2c 8d 37 04 99 76 cc  .`.>....W,.7..v.
01 00 01 00                                      ....
[0] FBM @ [0x0000005c-0x0000036c] len: 0x310 (784) Bytes
[1] METADATA @ [0x0000036c-0x000003ec] len: 0x80 (128) Bytes
[2] PAYLOAD @ [0x000003ec-0x00033f8c] len: 0x33ba0 (211872) Bytes
Writing... Okay

```
The following output files are generated:

* `fkm.bin` : Firmware Key Manifest data
* `out.bin` : Signed `PseFw.bin` with manifest data (Firmware Blob Manifest and Metadata)

# Examples

Note you will need to enter `scripts` sub-directory to run the following examples.

## Stitching PSE Image

Note: You will need IFWI image and PSE image as input files

```
siip_stitch.py -o output.bin -ip pse IFWI.bin pse-rom.bin
```

## Stitching FKM Image

Note: You will need IFWI image and FKM image as input files. The FKM image is
generated from the siip_sign.py script. Please refer to `siip_sign.py` for
additional information.

```
siip_stitch.py -o output.bin -ip fkm IFWI.bin fkm.bin
```

## Stitching TSN MAC address using a JSON file

Note: You will need IFWI image and TSN JSON files as input files. Sample JSON
are provided under `Examples` directory

```
siip_stitch.py -o output.bin -ip tmac IFWI.bin Examples\tsn_mac_address.json
```

## Stitching VBT data

Note: You will need IFWI image, the same signing RSA key used for IFWI, VBT data file.

```
siip_stitch.py -o output.bin -ip vbt IFWI.bin vbt.bin
```

## Generate a Sub-Region Capsule for OOB configuration

Note: you will need to certificate files, `telit.pem` and OOB JSON file.

```
... copy telit.pem to the current directory
... copy certificate files to the same directory
subregion_capsule.py -o output.bin -s TestCert.pem -p TestSub.pub.pem -t TestRoot.pub.pem Examples\oob_manageability.json

```

## Signing and Stitching PSE firmware with two different keys

Note: You will need to prepare two RSA keys in PEM format with length 3072 bit
and an unsigned PSE firmware (`PseFw.bin`)

```
openssl genrsa -out key1.pem 3072
openssl genrsa -out key2.pem 3072
siip_sign.py sign -o signed.bin -i tests\images\PseFw.bin,key2.pem -k key1.pem
```

`key1.pem`: Signing key for FKM data
`key2.pem`: Signing key for FBM data, separated by comma `","` after `PseFw.bin`


# FAQs

Who should use the scripts?
---------------------------
Anyone who needs to modify firmware or data in an IFWI Image or create a UEFI sub-region capsule. Please consult documentation in the release package on the supported sub-region types and features.

Do the scripts run in Python 2.7?
----------------------------------
No. Python 2.7 will be no longer be maintained past 2020 (see https://pythonclock.org/). The minimum required version is 3.6.


Can I have multiple versions of Python installed in the system to run the scripts?
-----------------------------------------------------------------------------------
You may keep multiple versions of Python but it is highly recommended to use [`virtualenv`](https://virtualenv.pypa.io/en/stable/) or [`pipenv`](https://docs.pipenv.org/en/latest/) to setup the host environment then run the scripts inside the "contained" Python environment.


Where can I get the signing keys or certificates?
-------------------------------------------------
For security reasons, the official software release does not provide any signing keys or certificate files, which are required for generating capsule image or in some cases, stitching firmware into IFWI image. Typically these files are obtained from the owner of the firmware or capsule to be signed. For testing purpose, you can get certificate files for capsule tool from [here](https://github.com/tianocore/edk2/tree/master/BaseTools/Source/Python/Pkcs7Sign). **Note**: if the signing keys or certificate files are not supported by BIOS, the created image may not work or boot!


Following the instructions above, the script returns with errors. What should I do?
------------------------------------------------------------------------------------
It is recommended to take some steps to narrow down the problem first.

1. What is the first error message from output?
2. Have you installed python `cryptography` module?  --> run `python -c "import cryptography" to confirm`
3. Is the command line parameter correct? --> run `<script> -h` to get help message
4. Does any of input files exist or valid?


You generated the new image, but it does not work or boot. What should I do?
-----------------------------------------------------------------------------
This situation is more complex to trouble shoot. We should find the last known configuration first.

* Does the original image work or boot at all?
* Verify that the new changes are compatible with the original image?

Finally, contact technical support with the domain knowledge for help.


Do these scripts support graphic user interface (GUI)?
------------------------------------------------------
Not currently. These command line scripts only run inside a command shell (`cmd.exe` or `bash`)
