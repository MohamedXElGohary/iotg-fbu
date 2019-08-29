
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
  - SHA256
  - SHA384
  - SHA512
* RSA key size: 2048 bit or longer


## Environment Requirements

SIIP Sign Tool supports python 3.7.x. Additionally, it requires the following python modules:

* python cryptography version 2.2.2 or newer


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


### STEP 1: Unpack SIIP Tools package into a new directory (e.g., `D:\user\tools`)


### STEP 2: Install python3 and required python module `cryptography` using pip

Note: If your host is behind proxy server, add `--proxy=<proxy_server>:<proxy_port>`


### STEP 3: Copy RSA private key and rename to `privkey.pem` into the same working directory

For testing, you can generate a test key using OpenSSL:

```
openssl genrsa -out privkey.pem 2048
```

### STEP 4: Copy SIIP firmware image to be signed (e.g. `OseFw.bin`)

At this point, the working directory should contain the following files and directories:

```
	OseFw.bin
	privkey.pem
	siip_sign.py
```


### STEP 5: Run SIIP Sign Tool to sign the SIIP image

For example:

```
siip_sign.py sign -i OseFw.bin -k privkey.pem -o out.bin

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
* `out.bin` : Signed `OseFw.bin` with manifest data (Firmware Blob Manifest and Metadata)
