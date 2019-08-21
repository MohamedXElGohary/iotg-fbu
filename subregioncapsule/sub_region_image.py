# @file
# Sub Region Image functions
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import struct
import sys
import os
import shutil
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sub_region_descriptor as Srd

# TODO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from siip_support import ToolsLoc as TDir  # noqa: E402

default_workspace = "./temp/"

section_name_lookup_table = {
    "EBA4A247-42C0-4C11-A167-A4058BC9D423": "IntelOseFw",
    "12E29FB4-AA56-4172-B34E-DD5F4B440AA9": "IntelTsnMacAddr",
    "4FB7994D-D878-4BD1-8FE0-777B732D0A31": "IntelOseTsnMacConfig",
}


def create_buffer_from_data_field(data_field):
    buffer = None
    if data_field.Type == Srd.data_types.FILE:
        buffer = bytearray(data_field.ByteSize)  # Allocate the buffer
        with open(data_field.Value, "rb") as DataFile:
            tmp = DataFile.read(data_field.ByteSize)
        buffer[:len(tmp)] = tmp  # copy data to the beginning of the buffer

    if data_field.Type == Srd.data_types.STRING:
        fmt = "{}s".format(data_field.ByteSize)
        if data_field.Value == "_STDIN_":
            buffer = struct.pack(fmt, bytes(sys.stdin.readline(), "utf-8"))
        else:
            buffer = struct.pack(fmt, bytes(data_field.sValue, "utf-8"))

    if data_field.Type in [Srd.data_types.DECIMAL, Srd.data_types.HEXADECIMAL]:
        buffer = data_field.dValue.to_bytes(data_field.ByteSize, "little")

    return buffer


def generate_sub_region_image(ffs_file, output_file="./output.bin"):
    with open(output_file, "wb") as out_buffer:
        for data_field in ffs_file.data:
            line_buffer = create_buffer_from_data_field(data_field)
            out_buffer.write(line_buffer)


def lookup_section_name(ffs_guid):
    try:
        return section_name_lookup_table[ffs_guid]
    except KeyError:
        return None


def create_gen_sec_command(
    ffs_file, image_file=None, index=0, output_file="SubRegionSec.sec", name=None
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


def create_gen_ffs_command(ffs_file, section_file, output_file="SubRegionFfs.ffs"):
    gen_ffs_cmd = ["GenFfs"]
    gen_ffs_cmd += ["-o", output_file]
    gen_ffs_cmd += ["-t", "EFI_FV_FILETYPE_FREEFORM"]
    gen_ffs_cmd += ["-g", ffs_file.s_ffs_guid]
    gen_ffs_cmd += ["-i", section_file]
    return gen_ffs_cmd


def create_gen_fv_command(sub_region_desc, output_fv_file, ffs_files):
    gen_fv_cmd = ["GenFv"]
    gen_fv_cmd += ["-o", output_fv_file]
    gen_fv_cmd += ["-b", "0x1000"]
    gen_fv_cmd += ["-f", " -f ".join(ffs_files)]
    gen_fv_cmd += [
        "-g",
        "8C8CE578-8A3D-4F1C-9935-896185C32DD3",
    ]  # gEfiFirmwareFileSystem2Guid
    gen_fv_cmd += ["--FvNameGuid", sub_region_desc.s_fv_guid]
    return gen_fv_cmd


def create_clean_workspace(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)


def generate_sub_region_fv(
        image_file, sub_region_descriptor, output_fv_file="./SubRegion.FV"
):
    sub_region_image = "SubRegionImage.bin"
    workspace_path = default_workspace
    create_clean_workspace(workspace_path)

    if os.name == "nt":
        bin_path = TDir.TOOLSWINDIR
    else:
        print("Only support Windows OS")
        exit(-1)
    os.environ["PATH"] += os.pathsep + bin_path

    fv_ffs_file_list = []
    for file_index, ffs_file in enumerate(sub_region_descriptor.ffs_files):
        generate_sub_region_image(ffs_file, sub_region_image)
        sec_file_path = "{0}SubRegionSec{1}.sec".format(workspace_path, file_index)
        gen_sec_cmd = create_gen_sec_command(
            ffs_file,
            image_file=sub_region_image,
            index=file_index,
            output_file=sec_file_path,
        )
        p_open_object = subprocess.Popen(
            " ".join(gen_sec_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while p_open_object.returncode is None:
            p_open_object.wait()
        if p_open_object.returncode != 0:
            print("Error generating Section")
            exit(-1)

        sec_ui_name = lookup_section_name(ffs_file.ffs_guid)
        if sec_ui_name is not None:
            sec_ui_file = "{0}SubRegionSecUi{1}.sec".format(workspace_path, file_index)
            gen_sec_ui_cmd = create_gen_sec_command(
                ffs_file, name=sec_ui_name, output_file=sec_ui_file
            )
            p_open_object = subprocess.Popen(
                " ".join(gen_sec_ui_cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            while p_open_object.returncode is None:
                p_open_object.wait()
            if p_open_object.returncode != 0:
                print("Error generating UI Section")
                exit(-1)

            # Cat Image Section with UI Section
            with open(sec_file_path, "ab") as sec_file_handle, open(
                sec_ui_file, "rb"
            ) as sec_ui_file_handle:
                sec_file_handle.write(sec_ui_file_handle.read())

        ffs_file_path = "{0}SubRegionFfs{1}.ffs".format(workspace_path, file_index)
        gen_ffs_cmd = create_gen_ffs_command(
            ffs_file, sec_file_path, output_file=ffs_file_path
        )
        p_open_object = subprocess.Popen(
            " ".join(gen_ffs_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        while p_open_object.returncode is None:
            p_open_object.wait()
        if p_open_object.returncode != 0:
            print("Error generating FFS File")
            exit(-1)
        fv_ffs_file_list.append(ffs_file_path)

    gen_fv_cmd = create_gen_fv_command(sub_region_descriptor, output_fv_file, fv_ffs_file_list)
    p_open_object = subprocess.Popen(
        " ".join(gen_fv_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    print(" ".join(gen_fv_cmd))
    while p_open_object.returncode is None:
        p_open_object.wait()
    if p_open_object.returncode != 0:
        print("Error generating FV File")
        exit(-1)


if __name__ == "__main__":
    sub_region_fv_file = "./SubRegionFv.fv"
    sub_region_image_file = "./SubRegionData.bin"
    sub_region_desc = Srd.SubRegionDescriptor()
    sub_region_desc.parse_json_data("./Tests/Collateral/GoodSubRegDescExample.json")
    generate_sub_region_image(sub_region_desc, sub_region_image_file)
    generate_sub_region_fv(sub_region_desc, sub_region_fv_file)
