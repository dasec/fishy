# pylint: disable=missing-docstring
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


def tearDownModule():  # pylint: disable=invalid-name
    # remove created filesystem images
    shutil.rmtree(IMAGEDIR)


class CaptureStdout(list):
    def __enter__(self):
        self._stdout = sys.stdout  # pylint: disable=attribute-defined-outside-init
        self._bytestream = io.BytesIO()  # pylint: disable=attribute-defined-outside-init
        sys.stdout = self._iow = io.BufferedWriter(self._bytestream)  # pylint: disable=attribute-defined-outside-init
        sys.stdout.buffer = self._iow2 = io.BufferedWriter(self._bytestream)  # pylint: disable=attribute-defined-outside-init
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
        os.path.join(IMAGEDIR, 'testfs-fat12-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32-stable1.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
              + " -d " + IMAGEDIR + " -u -s '-stable1'"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_write_fileslack_from_file(self):
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

    def test_write_fileslack_from_stdin(self):
        teststring = "Small test for CLI"
        metadata_file = tempfile.NamedTemporaryFile().name
        expected = json.dumps(json.loads('{"version": 2, "files": {"0": ' \
                   + '{"uid": "0", "filename": ' \
                   + '"0", "metadata": {"clusters": ' \
                   + '[[3, 512, 18]]}}}, "module": "fat-file-slack"}'))
        for img_path in TestCliFileSlack.image_paths:
            # write metadata
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file]
            sys.argv = args
            with io.BufferedRandom(io.BytesIO()) as patch_buffer:
                # save real stdin before monkey pathing it
                real_stdin = sys.stdin
                sys.stdin = patch_buffer
                sys.stdin.buffer = patch_buffer
                sys.stdin.write(teststring.encode('utf-8'))
                patch_buffer.seek(0)
                cli.main()
                # restore real stdin
                sys.stdin = real_stdin
            # compare outputted metadata
            with open(metadata_file) as metaf:
                metafcontent = metaf.read()
            self.assertEqual(metafcontent, expected)
        # remove testfiles
        os.remove(metadata_file)

    def test_read_fileslack_stdout(self):
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
            args = ["fishy", "-d", img_path, "fileslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            # compare stdout output with string we gave as input
            with CaptureStdout() as output:
                cli.main()
            self.assertEqual(output[0].decode('utf-8'), teststring)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_fileslack_outfile(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        outfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliFileSlack.image_paths:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "fileslack", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content into file
            args = ["fishy", "-d", img_path, "fileslack", "-o", outfilepath,
                    "-m", metadata_file]
            sys.argv = args
            cli.main()
            with open(outfilepath, 'r') as outfile:
                result = outfile.read()
                self.assertEqual(result, teststring)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
        os.remove(outfilepath)

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
            args = ["fishy", "-d", img_path, "fileslack", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with CaptureStdout() as output:
                cli.main()
            expected = len(teststring.encode('utf-8')) * b'\x00'
            self.assertEqual(output[0], expected)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)


class TestCliClusterAllocation(unittest.TestCase):

    image_paths = [
        os.path.join(IMAGEDIR, 'testfs-fat12-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat16-stable1.dd'),
        os.path.join(IMAGEDIR, 'testfs-fat32-stable1.dd'),
        ]

    @classmethod
    def setUpClass(cls):
        # regenerate test filesystems
        cmd = os.path.join(UTILSDIR, "create_testfs.sh") + " -w " + UTILSDIR \
              + " -d " + IMAGEDIR + " -u -s '-stable1'"
        subprocess.call(cmd, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_write_from_file(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliClusterAllocation.image_paths:
            # write metadata
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # check if there is a file in metadata
            with open(metadata_file) as metaf:
                metafcontent = json.loads(metaf.read())
            filecount = len(metafcontent['files'])
            self.assertEqual(filecount, 1)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_write_from_stdin(self):
        teststring = "Small test for CLI"
        metadata_file = tempfile.NamedTemporaryFile().name
        for img_path in TestCliClusterAllocation.image_paths:
            # write metadata
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file]
            sys.argv = args
            with io.BufferedRandom(io.BytesIO()) as patch_buffer:
                # save real stdin before monkey pathing it
                real_stdin = sys.stdin
                sys.stdin = patch_buffer
                sys.stdin.buffer = patch_buffer
                sys.stdin.write(teststring.encode('utf-8'))
                patch_buffer.seek(0)
                cli.main()
                # restore real stdin
                sys.stdin = real_stdin
            # check if there is a file in metadata
            with open(metadata_file) as metaf:
                metafcontent = json.loads(metaf.read())
            filecount = len(metafcontent['files'])
            self.assertEqual(filecount, 1)
        # remove testfiles
        os.remove(metadata_file)

    def test_read_stdout(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliClusterAllocation.image_paths:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content
            args = ["fishy", "-d", img_path, "addcluster", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            # compare stdout output with string we gave as input
            with CaptureStdout() as output:
                cli.main()
            self.assertEqual(output[0].decode('utf-8'), teststring)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)

    def test_read_outfile(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        outfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliClusterAllocation.image_paths:
            # write someting we want to read
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # read written content into file
            args = ["fishy", "-d", img_path, "addcluster", "-o", outfilepath,
                    "-m", metadata_file]
            sys.argv = args
            cli.main()
            with open(outfilepath, 'r') as outfile:
                result = outfile.read()
                self.assertEqual(result, teststring)
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
        os.remove(outfilepath)

    def test_clear(self):
        teststring = "Small test for CLI"
        testfilepath = tempfile.NamedTemporaryFile().name
        metadata_file = tempfile.NamedTemporaryFile().name
        with open(testfilepath, 'w+') as testfile:
            testfile.write(teststring)
        for img_path in TestCliClusterAllocation.image_paths:
            # write something we want to clear
            args = ["fishy", "-d", img_path, "addcluster", "-w", "-d",
                    "another", "-m", metadata_file, testfilepath]
            sys.argv = args
            cli.main()
            # clear the written information
            args = ["fishy", "-d", img_path, "addcluster", "-c", "-m",
                    metadata_file]
            sys.argv = args
            cli.main()
            args = ["fishy", "-d", img_path, "addcluster", "-r", "-m",
                    metadata_file, testfilepath]
            sys.argv = args
            with self.assertRaises(Exception):
                cli.main()
        # remove testfiles
        os.remove(testfilepath)
        os.remove(metadata_file)
