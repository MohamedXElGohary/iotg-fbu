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

## Example
```
python subregion_capsule.py  -o .\signed_capsule.cap --signer-private-cert=.\test_cert.pem --other-public-cert=.\test_cert.pub.pem --trusted-public-cert=.\test_cert.pub.pem .\Examples\tsn_mac_address.json
```