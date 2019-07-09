#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2019 Intel Corporation.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE


from __future__ import print_function

import os
import sys
import argparse
import binascii

from ctypes import Structure
from ctypes import c_char, c_uint32, c_uint8, c_uint64, c_uint16, sizeof, ARRAY

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3 (for now)")

try:
    from cryptography.hazmat.primitives import hashes as hashes
    from cryptography.hazmat.primitives import serialization as serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric \
        import padding as crypto_padding

    # Check its version
    import cryptography
    if cryptography.__version__ < '2.2.2':
        print("Error: Cryptography version must be 2.2.2 or higher"
              " (installed version: {})".format(cryptography.__version__))
        exit(1)

except ImportError:
    print("Error: Cryptography could not be found, please install using pip")
    sys.exit(1)


__version__ = "0.3.0"

RSA_KEYMOD_SIZE = 256
RSA_KEYEXP_SIZE = 4
KB = 1024
MB = 1024 * KB

HASH_CHOICES = {
  'sha256': (hashes.SHA256(), 2),
  'sha384': (hashes.SHA384(), 3),
  'sha512': (hashes.SHA512(), 4),
}

HASH_OPTION = None
HASH_SIZE = 0


def hex_dump(data, n=16, indent=0, msg='Hex Dump'):
    print('%s (%d Bytes):' % (msg, len(data)))
    for i in range(0, len(data), n):
        line = bytearray(data[i:i+n])
        hex = ' '.join('%02x' % c for c in line)
        text = ''.join(chr(c) if 0x21 <= c <= 0x7e else '.' for c in line)
        print('%*s%-*s %s' % (indent, '', n*3, hex, text))


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

    global HASH_OPTION

    digest = hashes.Hash(HASH_OPTION, backend=default_backend())
    digest.update(data)
    result = digest.finalize()

    return result


def verify_hash(data, expected_hash):
    '''Compute hash from data and compare with expected value'''

    result = compute_hash(data)
    if result != expected_hash:
        hex_dump(result, indent=4, msg='Actual')
        hex_dump(expected_hash, indent=4, msg='Expected')
        raise Exception('Hash values mismatch!')

    return result


def get_pubkey_from_privkey(privkey_pem):
    '''Extract public key from private key in PEM format'''

    with open(privkey_pem, 'rb') as privkey_file:
        key = serialization.load_pem_private_key(
            privkey_file.read(),
            password=None,
            backend=default_backend()
        )

    return key.public_key()


def get_pubkey_hash_from_privkey(privkey_pem):
    '''Calculate public key hash from a private key in PEM format'''

    puk = get_pubkey_from_privkey(privkey_pem)
    puk_num = puk.public_numbers()

    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)
    hex_dump((mod_buf + exp_buf), msg='Public Key (%s)' % privkey_pem)

    pubkey_data = mod_buf + exp_buf
    hash_result = compute_hash(bytes(pubkey_data))

    return hash_result


def compute_signature(data, privkey_pem):
    '''Compute signature from data'''

    global HASH_OPTION

    with open(privkey_pem, 'rb') as privkey_file:
        key = serialization.load_pem_private_key(
            privkey_file.read(),
            password=None,
            backend=default_backend()
        )

    if key.key_size < 2048:
        raise Exception('Key size {} bits is too small.'.format(key.key_size))

    # Calculate signature using private key
    signature = key.sign(
        bytes(data), crypto_padding.PKCS1v15(), HASH_OPTION)

    return (signature, key)


def verify_signature(signature, data, pubkey_pem):
    '''Verify signature with public key'''

    global HASH_OPTION

    with open(pubkey_pem, 'rb') as pubkey_file:
        puk = serialization.load_pem_public_key(
            pubkey_file.read(), backend=default_backend())

    # Raises InvalidSignature error if not match
    puk.verify(signature, data, crypto_padding.PKCS1v15(), HASH_OPTION)


def compute_pubkey_hash(pubkey_pem_file):
    '''Compute hash of the public key provided in PEM file'''

    with open(pubkey_pem_file, 'rb') as pubkey_pem_fd:
        puk = serialization.load_pem_public_key(
            pubkey_pem_fd.read(), backend=default_backend())

    puk_num = puk.public_numbers()
    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)

    puk_hash = compute_hash(bytes(mod_buf + exp_buf))

    return puk_hash


def create_fkm(privkey, payload_privkey, hash_option):
    '''Create FKM data from a list of keys'''

    global HASH_CHOICES
    global HASH_SIZE

    fkm_data = bytearray(sizeof(FIRMWARE_KEY_MANIFEST))

    fkm = FIRMWARE_KEY_MANIFEST.from_buffer(fkm_data, 0)
    fkm.manifest_header.type = 0x4
    fkm.manifest_header.length = sizeof(FIRMWARE_MANIFEST_HEADER)
    fkm.manifest_header.version = 0x10000
    fkm.manifest_header.flags = 0x0
    fkm.manifest_header.vendor = 0x8086  # Intel device
    # int(datetime.now().strftime('%Y%m%d'), 16)
    fkm.manifest_header.date = 0x20190418
    fkm.manifest_header.size = sizeof(FIRMWARE_KEY_MANIFEST)
    fkm.manifest_header.id = 0x324e4d24  # '$MN2'
    fkm.manifest_header.num_of_metadata = 0  # FKM has no metadata appended
    fkm.manifest_header.structure_version = 0x1000
    fkm.manifest_header.modulus_size = 64  # In DWORD
    fkm.manifest_header.exponent_size = 1

    # 3: SIIP OEM Firmware Manifest; 4: SIIP Intel Firmware Manifest
    fkm.extension_type = 14  # CSE Key Manifest Extension Type
    fkm.key_manifest_type = 4
    fkm.key_manifest_svn = 0
    fkm.oem_id = 0
    fkm.key_manifest_id = 0  # Not used
    fkm.num_of_keys = FIRMWARE_KEY_MANIFEST.NUM_OF_KEYS
    fkm.extension_length = 36 + 68 * fkm.num_of_keys  # Hardcoded from now
    fkm.key_usage_array[0].key_usage[7] = 0x08  # 1 << 59 in arr[16]
    fkm.key_usage_array[0].key_reserved[:] = [0] * 16
    fkm.key_usage_array[0].key_policy = 1  # may signed only by Intel
    fkm.key_usage_array[0].key_hash_algorithm = HASH_CHOICES[hash_option][1]
    fkm.key_usage_array[0].key_hash_size = HASH_SIZE

    # Calculate public key hash used by payload and store it in FKM

    # Hash of public key used by FBM
    fkm.key_usage_array[0].key_hash[:] = [0xFF] * 64

    hash_result = get_pubkey_hash_from_privkey(payload_privkey)
    fkm.key_usage_array[0].key_hash[:] = hash_result + bytes(64 - HASH_SIZE)

    # Calculate FKM signature (except signature and public key)
    # and store it in FKM header
    (signature, key) = compute_signature(fkm_data, privkey)
    puk = get_pubkey_from_privkey(privkey)
    puk_num = puk.public_numbers()

    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)
    hex_dump((mod_buf + exp_buf), msg='FKM Public Key')

    fkm.manifest_header.public_key[:] = mod_buf
    fkm.manifest_header.exponent[:] = exp_buf
    fkm.manifest_header.signature[:] = signature

    return fkm_data


def create_cpd_header(files_info):
    '''Create a new CPD directory'''

    data = bytearray(sizeof(SUBPART_DIR_HEADER) +
                     len(files_info) * sizeof(SUBPART_DIR_ENTRY))
    ptr = 0

    cpd = SUBPART_DIR_HEADER.from_buffer(data, ptr)
    cpd.header_marker = 0x44504324   # '$CPD'
    cpd.num_of_entries = len(files_info)
    cpd.header_version = 2  # 1: layout v1.5/1.6/2.0; 2: layout v1.7
    cpd.entry_version = 1
    cpd.header_length = sizeof(SUBPART_DIR_HEADER)
    cpd.reserved = 0  # was 8-bit checksum
    cpd.subpart_name = bytes('SIIP', encoding='Latin-1')
    cpd.crc32 = 0  # New in layout 1.7

    ptr += sizeof(SUBPART_DIR_HEADER)
    offset = len(data)
    for f in files_info:
        cpd_entry = SUBPART_DIR_ENTRY.from_buffer(data, ptr)
        cpd_entry.name = bytes(f[0], encoding='Latin-1')
        cpd_entry.offset = offset
        cpd_entry.length = f[1]
        ptr += sizeof(SUBPART_DIR_ENTRY)
        offset += f[1]

    # Fill CRC32 checksum
    cpd.crc32 = binascii.crc32(data)
    print('CPD Header CRC32 : 0x%X' % cpd.crc32)

    return data


def parse_cpd_header(cpd_data):
    '''Parse CPD header and return files information'''

    ptr = 0
    cpd = SUBPART_DIR_HEADER.from_buffer(cpd_data, 0)
    if cpd.header_marker != 0x44504324:
        print('Invalid input file. CPD signature not found.')
        exit(1)

    files = []
    entry_count = cpd.num_of_entries

    expected_crc = cpd.crc32
    cpd.crc32 = 0
    cpd_length = sizeof(SUBPART_DIR_HEADER) + \
                       (entry_count * sizeof(SUBPART_DIR_ENTRY))
    actual_crc = binascii.crc32(cpd_data[0:cpd_length])

    if expected_crc != actual_crc:
        print('CPD header CRC32 invalid (exp: 0x%x, actual: 0x%x)' %
              (expected_crc, actual_crc))
        exit(1)

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
        ('reserved', c_uint8),
        ('subpart_name', ARRAY(c_char, 4)),
        ('crc32', c_uint32),
    ]


class SUBPART_DIR_ENTRY(Structure):
    _pack_ = 1
    _fields_ = [
        ('name', ARRAY(c_char, 12)),
        ('offset', c_uint32),
        ('length', c_uint32),
        ('module_type', c_uint32),
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
        ('module_hash_algorithm', c_uint32),
        ('module_hash_value', ARRAY(c_uint8, 64)),
        ('num_of_keys', c_uint32),
        ('key_usage_id', ARRAY(c_uint8, 16)),
        ('non_std_section_size', c_uint32),
        # Followed by the non-standard section data
    ]


class FIRMWARE_MANIFEST_HEADER(Structure):
    _pack_ = 1
    _fields_ = [
        ('type', c_uint32),
        ('length', c_uint32),
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
        ('key_hash', ARRAY(c_uint8, 64)),
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
        ('hash', ARRAY(c_uint8, 64)),
    ]


class FIRMWARE_BLOB_MANIFEST(Structure):
    _pack_ = 1
    _fields_ = [
        ('manifest_header', FIRMWARE_MANIFEST_HEADER),
        ('extension_type', c_uint32),
        ('extension_length', c_uint32),
        ('package_name', c_uint32),
        ('version_control_num', c_uint64),
        ('usage_bitmap', ARRAY(c_uint8, 16)),
        ('svn', c_uint32),
        ('fw_type', c_uint8),
        ('fw_subtype', c_uint8),
        ('reserved', c_uint16),
        ('num_of_devices', c_uint32),
        ('device_list', ARRAY(c_uint32, 4)),
        ('metadata_entries', ARRAY(METADATA_ENTRY, 1))
    ]


def create_image(payload_file, outfile, privkey, hash_option):
    '''Create a new image with manifest data in front it'''

    global HASH_OPTION
    global HASH_SIZE

    HASH_OPTION = HASH_CHOICES[hash_option][0]
    HASH_SIZE = HASH_OPTION.digest_size

    print('Hashing Algorithm : %s' % HASH_OPTION.name)

    payload_cfg = payload_file.split(',')  # <file>,<signing_key>
    if len(payload_cfg) == 2:
        payload_privkey = payload_cfg[1]
        payload_file = payload_cfg[0]
    else:
        payload_privkey = privkey  # Use the same key from -k commandline

    print('FKM signing key : %s' % privkey)
    print('FBM signing key : %s' % payload_privkey)

    # Create FKM blob separately required by spec
    fkm_data = create_fkm(privkey, payload_privkey, hash_option)
    cpd_data = create_cpd_header([('FKM', len(fkm_data))])
    with open('fkm.bin', 'wb') as fkm_fd:
        fkm_fd.write(cpd_data)
        fkm_fd.write(fkm_data)

    # Create the rest (FBM, Meta Data and payaload) in one piece
    with open(payload_file, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    fbm_length = sizeof(FIRMWARE_BLOB_MANIFEST)
    metadata_length = sizeof(METADATA_FILE_STRUCT)
    payload_length = len(in_data)

    files_info = [
                  ('FBM',      fbm_length),
                  ('METADATA', metadata_length),
                  ('PAYLOAD',  payload_length),
                 ]

    cpd_length = sizeof(SUBPART_DIR_HEADER) + \
                       (len(files_info) * sizeof(SUBPART_DIR_ENTRY))
    fbm_offset = cpd_length
    metadata_offset = fbm_offset + fbm_length

    total_length = cpd_length
    total_length += fbm_length + metadata_length + payload_length
    data = bytearray(total_length)

    data[0:len(cpd_data)] = create_cpd_header(files_info)

    # Create FBM
    fbm = FIRMWARE_BLOB_MANIFEST.from_buffer(data, fbm_offset)
    fbm.manifest_header.type = 0x4
    fbm.manifest_header.length = sizeof(FIRMWARE_BLOB_MANIFEST)
    fbm.manifest_header.version = 0x10000
    fbm.manifest_header.flags = 0x0
    fbm.manifest_header.vendor = 0x8086  # Intel device
#    fbm.manifest_header.date = int(create_date)
    fbm.manifest_header.date = 0x20190418
    fbm.manifest_header.size = fbm.manifest_header.length
    fbm.manifest_header.id = 0x324e4d24  # '$MN2'
    fbm.manifest_header.num_of_metadata = 1  # FBM has exactly one metadata
    fbm.manifest_header.structure_version = 0x1000
    fbm.manifest_header.modulus_size = 64  # In DWORD
    fbm.manifest_header.exponent_size = 1
    fbm.extension_type = 15  # CSME Signed Package Info Extension type

    fbm.package_name = 0x45534f24  # '$OSE'
    fbm.version_control_num = 0
    fbm.usage_bitmap[7] = 0x08  # Bit 59: OSE firmware
    fbm.svn = 0
    fbm.fw_type = 0
    fbm.fw_subtype = 0
    fbm.reserved = 0
    fbm.num_of_devices = 4
    fbm.device_list[:] = [0] * fbm.num_of_devices

    fbm.metadata_entries[0].id = 0xDEADBEEF
    # 0: process; 1: shared lib; 2: data (for SIIP)
    fbm.metadata_entries[0].type = 2
    fbm.metadata_entries[0].hash_algorithm = HASH_CHOICES[hash_option][1]
    fbm.metadata_entries[0].hash_size = HASH_SIZE
    fbm.metadata_entries[0].size = sizeof(METADATA_FILE_STRUCT)
    fbm.metadata_entries[0].hash[:] = [0] * 64

    fbm.extension_length = sizeof(FIRMWARE_BLOB_MANIFEST)

    # Create Meta Data
    metadata = METADATA_FILE_STRUCT.from_buffer(data, metadata_offset)
    metadata.size = sizeof(METADATA_FILE_STRUCT)
    # Match one of FBM metadata entries by ID
    metadata.id = fbm.metadata_entries[0].id
    metadata.version = 0
    metadata.num_of_modules = 1
    metadata.module_id = 0xFF  # TBD
    metadata.module_size = len(in_data)
    metadata.module_version = 0
    metadata.module_hash_size = HASH_SIZE
    metadata.module_entry_point = 0
    metadata.module_hash_algorithm = HASH_CHOICES[hash_option][1]

    # STEP 1: Calculate payload hash and store it in Metadata file
    hash_result = compute_hash(bytes(in_data))
    hex_dump(hash_result, msg='Payload Hash')

    metadata.module_hash_value[:HASH_SIZE] = hash_result
    metadata.num_of_keys = 1
    metadata.key_usage_id[7] = 0x08  # Bit 59: OSE firmware
    metadata.non_std_section_size = 0  # Empty non-standard section for now

    # STEP 2: Calculate Metadata file hash and store it in FBM
    metadata_limit = metadata_offset + metadata_length

    hash_result = compute_hash(bytes(data[metadata_offset:metadata_limit]))
    fbm.metadata_entries[0].hash[:HASH_SIZE] = hash_result

    # STEP 3: Calculate signature of FBM (except signature and public keys)
    #         and store it in FBM header
    fbm_limit = fbm_offset + fbm_length
    fbm.manifest_header.public_key[:] = [0] * 256
    fbm.manifest_header.exponent[:] = [0] * 4
    fbm.manifest_header.signature[:] = [0] * 256
    (signature, key) = compute_signature(bytes(data[fbm_offset:fbm_limit]),
                                         payload_privkey)

    puk = get_pubkey_from_privkey(payload_privkey)
    puk_num = puk.public_numbers()

    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)
    hex_dump((mod_buf + exp_buf), msg='FBM Public Key')

    fbm.manifest_header.public_key[:] = mod_buf
    fbm.manifest_header.exponent[:] = exp_buf
    fbm.manifest_header.signature[:] = signature

    # STEP 4: Append payload data as is
    data[total_length-payload_length:total_length] = in_data

    files = parse_cpd_header(data[0:cpd_length])

    for idx, (name, ioff, ilen) in enumerate(files):
        print('[%d] %s @ [0x%08x-0x%08x] len: 0x%x (%d) Bytes' %
              (idx, name, ioff, ioff + ilen, ilen, ilen))

    sys.stdout.write('Writing... ')
    with open(outfile, 'wb') as out_fd:
        out_fd.write(data)
    print('Okay')


def decompose_image(infile_signed):
    '''Decompose image to indivisual files'''

    with open(infile_signed, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    files = parse_cpd_header(
        in_data[0:sizeof(SUBPART_DIR_HEADER) + 4 * sizeof(SUBPART_DIR_ENTRY)])

    # Extract images
    if not os.path.exists('extract'):
        os.makedirs('extract')
    for idx, (name, ioff, ilen) in enumerate(files):
        print('[%d] Extracting to %s.bin @ [0x%08x-0x%08x] len: 0x%x (%d) ' %
              (idx, name, ioff, (ioff + ilen), ilen, ilen))
        with open(os.path.join('extract', '%s.bin' % name), 'wb') as out_fd:
            out_fd.write(in_data[ioff:ioff + ilen])


def verify_image(infile_signed, pubkey_pem_file, hash_option):
    '''Verify a signed image with public key end-to-end'''

    global HASH_OPTION
    global HASH_SIZE

    HASH_OPTION = HASH_CHOICES[hash_option][0]
    HASH_SIZE = HASH_OPTION.digest_size

    puk_cfg = infile_signed.split(',')  # <infile>,<puk.pem>
    if len(puk_cfg) == 2:
        infile_signed = puk_cfg[0]
        payload_puk_file = puk_cfg[1]
    else:
        payload_puk_file = pubkey_pem_file

    with open(infile_signed, 'rb') as in_fd:
        in_data = bytearray(in_fd.read())

    with open('fkm.bin', 'rb') as fkm_fd:
        fkm_data = bytearray(fkm_fd.read())

    # STEP 1: Validate FKM key hash then signature
    with open(pubkey_pem_file, 'rb') as pubkey_pem_fd:
        puk = serialization.load_pem_public_key(
            pubkey_pem_fd.read(), backend=default_backend())
    puk_num = puk.public_numbers()
    mod_buf = pack_num(puk_num.n, RSA_KEYMOD_SIZE)
    exp_buf = pack_num(puk_num.e, RSA_KEYEXP_SIZE)

    hash_expected = compute_hash(bytes(mod_buf + exp_buf))

    files = parse_cpd_header(fkm_data)

    name, ioff, ilen = files[0]  # FKM
    fkm_offset = ioff
    fkm_limit = fkm_offset + ilen
    fkm = FIRMWARE_KEY_MANIFEST.from_buffer(fkm_data, fkm_offset)
    if fkm.manifest_header.id != 0x324e4d24:
        print('Bad FKM signature.')
        exit(1)

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

        verify_signature(fkm_sig, bytes(fkm_data[fkm_offset:fkm_limit]),
                         pubkey_pem_file)

        print('Okay')
    except Exception:
        print('Failed')
        exit(1)

    # STEP 2: Validate FBM key hash and signature
    hash_expected = compute_pubkey_hash(payload_puk_file)

    files = parse_cpd_header(in_data)
    name, ioff, ilen = files[0]  # FBM
    fbm_offset = ioff
    fbm_limit = fbm_offset + ilen

    fbm = FIRMWARE_BLOB_MANIFEST.from_buffer(in_data, fbm_offset)
    if fbm.manifest_header.id != 0x324e4d24:
        print('Bad FBM signature.')
        exit(1)

    # TODO: compare key usage bitmaps between FKM and FBM
    print('FBM Usage Bitmap      : 0x%2x' % fbm.usage_bitmap[7])

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
                         payload_puk_file)
        print('Okay')
    except Exception:
        print('Failed')
        exit(1)

    # STEP 3: Validate Metadata hash
    name, ioff, ilen = files[1]  # Metadata
    metafile_offset = ioff
    metafile_limit = metafile_offset + ilen

    metadata = METADATA_FILE_STRUCT.from_buffer(in_data, metafile_offset)

    hash_actual = compute_hash(bytes(in_data[metafile_offset:metafile_limit]))
    hash_actual = [x for x in hash_actual]  # Convert to list

    hash_expected = fbm.metadata_entries[0].hash[:len(hash_actual)]
    if (hash_actual != hash_expected):
        raise Exception('Verification failed: Metadata hash mismatch')

    # STEP 4: Validate payload
    name, ioff, ilen = files[2]  # Payload
    payload_offset = ioff
    payload_limit = payload_offset + ilen

    hash_actual = compute_hash(bytes(in_data[payload_offset:payload_limit]))
    hash_actual = [x for x in hash_actual]  # Convert to list

    hash_expected = metadata.module_hash_value[:len(hash_actual)]
    if (hash_actual != hash_expected):
        raise Exception('Verification failed: payload hash mismatch')

    print('Verification success!')


def main():

    ap = argparse.ArgumentParser(
        description='A SIIP signing tool to create manifest data supporting'
                    ' SIIP firmware loading specification')

    sp = ap.add_subparsers(help='command')

    def cmd_create(args):
        print('Creating image with manifest data using key %s ...' %
              args.private_key)
        create_image(args.input_file,
                     args.output_file,
                     args.private_key,
                     args.hash_option)

    signp = sp.add_parser('sign', help='Sign an image')
    signp.add_argument('-i', '--input-file',
                       required=True,
                       type=str,
                       help='Input unsigned file, optionally followed by its'
                            ' signing key, with a comma as seperator. '
                            'E.g., <file>,<rsa.pem>')
    signp.add_argument('-o', '--output-file',
                       required=True,
                       type=str,
                       help='Output signed file')
    signp.add_argument('-k', '--private-key',
                       required=True,
                       type=str,
                       help='RSA signing key in PEM format')
    signp.add_argument('-s', '--hash-option',
                       default='sha256',
                       choices=list(HASH_CHOICES.keys()),
                       help='Hashing algorithm')

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
        verify_image(args.input_file, args.pubkey_pem_file, args.hash_option)

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
    verifyp.add_argument('-s', '--hash-option',
                         default='sha256',
                         choices=list(HASH_CHOICES.keys()),
                         help='Hashing algorithm')
    verifyp.set_defaults(func=cmd_verify)

    ap.add_argument('-V', '--version', action='version',
                    version='%(prog)s ' + __version__)

    args = ap.parse_args()
    if 'func' not in args:
        ap.print_usage()
        sys.exit(2)
    sys.exit(args.func(args))


if __name__ == '__main__':
    main()
