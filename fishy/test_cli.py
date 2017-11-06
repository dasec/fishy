import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from . import cli


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
UTILSDIR = os.path.join(THIS_DIR, os.pardir, 'utils')
IMAGEDIR = tempfile.mkdtemp()


class CaptureStdout(list):
    def __enter__(self):
        self._stdout = sys.stdout
        self._bytestream = io.BytesIO()
        sys.stdout = self._iow = io.BufferedWriter(self._bytestream)
        sys.stdout.buffer = self._iow2 = io.BufferedWriter(self._bytestream)
        return self

    def __exit__(self, *args):
        self._iow.seek(0)
        self._iow2.seek(0)
        self.extend(self._bytestream)
        del self._iow    # free up some memory
        del self._iow2    # free up some memory
        del self._bytestream
        sys.stdout = self._stdout


class TestCliFileSlack(unittest.TestCase):

    image_paths = [
        os.path.join(IMAGEDIR, 'testfs-fat12.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " " + UTILSDIR \
              + " " + IMAGEDIR + " '' true"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        # stderr=subprocess.PIPE,
                        shell=True)

    @classmethod
    def tearDownClass(cls):
        # remove created filesystem images
        shutil.rmtree(IMAGEDIR)

    def test_write_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        testfilename = os.path.basename(testfilepath)
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"' + testfilename + '", "metadata": {"clusters": ' \
                   + '[[3, 512, 18]]}}}, "module": "fat-file-slack"}'))
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliFileSlack.image_paths:
            # write metadata
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            self.assertEqual(metafcontent, expected)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliFileSlack.image_paths:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content
            args = ["fishy", "-d", img_path, "fileslack", "-r", "0", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with CaptureStdout() as output:
                cli.main()
            self.assertEqual(output[0].decode('utf-8'), teststring)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_clear_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliFileSlack.image_paths:
            # write something we want to clear
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # clear the written information
            args = ["fishy", "-d", img_path, "fileslack", "-c", "-m",
                    metadata_file]
            sys.argv = args
            cli.main()
            args = ["fishy", "-d", img_path, "fileslack", "-r", "0", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with CaptureStdout() as output:
                cli.main()
            expected = len(teststring.encode('utf-8')) * b'\x00'
            self.assertEqual(output[0], expected)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
