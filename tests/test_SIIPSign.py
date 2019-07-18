#!/usr/bin/env python

import sys
import os
import unittest
import subprocess
import shutil
import glob

SIIPSIGN = os.path.join('siipSign', 'SIIPSign.py')

class TestSIIPSign(unittest.TestCase):
	'''A set of integration test cases (for now)'''

	def setUp(self):
		'''Create required files'''
		pass

	def tearDown(self):
		'''Clean up generated files'''

		shutil.rmtree('extract', ignore_errors=True)
		files_to_clean = glob.glob(os.path.join('tests', 'signed.bin'))

		for f in files_to_clean:
			os.remove(f)

	def test_empty_args(self):
		'''Test empty args'''

		cmd = ['python', SIIPSIGN]
		with self.assertRaises(subprocess.CalledProcessError) as cm:
			subprocess.check_call(cmd)
		self.assertEqual(cm.exception.returncode, 2)

	def test_invalid_args(self):
		'''Test invalid args'''

		cmd = ['python', SIIPSIGN, 'build']
		with self.assertRaises(subprocess.CalledProcessError) as cm:
			subprocess.check_call(cmd)
		self.assertEqual(cm.exception.returncode, 2)

		cmd = ['python', SIIPSIGN, 'sign', '-s', 'sha_foo']
		with self.assertRaises(subprocess.CalledProcessError) as cm:
			subprocess.check_call(cmd)
		self.assertEqual(cm.exception.returncode, 2)

	def test_help(self):
		'''Test help message'''

		cmd = ['python', SIIPSIGN, '-h']
		subprocess.check_call(cmd)

	def test_version(self):
		'''Test version info'''
		cmd = ['python', SIIPSIGN, '-V']
		subprocess.check_call(cmd)

	def test_signing(self):
		'''Test signing'''

		hash_options = ['sha256', 'sha384', 'sha512']
		PLDFILE = os.path.join('tests', 'payload.bin')
		OUTFILE = os.path.join('tests', 'signed.bin')

		with open(PLDFILE, 'wb') as pld:
			pld.write(os.urandom(1024*1024))

		# Create a new test RSA key
		cmd = ['openssl', 'genrsa', '-out', 'test_key.pem', '2048']
		subprocess.check_call(cmd)

		# Get public key from test key
		cmd = ['openssl', 'rsa', '-pubout', '-in', 'test_key.pem', '-out', 'public_key.pem']
		subprocess.check_call(cmd)

		for hash_alg in hash_options:
			cmd = ['python', SIIPSIGN, 'sign', '-i', PLDFILE, '-o', OUTFILE,
			          '-k', 'test_key.pem', '-s', hash_alg]
			subprocess.check_call(cmd)

			cmd = ['python', SIIPSIGN, 'verify', '-i', OUTFILE,
			         '-p', 'public_key.pem', '-s', hash_alg]
			subprocess.check_call(cmd)

			cmd = ['python', SIIPSIGN, 'decompose', '-i', OUTFILE]
			subprocess.check_call(cmd)

	def test_key_size_too_small(self):
		'''Test with signing key with size smaller than 2048 bit'''

		PLDFILE = os.path.join('tests', 'payload.bin')
		OUTFILE = os.path.join('tests', 'signed.bin')

		with open(PLDFILE, 'wb') as pld:
			pld.write(os.urandom(1024*1024))

		# Create a new test RSA key
		cmd = ['openssl', 'genrsa', '-out', 'test_key.pem', '1024']
		subprocess.check_call(cmd)

		cmd = ['python', SIIPSIGN, 'sign', '-i', PLDFILE, '-o', OUTFILE,
		          '-k', 'test_key.pem', '-s', 'sha384']
		with self.assertRaises(subprocess.CalledProcessError) as cm:
			subprocess.check_call(cmd)
		self.assertEqual(cm.exception.returncode, 1)

	def test_signing_with_two_keys(self):
		'''Test signing with two keys'''

		hash_options = ['sha256', 'sha384', 'sha512']
		PLDFILE = os.path.join('tests', 'payload.bin')
		OUTFILE = os.path.join('tests', 'signed.bin')
		FKM_KEY = ('key1.pem', 'key1.pub.pem')
		PLD_KEY = ('key2.pem', 'key2.pub.pem')

		with open(PLDFILE, 'wb') as pld:
			pld.write(os.urandom(1024*1024))

		# Create test keys
		for priv, pub in [FKM_KEY, PLD_KEY]:
			cmd = ['openssl', 'genrsa', '-out', priv, '2048']
			subprocess.check_call(cmd)

			cmd = ['openssl', 'rsa', '-pubout', '-in', priv, '-out', pub]
			subprocess.check_call(cmd)

		for hash_alg in hash_options:
			cmd = ['python', SIIPSIGN, 'sign', '-i', PLDFILE + ',' + PLD_KEY[0],
			                                        '-o', OUTFILE,
			                                        '-k', FKM_KEY[0],
			                                        '-s', hash_alg]
			subprocess.check_call(cmd)

			cmd = ['python', SIIPSIGN, 'verify', '-i', OUTFILE + ',' + PLD_KEY[1],
			                                          '-p', FKM_KEY[1],
			                                          '-s', hash_alg]
			subprocess.check_call(cmd)

			cmd = ['python', SIIPSIGN, 'decompose', '-i', OUTFILE]
			subprocess.check_call(cmd)


if __name__ == '__main__':
	unittest.main()

