#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# INTEL CONFIDENTIAL
# Copyright 2019 Intel Corporation.
#
# This software and the related documents are Intel copyrighted 
# materials, and your use of them is governed by the express license 
# under which they were provided to you ("License"). Unless the License
# provides otherwise, you may not use, modify, copy, publish, 
# distribute, disclose or transmit this software or the related 
# documents without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no 
# express or implied warranties, other than those that are expressly 
# stated in the License.
#

from __future__ import print_function

from ctypes import Structure, c_char, c_uint32, c_uint8, c_uint64, c_uint16, sizeof, ARRAY
import os
import re
import sys
import struct
import shutil
import subprocess
import argparse
import collections

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

try:
    from cryptography.hazmat.primitives import hashes as hashes
    from cryptography.hazmat.primitives import serialization as serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.asymmetric import padding as crypto_padding

    # Check its version
    import cryptography
    if cryptography.__version__ < '2.2.2':
        print("Error: Cryptography version must be 2.2.2 or higher"
              " (installed version: {})".format(cryptography.__version__))
        exit(1)

except ImportError:
    print("Error: Cryptography could not be found, please install using pip")
    sys.exit(1)


__version__ = "0.0.2"

RSA_KEYMOD_SIZE = 256
RSA_KEYEXP_SIZE = 4
KB = 1024
MB = 1024 * KB


def pack_num(val, minlen=0):
    buf = bytearray()
    while val > 0:
        if sys.version_info > (3, 0):
            buf += bytes([val & 0xff])
        else:
            buf += chr(val & 0xff)
        val >>= 8
    buf += bytearray(max(0, minlen - len(buf)))
    return buf


def compute_hash(data):
    '''Compute hash from data'''

    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data)
    result = digest.finalize()

    return result


def verify_hash(data, expected_hash):
    '''Compute hash from data and compare with expected value'''

    result = compute_hash(data)
    if result != expected_hash:
        raise Exception('Hash values mismatch!')

    return result


def compute_signature(data, privkey_pem):
    '''Compute signature from data'''

    with open(privkey_pem, 'rb') as privkey_file:
        key = serialization.load_pem_private_key(
            privkey_file.read(),
            password=None,
            backend=default_backend()
        )

    # Calculate signature using private key
    signature = key.sign(
        bytes(data), crypto_padding.PKCS1v15(), hashes.SHA256())

    return (signature, key)


def verify_signature(signature, data, pubkey_pem):
    '''Verify signature with public key'''

    with open(pubkey_pem, 'rb') as pubkey_file:
        puk = serialization.load_pem_public_key(
            pubkey_file.read(), backend=default_backend())

    # Raises InvalidSignature error if not match
    puk.verify(signature, data, crypto_padding.PKCS1v15(), hashes.SHA256())


def parse_cpd_header(cpd_data):
    '''Parse CPD header and return files information'''

    ptr = 0
    cpd = SUBPART_DIR_HEADER.from_buffer(cpd_data, 0)
    if cpd.header_marker != 0x44504324:
        print('Invalid input file. CPD signature not found.')
        exit(1)

    files = []
    entry_count = cpd.num_of_entries

    ptr += sizeof(SUBPART_DIR_HEADER)
    for i in range(entry_count):
        cpd_entry = SUBPART_DIR_ENTRY.from_buffer(cpd_data, ptr)
        files.append((cpd_entry.name.decode(),
                      cpd_entry.offset, cpd_entry.length))
        ptr += sizeof(SUBPART_DIR_ENTRY)

    return files


class SUBPART_DIR_HEADER(Structure):
    _pack_ = 1
    _fields_ = [
        ('header_marker', c_uint32),
        ('num_of_entries', c_uint32),
        ('header_version', c_uint8),
        ('entry_version', c_uint8),
        ('header_length', c_uint8),
        ('check_sum', c_uint8),
        ('subpart_name', ARRAY(c_char, 4)),
    ]


class SUBPART_DIR_ENTRY(Structure):
    _pack_ = 1
    _fields_ = [
        ('name', ARRAY(c_char, 12)),
        ('offset', c_uint32, 24),
        ('reserved1', c_uint32, 8),
        ('length', c_uint32),
        ('reserved2', c_uint32),
    ]


class METADATA_FILE_STRUCT(Structure):
    _pack_ = 1
    _fields_ = [
        ('size', c_uint32),
        ('id', c_uint32),
        ('version', c_uint32),
        ('num_of_modules', c_uint32),
        ('module_id', c_uint32),
        ('module_size', c_uint32),
        ('module_version', c_uint32),
        ('module_hash_size', c_uint32),
        ('module_entry_point', c_uint32),
        ('module_hash_alogorithm', c_uint32),
        ('module_hash_value', ARRAY(c_uint8, 32)),
        ('num_of_keys', c_uint32),
        ('key_usage_id', ARRAY(c_uint8, 16)),
        # Size of non-standard section follows
    ]


class FIRMWARE_MANIFEST_HEADER(Structure):
    _pack_ = 1
    _fields_ = [
        ('type', c_uint32),
        ('length', c_uint32),  # in DWORDS
        ('version', c_uint32),  # 0x10000
        ('flags', c_uint32),
        ('vendor', c_uint32),
        ('date', c_uint32),
        ('size', c_uint32),  # in DWORDS. max 2K
        ('id', c_uint32),  # '$MN2'
        ('num_of_metadata', c_uint32),
        ('structure_version', c_uint32),
        ('reserved', ARRAY(c_uint8, 80)),
        ('modulus_size', c_uint32),
        ('exponent_size', c_uint32),
        ('public_key', ARRAY(c_uint8, 256)),  # 256B for PKCS 1.5 2048bit
        ('exponent', ARRAY(c_uint8, 4)),
        ('signature', ARRAY(c_uint8, 256)),  # 256B for PKCS 1.5 2048bit
    ]


class KEY_USAGE_STRUCTURE(Structure):
    _pack_ = 1
    _fields_ = [
        ('key_usage', ARRAY(c_uint8, 16)),
        ('key_reserved', ARRAY(c_uint8, 16)),
        ('key_policy', c_uint8),
        ('key_hash_algorithm', c_uint8),
        ('key_hash_size', c_uint16),
        ('key_hash', ARRAY(c_uint8, 64)),  # TODO: spec requires is 64
    ]


class FIRMWARE_KEY_MANIFEST(Structure):
    NUM_OF_KEYS = 1
    _pack_ = 1
    _fields_ = [
        ('manifest_header', FIRMWARE_MANIFEST_HEADER),
        ('extension_type', c_uint32),
        ('extension_length', c_uint32),
        ('key_manifest_type', c_uint32),
        ('key_manifest_svn', c_uint32),
        ('oem_id', c_uint16),
        ('key_manifest_id', c_uint8),
        ('reserved', c_uint8),
        ('reserved2', ARRAY(c_uint8, 12)),
        ('num_of_keys', c_uint32),
        ('key_usage_array', ARRAY(KEY_USAGE_STRUCTURE, NUM_OF_KEYS)),
    ]


class METADATA_ENTRY(Structure):
    _pack_ = 1
    _fields_ = [
        ('id', c_uint32),
        ('type', c_uint8),
        ('hash_algorithm', c_uint8),
        ('hash_size', c_uint16),
        ('size', c_uint32),
        ('hash', ARRAY(c_uint8, 32)),
    ]


class FIRMWARE_BLOB_MANIFEST(Structure):
    _pack_ = 1
    _fields_ = [
        ('manifest_header', FIRMWARE_MANIFEST_HEADER),
        ('extension_type', c_uint32),
        ('package_name', c_uint32),
        ('version_control_num', c_uint64),
        ('usage_bitmap', ARRAY(c_uint8, 16)),
        ('svn', c_uint32),
        ('fw_type', c_uint8),
        ('fw_subtype', c_uint8),
        ('reserved', c_uint16),
        ('num_of_devices', c_uint32),
        ('device_list', ARRAY(c_uint8, 32)),
        ('metadata_entries', ARRAY(METADATA_ENTRY, 1))
    ]


def create_image(payload_file, outfile, privkey):
    '''Create a new image with manifest data in front it'''

    with open(payload_file, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    cpd_length = sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)
    fkm_length = sizeof(FIRMWARE_KEY_MANIFEST)
    fbm_length = sizeof(FIRMWARE_BLOB_MANIFEST)
    metadata_length = sizeof(METADATA_FILE_STRUCT)
    payload_length = len(in_data)

    total_length = cpd_length + fkm_length + \
        fbm_length + metadata_length + payload_length

    data = bytearray(total_length)
    ptr = 0

    cpd = SUBPART_DIR_HEADER.from_buffer(data, ptr)
    cpd.header_marker = 0x44504324   # '$CPD'
    cpd.num_of_entries = 4  # FKM, FBM, Metadata and payload
    cpd.header_version = 1
    cpd.entry_version = 1
    cpd.header_length = 0x10
    cpd.check_sum = 0xFF  # TODO: 8-bit XOR checksum
    cpd.subpart_name = bytes('SIIP', encoding='Latin-1')

    files_info = [('FKM', fkm_length), ('FBM', fbm_length),
                  ('METADATA', metadata_length), ('PAYLOAD', payload_length)]

    ptr += sizeof(SUBPART_DIR_HEADER)
    offset = sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)
    for i in range(4):
        cpd_entry = SUBPART_DIR_ENTRY.from_buffer(data, ptr)
        cpd_entry.name = bytes(files_info[i][0], encoding='Latin-1')
        cpd_entry.offset = offset
        cpd_entry.length = files_info[i][1]
        ptr += sizeof(SUBPART_DIR_ENTRY)
        offset += files_info[i][1]

    fkm = FIRMWARE_KEY_MANIFEST.from_buffer(data, ptr)
    fkm.manifest_header.type = 0x4
    fkm.manifest_header.length = sizeof(FIRMWARE_KEY_MANIFEST) // 4  # In DWORD
    fkm.manifest_header.version = 0x10000
    fkm.manifest_header.flags = 0x0
    fkm.manifest_header.vendor = 0x8086  # Intel device
    fkm.manifest_header.date = 0x20190418
    fkm.manifest_header.size = fkm.manifest_header.length
    fkm.manifest_header.id = 0x324e4d24  # '$MN2'
    fkm.manifest_header.num_of_metadata = 1  # Only 1 Metadata module for now
    fkm.manifest_header.structure_version = 0x1000
    fkm.manifest_header.modulus_size = 64  # In DWORD
    fkm.manifest_header.exponent_size = 1

    # Calculate payload signature using private key
    (signature, key) = compute_signature(bytes(in_data), privkey)
    puk = key.public_key()
    puk_num = puk.public_numbers()

    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)

    fkm.extension_type = 14  # CSE Key Manifest Extension Type
    fkm.extension_length = 36 + 68 * FIRMWARE_KEY_MANIFEST.NUM_OF_KEYS
    # 3: SIIP OEM Firmware Manifest; 4: SIIP Intel Firmware Manifest
    fkm.key_manifest_type = 3
    fkm.key_manifest_svn = 0
    fkm.oem_id = 0
    fkm.key_manifest_id = 0  # Not used
    fkm.num_of_keys = FIRMWARE_KEY_MANIFEST.NUM_OF_KEYS
    fkm.key_usage_array[0].key_usage[14] = 0x80  # 1 << 59 in arr[16]
    fkm.key_usage_array[0].key_reserved[:] = [0] * 16
    fkm.key_usage_array[0].key_policy = 1  # may signed only by Intel
    # 0: reserved; 1: SHA256; 2: SHA384; 3: SHA-512
    fkm.key_usage_array[0].key_hash_algorithm = 1
    fkm.key_usage_array[0].key_hash_size = 32  # Size of the hash in bytes
    fkm.key_usage_array[0].key_hash[:] = [0xFF] * \
        64  # Hash of public key in FBM header

    ptr += sizeof(FIRMWARE_KEY_MANIFEST)

    fbm = FIRMWARE_BLOB_MANIFEST.from_buffer(data, ptr)
    fbm.manifest_header.type = 0x4
    fbm.manifest_header.length = sizeof(
        FIRMWARE_BLOB_MANIFEST) // 4  # In DWORD
    fbm.manifest_header.version = 0x10000
    fbm.manifest_header.flags = 0x0
    fbm.manifest_header.vendor = 0x8086  # Intel device
    fbm.manifest_header.date = 0x20190418
    fbm.manifest_header.size = fbm.manifest_header.length
    fbm.manifest_header.id = 0x324e4d24  # '$MN2'
    fbm.manifest_header.num_of_metadata = 1  # Only 1 Metadata module for now
    fbm.manifest_header.structure_version = 0x1000
    fbm.manifest_header.modulus_size = 64  # In DWORD
    fbm.manifest_header.exponent_size = 1

    fbm.package_name = 0x45534f24  # '$OSE'
    fbm.version_control_num = 0
    fbm.usage_bitmap[14] = 0x80  # 1 << 59 in arr[16]
    fbm.svn = 0
    fbm.fw_type = 0
    fbm.fw_subtype = 0
    fbm.reserved = 0
    fbm.num_of_devices = 4

    fbm.metadata_entries[0].id = 0xDEADBEEF
    # 0: process; 1: shared lib; 2: data (for SIIP)
    fbm.metadata_entries[0].type = 2
    fbm.metadata_entries[0].hash_algorithm = 2  # SHA256
    fbm.metadata_entries[0].hash_size = 32
    fbm.metadata_entries[0].size = sizeof(METADATA_FILE_STRUCT)
    fbm.metadata_entries[0].hash[:] = [0xAA] * 32  # Hash of the metadata file

    ptr += sizeof(FIRMWARE_BLOB_MANIFEST)

    metadata = METADATA_FILE_STRUCT.from_buffer(data, ptr)
    metadata.size = sizeof(METADATA_FILE_STRUCT)
    metadata.id = 0x11223344
    metadata.version = 0
    metadata.num_of_modules = 1
    metadata.module_id = 0xFF  # TBD
    metadata.module_size = len(in_data)
    metadata.module_version = 0
    metadata.module_version = 0
    metadata.module_hash_size = 32
    metadata.module_entry_point = 0x44332211
    metadata.module_hash_alogorithm = 2  # SHA256

    # STEP 1: Calculate payload hash and store it in Metadata file
    hash_result = compute_hash(bytes(in_data))

    metadata.module_hash_value[:] = hash_result
    metadata.num_of_keys = 1
    metadata.key_usage_id[14] = 0x80  # 1 << 59 in arr[16]

    # STEP 2: Calculate Metadata file hash and store it in FBM
    metadata_offset = cpd_length + fkm_length + fbm_length
    metadata_limit = metadata_offset + metadata_length

    hash_result = compute_hash(bytes(data[metadata_offset:metadata_limit]))
    fbm.metadata_entries[0].hash[:] = hash_result

    # STEP 3: Calculate signature of FBM (except signature and public keys) and store it in FBM header
    fbm_offset = cpd_length + fkm_length
    fbm_limit = fbm_offset + fbm_length
    fbm.manifest_header.public_key[:] = [0] * 256
    fbm.manifest_header.exponent[:] = [0] * 4
    fbm.manifest_header.signature[:] = [0] * 256
    (signature, key) = compute_signature(bytes(data[fbm_offset:fbm_limit]),
                                         privkey)

    fbm.manifest_header.public_key[:] = mod_buf
    fbm.manifest_header.exponent[:] = exp_buf
    fbm.manifest_header.signature[:] = signature

    # STEP 4: Calculate public key hash in FBM header and store it in FKM
    pubkey_data = mod_buf + exp_buf
    hash_result = compute_hash(bytes(pubkey_data))
    # TODO: There is mismatch in the spec
    fkm.key_usage_array[0].key_hash[:] = hash_result + bytes(32)

    # STEP 5: Calculate signature of FKM (except signature and public key) and store it in FKM header
    fkm_offset = cpd_length
    fkm_limit = fkm_offset + fkm_length

    (signature, key) = compute_signature(bytes(data[fkm_offset:fkm_limit]),
                                         privkey)

    fkm.manifest_header.public_key[:] = mod_buf
    fkm.manifest_header.exponent[:] = exp_buf
    fkm.manifest_header.signature[:] = signature

    # STEP 6: Append payload data as is
    ptr += sizeof(METADATA_FILE_STRUCT)
    data[total_length - payload_length:total_length] = in_data

    cpd_limit = sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)
    files = parse_cpd_header(data[0:cpd_limit])

    count = 0
    for name, ioff, ilen in files:
        print('[%d] %s @ [0x%08x-0x%08x] len: 0x%x (%d) Bytes' %
              (count, name, ioff, ioff + ilen, ilen, ilen))
        count += 1

    sys.stdout.write('Writing... ')
    with open(outfile, 'wb') as out_fd:
        out_fd.write(data)
    print('Okay')


def decompose_image(infile_signed):
    '''Decompose image to indivisual files'''

    with open(infile_signed, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    cpd = SUBPART_DIR_HEADER.from_buffer(in_data, 0)
    files = parse_cpd_header(
        in_data[0:sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)])

    # Extract images
    if not os.path.exists('extract'):
        os.makedirs('extract')
    count = 0
    for name, ioff, ilen in files:
        print('[%d] Extracting to %s.bin @ [0x%08x-0x%08x] len: 0x%x (%d) Bytes' %
              (count, name, ioff, ioff + ilen, ilen, ilen))
        with open(os.path.join('extract', '%s.bin' % name), 'wb') as out_fd:
            out_fd.write(in_data[ioff:ioff + ilen])
        count += 1


def verify_image(infile_signed, pubkey_pem_file):
    '''Verify a signed image with public key end-to-end'''

    with open(infile_signed, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    with open(pubkey_pem_file, 'rb') as pubkey_pem_fd:
        puk = serialization.load_pem_public_key(
            pubkey_pem_fd.read(), backend=default_backend())
    puk_num = puk.public_numbers()
    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)

    hash_expected = compute_hash(bytes(mod_buf + exp_buf))

    cpd = SUBPART_DIR_HEADER.from_buffer(in_data, 0)
    files = parse_cpd_header(
        in_data[0:sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)])

    name, ioff, ilen = files[0]  # FKM
    fkm = FIRMWARE_KEY_MANIFEST.from_buffer(in_data, ioff)
    if fkm.manifest_header.id != 0x324e4d24:
        print('Bad FKM signature.')
        exit(1)

    # STEP 1: Validate FKM key hash then signature

    # Calculate public key hash in FKM header
    pubkey_n = fkm.manifest_header.public_key[:]
    pubkey_e = fkm.manifest_header.exponent[:]

    hash_actual = verify_hash(bytes(pubkey_n + pubkey_e), hash_expected)

    try:
        sys.stdout.write('Verifying FKM ...')

        fkm_sig = fkm.manifest_header.signature[:]

        # Clear public key and signature data first
        fkm.manifest_header.public_key[:] = [0] * 256
        fkm.manifest_header.exponent[:] = [0] * 4
        fkm.manifest_header.signature[:] = [0] * 256

        fkm_offset = ioff
        fkm_limit = fkm_offset + ilen
        verify_signature(fkm_sig, bytes(in_data[fkm_offset:fkm_limit]),
                         pubkey_pem_file)

        print('Okay')
    except:
        print('Failed')
        exit(1)

    # STEP 2: Validate FBM key hash and signature
    name, ioff, ilen = files[1]  # FBM
    fbm_offset = ioff
    fbm_limit = fbm_offset + ilen

    fbm = FIRMWARE_BLOB_MANIFEST.from_buffer(in_data, ioff)
    if fkm.manifest_header.id != 0x324e4d24:
        print('Bad FBM signature.')
        exit(1)

    # TODO: compare key usage bitmaps between FKM and FBM. Proceed only when they match
    print('FBM Usage Bitmap      : 0x%2x' % fbm.usage_bitmap[14])

    hash_data = fkm.key_usage_array[0].key_hash

    pubkey_n = fbm.manifest_header.public_key[:]
    pubkey_e = fbm.manifest_header.exponent[:]

    hash_actual = compute_hash(bytes(pubkey_n + pubkey_e))

    if (hash_expected != hash_actual):
        print('Verification failed: FBM key hash mismatch')
        exit(1)

    # Validate FBM
    fbm_sig = fbm.manifest_header.signature[:]

    try:
        sys.stdout.write('Verifying FBM ...')

        # Clear public key and signature data first
        fbm.manifest_header.public_key[:] = [0] * 256
        fbm.manifest_header.exponent[:] = [0] * 4
        fbm.manifest_header.signature[:] = [0] * 256

        verify_signature(fbm_sig, bytes(in_data[fbm_offset:fbm_limit]),
                         pubkey_pem_file)
        print('Okay')
    except:
        print('Failed')
        exit(1)

    # STEP 3: Validate Metadata hash
    name, ioff, ilen = files[2]  # Metadata
    metafile_offset = ioff
    metafile_limit = metafile_offset + ilen

    metadata = METADATA_FILE_STRUCT.from_buffer(in_data, metafile_offset)

    hash_actual = compute_hash(bytes(in_data[metafile_offset:metafile_limit]))
    hash_actual = [x for x in hash_actual]  # Convert to list

    hash_expected = fbm.metadata_entries[0].hash[:]
    if (hash_actual != hash_expected):
        Raise('Verification failed: Metadata hash mismatch')

    # STEP 4: Validate payload
    name, ioff, ilen = files[3]  # Payload
    payload_offset = ioff
    payload_limit = payload_offset + ilen

    hash_actual = compute_hash(bytes(in_data[payload_offset:payload_limit]))
    hash_actual = [x for x in hash_actual]  # Convert to list

    hash_expected = metadata.module_hash_value[:]
    if (hash_actual != hash_expected):
        raise('Verification failed: payload hash mismatch')

    print('Verification success!')


def main():

    ap = argparse.ArgumentParser(
        description='A mini-MEU-like signing tool to create manifest data compliant to SIIP firmware loader specification')

    sp = ap.add_subparsers(help='command')

    def cmd_create(args):
        print('Creating image with manifest data using key %s ...' %
              args.private_key)
        create_image(args.input_file, args.output_file, args.private_key)

    signp = sp.add_parser('sign', help='Sign an image')
    signp.add_argument('-i', '--input-file',
                       required=True,
                       type=str,
                       help='Input unsigned file')
    signp.add_argument('-o', '--output-file',
                       required=True,
                       type=str,
                       help='Output signed file')
    signp.add_argument('-k', '--private-key',
                       required=True,
                       type=str,
                       help='RSA signing key in PEM format')
    signp.set_defaults(func=cmd_create)

    def cmd_decomp(args):
        print('Decomposing %s ...' % args.input_file)
        decompose_image(args.input_file)

    decompp = sp.add_parser('decompose', help='Decompose a signed image')
    decompp.add_argument('-i', '--input-file',
                         required=True,
                         type=str,
                         help='Input signed image')
    decompp.set_defaults(func=cmd_decomp)

    def cmd_verify(args):
        print('Verifying a signed image ...')
        verify_image(args.input_file, args.pubkey_pem_file)

    verifyp = sp.add_parser(
        'verify', help='Verify a signed image')
    verifyp.add_argument('-i', '--input-file',
                         required=True,
                         type=str,
                         help='Input signed image')
    verifyp.add_argument('-p', '--pubkey-pem-file',
                         required=True,
                         type=str,
                         help='Public key in PEM format')
    verifyp.set_defaults(func=cmd_verify)

    ap.add_argument('-V', '--version', action='version',
                    version='%(prog)s ' + __version__)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
