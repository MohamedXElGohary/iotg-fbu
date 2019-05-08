# SIIP Capsule Script

The Sub Region Capsule Generator scripts creates a capsule to update SIIP sub regions, which are regions

located within the boot firmware.

## Environment Requirments

SIIP Stitch scripts supports python 3.x.

SIIP Capsule scripts runs on Windows 10 OS


## Usage

```
The usage for JSON input for one or more payload capsules is
usage: GenerateSubRegionCapsule [-h] [-o OUTPUTCAPSULEFILE]
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

  -o, --output
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

member_value - An integer or string. If a the string is "_STDIN_" then value will come from stdin

## Example

python GenerateSubRegionCapsule.py  -o .\SiipCapSigned.cap --signer-private-cert=.\TestCert.pem --other-public-cert=.\TestSub.pub.pem --trusted-public-cert=.\TestRoot.pub.pem .\Tests\Collateral\TsnMacConfigDescExample.json