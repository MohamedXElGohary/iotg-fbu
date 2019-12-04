import subprocess
import abc
import re
import os
import time
import shutil
from . import linuxutils
from . import pcie


# Note:  more names can be added to __all__ later.
__all__ = (["fip_check", "USBDevice", "FastbootDevice", "PCIEDevice", "DeviceNotFoundError", "FIPCheckError"])

# Exception classes used by this module.
class ToolError(Exception): pass


class DeviceDownloadError(ToolError):
    def __init__(self, err_str, dev):
        self.err_str = err_str
        self.dev = dev

    def __str__(self):
        return "Download failed for device:{} due to {}".format(self.dev, self.err_str)


class DeviceNotFoundError(ToolError):
    def __init__(self, err_msg):
        self.err_msg = err_msg
    def __str__(self):
        return self.err_msg


class FIPCheckError(ToolError):
    def __init__(self, err_str, fip):
        self.err_str = err_str
        self.fip = fip

    def __str__(self):
        return "FIP check failed for FIP:{} due to {}".format(self.fip, self.err_str)


class BaseDevice(abc.ABC):
    """Abstract Base Class to create a new device class

    """
    @classmethod
    @abc.abstractmethod
    def discover(cls):
        raise NotImplementedError

    @abc.abstractmethod
    def download(self, fip):
        raise NotImplementedError


class FastbootDevice(BaseDevice):
    """A USB Device class which also has a factory method which returns a list of USB devices in the system

    Attributes:
    dev_id: A unique identifier for each USB device instance
    """
    get_all_cmd = ["./fastboot", "devices"]
    get_parse = r"^(\w+)\sfastboot"
    # dl_cmd = ["./fastboot", "-s", "dev_id", "flash", "boot", "fip"]
    dl_cmd = ["./fastboot", "stage", "fip"]
    dl_parse = r"^Sending\s+'(.+)'\s+\((.+)\)\s+(OKAY)\s+\[\s+(.+)s\]\s+(Finished).\s+Total\s+time:\s+(.+)s\s*"

    def __init__(self, dev_id):
        self.dev_id = dev_id

    def __repr__(self):
        return "USB Fastboot: SN {} Intel Movidius Keembay 3xxx.".format(self.dev_id)

    @classmethod
    def discover(cls, **kwds):
        """Returns a list of devices

        Args:
        **kwds: keyword args for subprocess.run(). E.g timeout=10

        Parses stdout of "./fastboot devices" command to get the serial no. For each serial number gotten,
        instantiates the device class and append instance to list. Returns list

        example of stdout expected: "FA57B007B04D0007        fastboot"
        """
        try:
            args, returncode, stdout = _run_cmd(cls.get_all_cmd, **kwds)
        except subprocess.TimeoutExpired:
            stdout = ""
        devices = []
        for line in stdout.split("\n"):
            m = re.match(r"^(\S+)\sfastboot", line)
            try:
                dev_id = m.group(1)
                devices.append(cls(dev_id))
            except AttributeError:
                continue
        return devices

    def download(self, fip, **kwds):
        """Download FIP file into device. Returns results in a dictionary.

        Args:
        **kwds: keyword args for subprocess.run(). E.g timeout=10

        Parses stdout of "./fastboot -s {dev_id} flash boot {fip}" command to get the serial no. For each serial number gotten,
        instantiates the device class and append instance to list. Returns list

        example of stdout expected:
        "Sending 'boot' (687 KB)                            OKAY [  0.124s]
        Writing 'boot'                                     OKAY [  1.102s]
        Finished. Total time: 1.519s"

        example of result in dictionary
        {
            'download': {'status': 'OKAY', 'time': 0.112, 'size': '687 KB'}, 
            'total': {'status': 'Finished', 'time': 0.428}
        }
        """
        retries = kwds.pop("retries", None)
        self.dl_cmd[2] = fip
        args, returncode, stdout = _run_cmd(self.dl_cmd, **kwds)
        m = re.match(self.dl_parse, stdout)
        result = {}
        try:
            result["download"] = {"size": m.group(2), "status": m.group(3), "time": float(m.group(4))}
            result["total"] = {"status": m.group(5), "time": float(m.group(6))}
            return result, args, returncode, stdout
        except:
            raise DeviceDownloadError(stdout, self) from None


class USBDevice(BaseDevice):
    get_all_cmd = ["lsusb", "-d", "8087:0b39"]
    get_parse = r"^Bus\s+(\w+)\s+Device\s+(\w+):\s+ID\s+\w+:\w+\s+(.+)"
    dl_cmd = ["./fastboot", "-s", "dev_id", "stage", "fip"]
    dl_parse = r"^Sending\s+'(.+)'\s+\((.+)\)\s+(OKAY)\s+\[\s+(.+)s\]\s+(Finished).\s+Total\s+time:\s+(.+)s\s*"

    def __init__(self, bus, dev, prod, serialno):
        self.bus = bus
        self.dev = dev
        self.prod = prod
        self.serialno = serialno

    @classmethod
    def discover(cls, **kwds):
        devices = [cls(device["bus"], device["dev"], device["prod"], device["iSerial"]) for device in linuxutils.kmb_lsusb("iSerial")]
        # try:
        #     args, returncode, stdout = _run_cmd(cls.get_all_cmd, **kwds)
        # except subprocess.TimeoutExpired:
        #     stdout = ""
        # devices = []
        # for line in stdout.split("\n"):
        #     m = re.match(cls.get_parse, line)
        #     try:
        #         bus = m.group(1)
        #         dev = m.group(2)
        #         devices.append(cls(bus, dev))
        #         break
        #     except AttributeError:
        #         continue
        return devices

    def download(self, fip, **kwds):
        retries = kwds.pop("retries", 0)
        self.dl_cmd[2], self.dl_cmd[4] = self.serialno, fip
        args, returncode, stdout = _run_cmd(self.dl_cmd, **kwds)
        m = re.match(self.dl_parse, stdout)
        result = {}
        try:
            result["download"] = {"size": m.group(2), "status": m.group(3), "time": float(m.group(4))}
            result["total"] = {"status": m.group(5), "time": float(m.group(6))}
            return result, args, returncode, stdout
        except AttributeError:
            raise DeviceDownloadError(stdout, self) from None

    def __repr__(self):
        return "USB Bus {} Device {} SerialNumber {} ID 8087:0b39 Intel Movidius Keembay 3xxx.".format(self.bus, self.dev, self.serialno)


class PCIEDevice:
    def __init__(self, domain, bus, slot, func, prod, serialno, bar2):
        self.domain = domain
        self.bus = bus
        self.slot = slot
        self.func = func
        self.prod = prod
        self.serialno = serialno
        self.bar2 = bar2

    @classmethod
    def discover(cls, **kwds):
        return [cls(device["domain"],
                device["bus"],
                device["slot"],
                device["func"],
                device["prod"],
                device["Serial"],
                device["bar2"]) for device in linuxutils.kmb_lspci("Serial") if pcie.check_recovery(device["bar2"])]

    @property
    def dev_path(self):
        return ".".join([":".join([self.domain, self.bus, self.slot]), self.func])

    def download(self, fip, **kwds):
        result = {"total": {"status": "success", "time": pcie.download_fip(self.dev_path, fip)}}
        return result, "pcie.download_fip({},{})".format(self.dev_path, fip), 0, "NA"

    def __repr__(self):
        return "PCIE {} SerialNumber {} Intel Movidius Keembay 3xxx.".format(self.dev_path, self.serialno)


class XLinkDevice(BaseDevice):
    """A PCIE Device class which also has a factory method which returns a list of PCIE devices in the system

    Attributes:
    name: A unique identifier for each PCIE device instance
    """
    get_all_cmd = ["./xlinkdevices"]
    dl_cmd = ["./xlinkdownload"]

    def __init__(self, dev_id):
        self.dev_id = dev_id

    def __repr__(self):
        return "PCIE: ID {} Intel Movidius Keembay 3xxx.".format(self.dev_id)

    @classmethod
    def discover(cls, **kwds):
        """Returns a list of devices

        Parses stdout of "./xlinkdevices" command to get the serial no. For each serial number gotten,
        instantiates the device class and append instance to list. Returns list

        example of stdout expected: "Device Found name 3-ma2480"

        Args:
        **kwds: keyword args for subprocess.run(). E.g timeout=10
        """
        try:
            _, _, stdout = _run_cmd(cls.get_all_cmd, **kwds)
        except subprocess.TimeoutExpired:
            stdout = ""
        devices = []
        for line in stdout.split("\n"):
            m = re.match(r"^Device\sFound\sname\s(.+)", line)
            try:
                dev_id = m.group(1)
                devices.append(cls(dev_id))
            except AttributeError:
                continue
        return devices

    def download(self, fip, **kwds):
        """Downloads FIP into device and returns results in a dictionary.

        Moves FIP file to /lib/firmware. Parses stdout of "./xlinkdownload" command. Time is calculated using time.perf_counter()

        example of stdout expected:
        "Device Found name 3-ma2480 
        Booting /lib/firmware/myriad.mvcmd
        Device boot Finished"

        example of result in dictionary
        {
            "total":{"status":"Finished", "time":1.519}
        }

        Args:
        **kwds: keyword args for subprocess.run(). E.g timeout=10
        """
        # retries = kwds.pop("retries", 0)
        shutil.copy(fip, '/lib/firmware/myriad.mvcmd')
        start = time.perf_counter()
        args, returncode, stdout = _run_cmd(self.dl_cmd, **kwds)
        end = time.perf_counter()
        elapsed = "{0:.3f}".format(end - start)
        pattern = r"^Device\sFound\sname\s(\w+-\w+)\s+Booting\s+\/lib\/firmware\/myriad.mvcmd\s+Device\sboot\s(Finished)"
        m = re.match(pattern, stdout)
        result = {}
        try:
            result["total"] = {"status": m.group(2), "time": elapsed}
            return result, args, returncode, stdout
        except:
            raise DeviceDownloadError(stdout, self) from None


# for subprocess.run()
curr_dir = os.path.dirname(__file__)
bin_rel_dir = "thirdparty"
bin_dir = os.path.join(curr_dir, bin_rel_dir)

def _run_cmd(cmd, **kwds):
    """call subprocess.run().
    Returns stdout with enclosing whitespaces stripped
    """
    _ = kwds.setdefault("stdout", subprocess.PIPE)
    _ = kwds.setdefault("stderr", subprocess.STDOUT)
    _ = kwds.setdefault("cwd", bin_dir)
    completed = subprocess.run(cmd, **kwds)
    args, returncode, stdout = completed.args, completed.returncode, completed.stdout
    stdout = stdout.decode("utf-8").strip()
    return args, returncode, stdout

def fip_check(fip, **kwds):
    cmd = ["./fiptool", "info", "{}".format(fip)]
    args, returncode, stdout = _run_cmd(cmd, **kwds)
    pattern = r"^ERROR:\s+(.+)"
    m = re.match(pattern, stdout)
    if m:
        err_str = m.group(1)
        raise FIPCheckError(err_str, fip)
    return "\n{}".format(stdout)

# # Module functions: Frequent use cases of the device classes.
# def discover(*classes, **kwds):
#     devices = [device for cls in classes if issubclass(cls, BaseDevice) for device in cls.discover(**kwds)]
#     if devices:
#         return devices
#     raise DeviceNotFoundError
