#!/usr/bin/env python

import sys
import os
import unittest
import subprocess
import shutil
import glob

SIIPSIGN = os.path.join('scripts', 'siip_sign.py')


class TestSIIPSign(unittest.TestCase):
    '''A set of integration test cases (for now)'''

    def setUp(self):
        '''Create required files'''
        pass

    def tearDown(self):
        '''Clean up generated files'''

        shutil.rmtree('extract', ignore_errors=True)
        files_to_clean = glob.glob('key*.pem')
        files_to_clean.append('payload.bin')
        files_to_clean.append('signed.bin')
        files_to_clean.append('fkm.bin')

        for f in files_to_clean:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

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

    def test_signing_rsa2k(self):
        '''Test signing'''

        hash_options = ['sha256', 'sha384', 'sha512']
        pld_file = 'payload.bin'
        out_file = 'signed.bin'

        with open(pld_file, 'wb') as pld:
            pld.write(os.urandom(1024*1024))

        # Create a new test RSA key
        cmd = ['openssl', 'genrsa', '-out', 'key.pem', '2048']
        subprocess.check_call(cmd)

        # Get public key from test key
        cmd = ['openssl', 'rsa', '-pubout', '-in',
               'key.pem', '-out', 'key.pub.pem']
        subprocess.check_call(cmd)

        for hash_alg in hash_options:
            cmd = ['python', SIIPSIGN, 'sign', '-i', pld_file, '-o', out_file,
                   '-k', 'key.pem', '-s', hash_alg]
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'verify', '-i', out_file,
                   '-p', 'key.pub.pem', '-s', hash_alg]
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'decompose', '-i', out_file]
            subprocess.check_call(cmd)

    def test_signing_rsa3k(self):
        '''Test signing'''

        hash_options = ['sha256', 'sha384', 'sha512']
        pld_file = 'payload.bin'
        out_file = 'signed.bin'

        with open(pld_file, 'wb') as pld:
            pld.write(os.urandom(1024*1024))

        # Create a new test RSA key
        cmd = ['openssl', 'genrsa', '-out', 'key.pem', '3072']
        subprocess.check_call(cmd)

        # Get public key from test key
        cmd = ['openssl', 'rsa', '-pubout', '-in',
               'key.pem', '-out', 'key.pub.pem']
        subprocess.check_call(cmd)

        for hash_alg in hash_options:
            cmd = ['python', SIIPSIGN, 'sign', '-i', pld_file, '-o', out_file,
                   '-k', 'key.pem', '-s', hash_alg]
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'verify', '-i', out_file,
                   '-p', 'key.pub.pem', '-s', hash_alg]
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'decompose', '-i', out_file]
            subprocess.check_call(cmd)

    def test_key_size_too_small(self):
        '''Test with signing key with size smaller than 2048 bit'''

        pld_file = 'payload.bin'
        out_file = 'signed.bin'

        with open(pld_file, 'wb') as pld:
            pld.write(os.urandom(1024*1024))

        # Create a new test RSA key
        cmd = ['openssl', 'genrsa', '-out', 'key.pem', '1024']
        subprocess.check_call(cmd)

        cmd = ['python', SIIPSIGN, 'sign', '-i', pld_file, '-o', out_file,
               '-k', 'key.pem', '-s', 'sha384']
        with self.assertRaises(subprocess.CalledProcessError) as cm:
            subprocess.check_call(cmd)
        self.assertEqual(cm.exception.returncode, 1)

    def test_fkm_subcommand(self):
        '''Test FKM generation and verify subcommand'''

        hash_options = ['sha256', 'sha384', 'sha512']
        out_file = 'fkm_only.bin'
        fkm_key = ('key1.pem', 'key1.pub.pem')
        pld_key = ('key2.pem', 'key2.pub.pem')

        # Create test keys
        for priv, pub in [fkm_key, pld_key]:
            cmd = ['openssl', 'genrsa', '-out', priv, '3072']
            subprocess.check_call(cmd)

            cmd = ['openssl', 'rsa', '-pubout', '-in', priv, '-out', pub]
            subprocess.check_call(cmd)

        for hash_alg in hash_options:
            cmd = ['python', SIIPSIGN, 'fkmgen',
                                       '-k', fkm_key[0],
                                       '-p', pld_key[1],  # Use public key
                                       '-s', hash_alg,
                                       '-o', out_file]
            print(" ".join(cmd))
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'fkmcheck', '-i', out_file,
                                                   '-p', fkm_key[1],
                                                   '-t', pld_key[1]]  # pubkey
            subprocess.check_call(cmd)

            cmd = ['python', SIIPSIGN, 'decompose', '-i', out_file]
            subprocess.check_call(cmd)


if __name__ == '__main__':
    unittest.main()
