# pcie.py

import os
import mmap
import shutil
import time


def download_fip(dev_path, fip):
    shutil.copy(fip, '/lib/firmware/intel-kmb/fip.bin')
    start = time.perf_counter()
    sys_base_path = "/sys/bus/pci/devices/"
    boot_api = "test_boot"
    sys_path = os.path.join(sys_base_path, dev_path, boot_api)
    with open(sys_path, 'w') as f:
        f.write('1')
    end = time.perf_counter()
    return "{0:.3f}".format(end - start)

def check_recovery(mem_offset):
    if type(mem_offset) == str:
        mem_offset = "".join(["0x", mem_offset])
        mem_offset = int(mem_offset, base=16)
    filename = '/dev/mem'
    fd = os.open(filename, os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(fd, 8, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=mem_offset)
    return mem.read() == b'VPUEMMC-'

if __name__=="__main__":
    if check_recovery('d2000000'):
        domain, bus, slot, func = '0000', '02', '00', '0'
        dev_path = ".".join([":".join([domain, bus, slot]), func])
        fip = 'fip.bin'
        print(download_fip(dev_path, fip))
