#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###################################################################################################
## SIIP Constants
## {The SIIP Constants}
###################################################################################################
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

class IP_constants:
    '''constants for guid and user interface names'''
    PSE_UI = 'IntelOseFw'
    PSE_SEC_GUID = 'EE4E5898-3914-4259-9D6E-DC7BD79403CF'
    PSE_FFS_GUID = 'EBA4A247-42C0-4C11-A167-A4058BC9D423'

    TMAC_UI = 'IntelTsnMacAddrFv'
    TMAC_FFS_GUID = '12E29FB4-AA56-4172-B34E-DD5F4B440AA9'

    PTMAC_UI = 'IntelOseTsnMacConfig'
    PTMAC_FFS_GUID = '4FB7994D-D878-4BD1-8FE0-777B732D0A31'

    TCC_UI = 'IntelTccConfig'
    TCC_FFS_GUID = '7F6AD829-15E9-4FDE-9DD3-0548BB7F56F3'

    OOB_UI = 'IntelOobConfig'
    OOB_FFS_GUID = '4DB2A373-C936-4544-AA6D-8A194AA9CA7F'

    GOP_UI = 'IntelGopDriver'
    GOP_FFS_GUID = 'FF0C8745-3270-4439-B74F-3E45F8C77064'

    PEI_UI = 'IntelGraphicsPeim'
    PEI_FFS_GUID = '76ED893A-B2F9-4C7D-A05F-1EA170ECF6CD'

    VBT_UI = 'IntelGopVbt'
    VBT_FFS_GUID = '56752da9-de6b-4895-8819-1945b6b76c22'

