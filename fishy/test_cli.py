import unittest
import os
import subprocess
import sys
from . import cli
import sys
import io


this_dir = os.path.dirname(os.path.abspath(__file__))
utilsdir = os.path.join(this_dir, os.pardir, 'utils')


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        self._bytestream = io.BytesIO()
        sys.stdout = self._stringio = io.BufferedWriter(self._bytestream)
        sys.stdout.buffer = self._stringio2 = io.BufferedWriter(self._bytestream)
        return self
    def __exit__(self, *args):
        self._stringio.seek(0)
        self._stringio2.seek(0)
        self.extend(self._bytestream)
        del self._stringio    # free up some memory
        sys.stdout = self._stdout


class TestCliFileSlack(unittest.TestCase):

    image_paths = [
                    os.path.join(utilsdir, 'testfs-fat12.dd'),
                    os.path.join(utilsdir, 'testfs-fat16.dd'),
                    os.path.join(utilsdir, 'testfs-fat32.dd'),
                  ]

    @classmethod
    def setUpClass(cls):
        pass
        # regenerate test filesystems
        cmd = os.path.join(utilsdir, "create_testfs.sh") + " " + utilsdir
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, shell=True)


    def test_write_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = "/tmp/fishy-testfile.txt"
        metadata_file = "/tmp/test-metadata.json"
        expected = '{"version": 2, "files": {"0": {"uid": 0, "filename": ' \
                   + '"fishy-testfile.txt", "metadata": {"clusters": ' \
                   + '[[3, 512, 18]]}}}, "module": "fat-file-slack"}'
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

    def test_read_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = "/tmp/fishy-testfile.txt"
        metadata_file = "/tmp/test-metadata.json"
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
            with Capturing() as output:
                cli.main()
            self.assertEqual(output[0].decode('utf-8'), teststring)

    def test_clear_fileslack(self):
        teststring = "Small test for CLI"
        testfilepath = "/tmp/fishy-testfile.txt"
        metadata_file = "/tmp/test-metadata.json"
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
            with Capturing() as output:
                cli.main()
            expected = len(teststring.encode('utf-8')) * b'\x00'
            self.assertEqual(output[0], expected)
