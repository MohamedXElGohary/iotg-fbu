# test_devices.py
import unittest.mock as mock
import flashtool as kbydevices
import pytest
import subprocess as sp
import flashtool.linuxutils as lu


@pytest.fixture(params=["FA57B007B04D0007", "3-ma2480"])
def serialno(request):
    yield request.param


@pytest.fixture(params=["fip.bin", "/home/somewhere/fip.bin", "../fip/fip.bin"])
def fip(request):
    yield request.param 

def test_lsusb_get_devices(serialno):

    with mock.patch("flashtool.linuxutils.subprocess") as mocked:
        lsusb_stdout = b'\nBus 002 Device 009: ID 8087:0b39 Intel Corp. \nDevice Descriptor:\n  bLength                18\n  bDescriptorType         1\n  bcdUSB               2.00\n  bDeviceClass            0 (Defined at Interface level)\n  bDeviceSubClass         0 \n  bDeviceProtocol         0 \n  bMaxPacketSize0        64\n  idVendor           0x8087 Intel Corp.\n  idProduct          0x0b39 \n  bcdDevice            0.01\n  iManufacturer           1 Intel Corp.\n  iProduct                2 Intel Movidius 3xxx\n  iSerial                 3 %b\n  bNumConfigurations      1\n  Configuration Descriptor:\n    bLength                 9\n    bDescriptorType         2\n    wTotalLength           32\n    bNumInterfaces          1\n    bConfigurationValue     1\n    iConfiguration          0 \n    bmAttributes         0x80\n      (Bus Powered)\n    MaxPower              500mA\n    Interface Descriptor:\n      bLength                 9\n      bDescriptorType         4\n      bInterfaceNumber        0\n      bAlternateSetting       0\n      bNumEndpoints           2\n      bInterfaceClass       255 Vendor Specific Class\n      bInterfaceSubClass     66 \n      bInterfaceProtocol      3 \n      iInterface              0 \n      Endpoint Descriptor:\n        bLength                 7\n        bDescriptorType         5\n        bEndpointAddress     0x81  EP 1 IN\n        bmAttributes            2\n          Transfer Type            Bulk\n          Synch Type               None\n          Usage Type               Data\n        wMaxPacketSize     0x0200  1x 512 bytes\n        bInterval               0\n      Endpoint Descriptor:\n        bLength                 7\n        bDescriptorType         5\n        bEndpointAddress     0x01  EP 1 OUT\n        bmAttributes            2\n          Transfer Type            Bulk\n          Synch Type               None\n          Usage Type               Data\n        wMaxPacketSize     0x0200  1x 512 bytes\n        bInterval               0\nDevice Qualifier (for other device speed):\n  bLength                10\n  bDescriptorType         6\n  bcdUSB               2.00\n  bDeviceClass            0 (Defined at Interface level)\n  bDeviceSubClass         0 \n  bDeviceProtocol         0 \n  bMaxPacketSize0        64\n  bNumConfigurations      1\nDevice Status:     0x0000\n  (Bus Powered)\n' % bytes(serialno, "utf-8")
        mocked.run.return_value = sp.CompletedProcess(
            args=["lsusb", "-v", "-d", "8087:0b39"],
            returncode=0,
            stdout=lsusb_stdout
        )
        devices = lu.kmb_lsusb("iSerial")
    assert len(devices) == 1
    assert devices[0]["iSerial"] == serialno

def test_fastboot_get_devices(serialno):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = bytes("{}\tfastboot\n".format(serialno), "utf-8")
        mocked.run.return_value = sp.CompletedProcess(
            args=["./fastboot", "devices"],
            returncode=0,
            stdout=stdout
        )

        devices = kbydevices.USBDevice.discover()

        assert len(devices) == 1
        assert devices[0].dev_id == serialno


def test_usb_download(serialno, fip):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = b"Sending '/home/tooldev/develop/fip/fip.bin' (687 KB) OKAY [  0.172s]\nFinished. Total time: 0.173s"
        mocked.run.return_value = sp.CompletedProcess(
            args=["./fastboot", "-s", serialno, "stage", fip],
            returncode=0,
            stdout=stdout
        )

        usb = kbydevices.USBDevice(serialno)
        result, _, _, _ = usb.download(fip)

        assert result == {
            "download": {
                "time": 0.172,
                "status": "OKAY",
                "size": "687 KB",
            },
            "total": {"time": 0.173, "status": "Finished"},
        }

def test_pcie_get_devices(serialno):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = bytes("Device Found name {}".format(serialno), "utf-8")
        mocked.run.return_value = sp.CompletedProcess(
            args=["./XLinkDevices"],
            returncode=0,
            stdout=stdout
        )

        devices = kbydevices.XLinkDevice.discover()

        assert len(devices) == 1
        assert devices[0].dev_id == serialno


def test_pcie_download(serialno, fip):
    with mock.patch("flashtool.shutil") as shutil_mocked:
        with mock.patch("flashtool.subprocess") as mocked:
            shutil_mocked.copy.return_value = None
            stdout = b"Device Found name 3-ma2480\nBooting /lib/firmware/myriad.mvcmd\nDevice boot Finished"
            mocked.run.return_value = sp.CompletedProcess(
                args=["./xlinkdownload"],
                returncode=0,
                stdout=stdout
            )

            pcie = kbydevices.XLinkDevice(serialno)
            result, _, _, _ = pcie.download(fip)

            assert result["total"]["status"] == "Finished" 

def test_fip_check(fip):
    with mock.patch("flashtool.subprocess") as spmocked:
        stdout = b'Trusted Boot Firmware BL2: offset=0x1A0, size=0x10348, cmdline="--tb-fw"\nEL3 Runtime Firmware BL31: offset=0x104F0, size=0x10058, cmdline="--soc-fw"\nNon-Trusted Firmware BL33: offset=0x20550, size=0x8AC5C, cmdline="--nt-fw"\nTrusted key certificate: offset=0xAB1B0, size=0x2C0, cmdline="--trusted-key-cert"\nSoC Firmware key certificate: offset=0xAB470, size=0x21E, cmdline="--soc-fw-key-cert"\nNon-Trusted Firmware key certificate: offset=0xAB690, size=0x22D, cmdline="--nt-fw-key-cert"\nTrusted Boot Firmware BL2 certificate: offset=0xAB8C0, size=0x2F0, cmdline="--tb-fw-cert"\nSoC Firmware content certificate: offset=0xABBB0, size=0x20D, cmdline="--soc-fw-cert"\nNon-Trusted Firmware content certificate: offset=0xABDC0, size=0x21E, cmdline="--nt-fw-cert"\n'
        spmocked.run.return_value = sp.CompletedProcess(
            args=["./fiptool", "info", "{}".format(fip)],
            returncode=0,
            stdout=stdout
        )

        output = kbydevices.fip_check(fip)

        assert (
            output == '\nTrusted Boot Firmware BL2: offset=0x1A0, size=0x10348, cmdline="--tb-fw"\nEL3 Runtime Firmware BL31: offset=0x104F0, size=0x10058, cmdline="--soc-fw"\nNon-Trusted Firmware BL33: offset=0x20550, size=0x8AC5C, cmdline="--nt-fw"\nTrusted key certificate: offset=0xAB1B0, size=0x2C0, cmdline="--trusted-key-cert"\nSoC Firmware key certificate: offset=0xAB470, size=0x21E, cmdline="--soc-fw-key-cert"\nNon-Trusted Firmware key certificate: offset=0xAB690, size=0x22D, cmdline="--nt-fw-key-cert"\nTrusted Boot Firmware BL2 certificate: offset=0xAB8C0, size=0x2F0, cmdline="--tb-fw-cert"\nSoC Firmware content certificate: offset=0xABBB0, size=0x20D, cmdline="--soc-fw-cert"\nNon-Trusted Firmware content certificate: offset=0xABDC0, size=0x21E, cmdline="--nt-fw-cert"'
        )
