# Sub-Region Capsule Script

The Sub Region Capsule Generator scripts creates a capsule to update sub-regions, which are regions

located within the boot firmware.

## Environment Requirments

Sub Region Capsule script supports python 3.x.

Sub Region Capsule script runs on Windows 10 OS


## Installation

Sub Region Capsule script depends on EDKII capsule tool (included) and OpenSSL to generate the output. You will
need to install OpenSSL manually to the host and add it to the system environment viarable PATH.

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

The input file is a JSON file that describes the BIOS sub region. BIOS sub regions are firmware volumes

that contain one or many FFS files which contain the data or firmware. Example JSON files are located

in Examples directory.

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

data_type - One of the following is supported ["DECIMAL", "HEXADECIMAL", "STRING", "FILE"]

member_value - An integer or string. If a the string is "\_STDIN\_" then value will come from stdin

## Step-by-Step Instructions


### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `C:\siip_tools`)
At this point the directory should contain the following files and directory:

```
 Directory of C:\siip_tools\fbu_siip_20190910

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

### STEP 2: Install python3 and required python module `cryptography` using pip

Note: If your host is behind proxy server, add `--proxy=<proxy_server>:<proxy_port>`


### STEP 3: Copy Capsule certificate files used for capsule generation to the working directory (e.g., `C:\siip_tools\scripts`)

At this point, the working directory should contain the following files/directory:


```
	TestCert.pem
	TestSub.pub.pem
	TestRoot.pub.pem
	subregion_capsule.py
	Examples
```


### STEP 4: Run subregion_capsule to create Sub Region Capsule Image (output: `capsule.out.bin`)

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
