# Running USB Proof of Concept
This POC(Proof of Concept) is to demonstrate the ability to detect devices in USB Boot Mode and issue fastboot DOWNLOAD command which downloads the FIP(firmware image package) into the device.
## System Requirements:
1. Intel® Movidius™ Myriad™ X Development Board (MV0235)
2. Linux Ubuntu 16.04
3. Python 3.5
## Emulating Keembay behavior in MyriadX with modified ROM
### Background
We need to emulate Keembay behavior in MyriadX to test our flash tool. This is due to:
1. No flash command available in myriadx. Currently it just responds, 'not supported'. As a workaround, we can add it to the myriadx rom code to emulate it having the command we want. Replace ma_fastboot.c in /mv_myriadx-rom/src/leon/3-drv/fastboot/ with the version in this repo.
2. Serial number contains non-ASCII charecters. This makes it difficut to select device using serial number in terminal. As a workaround, we can hardcode the serial number. Replace ma_usbd_setup_descriptors.c and ma_usbd_setup_descriptors.h in /mv_myriadx-rom/src/leon/3-drv/usbd/ with the version in this repo.
### Steps to change and load the new ROM
1. Before doing this, the user should have setup the environment as per this guide: https://wiki.ith.intel.com/x/wHyrTQ
2. Replace the original files with files from the directory mv_myriadx-rom/ here.
3. Build the rom.
```
$ cd mv_myriadx-rom
$ make -f Makefile.app clean
$ make -f Makefile.app
```
3. Alternatively, you can copy the prebuilt myriad2_rom_image.elf in this repo to mv_myriadx-rom/output/

4. To load the rom, on a separate terminal, start the debug server.
```
$ cd ~/WORK/Tools/18.08.3/linux64/bin/
$ sudo ./moviDebugServer
```
5. Back in the first terminal.
```
$ make -f Makefile.app debugi
```
6. In the debugger shell, run
```
breset; loadelf ./output/myriad2_rom_image.elf; run
```
## Install and run:
1. Install and run following the readme.md in the fwupdate repository.
2. The download can be verified from the Movidius Debugger (moviDebug2) terminal.
```
UART: Cmd: getvar:max-download-size
UART: Resp: OKAY1048576
UART: Cmd: download:000abfe0
UART: Resp: DATA000abfe0
UART: Resp: OKAY
UART: Cmd: flash:boot
UART: Resp: OKAY
```
# Running PCIE Proof of Concept
This POC(Proof of Concept) is to demonstrate the ability to detect devices and download the FIP(firmware image package) into the device using XLink User API.
## System Requirements:
1. Intel® Movidius™ Myriad™ X Development Board (MV0235)
2. Linux Ubuntu 16.04
3. Python 3.5
4. Intel® Movidius™ Myriad™ X Development Kit (MDK). You can clone it from here: https://tf-amr-1.devtools.intel.com/ctf/code/projects.ntg_kmb/git/scm.mdk/tree?treeId=refs%2Fheads%2Fdevelop
## Steps to run
1. cd to <mdk_release>/mdk/examples/HowTo/XLink/SingleStream/pc
2. Replace main.c with the one in the pc/ directory here.
3. Place the myriad.mvcmd in /lib/firmware/
4. Follow the steps in <mdk_release>/mdk/examples/HowTo/XLink/SingleStream/readme.txt to build and run.
5. Output below can be seen that shows fip file downloaded.
```
$ sudo ./XLink
XLink pc example application used to communicate to the Myriad USB device.
Device Found name 3-ma2480 
Booting /lib/firmware/myriad.mvcmd
Myriad was booted
Initialize done
XLinkConnect done - link Id 0
reset success
```

