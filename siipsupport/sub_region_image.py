# @file
# Converts Sub Regions JSON into binary image
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import struct
import sys

from siipsupport import sub_region_descriptor as srd


def create_gen_sec_command(
    ffs_file, image_file=None, index=0,
        output_file="SubRegionSec.sec", name=None
):
    compression_scheme = None
    gen_sec_cmd = ["GenSec"]
    gen_sec_cmd += ["-o", output_file]
    if name is not None:
        section_type = "EFI_SECTION_USER_INTERFACE"
    elif ffs_file.compression is True:
        section_type = "EFI_SECTION_COMPRESSION"
        compression_scheme = "PI_STD"
    else:
        section_type = "EFI_SECTION_RAW"
        compression_scheme = "PI_NONE"
    gen_sec_cmd += ["-s", section_type]
    if compression_scheme is not None:
        gen_sec_cmd += ["-c", compression_scheme]
    if image_file is not None:
        gen_sec_cmd += [image_file]
    if name is not None:
        gen_sec_cmd += ["-n", name]
    return gen_sec_cmd


def create_gen_ffs_command(ffs_file, section_file,
                           output_file="SubRegionFfs.ffs"):
    gen_ffs_cmd = ["GenFfs"]
    gen_ffs_cmd += ["-o", output_file]
    gen_ffs_cmd += ["-t", "EFI_FV_FILETYPE_FREEFORM"]
    gen_ffs_cmd += ["-g", ffs_file.s_ffs_guid]
    gen_ffs_cmd += ["-i", section_file]
    return gen_ffs_cmd


def create_gen_fv_command(sub_region_desc, output_fv_file, ffs_files):
    gen_fv_cmd = ["GenFv"]
    gen_fv_cmd += ["-o", output_fv_file]
    gen_fv_cmd += ["-b", "0x10000"]
    gen_fv_cmd += ["-f", " -f ".join(ffs_files)]
    gen_fv_cmd += [
        "-g",
        "8C8CE578-8A3D-4F1C-9935-896185C32DD3",
    ]  # gEfiFirmwareFileSystem2Guid
    gen_fv_cmd += ["--FvNameGuid", sub_region_desc.s_fv_guid]
    return gen_fv_cmd


def create_buffer_from_data_field(data_field):
    buffer = None
    if data_field.Type == srd.data_types.FILE:
        buffer = bytearray(data_field.ByteSize)  # Allocate the buffer
        with open(data_field.Value, "rb") as DataFile:
            tmp = DataFile.read(data_field.ByteSize)
        buffer[:len(tmp)] = tmp  # copy data to the beginning of the buffer

    if data_field.Type == srd.data_types.STRING:
        fmt = "{}s".format(data_field.ByteSize)
        if data_field.Value == "_STDIN_":
            buffer = struct.pack(fmt, bytes(sys.stdin.readline(), "utf-8"))
        else:
            buffer = struct.pack(fmt, bytes(data_field.sValue, "utf-8"))

    if data_field.Type in [srd.data_types.DECIMAL,
                           srd.data_types.HEXADECIMAL]:
        buffer = data_field.dValue.to_bytes(data_field.ByteSize, "little")

    return buffer


def generate_sub_region_image(ffs_file, output_file="./output.bin"):
    with open(output_file, "wb") as out_buffer:
        for data_field in ffs_file.data:
            line_buffer = create_buffer_from_data_field(data_field)
            out_buffer.write(line_buffer)
