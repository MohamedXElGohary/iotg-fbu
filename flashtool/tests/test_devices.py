# test_devices.py
import unittest.mock as mock
import flashtool as kbydevices
import pytest
import subprocess as sp


@pytest.fixture(params=["FA57B007B04D0007", "3-ma2480"])
def dev_id(request):
    yield request.param


@pytest.fixture(params=["fip.bin", "/home/somewhere/fip.bin", "../fip/fip.bin"])
def fip(request):
    yield request.param


def test_usb_get_devices(dev_id):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = bytes("{}\tfastboot\n".format(dev_id), "utf-8")
        mocked.run.return_value = sp.CompletedProcess(
            args=["./fastboot", "devices"],
            returncode=0,
            stdout=stdout
        )

        devices = kbydevices.USBDevice.discover()

        assert len(devices) == 1
        assert devices[0].dev_id == dev_id


def test_usb_download(dev_id, fip):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = b"Sending '/home/tooldev/develop/fip/fip.bin' (687 KB) OKAY [  0.172s]\nFinished. Total time: 0.173s"
        mocked.run.return_value = sp.CompletedProcess(
            args=["./fastboot", "-s", dev_id, "stage", fip],
            returncode=0,
            stdout=stdout
        )

        usb = kbydevices.USBDevice(dev_id)
        result, args, returncode, stdout = usb.download(fip)

        assert result == {
            "download": {
                "time": 0.172,
                "status": "OKAY",
                "size": "687 KB",
            },
            "total": {"time": 0.173, "status": "Finished"},
        }

def test_pcie_get_devices(dev_id):
    with mock.patch("flashtool.subprocess") as mocked:
        stdout = bytes("Device Found name {}".format(dev_id), "utf-8")
        mocked.run.return_value = sp.CompletedProcess(
            args=["./xlinkdevices"],
            returncode=0,
            stdout=stdout
        )

        devices = kbydevices.PCIEDevice.discover()

        assert len(devices) == 1
        assert devices[0].dev_id == dev_id


def test_pcie_download(dev_id, fip):
    with mock.patch("flashtool.shutil") as shutil_mocked:
        with mock.patch("flashtool.subprocess") as mocked:
            shutil_mocked.copy.return_value = None
            stdout = b"Device Found name 3-ma2480\nBooting /lib/firmware/myriad.mvcmd\nDevice boot Finished"
            mocked.run.return_value = sp.CompletedProcess(
                args=["./xlinkdownload"],
                returncode=0,
                stdout=stdout
            )

            pcie = kbydevices.PCIEDevice("3-ma2480")
            result, args, returncode, stdout = pcie.download(fip)

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
