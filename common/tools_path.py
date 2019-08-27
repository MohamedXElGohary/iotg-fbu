#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Intel Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import os


THIRD_PARTY_DIR = "thirdparty"
TOOLS_DIR = os.path.abspath(os.path.join(THIRD_PARTY_DIR, "Bin", "Win32"))
FMMT = os.path.join(TOOLS_DIR, "FMMT.exe")
GENSEC = os.path.join(TOOLS_DIR, "GenSec.exe")
GENFFS = os.path.join(TOOLS_DIR, "GenFfs.exe")
GENFV = os.path.join(TOOLS_DIR, "GenFV.exe")
LZCOMPRESS = os.path.join(TOOLS_DIR, "LzmaCompress.exe")

EDK2_CAPSULE_TOOL = os.path.abspath(os.path.join(THIRD_PARTY_DIR,
                                                 "edk2_capsule_tool",
                                                 "GenerateCapsule.py"))
