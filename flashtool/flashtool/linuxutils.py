# linuxutils.py

import subprocess
import re


lsusb_cmd=["lsusb", "-v", "-d", "8087:0b39"]
lsusb_parse=re.compile(r"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<dev>\d+):\s+ID\s+8087:0b39\s+(?P<prod>.+)(?P<desc>(?:.|\n)*?)(?=\n\n)")
lspci_cmd = ["lspci", "-vvD", "-d", "8086:6240"]
lspci_parse = re.compile(r"(?P<domain>\d+):(?P<bus>\d+):(?P<slot>\d+)\.(?P<func>\d+)\s+(?P<prod>.+)(?P<desc>(?:.|\n)*?)(?=\n\n)")
bar2_parse = re.compile(r"Region\s+2:\s+Memory\s+at\s+(\w+)\s+.+")

def kmb_lsusb(*dev_attrs, **sp_options):

    _, _, stdout = _run(lsusb_cmd, **sp_options)
    stdout = "\n".join([stdout, ""]) # adding a \n to the stdout of lsusb so the re pattern will work
    devices = [m.groupdict() for  m in lsusb_parse.finditer(stdout)]

    for device in devices:
        for line in device.pop("desc").split("\n"):
            splitted = re.split(r'\s+', line.strip())
            if splitted[0] in dev_attrs:
                device[splitted[0]] = splitted[-1]

    return devices

def kmb_lspci(*dev_attrs, **sp_options):
    _, _, stdout = _run(lspci_cmd, **sp_options)
    devices = [m.groupdict() for  m in lspci_parse.finditer(stdout)]
    for device in devices:
        for line in device.pop("desc").split("\n"):
            #import pdb;pdb.set_trace()
            m = bar2_parse.match(line.strip())
            try:
                device["bar2"] = m.group(1)
            except AttributeError:
                for attr in dev_attrs:
                    if attr in line:
                        splitted = re.split(r'\s+', line.strip())
                        device[attr] = splitted[-1]
    return devices

def _run(cmd, **options):
    """call subprocess.run().
    Returns stdout with enclosing whitespaces stripped
    """
    _ = options.setdefault("stdout", subprocess.PIPE)
    _ = options.setdefault("stderr", subprocess.STDOUT)
    completed = subprocess.run(cmd, **options)
    args, returncode, stdout = completed.args, completed.returncode, completed.stdout
    stdout = stdout.decode("utf-8")
    return args, returncode, stdout
