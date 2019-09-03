# Elkhart Lake Firmware and BIOS Utilities

This software contains a few tools and scripts to support binary modifications on UEFI BIOS images:

* **Signing Tool** (`siip_sign.py`): Sign a payload image according to SIIP specification
* **Stitching Tool** (`siip_stitch.py`): Stitch an image into an IFWI image according to UEFI Firmware File System format
* **Subregion Capsule Tool** (`subregion_capsule.py`): Create a UEFI capsule image with subregion images generated from user defined configuration file

The flowchart with associated input and output files are illustrated in the following diagram:

![Signing Diagram](docs/stitching_usage_flow.png)
![Signing Diagram2](docs/subregion_capsule_usage_flow.png)

All of these tools are command line driven scripts.


# Getting Started

## STEP 1: Setup Host Environment with Python

### Installing Python 3.7.3 for Windows to `C:\Python37`

1. Download Python from: https://www.python.org/downloads/
2. Start installation and choose 'Customized Install'
3. Change install path to `C:\Python37`
4. Make sure pip and 'Add to PATH' are selected
5. Complete installation

Note: On Windows, files with extension `.py` may not associate to Python interpreter, e.g `*.py` is opened by text editor by default. Please fix that before running the script.


### Installing Python Modules

Set PROXY environment if your host is behind proxy server:

```
  D:\tmp>set HTTP_PROXY=<...>
  D:\tmp>set HTTPS_PROXY=<...>
```

Install addiontional Python modules

```
  C:\Python37\Scripts\pip.exe install cryptography
```

Note: If there are multiple Python versions installed on the host, it is highly recommended to use virtualenv or pipenv before running the scripts.


## STEP 2: Required Input Files

Before you are running scripts, please prepare the input files including images and signing keys

* IFWI image that contains Firmware Volume for the signed image identified by GUID and section UI string (e.g., `IFWI.bin`)
* RSA private key (e.g., `privkey.pem`) - The signing key used by BIOS for signing PEI modules and DXE drivers
* Payload image (e.g., `PseFw.bin`)
* Capsule certificate files used for capsule generation:
  - `TestCert.pem`
  - `TestRoot.pub.pem`
  - `TestSub.pub.pem`
* Capsule payload configuration files (e.g., `tsn_mac_address.json`)

## STEP 3: Running

Tip: Copying all inputs files to the same directory as the script is located makes it easier to execute the script.

All scripts are located inside `scripts` directory.

### Signing (output: `PseFw.signed.bin`)

```
  siip_sign.py sign -i PseFw.bin -o PseFw.signed.bin -k privkey.pem
```

### Stitching (output: `IFWI.new.bin`)

```
  siip_stitch.py -ip pse -o IFWI.new.bin IFWI.bin PseFw.bin
```

### Creating Sub Region Capsule Image (output: `capsule.out.bin`)

```
  subregion_capsule.py -o capsule.out.bin --signer-private-cert=TestCert.pem --other-public-cert=TestSub.pub.pem --trusted-public-cert=TestRoot.pub.pem tsn_mac_address.json
```

You are done here!

