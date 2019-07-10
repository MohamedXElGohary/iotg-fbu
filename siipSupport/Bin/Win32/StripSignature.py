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
# POSSIBILITY OF SUCH DAMAGE.


import argparse

def remove_signature(infile, outfile):
	with open(infile, 'rb') as input_file:
		data = input_file.read()
	with open(outfile, 'wb') as output_file:
		output_file.write(data[0x210:])

def prefix_signature(infile, outfile):
  with open(infile, 'rb') as input_file:
    data = input_file.read()
  with open(outfile, 'wb') as output_file:
    output_file.write(bytearray(0x210))
    output_file.write(data)

def main():

  parser = argparse.ArgumentParser(description='Remove signature data from a GUID section')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-d", action="store_true", dest='Decode', help='decode file')
  group.add_argument("-e", action="store_true", dest='Encode', help='encode file')
  parser.add_argument("-o", "--output", dest='OutputFile', type=str, metavar='filename', help="specify the output filename", required=True)
  parser.add_argument("--private-key", dest='PrivateKeyFile', help="specify the private key filename.  If not specified, a test signing key is used.")
  parser.add_argument(metavar="input_file", dest='InputFile', help="specify the input filename")

  #
  # Parse command line arguments
  #
  args = parser.parse_args()

  if args.Decode:
    remove_signature(args.InputFile, args.OutputFile)
  elif args.Encode:
    prefix_signature(args.InputFile, args.OutputFile)
  else:
    raise Exception("Invalid command line argument (use either -d or -e)")


if __name__ == '__main__':
    main()