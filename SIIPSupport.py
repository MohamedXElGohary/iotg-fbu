#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################################
## SIIP Support Package
## {The SIIP Support package points to the required directories and excutable files need to run
##   the different SIIP Scripts}
################################################################################################
#
# Copyright 2019 Intel Corporation
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#  1. Redistributions of source code must retain the above copyright notice, this list of
#     conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright notice, this list of
#     conditions and the following disclaimer in the documentation and/or other materials provided
#     with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#################################################################################################
import os

__version__ = '0.2.0'

class ToolsLoc:
    '''directorys needed for the SIIP tools'''

    TOOLSDIR = os.path.join(os.path.dirname(__file__), 'SiipSupport')
    TOOLSWINDIR = os.path.join(TOOLSDIR, 'bin', 'win32')


class EdkTools:
    ''' Executables that are needed for the SIIP tools'''

    GENSEC = os.path.join(ToolsLoc.TOOLSWINDIR, 'GenSec.exe')
    GENFFS = os.path.join(ToolsLoc.TOOLSWINDIR, 'GenFfs.exe')
    GENFV = os.path.join(ToolsLoc.TOOLSWINDIR, 'GenFV.exe')
