
# SIIP Sign Tool

SoC Independent Intellectual Property (SIIP) refers to a new BIOS firmware loading architecture that specifies an unified flow for loading one or more firmware modules of SoC IP components from SPI flash to memory by BIOS.

Before an SIIP firmware image is loaded to memory, BIOS validates the authenticity and integrity by verifying manifest data associated with the firmware image.

The SIIP Sign Tool is used to create manifest data for the firmware image to be authenticated.

## Features

* Generate a signed image from a single payload
* Decompose a signed image to multiple files including FKM, FBM, Metafile and payload (developer use)
* Run a self-test that mimics SIIP verification flow BIOS performs (developer use)
* RSA Padding scheme supported: PKCS#1 v1.5
* Hashing algorithm supported:
  - SHA1
  - SHA256
  - SHA384
  - SHA512


## Environment Requirements

SIIP Stitch Tool supports python 3.x. Additionally, it requires the follow python modules to perform the required functions:

* python cryptography ver 2.2.2 or newer

SIIP Sign Tool runs on Windows 10 OS and Linux.

## Usage

```
	usage: SIIPSign.py [-h] [-V] {sign,decompose,verify} ...

	A mini-MEU-like signing tool to create manifest data compliant to SIIP
	firmware loader specification

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


### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `/home/user/SIIP_tools`)

### STEP 2: Install python3 and required python module `cryptography` using pip

On Linux:

```
    sudo apt-get install python3
    sudo pip3 install cryptography
```

If the host is behind proxy server, add `--proxy=<proxy_server>:<proxy_port>`


### STEP 3: Copy RSA private key and rename to `privkey.pem` into the same working directory

### STEP 4: Copy SIIP firmware image to be signed (e.g. `OseFw.bin`)

At this point, the working directory should contain the following files and directories:

```
	OseFw.bin
	privkey.pem
	SIIPSign.py
```


### STEP 5: Run SIIP Sign Tool to sign the SIIP image

For example:

```
	./SIIPSign.py sign -i OseFw.bin -k privkey.pem -o out.bin
	Creating image with manifest data using key privkey.pem ...
	[0] FKM @ [0x00000070-0x0000037c] len: 0x30c (780) Bytes
	[1] FBM @ [0x0000037c-0x00000678] len: 0x2fc (764) Bytes
	[2] METADATA @ [0x00000678-0x000006d4] len: 0x5c (92) Bytes
	[3] PAYLOAD @ [0x000006d4-0x001006d4] len: 0x100000 (1048576) Bytes
	Writing... Okay

```

The new image `out.bin` is generated with manifest data and `OseFw.bin` combined.
